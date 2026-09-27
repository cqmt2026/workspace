"""
涨停板分析v2 - 扩展分析 (优化版，避免全量加载)
1. 涨停次日溢价率分析
2. 炸板率分析
3. 强势股追踪（连续涨停）
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = r'F:\market_data.db'
OUTPUT_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\zt_analysis_v2.json'

def get_db_connection():
    return sqlite3.connect(DB_PATH)

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ============================================================
# 1. 涨停次日溢价率分析 (优化版)
# ============================================================
def analyze_next_day_premium():
    """计算涨停后次日的开盘买入收益率"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # 获取所有涨停记录
    c.execute("""
        SELECT code, trade_date, close_price, open_price, zt_type 
        FROM daily_zt 
        ORDER BY code, trade_date
    """)
    zt_records = c.fetchall()
    
    if not zt_records:
        print("警告: daily_zt表无数据")
        return None
    
    premium_list = []
    
    # 逐条处理，避免全量加载
    for code, zt_date, zt_close, zt_open, zt_type in zt_records:
        try:
            zt_date_obj = datetime.strptime(zt_date, '%Y-%m-%d')
        except:
            continue
        
        # 找下一个交易日
        next_date = (zt_date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 直接查询次日数据
        c.execute("""
            SELECT open, close FROM daily_k 
            WHERE code = ? AND date = ?
        """, (code, next_date))
        
        row = c.fetchone()
        if row and row[0] and row[1] and zt_close > 0:
            next_open, next_close = row
            return_rate = next_close / zt_close - 1
            premium_list.append({
                'code': code,
                'zt_date': zt_date,
                'zt_close': zt_close,
                'next_open': next_open,
                'next_close': next_close,
                'return_rate': return_rate,
                'zt_type': zt_type
            })
    
    conn.close()
    
    if not premium_list:
        print("警告: 无法匹配到次日数据")
        return None
    
    # 统计分析
    returns = [p['return_rate'] for p in premium_list]
    positive_count = sum(1 for r in returns if r > 0)
    win_rate = positive_count / len(returns) * 100 if returns else 0
    
    # 按收益率排序
    sorted_returns = sorted(returns)
    
    # 过滤极端值
    normal_returns = [r for r in returns if -0.15 <= r <= 0.15]
    
    # 分位数
    n = len(sorted_returns)
    result = {
        '分析类型': '涨停次日溢价率分析',
        '样本数': len(premium_list),
        '有效样本数(剔除极端值)': len(normal_returns),
        '平均溢价率': round(sum(returns) / len(returns) * 100, 2) if returns else 0,
        '有效平均溢价率': round(sum(normal_returns) / len(normal_returns) * 100, 2) if normal_returns else 0,
        '胜率(次日上涨)': round(win_rate, 2),
        '最佳案例': {
            'code': premium_list[returns.index(max(returns))]['code'],
            '日期': premium_list[returns.index(max(returns))]['zt_date'],
            '收益率': round(max(returns) * 100, 2)
        },
        '最差案例': {
            'code': premium_list[returns.index(min(returns))]['code'],
            '日期': premium_list[returns.index(min(returns))]['zt_date'],
            '收益率': round(min(returns) * 100, 2)
        },
        '分位数分析': {
            '10%分位': round(sorted_returns[n//10] * 100, 2) if n >= 10 else None,
            '25%分位': round(sorted_returns[n//4] * 100, 2) if n >= 4 else None,
            '50%分位(中位数)': round(sorted_returns[n//2] * 100, 2) if n >= 2 else None,
            '75%分位': round(sorted_returns[3*n//4] * 100, 2) if n >= 4 else None,
            '90%分位': round(sorted_returns[9*n//10] * 100, 2) if n >= 10 else None,
        }
    }
    
    return result

# ============================================================
# 2. 炸板率分析 (优化版)
# ============================================================
def analyze_break_rate():
    """分析涨停股次日炸板情况"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # 获取所有涨停记录
    c.execute("""
        SELECT code, trade_date, close_price 
        FROM daily_zt 
        ORDER BY trade_date
    """)
    zt_records = c.fetchall()
    
    if not zt_records:
        return None
    
    # 按日期统计炸板情况
    date_stats = defaultdict(lambda: {'zt_count': 0, 'break_count': 0, 'break_stocks': []})
    
    for code, zt_date, zt_close in zt_records:
        try:
            zt_date_obj = datetime.strptime(zt_date, '%Y-%m-%d')
        except:
            continue
        
        next_date = (zt_date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
        
        date_stats[zt_date]['zt_count'] += 1
        
        # 直接查询次日数据
        c.execute("""
            SELECT close FROM daily_k 
            WHERE code = ? AND date = ?
        """, (code, next_date))
        
        row = c.fetchone()
        if row and row[0] and zt_close > 0:
            next_close = row[0]
            next_return = next_close / zt_close - 1
            
            # 炸板定义：次日涨幅 < 9%
            if next_return < 0.09:
                date_stats[zt_date]['break_count'] += 1
                date_stats[zt_date]['break_stocks'].append({
                    'code': code,
                    'next_return': round(next_return * 100, 2)
                })
    
    conn.close()
    
    # 计算每日炸板率
    daily_break_rates = []
    for date in sorted(date_stats.keys()):
        stats = date_stats[date]
        if stats['zt_count'] > 0:
            break_rate = stats['break_count'] / stats['zt_count'] * 100
            daily_break_rates.append({
                'date': date,
                'zt_count': stats['zt_count'],
                'break_count': stats['break_count'],
                'break_rate': round(break_rate, 2),
                'break_stocks': stats['break_stocks'][:5]
            })
    
    if not daily_break_rates:
        return None
    
    break_rates = [d['break_rate'] for d in daily_break_rates]
    avg_break_rate = sum(break_rates) / len(break_rates)
    
    max_break = max(daily_break_rates, key=lambda x: x['break_rate'])
    min_break = min(daily_break_rates, key=lambda x: x['break_rate'])
    
    result = {
        '分析类型': '炸板率分析',
        '统计日期范围': f"{daily_break_rates[0]['date']} 至 {daily_break_rates[-1]['date']}",
        '总交易日数': len(daily_break_rates),
        '平均炸板率': round(avg_break_rate, 2),
        '最高炸板率日期': {
            'date': max_break['date'],
            'break_rate': max_break['break_rate'],
            'zt_count': max_break['zt_count'],
            'break_count': max_break['break_count']
        },
        '最低炸板率日期': {
            'date': min_break['date'],
            'break_rate': min_break['break_rate'],
            'zt_count': min_break['zt_count'],
            'break_count': min_break['break_count']
        },
        '每日炸板详情': daily_break_rates
    }
    
    return result

# ============================================================
# 3. 强势股追踪（连续涨停）
# ============================================================
def analyze_consecutive_zt():
    """追踪连续涨停的强势股"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # 获取所有涨停记录
    c.execute("""
        SELECT code, trade_date, close_price, zt_type 
        FROM daily_zt 
        ORDER BY code, trade_date
    """)
    zt_records = c.fetchall()
    conn.close()
    
    if not zt_records:
        return None
    
    # 按股票分组
    stock_zt = defaultdict(list)
    for code, trade_date, close_price, zt_type in zt_records:
        stock_zt[code].append({
            'date': trade_date,
            'close': close_price,
            'type': zt_type
        })
    
    # 找出连续涨停
    consecutive_results = []
    
    for code, records in stock_zt.items():
        if len(records) < 2:
            continue
        
        records.sort(key=lambda x: x['date'])
        
        count = 1
        start_date = records[0]['date']
        
        for i in range(1, len(records)):
            try:
                prev_date = datetime.strptime(records[i-1]['date'], '%Y-%m-%d')
                curr_date = datetime.strptime(records[i]['date'], '%Y-%m-%d')
                diff_days = (curr_date - prev_date).days
            except:
                continue
            
            # 连续交易日（间隔<=5天）
            if diff_days <= 5:
                count += 1
            else:
                if count >= 3:
                    consecutive_results.append({
                        'code': code,
                        'start_date': start_date,
                        'end_date': records[i-1]['date'],
                        'consecutive_days': count,
                        'total_zt_count': count
                    })
                count = 1
                start_date = records[i]['date']
        
        if count >= 3:
            consecutive_results.append({
                'code': code,
                'start_date': start_date,
                'end_date': records[-1]['date'],
                'consecutive_days': count,
                'total_zt_count': count
            })
    
    consecutive_results.sort(key=lambda x: x['consecutive_days'], reverse=True)
    
    if not consecutive_results:
        return {
            '分析类型': '强势股追踪',
            '说明': '未发现连续3天及以上涨停的股票',
            '样本数': len(stock_zt),
            '3连板以上': []
        }
    
    consecutive_3plus = [r for r in consecutive_results if r['consecutive_days'] >= 3]
    consecutive_4plus = [r for r in consecutive_results if r['consecutive_days'] >= 4]
    consecutive_5plus = [r for r in consecutive_results if r['consecutive_days'] >= 5]
    
    result = {
        '分析类型': '强势股追踪',
        '统计股票总数': len(stock_zt),
        '有涨停记录股票数': len([k for k, v in stock_zt.items() if len(v) >= 1]),
        '3连板以上统计': {
            '次数': len(consecutive_3plus),
            '示例': consecutive_3plus[:10]
        },
        '4连板以上统计': {
            '次数': len(consecutive_4plus),
            '示例': consecutive_4plus[:5]
        },
        '5连板以上统计': {
            '次数': len(consecutive_5plus),
            '示例': consecutive_5plus[:5]
        },
        '最长连续涨停记录': consecutive_results[0] if consecutive_results else None,
        '全部连续涨停记录': consecutive_results[:20]
    }
    
    return result

# ============================================================
# 主程序
# ============================================================
def main():
    print("=" * 60)
    print("涨停板分析v2 - 开始分析")
    print("=" * 60)
    
    results = {}
    
    # 1. 涨停次日溢价率分析
    print("\n[1/3] 分析涨停次日溢价率...")
    try:
        premium_result = analyze_next_day_premium()
        if premium_result:
            results['次日溢价率分析'] = premium_result
            print(f'  [OK] 完成，有效样本: {premium_result.get("有效样本数(剔除极端值)", "N/A")}')
            print(f'  [OK] 平均溢价率: {premium_result.get("有效平均溢价率", 0)}%')
            print(f'  [OK] 胜率: {premium_result.get("胜率(次日上涨)", 0)}%')
    except Exception as e:
        print(f'  [FAIL] 失败: {e}')
        import traceback
        traceback.print_exc()
    
    # 2. 炸板率分析
    print("\n[2/3] 分析炸板率...")
    try:
        break_result = analyze_break_rate()
        if break_result:
            results['炸板率分析'] = break_result
            print(f'  [OK] 完成，统计天数: {break_result.get("总交易日数", "N/A")}')
            print(f'  [OK] 平均炸板率: {break_result.get("平均炸板率", 0)}%')
            print(f'  [OK] 最高炸板率: {break_result.get("最高炸板率日期", {}).get("break_rate", 0)}% ({break_result.get("最高炸板率日期", {}).get("date", "")})')
    except Exception as e:
        print(f'  [FAIL] 失败: {e}')
        import traceback
        traceback.print_exc()
    
    # 3. 强势股追踪
    print("\n[3/3] 追踪强势股...")
    try:
        consecutive_result = analyze_consecutive_zt()
        if consecutive_result:
            results['强势股追踪'] = consecutive_result
            print(f'  [OK] 完成，3连板以上次数: {consecutive_result.get("3连板以上统计", {}).get("次数", 0)}')
            print(f'  [OK] 5连板以上次数: {consecutive_result.get("5连板以上统计", {}).get("次数", 0)}')
    except Exception as e:
        print(f'  [FAIL] 失败: {e}')
        import traceback
        traceback.print_exc()
    
    # 保存结果
    print("\n" + "=" * 60)
    print("保存结果...")
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f'[OK] 结果已保存到: {OUTPUT_PATH}')
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("分析结果摘要")
    print("=" * 60)
    
    if '次日溢价率分析' in results:
        r = results['次日溢价率分析']
        print(f"\n【涨停次日溢价率分析】")
        print(f"  样本数: {r.get('样本数', 'N/A')}")
        print(f"  有效样本数(剔除极端值): {r.get('有效样本数(剔除极端值)', 'N/A')}")
        print(f"  有效平均溢价率: {r.get('有效平均溢价率', 0)}%")
        print(f"  胜率: {r.get('胜率(次日上涨)', 0)}%")
        print(f"  最佳案例: {r.get('最佳案例', {}).get('code', '')} ({r.get('最佳案例', {}).get('收益率', 0)}%)")
        print(f"  最差案例: {r.get('最差案例', {}).get('code', '')} ({r.get('最差案例', {}).get('收益率', 0)}%)")
    
    if '炸板率分析' in results:
        r = results['炸板率分析']
        print(f"\n【炸板率分析】")
        print(f"  统计日期范围: {r.get('统计日期范围', 'N/A')}")
        print(f"  平均炸板率: {r.get('平均炸板率', 0)}%")
        print(f"  最高炸板率日期: {r.get('最高炸板率日期', {}).get('date', '')} ({r.get('最高炸板率日期', {}).get('break_rate', 0)}%)")
        print(f"  最低炸板率日期: {r.get('最低炸板率日期', {}).get('date', '')} ({r.get('最低炸板率日期', {}).get('break_rate', 0)}%)")
    
    if '强势股追踪' in results:
        r = results['强势股追踪']
        print(f"\n【强势股追踪】")
        print(f"  统计股票总数: {r.get('统计股票总数', 'N/A')}")
        print(f"  3连板以上次数: {r.get('3连板以上统计', {}).get('次数', 0)}")
        print(f"  4连板以上次数: {r.get('4连板以上统计', {}).get('次数', 0)}")
        print(f"  5连板以上次数: {r.get('5连板以上统计', {}).get('次数', 0)}")
        if r.get('最长连续涨停记录'):
            lr = r['最长连续涨停记录']
            print(f"  最长连续涨停: {lr.get('code', '')} {lr.get('consecutive_days', 0)}连板 ({lr.get('start_date', '')} ~ {lr.get('end_date', '')})")
    
    # 有趣规律发现
    print("\n" + "=" * 60)
    print("【有趣规律发现】")
    print("=" * 60)
    
    findings = []
    
    if '次日溢价率分析' in results:
        premium = results['次日溢价率分析'].get('有效平均溢价率', 0)
        if premium > 0:
            findings.append(f"1. 涨停股次日平均存在正向溢价({premium}%)，开盘买入策略总体盈利")
        else:
            findings.append(f"1. 涨停股次日平均溢价为负({premium}%)，追涨停风险较大")
    
    if '炸板率分析' in results:
        avg_break = results['炸板率分析'].get('平均炸板率', 0)
        findings.append(f"2. 平均每天约{avg_break}%的涨停股会炸板，说明追涨停有较大不确定性")
        
        max_break = results['炸板率分析'].get('最高炸板率日期', {})
        if max_break and max_break.get('break_rate', 0) > 30:
            findings.append(f"3. {max_break.get('date', '')}炸板率高达{max_break.get('break_rate', 0)}%，可能是市场情绪拐点信号")
    
    if '强势股追踪' in results:
        count_5plus = results['强势股追踪'].get('5连板以上统计', {}).get('次数', 0)
        if count_5plus > 0:
            findings.append(f"4. 近30日有{count_5plus}只股票实现5连板以上，说明市场存在强势主线")
        else:
            findings.append(f"4. 近30日无5连板以上股票，市场整体偏弱")
    
    for f in findings:
        print(f"  {f}")
    
    print("\n" + "=" * 60)
    print("分析完成!")
    print("=" * 60)

if __name__ == '__main__':
    main()
