# -*- coding: utf-8 -*-
import sqlite3, os
from datetime import date, timedelta

DB = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

today = date.today().strftime('%Y-%m-%d')
yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

# 统计今日
c.execute("SELECT COUNT(*) FROM call_logs WHERE call_date=?", (today,))
calls_today = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM call_logs WHERE call_date=? AND result='有效'", (today,))
valid_today = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM call_logs WHERE call_date=? AND result='有意向'", (today,))
int_today = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM call_logs WHERE call_date=? AND result='需跟进'", (today,))
follow_today = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM call_logs WHERE call_date=? AND result IN ('无效','拒接','关机')", (today,))
invalid_today = c.fetchone()[0]
c.execute("SELECT SUM(duration_sec) FROM call_logs WHERE call_date=?", (today,))
dur_today = c.fetchone()[0] or 0
avg_dur_today = dur_today / max(calls_today, 1)

# 统计昨日
c.execute("SELECT COUNT(*) FROM call_logs WHERE call_date=?", (yesterday,))
calls_yest = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM call_logs WHERE call_date=? AND result='有效'", (yesterday,))
valid_yest = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM call_logs WHERE call_date=? AND result='有意向'", (yesterday,))
int_yest = c.fetchone()[0]

# 客户总量
c.execute("SELECT COUNT(*) FROM customers")
total = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM customers WHERE status='待联系'")
pending = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM customers WHERE status='已联系'")
contacted = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM customers WHERE status='有意向'")
interested = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM customers WHERE status='已成交'")
deal = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM customers WHERE status='放弃'")
given_up = c.fetchone()[0]

# 今日通话详情
c.execute("""SELECT cl.id, c.name, cl.result, cl.duration_sec, cl.note 
             FROM call_logs cl LEFT JOIN customers c ON cl.customer_id=c.id 
             WHERE cl.call_date=? ORDER BY cl.id""", (today,))
today_logs = c.fetchall()

conn.close()

print(f"today={today} yesterday={yesterday}")
print(f"calls:{calls_today} valid:{valid_today} int:{int_today} follow:{follow_today} invalid:{invalid_today} avg_dur:{avg_dur_today:.0f}s")
print(f"yest_calls:{calls_yest} yest_valid:{valid_yest} yest_int:{int_yest}")
print(f"total:{total} pending:{pending} contacted:{contacted} interested:{interested} deal:{deal} given_up:{given_up}")
for row in today_logs:
    print("LOG:", row)

# 生成日报
effective_rate_today = valid_today / max(calls_today, 1) * 100
conversion_rate_today = int_today / max(calls_today, 1) * 100
effective_rate_yest = valid_yest / max(calls_yest, 1) * 100 if calls_yest > 0 else 0
conversion_rate_yest = int_yest / max(calls_yest, 1) * 100 if calls_yest > 0 else 0

call_delta = calls_today - calls_yest
valid_delta = valid_today - valid_yest
int_delta = int_today - int_yest

def mark(delta):
    if delta > 0:
        return f"📈 +{delta}"
    elif delta < 0:
        return f"📉 {delta}"
    else:
        return "➡️ 持平"

report = f"""# 百都销售日报 | {today}（周一）

> 生成时间：{date.today().strftime('%Y-%m-%d %H:%M')} | 报告人：小度

---

## 📊 今日拨打数据

| 指标 | 今日 | 昨日 | 变化 |
|------|------|------|------|
| 拨打数 | {calls_today} | {calls_yest} | {mark(call_delta)} |
| 接通数（有效） | {valid_today} | {valid_yest} | {mark(valid_delta)} |
| 有效率 | {effective_rate_today:.1f}% | {effective_rate_yest:.1f}% | {mark(effective_rate_today - effective_rate_yest) if abs(effective_rate_today - effective_rate_yest) > 0.5 else '➡️ 持平'} |
| 意向数 | {int_today} | {int_yest} | {mark(int_delta)} |
| 需跟进 | {follow_today} | - | - |
| 平均通话时长 | {avg_dur_today:.0f}秒 | - | - |

## 📋 客户池总览

| 状态 | 数量 |
|------|------|
| 总客户 | {total} |
| 待联系 | {pending} |
| 已联系 | {contacted} |
| 有意向 | {interested} |
| 已成交 | {deal} |
| 放弃 | {given_up} |

## 🔍 今日通话明细

"""

if today_logs:
    report += "| # | 客户 | 结果 | 时长 | 备注 |\n|---|------|------|------|------|\n"
    for row in today_logs:
        log_id, name, result, dur, note = row
        dur_str = f"{dur//60}分{dur%60}秒" if dur and dur >= 60 else (f"{dur}秒" if dur else "-")
        note_str = (note[:30] + "...") if note and len(note) > 30 else (note or "-")
        report += f"| {log_id} | {name or '-'} | {result} | {dur_str} | {note_str} |\n"
else:
    report += "> 今日暂无通话记录\n"

report += f"""
---

## 💡 今日总结

"""

if calls_today == 0:
    report += "> ⚠️ 今日未进行任何拨打，需检查是否有工作记录缺失\n"
elif calls_today >= 20:
    report += f"> ✅ 今日拨打 {calls_today} 通，有效率 {effective_rate_today:.1f}%，意向 {int_today} 个。数据良好，继续保持！\n"
elif calls_today >= 10:
    report += f"> ⚠️ 今日拨打 {calls_today} 通，有效率 {effective_rate_today:.1f}%，意向 {int_today} 个。建议增加拨打量至日均20+。\n"
else:
    report += f"> 🔴 今日拨打仅 {calls_today} 通，效率偏低。明日目标：≥20通。\n"

report += f"""
---

*报告由小度自动生成 | 数据来源：baidu_crm.db*
"""

# 保存日报
log_dir = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\memory\logs'
os.makedirs(log_dir, exist_ok=True)
filepath = os.path.join(log_dir, f'daily_{today.replace("-", "")}.md')
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(report)

print(f"\n✅ 日报已保存: {filepath}")
print(report)
