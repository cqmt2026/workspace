# -*- coding: utf-8 -*-
"""多渠道数据统一管理 - 完整版（32渠道）"""
import json, os, sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')

LEDGER_FILE = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\multi_channel_ledger.json'

def load_ledger():
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {"channels": {}, "coverage_summary": {}}

def get_channel_status():
    ledger = load_ledger()
    channels = ledger.get('channels', {})
    
    print("=" * 78)
    print("【多渠道数据统一管理面板】- 32个渠道全景")
    print("=" * 78)
    
    # 按状态分组
    groups = {'✅': [], '⚠️': [], '❌': [], '⏳': [], '❓': []}
    
    for name, info in channels.items():
        status = str(info.get('status', ''))
        if '已覆盖' in status or '部分覆盖' in status:
            groups['✅'].append((name, info))
        elif '耗尽' in status or '恢复' in status:
            groups['⚠️'].append((name, info))
        elif '未' in status or '为空' in status:
            groups['❌'].append((name, info))
        elif '待' in status or '评估' in status:
            groups['⏳'].append((name, info))
        else:
            groups['❓'].append((name, info))
    
    for icon, items in groups.items():
        if not items:
            continue
        print(f"\n{icon} 状态渠道 ({len(items)}个):")
        for name, info in items:
            coverage = info.get('coverage', {})
            rows = coverage.get('row_count', 0)
            industries = coverage.get('covered_industries', [])
            note = info.get('description', '')[:30]
            ind_str = f"{len(industries)}个" if industries else "-"
            print(f"   {name:<16} {rows:>6}行  {ind_str:<4}  {note}")
    
    print("\n" + "=" * 78)
    
    # 低覆盖率行业
    summary = ledger.get('coverage_summary', {})
    low = summary.get('low_coverage', [])
    if low:
        print(f"\n🔴 低覆盖率行业（需补充）: {', '.join(low)}")
    
    high = summary.get('high_coverage', [])
    if high:
        print(f"🟢 高覆盖率行业（无需补充）: {', '.join(high[:5])}...")

def show_gap_analysis():
    """渠道缺口分析"""
    ledger = load_ledger()
    channels = ledger.get('channels', {})
    
    print("\n" + "=" * 78)
    print("【渠道缺口分析 - 哪些还没用】")
    print("=" * 78)
    
    used = [(n,i) for n,i in channels.items() if i.get('coverage',{}).get('row_count',0) > 0]
    unused = [(n,i) for n,i in channels.items() if i.get('coverage',{}).get('row_count',0) == 0]
    
    print(f"\n✅ 已覆盖渠道 ({len(used)}个):")
    for name, info in sorted(used, key=lambda x: -x[1]['coverage']['row_count']):
        rows = info['coverage']['row_count']
        inds = info['coverage'].get('covered_industries', [])
        print(f"   {name}: {rows}行 ({len(inds)}个行业)")
    
    print(f"\n❌ 未使用渠道 ({len(unused)}个):")
    for name, info in sorted(unused):
        status = info.get('status', '')
        inds = info.get('coverage', {}).get('covered_industries', [])
        ind_str = ', '.join(inds) if inds else '-'
        print(f"   {name}: {status} (覆盖{ind_str})")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'gap':
        show_gap_analysis()
    else:
        get_channel_status()
