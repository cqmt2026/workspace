# -*- coding: utf-8 -*-
"""
mx-search舆情回测模块
目标：用100次/天的API调用，摸清"公告/新闻关键词 → 次日涨跌"的规律

调用分配（5天 × 20次/天 = 100次）：
  每天：2只股票 × 3次搜索（公告/新闻/研报）× 3天窗口 + 2次板块 = 20次/天
  覆盖：10只代表性股票 × 5天历史窗口

代表股票池（主人自选230只中选10只，覆盖不同板块）：
  002236 大华股份    科技/AI
  300750 宁德时代    新能源
  600519 贵州茅台    消费
  688028 沃尔德      科创/高端制造
  002475 立讯精密    消费电子
  601012 隆基绿能    光伏
  300059 东方财富   金融科技
  600585 海螺水泥   建材
  301171 易点天下   互联网
  002050 三花智控   热管理

关键词体系：
  正面：业绩超预期、中标、产品突破、技术创新、产能扩张、订单增长
  负面：业绩下修、监管问询、减持、风险提示、诉讼、商誉减值
  中性：分红、回购、股权激励、高管变动
"""
import sys, os, winreg, json, time, sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# ─── APIKEY ───────────────────────────────────────────────
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
from mx_search import MXSearch
sys.path.insert(0, os.path.join(SKILLS, 'mx-data'))
from mx_data import MXData
import io

SEARCH = MXSearch()
MXDATA = MXData()

# ─── 全局配置 ───────────────────────────────────────────
DB = r'F:\market_data.db'
OUT_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\logs\mx_search_backtest')
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 代表股票池
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

# 关键词体系（扩展版）
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
NEUTRAL_KW  = [
    '分红', '回购', '股权激励', '高管变动', '担保', '更名',
    '发行债券', '吸收合并', '资产重组', '更名',
]

ALL_KW = POSITIVE_KW + NEGATIVE_KW + NEUTRAL_KW

# 搜索日期窗口（近5个交易日，往回推）
TRADE_DATES = [
    '2026-06-17', '2026-06-16', '2026-06-13',
    '2026-06-12', '2026-06-11',
]

# ─── 数据结构 ───────────────────────────────────────────
# 收集到的原始数据
RAW_DATA_FILE = OUT_DIR / 'raw_collected.json'
# 分析结果
ANALYSIS_FILE = OUT_DIR / 'keyword_analysis.json'

