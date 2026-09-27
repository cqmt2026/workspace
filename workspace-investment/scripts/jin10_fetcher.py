# -*- coding: utf-8 -*-
"""
金十数据采集器 (Jin10 Fetcher)
=============================
定时抓取金十实时快讯，作为新闻归因和决策日报的补充信号源。

不需要VIP，免费接口可抓取最新快讯。
每30分钟运行一次，存到本地JSON供其他脚本使用。

用法：
  python jin10_fetcher.py              # 抓取并保存
  python jin10_fetcher.py --print      # 只打印不保存
  python jin10_fetcher.py --filter 高测  # 搜索关键词
"""
import sys, os, json, urllib.request, re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORK_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
OUT_DIR = WORK_DIR / 'out_data'
os.makedirs(OUT_DIR, exist_ok=True)

# 已知的关键词映射（A股常用）
STOCK_KEYWORDS = {
    '高测股份': 'sh688556',
    '钢研高纳': 'sz300034',
    '中芯国际': 'sh688981',
    '兆易创新': 'sh603986',
    '澜起科技': 'sh688008',
    '宁德时代': 'sz300750',
    '贵州茅台': 'sh600519',
    '腾讯': 'TCEHY',
    '阿里巴巴': 'BABA',
}


def fetch_flash(max_items: int = 50) -> List[Dict]:
    """从金十API抓取最新快讯"""
    ts = int(datetime.now().timestamp() * 1000)
    url = f'https://flash-api.jin10.com/get_flash_list?channel=-8200&vip=1&max_time=&_={ts}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.jin10.com/',
        'x-app-id': 'bVBF4FyRTn5NJF5n',
        'x-version': '1.0.0',
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode('utf-8'))
        items = data.get('data', [])
        if not items:
            return []
        return items[:max_items]
    except Exception as e:
        return []


def clean_content(raw: str) -> str:
    """去除HTML标签和多余空格"""
    text = re.sub(r'<[^>]+>', '', raw)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def classify_flash(item: Dict) -> str:
    """分类快讯类型

    返回: 财报预告 / 机构观点 / 市场快讯 / 行业动态 / 宏观事件
    """
    content = clean_content(item.get('data', {}).get('content', ''))
    if '预计' in content and ('净利润' in content or '营收' in content):
        return '财报预告'
    if any(kw in content for kw in ['分析师', '机构', '预计', '看好', '展望', '评级']):
        return '机构观点'
    if any(kw in content for kw in ['收评', '开盘', '收盘', '涨', '跌', '指数']):
        return '市场快讯'
    if any(kw in content for kw in ['行业', '产业链', '产能', '订单', '需求']):
        return '行业动态'
    if any(kw in content for kw in ['美联储', '加息', '降息', '央行', 'CPI', 'GDP', '失业']):
        return '宏观事件'
    if any(kw in content for kw in ['战争', '冲突', '制裁', '谈判', '地缘']):
        return '地缘政治'
    return '其他'


def extract_stock_mentions(content: str) -> List[str]:
    """从内容中提取提到的股票"""
    mentioned = []
    for name, code in STOCK_KEYWORDS.items():
        if name in content:
            mentioned.append(f'{name}({code})')
    # 尝试提取A股代码格式（6位数字）
    codes = re.findall(r'\b(\d{6})\b', content)
    for c in codes:
        if c.startswith('6') or c.startswith('68'):
            mentioned.append(f'sh{c}')
        elif c.startswith('0') or c.startswith('3'):
            mentioned.append(f'sz{c}')
    return mentioned


def run_fetch(print_only: bool = False) -> List[Dict]:
    """抓取并处理快讯"""
    items = fetch_flash()
    if not items:
        print('抓取失败或无数据')
        return []

    processed = []
    for item in items:
        raw_time = item.get('time', '')
        raw_content = item.get('data', {}).get('content', '')
        content = clean_content(raw_content)
        if not content:
            continue

        processed.append({
            'time': raw_time,
            'content': content,
            'type': classify_flash(item),
            'stocks': extract_stock_mentions(content),
        })

    if print_only:
        # 按类型分组打印
        by_type = {}
        for p in processed:
            t = p['type']
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(p)

        for t, items in sorted(by_type.items()):
            print(f'\n[{t}] ({len(items)}条)')
            for p in items[:5]:
                print(f'  [{p["time"]}] {p["content"][:100]}')
                if p['stocks']:
                    print(f'    → 涉及: {", ".join(p["stocks"])}')
                if len(items) > 5:
                    print(f'  ... 还有{len(items)-5}条')
    else:
        # 保存到文件
        today = datetime.now().strftime('%Y-%m-%d')
        now = datetime.now().strftime('%H:%M')
        cache_path = OUT_DIR / f'jin10_flash_{today}.json'

        # 合并已有数据
        existing = []
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)

        # 去重（按content去重）
        existing_contents = {e['content'] for e in existing}
        new_items = [p for p in processed if p['content'] not in existing_contents]

        all_items = existing + new_items
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(all_items, f, ensure_ascii=False, indent=2)

        print(f'抓取: {len(processed)}条, 新增: {len(new_items)}条, 总计: {len(all_items)}条')
        print(f'已保存: {cache_path}')

        # 也保存最新（供news_pulse等脚本使用）
        latest_path = OUT_DIR / 'jin10_flash_latest.json'
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)

    return processed


def search_keyword(keyword: str) -> List[Dict]:
    """搜索快讯中的关键词"""
    today = datetime.now().strftime('%Y-%m-%d')
    cache_path = OUT_DIR / f'jin10_flash_{today}.json'

    if not cache_path.exists():
        print('今日无缓存数据，先抓取...')
        run_fetch()

    with open(cache_path, 'r', encoding='utf-8') as f:
        items = json.load(f)

    results = [p for p in items if keyword in p['content']]
    return results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='金十数据采集')
    parser.add_argument('--print', action='store_true', help='只打印不保存')
    parser.add_argument('--filter', type=str, help='搜索关键词')
    args = parser.parse_args()

    if args.filter:
        results = search_keyword(args.filter)
        if results:
            print(f'找到 {len(results)} 条相关快讯:')
            for r in results[:10]:
                print(f'  [{r["time"]}] {r["content"][:150]}')
        else:
            print(f'未找到包含"{args.filter}"的快讯')
    else:
        run_fetch(print_only=args.print)