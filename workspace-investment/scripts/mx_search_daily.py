# -*- coding: utf-8 -*-
"""MXSearch每日流水线 - 修复解析逻辑"""
import os
import sys
import json
import time
import sqlite3
import requests
import argparse
import subprocess
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ===================== 全局配置 =====================
INV = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
LOG_DIR = os.path.join(INV, 'logs', 'mx_search_daily')
STATS_FILE = os.path.join(LOG_DIR, 'stats.json')
TODAY_FILE = os.path.join(LOG_DIR, 'today.json')
POOL_FILE = os.path.join(INV, 'config', 'stock_pool.json')
DB_PATH = r'F:\market_data.db'
CHECKPOINT_FILE = os.path.join(LOG_DIR, 'checkpoint.json')
MX_SEARCH_SCRIPT = r'C:\Users\Administrator\AppData\Roaming\npm\node_modules\openclaw\skills\mx-search\mx_search.py'

os.makedirs(LOG_DIR, exist_ok=True)

# 关键词库（直接用in操作符匹配中文）
POSITIVE_KEYWORDS = [
    '增长', '提升', '突破', '创新', '合作', '战略', '扩产', '投产',
    '回购', '增持', '股权激励', '员工持股', '评级上调', '买入',
    '超预期', '订单', '中标', '签约', '供货', '量产', '发布',
    '分红', '派息', '业绩', '盈利', '扭亏', '复产', '复工',
    # 新增
    '预增', '扭亏为盈', '大幅上升', '大幅增长', '利好', '合同',
    '溢价', '要约收购', '增资', '扩充', '扩建', '新产线',
    '专项资金', '政府补贴', '补助', '税收优惠', '减免',
    '新产品', '新客户', '新市场', '海外', '出口', '市占率',
    '降价', '减费', '降本', '增效', '效率', '高增长',
    '自研', '国产替代', '龙头', '领先', '行业第一',
    '上调', '乐观', '看好', '推荐', '增持评级',
    '规划', '目标', '展望', '景气', '改善',
]
NEGATIVE_KEYWORDS = [
    '减持', '风险', '诉讼', '仲裁', '处罚', '立案', '调查',
    '亏损', '业绩下滑', '下调', '警告', '召回', '停产',
    '违约', '破产', '债务', '纠纷', '造假', '爆雷', 'ST',
    # 新增
    '预亏', '预减', '大幅下降', '大幅下滑', '恶化',
    '退市', '停牌', '暂停', '中止', '终止',
    '冻结', '查封', '扣押', '留置', '限制',
    '通报批评', '警示', '监管', '问询', '关注函',
    '利空', '暴跌', '跌停', '崩盘', '恐慌',
    '资金占用', '违规', '违法', '内幕', '操纵',
    '减值', '坏账', '担保', '关联', '质押',
]

# ===================== 工具函数 =====================
def get_key():
    return os.environ.get('MX_APIKEY') or ''

def extract_keywords(title, content=''):
    """直接用in匹配中文关键词"""
    text = title + ' ' + content
    pos_kw = [kw for kw in POSITIVE_KEYWORDS if kw in text]
    neg_kw = [kw for kw in NEGATIVE_KEYWORDS if kw in text]
    score = len(pos_kw) - len(neg_kw)
    return {
        'positive': pos_kw, 'negative': neg_kw, 'neutral': [],
        'score': score, 'has_positive': bool(pos_kw), 'has_negative': bool(neg_kw)
    }

def call_mx_search(query, timeout=25):
    """调用MX搜索（通过统一接口）"""
    from scripts.data_api import mx_search as api_mx_search
    return api_mx_search(query, timeout=timeout)

