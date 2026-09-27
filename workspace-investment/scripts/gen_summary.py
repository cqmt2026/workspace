import csv, io, sys

rows = []
with open('logs/xuangu_candidates.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

top10 = rows[:10]
lines = ['尾盘精选选股策略结果 (2026-07-23)', '', '═══ Top10 候选股 ═══']
for i, r in enumerate(top10, 1):
    code = r['code']
    name = r['name']
    score = float(r['score'])
    chg = float(r['chg_pct'])
    turnover = float(r['turnover'])
    vol_ratio = float(r['vol_ratio'])
    ml = float(r['ml_prob']) if r['ml_prob'] else 0.0
    tier = r['supply_tier'] or ''
    industry = r['industry'] or ''
    lines.append(f'{i}. {code} {name}')
    lines.append(f'   涨幅:{chg:+.2f}% | 换手:{turnover:.2f}% | 量比:{vol_ratio:.2f} | ML概率:{ml:.3f} | 评分:{score:.1f}')
    if tier:
        lines.append(f'   [{tier}级卡点] {industry}')
    else:
        lines.append(f'   无供应链卡点')
    lines.append('')

lines.append('统计: 全市场筛选190只候选，ML>50%有9只')
lines.append('注意：IC因子权重均为0（今日未采集），PPE周期编码数据缺失')
text = '\n'.join(lines)

# 输出到文件避免编码问题
with open('logs/scan_summary.txt', 'w', encoding='utf-8') as f:
    f.write(text)
print(text)
