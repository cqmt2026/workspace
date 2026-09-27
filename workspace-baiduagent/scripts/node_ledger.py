# -*- coding: utf-8 -*-
"""
数据获取节点台账 - 避免重复和遗漏
记录每次抓取：平台/行业/关键词/新增/去重/状态
"""
import json, os, sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

# 台账文件
LEDGER_FILE = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\node_ledger.json'

def load_ledger():
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {'records': []}

def add_record(channel, industry, keywords, added, deduped, note=''):
    ledger = load_ledger()
    record = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time': datetime.now().strftime('%H:%M'),
        'channel': channel,
        'industry': industry,
        'keywords': keywords,
        'added': added,
        'deduped': deduped,
        'note': note,
    }
    ledger['records'].append(record)
    with open(LEDGER_FILE, 'w', encoding='utf-8') as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)
    return record

def show_ledger():
    ledger = load_ledger()
    records = ledger['records']
    if not records:
        print("台账为空")
        return
    print("=" * 70)
    print("【数据获取节点台账】")
    print("=" * 70)
    print(f"{'日期':<12}{'渠道':<10}{'行业':<14}{'新增':>6}{'去重':>6}  备注")
    print("-" * 70)
    for r in records:
        ch = r.get('channel', r.get('platform', ''))
        print(f"{r['date']} {r['time']}  {ch:<10}{r['industry']:<14}{r['added']:>6}{r['deduped']:>6}  {r['note']}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'show':
        show_ledger()
    else:
        show_ledger()