def load_raw():
    if RAW_DATA_FILE.exists():
        with open(RAW_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_raw(data):
    with open(RAW_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─── 工具函数 ───────────────────────────────────────────
def search_news(stock_name: str, info_type: str = None, retries=2):
    """搜索个股相关资讯，info_type: announcement/news/research"""
    query = stock_name
    for attempt in range(retries):
        try:
            r = SEARCH.search(query)
            if isinstance(r, dict) and r.get('success'):
                raw_results = r.get('data', {}).get('data', {}).get('llmSearchResponse', {}).get('data', [])
                if not isinstance(raw_results, list):
                    raw_results = []
                # 按informationType过滤
                if info_type:
                    type_map = {
                        'announcement': ['公告', '公告书', '报告书'],
                        'news': ['新闻', '资讯'],
                        'research': ['研报', '研究报告', '分析报告'],
                    }
                    allowed_types = type_map.get(info_type, [])
                    raw_results = [x for x in raw_results
                                   if any(t in x.get('informationType', '') for t in allowed_types)]
                return raw_results
        except Exception as e:
            print(f'    [搜索异常] {e}')
        time.sleep(1)
    return []

def extract_keywords(title: str, content: str = '') -> dict:
    """从标题+内容中精确提取关键词命中情况（整词匹配，避免子串误匹配）"""
    import re
    full_text = title + ' ' + content
    pos_hits = []
    neg_hits = []
    neu_hits = []

    def is_cjk(char):
        return '\u4e00' <= char <= '\u9fff'

    def whole_word_match(text, keyword):
        """精确匹配：关键词前后必须是非CJK字符或边界"""
        idx = text.find(keyword)
        while idx != -1:
            before = text[idx - 1] if idx > 0 else ' '
            after = text[idx + len(keyword)] if idx + len(keyword) < len(text) else ' '
            # 关键词前后不都是CJK字符 = 整词匹配
            if not (is_cjk(before) and is_cjk(after)):
                return True
            idx = text.find(keyword, idx + 1)
        return False

    for kw in POSITIVE_KW:
        if whole_word_match(full_text, kw):
            pos_hits.append(kw)
    for kw in NEGATIVE_KW:
        if whole_word_match(full_text, kw):
            neg_hits.append(kw)
    for kw in NEUTRAL_KW:
        if whole_word_match(full_text, kw):
            neu_hits.append(kw)

    return {
        'positive': pos_hits,
        'negative': neg_hits,
        'neutral': neu_hits,
        'score': len(pos_hits) - len(neg_hits),
        'has_positive': bool(pos_hits),
        'has_negative': bool(neg_hits),
    }

def get_kline(code: str, days: int = 10) -> list:
    """从本地DB获取近N日收盘价（代码格式: sz.XXXXXX 或 sh.XXXXXX）"""
    # 判断市场前缀
    if code.startswith('6') or code.startswith('5'):
        db_code = f'sh.{code}'
    elif code.startswith('00') or code.startswith('30'):
        db_code = f'sz.{code}'
    elif code.startswith('688'):
        db_code = f'sh.{code}'
    elif code.startswith('8') or code.startswith('4'):
        db_code = f'bj.{code}'
    else:
        db_code = code

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "SELECT date, close FROM daily_k WHERE code=? ORDER BY date DESC LIMIT ?",
        (db_code, days)
    )
    rows = cur.fetchall()
    conn.close()
    return [(d, c) for d, c in rows]  # [(date, close), ...]

def compute_next_ret_by_name(stock_name: str, ref_date: str) -> float:
    """通过mx-data API，用股票名获取历史K线，计算T日到T+1日收益率"""
    try:
        result = MXDATA.query(f'{stock_name}近10日每日收盘价')
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

        close_key = None
        for k, v in nm.items():
            if '收盘' in str(v):
                close_key = k
                break
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

        all_dates = sorted(date_price.keys(), reverse=True)  # 降序：最新→最旧
        if ref_date not in date_price:
            return None
        idx = all_dates.index(ref_date)
        if idx >= len(all_dates) - 1:
            return None
        next_date = all_dates[idx + 1]  # 降序排列中下一个=次日
        p_today = date_price[ref_date]
        p_next = date_price[next_date]
        if p_today > 0:
            return (p_next / p_today - 1) * 100
        return None
    except Exception as e:
        return None


def compute_next_ret(code: str, news_date: str) -> float:
    """兼容旧接口：根据code查本地DB；备用方案：尝试用code做股票名查询mx-data"""
    # 先试本地DB
    klines = get_kline(code, 15)
    if klines:
        dates = [k[0] for k in klines]
        if news_date in dates:
            idx = dates.index(news_date)
            if idx > 0 and idx < len(klines) - 1:
                today_close = klines[idx][1]
                next_close = klines[idx - 1][1]
                if today_close and today_close > 0:
                    return (next_close / today_close - 1) * 100
    # 备用：通过mx-data（用code作为股票名查询）
    return compute_next_ret_by_name(code, news_date)

# ─── 每日采集任务 ───────────────────────────────────────
def daily_collect(batch_id: int):
    """
    每批采集：2只股票 × 3次搜索(公告/新闻/研报) × 3天窗口
    batch_id从0开始（对应TRADE_DATES[0]为最新）
    """
    day_offset_start = batch_id * 2      # 每批覆盖2天
    day_offset_end   = day_offset_start + 2

    if day_offset_start >= len(TRADE_DATES):
        print(f'  [完成] 所有批次已采集完毕')
        return

    days_to_process = TRADE_DATES[day_offset_start:day_offset_end]
    stocks_this_batch = STOCK_POOL[batch_id % len(STOCK_POOL):][:2]  # 轮转取2只

    raw = load_raw()
    total_calls = 0

    print(f'\n===== 批次{batch_id+1} =====')
    print(f'  日期窗口: {days_to_process}')
    print(f'  股票: {[n for _,n in stocks_this_batch]}')

    for code, name in stocks_this_batch:
        print(f'\n  --- {code} {name} ---')
        for date in days_to_process:
            # 近7日搜索（包含该日期前后的新闻）
            search_date = date.replace('2026-', '').replace('-', '.')
            
            # 搜索所有资讯（1次调用拿全部，按type分类）
            all_results = search_news(name)
            total_calls += 1
            date_key = f"{code}_{date}"
            raw.setdefault(date_key, {'code': code, 'name': name, 'date': date, 'items': []})

            # 按informationType分组
            # NOTICE=公告 NEWS/INV_NEWS=新闻 REPORT=研报
            type_map = {
                'announcement': {'NOTICE'},
                'news': {'NEWS', 'INV_NEWS'},
                'research': {'REPORT'},
            }
            for info_type, allowed_types in type_map.items():
                type_results = [x for x in all_results if x.get('informationType', '') in allowed_types]
                for item in type_results[:3]:
                    title = item.get('title', '')
                    content = item.get('content', '')[:800]
                    item_date = item.get('date', '')
                    kw_info = extract_keywords(title, content)
                    raw[date_key]['items'].append({
                        'type': info_type,
                        'title': title,
                        'content_preview': content[:200],
                        'keywords': kw_info,
                        'item_date': item_date,
                        'info_type_raw': item.get('informationType', ''),
                    })
                    print(f'    [{date}] {info_type[:3]}: {title[:30]} | 得分={kw_info["score"]:+d} | 日期={item_date}')

            time.sleep(0.3)

    save_raw(raw)
    print(f'\n  本批调用: {total_calls}次 | 累计: {len(load_raw())}条记录')

# ─── 次日收益回溯 ──────────────────────────────────────
def attach_next_returns():
    """给每条记录挂上次日收益率"""
    raw = load_raw()
    for key, record in raw.items():
        code = record['code']
        date = record['date']
        ret = compute_next_ret(code, date)
        record['next_return'] = ret

    save_raw(raw)
    return raw

# ─── 关键词分析 ─────────────────────────────────────────
def analyze():
    """分析关键词与次日收益的相关性"""
    raw = load_raw()
    records = [v for v in raw.values() if v.get('next_return') is not None]

    print(f'\n===== 关键词分析 =====')
    print(f'有效记录: {len(records)}条')

    if not records:
        print('  数据不足，等待更多采集')
        return

    # 按关键词分桶
    def bucket(records, kw_list, field='has_positive'):
        if field == 'has_positive':
            return [r['next_return'] for r in records if r['items'] and any(
                item['keywords']['has_positive'] for item in r['items'])]
        elif field == 'has_negative':
            return [r['next_return'] for r in records if r['items'] and any(
                item['keywords']['has_negative'] for item in r['items'])]

    pos_records = [r for r in records if r['items'] and any(
        item['keywords']['has_positive'] for item in r['items'])]
    neg_records = [ r for r in records if r['items'] and any(
        item['keywords']['has_negative'] for item in r['items'])]
    clean_records = [r for r in records if r['items'] and not any(
        (item['keywords']['has_positive'] or item['keywords']['has_negative']) for item in r['items'])]

    import numpy as np
    print(f'\n{"分组":<20} {"样本":>6} {"均值":>8} {"胜率":>8}')
    print('-' * 50)

    all_rets = [r['next_return'] for r in records]
    all_wins = sum(1 for r in all_rets if r > 0)
    print(f'{"全部":<20} {len(all_rets):>6} {np.mean(all_rets):>+7.3f}% {all_wins/len(all_rets):>7.1%}')

    if pos_records:
        pr = [r['next_return'] for r in pos_records]
        pw = sum(1 for r in pr if r > 0)
        print(f'{"有正面关键词":<20} {len(pr):>6} {np.mean(pr):>+7.3f}% {pw/len(pr):>7.1%}')

    if neg_records:
        nr = [r['next_return'] for r in neg_records]
        nw = sum(1 for r in nr if r > 0)
        print(f'{"有负面关键词":<20} {len(nr):>6} {np.mean(nr):>+7.3f}% {nw/len(nr):>7.1%}')

    if clean_records:
        cr = [r['next_return'] for r in clean_records]
        cw = sum(1 for r in cr if r > 0)
        print(f'{"无明显信号":<20} {len(cr):>6} {np.mean(cr):>+7.3f}% {cw/len(cr):>7.1%}')

    # 逐关键词分析
    print(f'\n===== 逐关键词统计 =====')
    print(f'{"关键词":<20} {"出现":>6} {"均值":>8} {"胜率":>8}')
    print('-' * 50)

    for kw in ALL_KW:
        hits = []
        for r in records:
            for item in r.get('items', []):
                kw_dict = item.get('keywords', {})
                # 关键词存在 positive/negative/neutral 列表中
                all_hits = (kw_dict.get('positive', []) +
                            kw_dict.get('negative', []) +
                            kw_dict.get('neutral', []))
                if kw in all_hits:
                    hits.append(r['next_return'])
                    break
        if hits:
            import numpy as np
            wins = sum(1 for h in hits if h > 0)
            print(f'{kw:<20} {len(hits):>6} {np.mean(hits):>+7.3f}% {wins/len(hits):>7.1%}')

    # 保存
    result = {
        'total_records': len(records),
        'date': datetime.now().isoformat(),
        'all_mean': float(np.mean(all_rets)),
        'all_win_rate': float(all_wins / len(all_rets)),
    }
    with open(ANALYSIS_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'\n分析结果已保存: {ANALYSIS_FILE}')

# ─── 每日调用入口 ──────────────────────────────────────
if __name__ == '__main__':

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', type=int, default=0, help='批次ID（0~4，每批2只股票2天窗口）')
    parser.add_argument('--analyze', action='store_true', help='仅运行分析')
    parser.add_argument('--attach', action='store_true', help='仅挂载收益率')
    args = parser.parse_args()

    if args.analyze:
        attach_next_returns()
        analyze()
    elif args.attach:
        attach_next_returns()
    else:
        daily_collect(args.batch)
        print('\n  采集完成后运行: python mx_search_backtest.py --analyze')