def parse_mx_text_result(text, stock_name, stock_code):
    """解析MX返回的文本格式结果"""
    if not text or '搜索结果' not in text:
        return None
    try:
        import re
        blocks = re.split(r'--- \d+\. ', text)
        if len(blocks) < 2:
            return None
        first = blocks[1].strip()
        lines = first.split('\n')
        if not lines:
            return None
        title = lines[0].strip().rstrip(' ---')
        date = ''
        info_type = ''
        for line in lines:
            m = re.search(r'日期:\s*(\S+)', line)
            if m: date = m.group(1)
            m = re.search(r'类型:\s*(\S+)', line)
            if m: info_type = m.group(1)
        content = ''
        date_found = False
        for line in lines:
            if '日期:' in line:
                date_found = True
                continue
            if date_found:
                content += line + ' '
        content = content.strip()[:500]
        keywords = extract_keywords(title, content)
        return {
            'code': stock_code,
            'name': stock_name,
            'title': title,
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'type': info_type.lower() if info_type else '',
            'score': keywords['score'],
            'has_positive': keywords['has_positive'],
            'has_negative': keywords['has_negative'],
            'keywords': keywords,
            'next_return': None
        }
    except Exception as e:
        print(f'  [ERR] 解析MX文本失败: {e}')
    return None

def parse_mx_result(result, stock_name, stock_code):
    """统一入口：支持文本和JSON"""
    if not result:
        return None
    if isinstance(result, str):
        return parse_mx_text_result(result, stock_name, stock_code)
    try:
        items = result.get('data', {}).get('data', {}).get('llmSearchResponse', {}).get('data', [])
        if not items:
            return None
        item = items[0]
        title = item.get('title', '')
        content = item.get('content', '')[:500]
        date = item.get('date', '')[:10]
        info_type = item.get('informationType', '').lower()
        keywords = extract_keywords(title, content)
        return {
            'code': stock_code, 'name': stock_name, 'title': title,
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'type': info_type, 'score': keywords['score'],
            'has_positive': keywords['has_positive'],
            'has_negative': keywords['has_negative'],
            'keywords': keywords, 'next_return': None
        }
    except Exception as e:
        print(f'  [ERR] 解析MX结果失败: {e}')
    return None

def load_pool():
    with open(POOL_FILE, encoding='utf-8') as f:
        data = json.load(f)
    stocks = []
    if isinstance(data, list):
        stocks = data
    elif isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                stocks.extend(v)
    seen = set()
    unique = []
    for s in stocks:
        code = s.get('code', s) if isinstance(s, dict) else s
        if code not in seen:
            seen.add(code)
            unique.append(s)
    return unique

def get_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {'offset': 0}

def save_checkpoint(offset):
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump({'offset': offset}, f)

def get_db_price(code, trade_date):
    mkt = 'sz' if code.startswith(('0', '3')) else 'sh'
    full_code = mkt + code
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT close FROM daily_k WHERE code=? AND date=? LIMIT 1", (full_code, trade_date)).fetchone()
    conn.close()
    return row[0] if row else None

def find_next_trading_day(code, from_date, max_days=10):
    mkt = 'sz' if code.startswith(('0', '3')) else 'sh'
    full_code = mkt + code
    conn = sqlite3.connect(DB_PATH)
    for i in range(1, max_days + 1):
        nd = (datetime.strptime(from_date, '%Y-%m-%d') + timedelta(days=i)).strftime('%Y-%m-%d')
        row = conn.execute("SELECT close FROM daily_k WHERE code=? AND date=? LIMIT 1", (full_code, nd)).fetchone()
        if row and row[0] and row[0] > 0:
            conn.close()
            return nd
    conn.close()
    return None

def get_tencent_price(code):
    mkt = 'sz' if code.startswith(('0', '3')) else 'sh'
    full_code = mkt + code
    url = f'https://qt.gtimg.cn/q={full_code}'
    try:
        r = requests.get(url, timeout=5)
        r.encoding = 'utf-8'
        fields = r.text.split('~')
        if len(fields) > 3:
            return float(fields[3])
    except:
        pass
    return None

