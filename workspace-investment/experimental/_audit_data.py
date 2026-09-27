# -*- coding: utf-8 -*-
"""
数据质量审计 — 检查DB数据是否可信
"""
import sys, sqlite3, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

DB = r'F:\market_data.db'
conn = sqlite3.connect(DB)

print("=" * 70)
print("数据质量审计")
print("=" * 70)

# 1. 检查每日股票数是否稳定
print("\n[1] 每日数据量是否稳定")
print("-" * 70)

daily_counts = conn.execute("""
    SELECT date, COUNT(*) as cnt FROM daily_k 
    WHERE date >= '2026-01-01' 
    GROUP BY date ORDER BY date
""").fetchall()

counts = np.array([c[1] for c in daily_counts])
print(f"  日均: {np.mean(counts):.0f} ± {np.std(counts):.0f}")
print(f"  最大: {np.max(counts)}, 最小: {np.min(counts)}")

# 异常日
anomaly = [(d, c) for d, c in daily_counts if c < np.mean(counts) * 0.5]
if anomaly:
    print(f"  异常日（数据<均值50%）: {len(anomaly)}天")
    for d, c in anomaly[:10]:
        print(f"    {d}: {c}只")

# 2. 检查前复权价格是否连续
print("\n[2] 价格连续性检查")
print("-" * 70)

# 抽检20只股票，看有无跳变
import random
codes = [r[0] for r in conn.execute(
    "SELECT DISTINCT code FROM daily_k WHERE code NOT LIKE 'bj.%' AND code NOT LIKE 'sh.8%' "
    "AND code NOT LIKE 'sh.000%' LIMIT 20"
).fetchall()]

jump_count = 0
total_checks = 0
for code in codes:
    df = pd.read_sql("SELECT date, close FROM daily_k WHERE code=? ORDER BY date", conn, params=(code,))
    if len(df) < 10: continue
    c = df['close'].values.astype(np.float64)
    for i in range(1, len(c)):
        total_checks += 1
        chg = abs(c[i] / c[i-1] - 1) * 100
        if chg > 20:  # 单日涨幅>20%
            jump_count += 1
            if jump_count <= 5:
                print(f"  跳变: {code} {df['date'].values[i]} {c[i-1]:.2f}→{c[i]:.2f} ({chg:.1f}%)")

print(f"  检查{total_checks}次, 跳变>20%: {jump_count}次 ({jump_count/total_checks*100:.4f}%)")

# 3. 检查收盘价异常值
print("\n[3] 收盘价异常值")
print("-" * 70)

# 检查价格=0的行
zero_prices = conn.execute("""
    SELECT COUNT(*) FROM daily_k WHERE close = 0 OR close IS NULL
""").fetchone()[0]
print(f"  收盘价=0或NULL: {zero_prices}行")

# 检查价格为负
neg_prices = conn.execute("""
    SELECT COUNT(*) FROM daily_k WHERE close < 0
""").fetchone()[0]
print(f"  收盘价<0: {neg_prices}行")

# 4. 检查退市股/停牌股
print("\n[4] 退市股/停牌股数据")
print("-" * 70)

# 最近一个月没有数据的股票
latest = '2026-07-03'
no_data = conn.execute("""
    SELECT code, MAX(date) as last_date FROM daily_k 
    WHERE code NOT LIKE 'bj.%' AND code NOT LIKE 'sh.8%'
    AND code NOT LIKE 'sh.000%'
    GROUP BY code 
    HAVING last_date < '2026-05-01'
    ORDER BY last_date DESC
""").fetchall()
print(f"  近2个月无数据的股票: {len(no_data)}只")
for code, last in no_data[:10]:
    print(f"    {code}: 最新{last}")

# 5. 检查复权一致性
print("\n[5] 复权数据一致性")
print("-" * 70)

# 检查是否有股票连续2天价格不变
stale = conn.execute("""
    SELECT a.code, a.date, a.close, b.date, b.close 
    FROM daily_k a JOIN daily_k b ON a.code = b.code 
    WHERE a.date < b.date AND a.close = b.close 
    AND a.date >= '2026-06-01'
    LIMIT 10
""").fetchall()
print(f"  连续2天价格不变样本: {len(stale)}")
for s in stale[:5]:
    print(f"    {s[0]}: {s[1]}={s[2]:.2f}, {s[3]}={s[4]:.2f}")

# 6. 检查训练集标签分布
print("\n[6] 训练集标签（5天涨幅）分布")
print("-" * 70)

# 采样100只股票
sample_codes = [r[0] for r in conn.execute(
    "SELECT DISTINCT code FROM daily_k WHERE code NOT LIKE 'bj.%' LIMIT 100"
).fetchall()]

all_fwd = []
for code in sample_codes:
    df = pd.read_sql("SELECT close FROM daily_k WHERE code=? ORDER BY date", conn, params=(code,))
    if len(df) < 70: continue
    c = df['close'].values.astype(np.float64)
    n = len(c)
    for i in range(65, n-5):
        all_fwd.append((c[i+5] / c[i] - 1) * 100)

if all_fwd:
    fwd = np.array(all_fwd)
    print(f"  样本: {len(fwd)}次")
    print(f"  均值: {np.mean(fwd):.2f}%")
    print(f"  中位数: {np.median(fwd):.2f}%")
    print(f"  胜率(>0): {np.mean(fwd>0)*100:.1f}%")
    print(f"  P10: {np.percentile(fwd, 10):.2f}%")
    print(f"  P25: {np.percentile(fwd, 25):.2f}%")
    print(f"  P50: {np.percentile(fwd, 50):.2f}%")
    print(f"  P75: {np.percentile(fwd, 75):.2f}%")
    print(f"  P90: {np.percentile(fwd, 90):.2f}%")
    print(f"  极端值: min={np.min(fwd):.2f}% max={np.max(fwd):.2f}%")
    # 检查>30%或<-30%的比例
    extreme = np.sum(np.abs(fwd) > 30)
    print(f"  极端值(|x|>30%): {extreme}次 ({extreme/len(fwd)*100:.2f}%)")

conn.close()
print(f"\n{'='*70}")
print("审计完成")
print(f"{'='*70}")