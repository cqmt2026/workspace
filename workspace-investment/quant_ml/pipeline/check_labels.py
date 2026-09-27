import sqlite3, numpy as np, pandas as pd, random
conn = sqlite3.connect('F:\\market_data.db')
all_codes = [r[0] for r in conn.execute("SELECT DISTINCT code FROM daily_k WHERE code NOT LIKE 'bj.%' AND code NOT LIKE 'sh.8%'")]
st = set(r[0] for r in conn.execute("SELECT code FROM stock_st_status WHERE is_st=1"))
codes = [c for c in all_codes if c not in st]
random.shuffle(codes)
codes = codes[:200]

labels = []
for code in codes:
    sub = pd.read_sql("SELECT date, close FROM daily_k WHERE code=? ORDER BY date DESC LIMIT 115", conn, params=(code,))
    if len(sub) < 70: continue
    sub = sub.sort_values('date').reset_index(drop=True)
    c = sub['close'].values.astype(np.float64)
    for i in range(65, len(c) - 5):
        labels.append(1 if c[i+5]/c[i]-1 > 0 else 0)

pos = sum(labels); neg = len(labels) - pos
print(f"Sample labels: {len(labels)} total")
print(f"  Up: {pos} ({pos/len(labels)*100:.1f}%)")
print(f"  Down: {neg} ({neg/len(labels)*100:.1f}%)")

# 再检查模型输出和标签的关系
import joblib
model = joblib.load(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\quant_ml\data\models\lgbm_unified.pkl')
print(f"\nModel: {model.__class__.__name__}, features={model.n_features_in_}")

# 检查训练时看到的数据
train_labels = labels[:5000] if len(labels) > 5000 else labels
pos2 = sum(train_labels)
print(f"\nIf trained on {len(train_labels)} samples: up={pos2} ({pos2/len(train_labels)*100:.1f}%)")