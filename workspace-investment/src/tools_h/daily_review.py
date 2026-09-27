# -*- coding: utf-8 -*-
"""
每日复盘脚本 v1.0
整合：六维评分 + 情绪追踪 + 持仓分析
运行时间：收盘后 15:30（周一至周五）
"""
import sys
import os
import datetime

# 添加路径
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\src\tools_h')

# 1. 运行情绪追踪
print("=" * 55)
print("STEP 1: 情绪追踪")
print("=" * 55)
try:
    import sentiment_tracker
    sentiment_result = sentiment_tracker.run_sentiment_check()
except Exception as e:
    print("情绪追踪出错: " + str(e))

print()

# 2. 运行六维评分（持仓股）
print("=" * 55)
print("STEP 2: 六维评分")
print("=" * 55)
try:
    import six_dim_scorer_ef
    stocks = [('600549', '1', '厦门钨业'), ('000539', '0', '粤电力A')]
    results = []
    for code, mkt, name in stocks:
        total, rating, detail = six_dim_scorer_ef.six_dim_score(code, mkt, name)
        results.append({'code': code, 'market': mkt, 'name': name,
                       'total': total, 'rating': rating, 'detail': detail})
except Exception as e:
    print("六维评分出错: " + str(e))
    results = []

# 3. 保存综合报告
print()
print("=" * 55)
print("STEP 3: 生成报告")
print("=" * 55)
save_dir = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\daily_review'
os.makedirs(save_dir, exist_ok=True)
today = datetime.datetime.now().strftime('%Y-%m-%d')
report_path = os.path.join(save_dir, 'review_' + today + '.json')
import json
report = {
    'date': today,
    'time': datetime.datetime.now().strftime('%H:%M'),
    'sentiment': sentiment_result if 'sentiment_result' in dir() else None,
    'positions': results,
}
with open(report_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print("报告已保存: " + report_path)
print()
print("=" * 55)
print("每日复盘完成")
print("=" * 55)