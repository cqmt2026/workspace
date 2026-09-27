#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
商业航天每日分析报告 - 直接执行版
使用 Wind CLI + mx-search 获取数据并生成报告
"""

import sys
import os
import json
import subprocess
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

WIND_DIR = os.path.expanduser('~/.agents/skills/wind-mcp-skill')
MX_DIR = os.path.join(os.environ.get('APPDATA', ''), '..', 'Roaming', 'npm',
                       'node_modules', 'openclaw', 'skills', 'mx-search')
WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace'
OUT_DIR = os.path.join(WORKSPACE, 'out_data')
os.makedirs(OUT_DIR, exist_ok=True)

now = datetime.now()
trading_date = now.strftime('%Y%m%d')
report_date_str = now.strftime('%Y年%m月%d日')

results = {
    'sector': [],
    'stocks': [],
    'news': [],
    'financial': [],
    'errors': []
}


def wind_call(stype, tool, params):
    if not os.path.exists(WIND_DIR):
        results['errors'].append(f'Wind dir not found: {WIND_DIR}')
        return None
    try:
        r = subprocess.run(
            ['node', 'scripts/cli.mjs', 'call', stype, tool,
             json.dumps(params, ensure_ascii=False)],
            capture_output=True, text=True, timeout=30,
            cwd=WIND_DIR, encoding='utf-8', errors='replace'
        )
        if r.returncode == 0:
            return r.stdout[:2000]
        else:
            err = (r.stdout or r.stderr or '')[:500]
            results['errors'].append(f'{stype}/{tool}: {err}')
            return None
    except Exception as e:
        results['errors'].append(f'{stype}/{tool}: {e}')
        return None


def mx_search(query):
    if not os.path.exists(MX_DIR):
        return None
    mx_py = os.path.join(MX_DIR, 'mx_search.py')
    if not os.path.exists(mx_py):
        return None
    try:
        r = subprocess.run(
            [sys.executable, mx_py, query],
            capture_output=True, text=True, timeout=30,
            encoding='utf-8', errors='replace'
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout[:1500]
    except Exception:
        pass
    return None


def extract_wind_text(data_str):
    """Extract text from Wind CLI JSON output."""
    if not data_str or data_str == '数据获取失败':
        return data_str or '数据获取失败'
    try:
        d = json.loads(data_str)
        if isinstance(d, dict) and 'content' in d:
            texts = []
            for c in d['content']:
                if isinstance(c, dict) and 'text' in c:
                    t = c['text'].strip()
                    if t:
                        texts.append(t)
            if texts:
                return '\n    '.join(texts)
        return str(d)[:500]
    except json.JSONDecodeError:
        return data_str.strip()[:500]


print('=' * 60)
print('商业航天每日分析报告 - 数据采集')
print(f'日期: {report_date_str}')
print('=' * 60)

# ========== 1. 板块指数 ==========
print('\n[1/5] 获取板块指数行情...')
sys.stdout.flush()

# 航天军工指数
r = wind_call('index_data', 'get_index_price_indicators', {
    'windcode': '886031.WI',
    'indexes': '最新成交价,涨跌幅,成交额,上涨家数,下跌家数'
})
if r:
    results['sector'].append(('航天军工指数(886031.WI)', r))
    print('  ✓ 航天军工指数')
else:
    results['sector'].append(('航天军工指数(886031.WI)', '数据获取失败'))
    print('  ✗ 航天军工指数')

# 卫星导航指数
r = wind_call('index_data', 'get_index_price_indicators', {
    'windcode': '886066.WI',
    'indexes': '最新成交价,涨跌幅,成交额'
})
if r:
    results['sector'].append(('卫星导航指数(886066.WI)', r))
    print('  ✓ 卫星导航指数')
else:
    print('  ✗ 卫星导航指数')

# 航空航天概念板块
r = wind_call('index_data', 'get_index_price_indicators', {
    'windcode': '884150.WI',
    'indexes': '最新成交价,涨跌幅,成交额'
})
if r:
    results['sector'].append(('航空航天概念(884150.WI)', r))
    print('  ✓ 航空航天概念')
else:
    print('  ✗ 航空航天概念')

# ========== 2. 重点股票行情 ==========
print('\n[2/5] 获取重点股票行情...')
sys.stdout.flush()

key_stocks = [
    ('中航西飞', '000768'),
    ('航发动力', '600893'),
    ('中航沈飞', '600760'),
    ('中航光电', '002179'),
    ('西部超导', '688122'),
    ('光威复材', '300699'),
    ('睿创微纳', '688002'),
    ('中国卫星', '600118'),
    ('航天电子', '600879'),
]

for name, code in key_stocks:
    r = wind_call('stock_data', 'get_stock_price_indicators', {
        'windcode': code,
        'indexes': '最新成交价,涨跌幅,成交额,换手率'
    })
    results['stocks'].append((name, code, r))
    print(f'  {name}({code})...', end='')
    print(' ✓' if r else ' ✗')
    sys.stdout.flush()

# ========== 3. 新闻资讯 ==========
print('\n[3/5] 获取商业航天新闻...')
sys.stdout.flush()

news_queries = [
    ('商业航天综合', '商业航天 最新消息 政策 2026年7月'),
    ('卫星互联网/火箭', '卫星互联网 火箭发射 低轨卫星 2026年7月'),
    ('航天产业政策', '航天产业 政策利好 发展规划 2026'),
]

for label, q in news_queries:
    r = mx_search(q)
    results['news'].append((label, r))
    print(f'  {label}...', end='')
    print(' ✓' if r else ' ✗')
    sys.stdout.flush()

# ========== 4. 财务数据 ==========
print('\n[4/5] 获取财务数据...')
sys.stdout.flush()

fin_stocks = ['中航西飞', '航发动力', '中航沈飞', '西部超导']
for name in fin_stocks:
    r = wind_call('stock_data', 'get_stock_fundamentals', {
        'question': f'{name} 2024年净利润 营收 增长率',
        'lang': '中文'
    })
    results['financial'].append((name, r))
    print(f'  {name}...', end='')
    print(' ✓' if r else ' ✗')
    sys.stdout.flush()

# ========== 5. 生成报告 ==========
print('\n[5/5] 生成报告...')
sys.stdout.flush()

lines = []
lines.append('=' * 65)
lines.append(f'  商业航天每日分析报告')
lines.append(f'  报告日期: {report_date_str} (交易日: {trading_date})')
lines.append(f'  生成时间: {now.strftime("%H:%M")}')
lines.append('=' * 65)
lines.append('')

# Section 1: Sector
lines.append('一、商业航天板块行情概览')
lines.append('-' * 40)
for name, data in results['sector']:
    lines.append(f'\n  【{name}】')
    text = extract_wind_text(data)
    lines.append(f'    {text}')

lines.append('')
lines.append('二、重点股票行情')
lines.append('-' * 40)
for name, code, data in results['stocks']:
    text = extract_wind_text(data)
    lines.append(f'\n  【{name}({code})】')
    lines.append(f'    {text}')

lines.append('')
lines.append('三、商业航天新闻与政策')
lines.append('-' * 40)
for source, data in results['news']:
    lines.append(f'\n  【{source}】')
    if data:
        for line in data.strip().split('\n'):
            line = line.strip()
            if line:
                lines.append(f'  {line}')
    else:
        lines.append(f'  [无法获取资讯]')

lines.append('')
lines.append('四、重点公司财务摘要')
lines.append('-' * 40)
for name, data in results['financial']:
    text = extract_wind_text(data)
    lines.append(f'\n  【{name}】')
    lines.append(f'    {text}')

if results['errors']:
    lines.append('')
    lines.append('五、数据获取说明')
    lines.append('-' * 40)
    for e in results['errors'][:10]:
        lines.append(f'  - {e[:120]}')

lines.append('')
lines.append('=' * 65)
lines.append('免责声明: 本报告由自动化工具生成，仅供参考，不构成投资建议。')
lines.append(f'生成时间: {now.strftime("%Y-%m-%d %H:%M:%S")}')
lines.append('=' * 65)

report_text = '\n'.join(lines)
out_file = os.path.join(OUT_DIR, f'aero_daily_{trading_date}.txt')
with open(out_file, 'w', encoding='utf-8') as f:
    f.write(report_text)

print(f'\n[保存] {out_file}')
print(f'[大小] {len(report_text)} 字符')

# Also print the report
print('\n' + '=' * 60)
print('报告内容:')
print('=' * 60)
print(report_text)
