# -*- coding: utf-8 -*-
"""
自我学习复盘脚本 - 每周五收盘后运行
1. 读取本周所有决策
2. 分析成功/失败模式
3. 更新策略因子权重
4. 生成复盘报告
"""
import io
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
DATA_DIR = os.path.join(WORK_DIR, 'data')
DECISIONS_FILE = os.path.join(DATA_DIR, 'decisions.json')
REVIEW_FILE = os.path.join(DATA_DIR, 'review_weekly.json')

def load_decisions():
    """加载决策日志"""
    if not os.path.exists(DECISIONS_FILE):
        return []
    try:
        with open(DECISIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('records', [])
    except json.JSONDecodeError as e:
        print(f'[ERROR] decisions.json 解析失败: {e}')
        return []
    except Exception as e:
        print(f'[ERROR] 加载决策日志失败: {e}')
        return []

def load_reviews():
    """加载历史复盘"""
    if not os.path.exists(REVIEW_FILE):
        return []
    try:
        with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('reviews', [])
    except json.JSONDecodeError as e:
        print(f'[ERROR] review_weekly.json 解析失败: {e}')
        return []
    except Exception as e:
        print(f'[ERROR] 加载历史复盘失败: {e}')
        return []

def get_this_week_decisions(records):
    """获取本周决策"""
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday(), hours=today.hour, minutes=today.minute)
    this_week_start = week_start.replace(hour=0, minute=0, second=0)
    
    this_week = []
    for r in records:
        decision_date = datetime.fromisoformat(r['timestamp'])
        if decision_date >= this_week_start:
            this_week.append(r)
    return this_week

def analyze_patterns(records):
    """分析成功/失败模式"""
    if not records:
        return {'summary': '本周无决策记录', 'patterns': []}
    
    success = [r for r in records if r.get('result') == 'success']
    failure = [r for r in records if r.get('result') == 'failure']
    pending = [r for r in records if r.get('result') == 'pending']
    
    patterns = {
        'success_factors': [],
        'failure_factors': [],
        'win_rate': len(success) / len(records) if records else 0
    }
    
    # 提取成功因子
    for r in success:
        for tag in r.get('tags', []):
            if tag not in patterns['success_factors']:
                patterns['success_factors'].append(tag)
    
    # 提取失败因子
    for r in failure:
        for tag in r.get('tags', []):
            if tag not in patterns['failure_factors']:
                patterns['failure_factors'].append(tag)
    
    return patterns

def generate_review(records):
    """生成本周复盘"""
    this_week = get_this_week_decisions(records)
    patterns = analyze_patterns(this_week)
    
    review = {
        'date': datetime.now().isoformat(),
        'period': 'this_week',
        'total_decisions': len(this_week),
        'success': len([r for r in this_week if r.get('result') == 'success']),
        'failure': len([r for r in this_week if r.get('result') == 'failure']),
        'pending': len([r for r in this_week if r.get('result') == 'pending']),
        'win_rate': patterns['win_rate'],
        'patterns': patterns,
        'recommendations': []
    }
    
    # 生成建议
    if patterns['failure_factors']:
        review['recommendations'].append({
            'type': 'avoid',
            'factors': patterns['failure_factors'],
            'action': '下次避免使用这些因子'
        })
    
    if patterns['success_factors']:
        review['recommendations'].append({
            'type': 'prefer',
            'factors': patterns['success_factors'],
            'action': '下次优先使用这些因子'
        })
    
    return review

def save_review(review):
    """保存复盘"""
    reviews = load_reviews()
    reviews.append(review)
    
    try:
        with open(REVIEW_FILE, 'w', encoding='utf-8') as f:
            json.dump({'schema': 'review_weekly', 'version': '1.0', 'reviews': reviews}, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f'[ERROR] 保存复盘文件失败: {e}')
    except Exception as e:
        print(f'[ERROR] 保存复盘失败: {e}')

def main():
    print('=' * 50)
    print('【自我学习复盘】开始分析本周决策...')
    print('=' * 50)
    
    records = load_decisions()
    print(f'总决策记录: {len(records)}条')
    
    this_week = get_this_week_decisions(records)
    print(f'本周决策: {len(this_week)}条')
    
    if not this_week:
        print('本周无决策，跳过复盘')
        return
    
    review = generate_review(records)
    save_review(review)
    
    print()
    print(f'【复盘结果】')
    print(f'  总决策: {review["total_decisions"]}')
    print(f'  成功: {review["success"]}')
    print(f'  失败: {review["failure"]}')
    print(f'  胜率: {review["win_rate"]:.1%}')
    print()
    
    if review['recommendations']:
        print('【建议】')
        for rec in review['recommendations']:
            print(f'  [{rec["type"]}] {rec["factors"]} → {rec["action"]}')
    
    print()
    print('复盘已保存到:', REVIEW_FILE)
    print('=' * 50)

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()