# ===================== 采集阶段 =====================
def collect():
    print('=' * 50)
    print('MXSearch 每日采集')
    print('=' * 50)

    pool = load_pool()
    print(f'股票池: {len(pool)} 只')

    checkpoint = get_checkpoint()
    offset = checkpoint['offset']

    records = []
    success_count = 0

    for i in range(10):
        idx = (offset + i) % len(pool)
        stock = pool[idx]
        stock_name = stock.get('name', stock.get('stock_name', '')) if isinstance(stock, dict) else str(stock)
        stock_code = stock.get('code', stock.get('stock_code', '')) if isinstance(stock, dict) else str(stock)
        if not stock_name or not stock_code:
            continue
        print(f'\n[{i+1}/10] 搜索: {stock_name}({stock_code})')
        query = f'{stock_name} {stock_code} 最新公告 研报'
        result = call_mx_search(query)
        if result:
            record = parse_mx_result(result, stock_name, stock_code)
            if record:
                records.append(record)
                kw = record['keywords']
                print(f'  标题: {record["title"][:40]}...')
                print(f'  关键词: pos={kw["positive"]} neg={kw["negative"]}')
                print(f'  得分: {kw["score"]}')
                success_count += 1
        time.sleep(2)

    new_offset = (offset + 10) % len(pool)
    save_checkpoint(new_offset)

    output = {'records': records, 'collected': datetime.now().isoformat(), 'success_count': success_count}
    with open(TODAY_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\n完成: 成功{success_count}/10 条记录已保存到 today.json')
    return output

# ===================== 计算阶段 =====================
def calculate():
    print('=' * 50)
    print('MXSearch T+1 收益计算')
    print('=' * 50)

    if not os.path.exists(TODAY_FILE):
        print('[ERROR] today.json 不存在，请先运行 --collect')
        return

    with open(TODAY_FILE, encoding='utf-8') as f:
        today_data = json.load(f)

    records = today_data.get('records', [])
    if not records:
        print('[WARN] today.json 无记录')
        return

    collected_date_str = today_data.get('collected', '')[:10]
    print(f'采集日期: {collected_date_str}')
    print(f'待计算: {len(records)} 只')

    today_records = []
    for rec in records:
        code = rec.get('code', '')
        name = rec.get('name', '')
        search_date = rec.get('date', '')
        print(f'\n{name}({code}) 搜索日={search_date}')
        t_close = get_db_price(code, search_date)
        if not t_close:
            print(f'  [WARN] T日({search_date}) DB无数据，跳过')
            rec['next_return'] = None
            today_records.append(rec)
            continue
        t1_date = find_next_trading_day(code, search_date)
        t1_close = None
        if t1_date:
            t1_close = get_db_price(code, t1_date)
        if t1_close and t1_close > 0:
            ret = (t1_close - t_close) / t_close * 100
            print(f'  T日={t_close} T+1日={t1_close} 收益={ret:.2f}%')
            rec['next_return'] = round(ret, 4)
        else:
            real_price = get_tencent_price(code)
            if real_price and real_price > 0:
                ret = (real_price - t_close) / t_close * 100
                print(f'  T日={t_close} 实时={real_price} 收益={ret:.2f}%')
                rec['next_return'] = round(ret, 4)
            else:
                print(f'  [WARN] 无法获取T+1价格')
                rec['next_return'] = None
        today_records.append(rec)

    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, encoding='utf-8') as f:
            stats = json.load(f)
    else:
        stats = {'records': [], 'total': 0, 'last_updated': None}

    stats['records'].extend(today_records)
    stats['total'] = len(stats['records'])
    stats['last_updated'] = datetime.now().isoformat()

    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    valid = [r for r in today_records if r['next_return'] is not None]
    if valid:
        rets = [r['next_return'] for r in valid]
        avg = sum(rets) / len(rets)
        wins = sum(1 for r in rets if r > 0)
        print(f'\n=== 本批次统计 ===')
        print(f'有效样本: {len(valid)}/{len(today_records)}')
        print(f'平均收益: {avg:+.2f}%')
        print(f'胜率: {wins}/{len(valid)} = {wins/len(valid)*100:.1f}%')

    print(f'\nstats.json 已更新 (总计 {stats["total"]} 条记录)')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MXSearch每日流水线')
    parser.add_argument('--collect', action='store_true', help='采集阶段: 搜索10只股票关键词')
    parser.add_argument('--calculate', action='store_true', help='计算阶段: T+1收益计算')
    args = parser.parse_args()
    if args.collect:
        collect()
    elif args.calculate:
        calculate()
    else:
        parser.print_help()