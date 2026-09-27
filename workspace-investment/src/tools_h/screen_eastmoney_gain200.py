#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
东方财富涨幅排行榜筛选短线股票
数据源：东方财富 API
标准：市值 50-300 亿、成交>3 亿、振幅>5%、涨停 1-5 次、六维>60
"""

import requests
import json
import baostock as bs
from datetime import datetime

print("=" * 80)
print("东方财富涨幅 TOP200 短线股票筛选")
print("=" * 80)
print(f"筛选日期：2026-03-06 (最新交易日)")
print()

# 东方财富涨幅排行榜 API（备用多个 URL）
urls = [
    "http://push2.eastmoney.com/api/qt/clist/get",
    "http://nufm.dfcfw.com/EM_Fund2099/QF_StockSort/StockSort.aspx",
    "http://quote.eastmoney.com/center/gridlist.html",
]

params = {
    'pn': '1',
    'pz': '200',
    'po': '1',
    'np': '1',
    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
    'fltt': '2',
    'invt': '2',
    'fid': 'f3',  # 按涨跌幅排序
    'fs': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23',  # 沪深 A 股
    'fields': 'f12,f14,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15,f16,f17,f18,f19,f20,f21,f22,f23,f24,f25',
    '_': '1623833739532',
}

print("Step 1: 获取东方财富涨幅 TOP200...")

top200 = None
for api_url in urls:
    try:
        print(f"  尝试：{api_url}")
        response = requests.get(api_url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and data['data'].get('diff'):
                top200 = data['data']['diff']
                print(f"  获取成功：{len(top200)} 只股票")
                break
    except Exception as e:
        print(f"  失败：{e}")
        continue

if not top200:
    print("所有 API 均失败，使用昨日成交量 TOP200 结果作为参考")
    # 读取昨日成交量 TOP200 结果
    try:
        with open('eastmoney_top200_result.json', 'r', encoding='utf-8') as f:
            prev_result = json.load(f)
        print(f"  加载昨日数据：{prev_result.get('passed', 0)} 只")
    except:
        print("  无历史数据")
    exit()
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('data') and data['data'].get('diff'):
            top200 = data['data']['diff']
            print(f"  获取成功：{len(top200)} 只股票")
            print()
            
            # 显示前 10 只
            print("涨幅 TOP10:")
            print("-" * 100)
            print(f"{'排名':<4} {'代码':<12} {'名称':<10} {'价格':<10} {'涨跌':<10} {'成交量':<15} {'成交额':<15} {'换手':<10}")
            print("-" * 100)
            
            for i, stock in enumerate(top200[:10], 1):
                code = stock.get('f12', '')
                name = stock.get('f14', '')
                price = stock.get('f2', 0)
                change = stock.get('f3', 0)
                volume = stock.get('f5', 0)
                amount = stock.get('f6', 0) / 100000000
                turnover = stock.get('f18', 0)
                
                print(f"{i:<4} {code:<12} {name:<10} {price:<10.2f} {change:+.2f}%{'':<5} {volume/10000:.1f}万手{'':<5} {amount:.2f}亿{'':<5} {turnover:.2f}%")
            
            print()
            print("=" * 80)
            print(f"总成交额：{sum(s.get('f6', 0) for s in top200) / 100000000:.2f}亿")
            print()
            
            # 保存原始数据
            with open('eastmoney_top200_gain_raw.json', 'w', encoding='utf-8') as f:
                json.dump({'date': '2026-03-06', 'type': 'gain', 'total': len(top200), 'stocks': top200}, f, ensure_ascii=False, indent=2)
            
            print("原始数据已保存：eastmoney_top200_gain_raw.json")
            print()
            
            # 获取详细数据并进行筛选
            print("Step 2: 获取详细数据并进行短线标准筛选...")
            print("(需要获取近 20 日数据，可能需要几分钟)")
            print()
            
            lg = bs.login()
            print(f"登录：{lg.error_msg}")
            print()
            
            passed = []
            for i, stock in enumerate(top200):
                code = stock.get('f12', '')
                name = stock.get('f14', '')
                
                # 添加市场前缀
                if code.startswith('6'):
                    full_code = 'sh.' + code
                else:
                    full_code = 'sz.' + code
                
                # 获取近 20 日数据
                rs = bs.query_history_k_data_plus(
                    full_code,
                    'date,open,high,low,close,volume,amount,turn',
                    start_date='2026-02-01',
                    end_date='2026-03-06'
                )
                
                data = []
                while rs.error_msg == 'success' and rs.next():
                    row = rs.get_row_data()
                    if row[5]:
                        data.append({
                            'open': float(row[1]),
                            'high': float(row[2]),
                            'low': float(row[3]),
                            'close': float(row[4]),
                            'amount': float(row[6]),
                            'turnover': float(row[7]) if row[7] else 0,
                        })
                
                if len(data) < 10:
                    continue
                
                # 计算指标
                last = data[-1]
                avg_amount_20 = sum(d['amount'] for d in data[-20:]) / min(20, len(data)) / 1e8
                avg_amp_20 = sum((d['high']-d['low'])/d['low']*100 for d in data[-20:]) / min(20, len(data))
                limit_up_count = sum(1 for d in data[-20:] if d['open']>0 and (d['close']/d['open']-1)*100 > 9.5)
                
                closes = [d['close'] for d in data]
                change_5d = (closes[-1]/closes[-5]-1)*100 if len(closes)>=5 else 0
                change_10d = (closes[-1]/closes[-10]-1)*100 if len(closes)>=10 else 0
                ma5 = sum(closes[-5:])/5
                ma10 = sum(closes[-10:])/10
                ma20 = sum(closes[-20:])/20
                ma_bull = ma5 > ma10 > ma20
                
                # 估算市值
                avg_turnover = sum(d['turnover'] for d in data[-20:]) / min(20, len(data))
                avg_vol = sum(d['amount'] for d in data[-20:]) / min(20, len(data))
                market_cap = last['close'] * (avg_vol / (avg_turnover/100) / 1e8) if avg_turnover > 0 else 100
                
                # 评分
                score = 0
                if 50 <= market_cap <= 300: score += 20
                if avg_amount_20 > 3: score += 20
                if avg_amp_20 > 5: score += 20
                if 1 <= limit_up_count <= 5: score += 20
                if ma_bull: score += 20
                
                # 检查是否通过
                if score >= 60:
                    passed.append({
                        'rank': len(passed)+1,
                        'code': code,
                        'name': name,
                        'market_cap': market_cap,
                        'avg_amount': avg_amount_20,
                        'avg_amplitude': avg_amp_20,
                        'limit_up_count': limit_up_count,
                        'change_5d': change_5d,
                        'change_10d': change_10d,
                        'ma_bull': ma_bull,
                        'score': score,
                        'gain_rank': i+1,
                    })
                
                if (i+1) % 50 == 0:
                    print(f"  处理进度：{i+1}/200...")
            
            # 按评分排序
            passed.sort(key=lambda x: x['score'], reverse=True)
            for i, p in enumerate(passed):
                p['rank'] = i+1
            
            bs.logout()
            
            print()
            print("=" * 80)
            print(f"筛选结果：{len(passed)}/200 只符合短线标准")
            print("=" * 80)
            print()
            
            if passed:
                print("符合短线标准的股票:")
                print("-" * 160)
                print(f"{'排名':<4} {'代码':<12} {'名称':<10} {'市值':<8} {'成交':<8} {'振幅':<8} {'涨停':<6} {'5 日':<8} {'10 日':<8} {'均线':<6} {'评分':<6} {'涨排':<6}")
                print("-" * 160)
                
                for p in passed:
                    ma = 'OK' if p['ma_bull'] else 'NO'
                    print(f"{p['rank']:<4} {p['code']:<12} {p['name']:<10} {p['market_cap']:.0f}亿{'':<3} {p['avg_amount']:.1f}亿{'':<3} {p['avg_amplitude']:.1f}%{'':<3} {p['limit_up_count']}次{'':<2} {p['change_5d']:+.1f}%{'':<3} {p['change_10d']:+.1f}%{'':<3} {ma:<6} {p['score']:<6} {p['gain_rank']:<6}")
                
                print()
                print("=" * 80)
                print(f"总计：{len(passed)} 只")
                print(f"评分>=80 分：{len([p for p in passed if p['score']>=80])} 只")
                print(f"评分 60-79 分：{len([p for p in passed if 60<=p['score']<80])} 只")
                
                # 保存结果
                result = {
                    'date': '2026-03-06',
                    'type': 'gain',
                    'total_screened': 200,
                    'passed': len(passed),
                    'stocks': passed,
                }
                
                with open('eastmoney_top200_gain_result.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"\n结果已保存：eastmoney_top200_gain_result.json")
            else:
                print("无股票符合标准！")
        else:
            print("获取数据失败：API 返回数据为空")
    else:
        print(f"获取数据失败：HTTP {response.status_code}")
except Exception as e:
    print(f"获取数据失败：{e}")

print()
print("=" * 80)
