# -*- coding: utf-8 -*-
"""
mx-search每日采集流水线
每天00:40运行 → 采集当天市场资讯
每天09:05运行 → 计算前一日资讯对应的T+1收益

API消耗：每天4次搜索 + 每只股票1次mx-data ≈ 6次/天
"""
import sys, os, winreg, json, time, sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# ─── APIKEY ───────────────────────────────────────────
key = None
for hive, path in [
    (winreg.HKEY_CURRENT_USER, r'Environment'),
    (winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'),
]:
    try:
        with winreg.OpenKey(hive, path) as h:
            key, _ = winreg.QueryValueEx(h, 'MX_APIKEY')
            if key: break
    except FileNotFoundError:
        pass
os.environ['MX_APIKEY'] = key or ''

SKILLS = r'C:\Users\Administrator\AppData\Roaming\npm\node_modules\openclaw\skills'
sys.path.insert(0, os.path.join(SKILLS, 'mx-search'))
sys.path.insert(0, os.path.join(SKILLS, 'mx-data'))
from mx_search import MXSearch
from mx_data import MXData
import io

SEARCH = MXSearch()
MXDATA = MXData()

OUT_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\logs\mx_search_daily')
OUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY_FILE = OUT_DIR / 'today.json'
STATS_FILE = OUT_DIR / 'stats.json'

# 代表股票池（分散板块）
STOCK_POOL = [
    ('002236', '大华股份'),
    ('300750', '宁德时代'),
    ('600519', '贵州茅台'),
    ('688028', '沃尔德'),
    ('002475', '立讯精密'),
    ('601012', '隆基绿能'),
    ('300059', '东方财富'),
    ('600585', '海螺水泥'),
    ('301171', '易点天下'),
    ('002050', '三花智控'),
]

POSITIVE_KW = [
    '业绩超预期', '中标', '产品突破', '技术创新', '产能扩张', '订单增长',
    '业绩预增', '净利润增长', '评级上调', '信用评级', '增持', '回购',
    '复产', '扩产', '员工持股', '股权激励', '战略合作', '全球领先',
    '订单饱满', '供货', '首发', '独家', '打破垄断', '填补空白',
    '营业收入增长', '利润增长', '市场份额', '突破', '增长', '提升',
]
NEGATIVE_KW = [
    '业绩下修', '监管问询', '减持', '风险提示', '诉讼', '商誉减值',
    '业绩预减', '净利润下降', '被立案', '召回', '造假', '停产',
    '亏损', '债务风险', '流动性紧张', '违规', '处罚', '立案调查',
    '竞争加剧', '价格战', '毛利率下降', '存货跌价', '应收款恶化',
    '大幅亏损', '持续亏损', '终止', '取消', '下降', '减少',
]
NEUTRAL_KW = ['分红', '回购', '股权激励', '高管变动', '担保', '更名',
               '发行债券', '吸收合并', '资产重组']

ALL_KW = POSITIVE_KW + NEGATIVE_KW + NEUTRAL_KW

# ─── 关键词提取 ────────────────────────────────────────
def is_cjk(char):
    return '\u4e00' <= char <= '\u9fff'

def whole_word_match(text, keyword):
    idx = text.find(keyword)
    while idx != -1:
        before = text[idx - 1] if idx > 0 else ' '
        after = text[idx + len(keyword)] if idx + len(keyword) < len(text) else ' '
        if not (is_cjk(before) and is_cjk(after)):
            return True
        idx = text.find(keyword, idx + 1)
    return False

def extract_keywords(title, content=''):
    full = title + ' ' + content
    pos = [kw for kw in POSITIVE_KW if whole_word_match(full, kw)]
    neg = [kw for kw in NEGATIVE_KW if whole_word_match(full, kw)]
    neu = [kw for kw in NEUTRAL_KW if whole_word_match(full, kw)]
    return {'positive': pos, 'negative': neg, 'neutral': neu,
            'score': len(pos) - len(neg),
            'has_positive': bool(pos), 'has_negative': bool(neg)}

# ─── 搜索单只股票 ─────────────────────────────────────
def search_stock(name, code):
    r = SEARCH.search(name)
    if not isinstance(r, dict) or not r.get('success'):
        return []
    results = r.get('data', {}).get('data', {}).get('llmSearchResponse', {}).get('data', [])
    if not isinstance(results, list):
        return []

    records = []
    for item in results:
        info_type = item.get('informationType', '')
        title = item.get('title', '')
        content = item.get('content', '')[:800]
        item_date_str = item.get('date', '')

        # 解析日期：'2026-06-18 17:24:22' -> '2026-06-18'
        item_date = item_date_str.split(' ')[0] if item_date_str else ''

        # 类型归类
        if info_type == 'NOTICE':
            itype = 'ann'
        elif info_type in ('NEWS', 'INV_NEWS'):
            itype = 'news'
        elif info_type == 'REPORT':
            itype = 'research'
        else:
            itype = 'other'

        kw_info = extract_keywords(title, content)
        records.append({
            'code': code, 'name': name,
            'title': title, 'content_preview': content[:200],
            'type': itype, 'date': item_date,
            'info_type': info_type,
            'keywords': kw_info,
            'score': kw_info['score'],
            'has_positive': kw_info['has_positive'],
            'has_negative': kw_info['has_negative'],
            'collected_at': datetime.now().isoformat(),
        })
    return records

# ─── 计算单只股票收益率 ────────────────────────────────
def compute_return(name, ref_date):
    try:
        result = MXDATA.query(f'{name}近10日每日收盘价')
        if not isinstance(result, dict):
            return None
        d = result.get('data', {}).get('data', {})
        sds = d.get('searchDataResultDTO', {})
        tables = sds.get('dataTableDTOList', [])
        if not tables:
            return None
        t = tables[0]
        tbl = t.get('table', {})
        nm = t.get('nameMap', {})
        head = tbl.get('headName', [])

        close_key = next((k for k, v in nm.items() if '收盘' in str(v)), None)
        if not close_key or close_key not in tbl:
            return None

        prices_raw = tbl.get(close_key, [])
        date_price = {}
        for i, h in enumerate(head):
            date_str = str(h).split('(')[0].strip()
            if i < len(prices_raw):
                try:
                    date_price[date_str] = float(str(prices_raw[i]).replace('元', '').replace(',', ''))
                except:
                    pass

        sorted_dates = sorted(date_price.keys(), reverse=True)
        if ref_date not in date_price:
            return None
        idx = sorted_dates.index(ref_date)
        if idx >= len(sorted_dates) - 1:
            return None
        next_date = sorted_dates[idx + 1]
        p_today = date_price[ref_date]
        p_next = date_price[next_date]
        if p_today > 0:
            return round((p_next / p_today - 1) * 100, 4)
        return None
    except Exception:
        return None

# ─── 采集今日资讯 ─────────────────────────────────────
def collect_today():
    """采集当天全市场+重点股票资讯，存入today.json"""
    print('===== 每日采集 =====')

    all_records = []

    # 对每只代表股票搜索
    for code, name in STOCK_POOL:
        print(f'  搜索: {name}...', end='', flush=True)
        items = search_stock(name, code)
        print(f' {len(items)}条')
        all_records.extend(items)
        time.sleep(0.5)

    # 保存
    with open(TODAY_FILE, 'w', encoding='utf-8') as f:
        json.dump({'records': all_records, 'collected': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
    print(f'  共采集 {len(all_records)} 条资讯')
    print(f'  正面信号: {sum(1 for r in all_records if r["has_positive"])} 条')
    print(f'  负面信号: {sum(1 for r in all_records if r["has_negative"])} 条')
    print(f'  保存: {TODAY_FILE}')

# ─── 计算T+1收益 ──────────────────────────────────────
def compute_returns_yesterday():
    """用昨天采集的today.json数据，计算每条资讯对应次日的收益率"""
    if not TODAY_FILE.exists():
        print('[计算收益] 今日无采集数据，跳过')
        return

    with open(TODAY_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    records = data.get('records', [])
    if not records:
        print('[计算收益] 无资讯记录')
        return

    print('===== 计算T+1收益 =====')
    print(f'  待处理: {len(records)} 条')

    # 按股票分组去重（同一股票同一天取score最高的1条）
    best_per_stock_day = {}
    for r in records:
        key = (r['code'], r['date'])
        if key not in best_per_stock_day or r['score'] > best_per_stock_day[key]['score']:
            best_per_stock_day[key] = r

    unique_records = list(best_per_stock_day.values())
    print(f'  去重后: {len(unique_records)} 条')

    stats = load_stats()
    for r in unique_records:
        ref_date = r['date']
        if not ref_date:
            continue
        ret = compute_return(r['name'], ref_date)
        if ret is not None:
            r['next_return'] = ret
            stats['records'].append({
                'code': r['code'], 'name': r['name'],
                'title': r['title'][:50],
                'date': ref_date,
                'type': r['type'],
                'score': r['score'],
                'has_positive': r['has_positive'],
                'has_negative': r['has_negative'],
                'next_return': ret,
                'keywords': r['keywords'],
            })
            print(f'  {r["code"]} {r["date"]}: score={r["score"]:>+2} ret={ret:>+7.3f}%')
        time.sleep(0.3)

    save_stats(stats)
    print(f'\n  累计: {stats["total"]} 条有效记录')

    # 打印简要分析
    do_analysis(stats['records'])

# ─── 分析 ─────────────────────────────────────────────
def do_analysis(records):
    import numpy as np
    rets = [r['next_return'] for r in records if r.get('next_return') is not None]
    if not rets:
        print('  暂无有效收益数据')
        return

    pos = [r for r in records if r.get('has_positive')]
    neg = [r for r in records if r.get('has_negative')]
    clean = [r for r in records if not r.get('has_positive') and not r.get('has_negative')]

    print(f'\n===== 累计分析（{len(records)}条）=====')
    print(f'{"分组":<20} {"样本":>5} {"均值":>8} {"胜率":>8}')
    print('-' * 48)

    def win_rate(rlist):
        rets2 = [r['next_return'] for r in rlist if r.get('next_return') is not None]
        if not rets2:
            return 0, 0
        return np.mean(rets2), sum(1 for x in rets2 if x > 0) / len(rets2)

    m, w = win_rate(records)
    print(f'{"全部":<20} {len(rets):>5} {m:>+7.3f}% {w:>7.1%}')
    if pos:
        m, w = win_rate(pos)
        print(f'{"有正面关键词":<20} {len(pos):>5} {m:>+7.3f}% {w:>7.1%}')
    if neg:
        m, w = win_rate(neg)
        print(f'{"有负面关键词":<20} {len(neg):>5} {m:>+7.3f}% {w:>7.1%}')
    if clean:
        m, w = win_rate(clean)
        print(f'{"无明显信号":<20} {len(clean):>5} {m:>+7.3f}% {w:>7.1%}')

# ─── 统计存储 ─────────────────────────────────────────
def load_stats():
    if STATS_FILE.exists():
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    return {'records': [], 'total': 0}

def save_stats(stats):
    stats['total'] = len([r for r in stats['records'] if r.get('next_return') is not None])
    stats['last_updated'] = datetime.now().isoformat()
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

# ─── 入口 ─────────────────────────────────────────────
if __name__ == '__main__':

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--collect', action='store_true', help='采集今日资讯')
    parser.add_argument('--compute', action='store_true', help='计算T+1收益（用today.json）')
    parser.add_argument('--analyze', action='store_true', help='仅打印分析')
    args = parser.parse_args()

    if args.analyze:
        stats = load_stats()
        do_analysis(stats['records'])
    elif args.compute:
        compute_returns_yesterday()
    elif args.collect:
        collect_today()
    else:
        # 默认：采集 + 计算（采集今天，计算昨天的today.json）
        collect_today()
        compute_returns_yesterday()
