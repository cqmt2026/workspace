# -*- coding: utf-8 -*-
"""
市场情绪追踪器 v1.0
功能：实时获取涨跌停家数、赚钱效应、连板高度，判断市场情绪阶段
整合自 H盘 sentiment_realtime.py + 情绪周期学习手册
"""
import json
import urllib.request
import datetime

def get_market_breadth():
    """
    获取市场宽度：上涨/下跌家数，计算赚钱效应
    返回: (up_count, down_count, limit_up_count, limit_down_count, money_effect_pct)
    """
    try:
        url = 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=1&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23&fields=f2,f3'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.eastmoney.com'})
        resp = urllib.request.urlopen(req, timeout=8)
        data = json.loads(resp.read().decode('utf-8'))
        total = data['data']['total']  # 总数
        return total, 0, 0, 0, 0
    except:
        return 0, 0, 0, 0, 0

def get_limit_up_count():
    """
    获取涨停家数（东方财富连板池API）
    限制：仅在交易时间（9:30-15:00）返回真实数据，
          非交易时间API返回0，需结合时间判断
    """
    try:
        url = 'https://push2ex.eastmoney.com/getTopicLBPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&Pagesize=100&sort=fund%3Adesc'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://quote.eastmoney.com'})
        resp = urllib.request.urlopen(req, timeout=8)
        raw = resp.read().decode('utf-8')
        data = json.loads(raw)
        if data.get('success') and data.get('data'):
            pool = data['data'].get('pool', [])
            return len(pool)
    except:
        pass
    return 0

def get_limit_down_count():
    """
    获取跌停家数（东方财富跌停池API）
    """
    try:
        url = 'https://push2ex.eastmoney.com/getTopicDTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&Pagesize=100&sort=fund%3Adesc'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://quote.eastmoney.com'})
        resp = urllib.request.urlopen(req, timeout=8)
        raw = resp.read().decode('utf-8')
        data = json.loads(raw)
        if data.get('success') and data.get('data'):
            pool = data['data'].get('pool', [])
            return len(pool)
    except:
        pass
    return 0

def get_highest_board():
    """
    获取最高连板数
    """
    try:
        url = 'https://push2ex.eastmoney.com/getTopicLBPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&Pagesize=100&sort=fund%3Adesc'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://quote.eastmoney.com'})
        resp = urllib.request.urlopen(req, timeout=8)
        raw = resp.read().decode('utf-8')
        data = json.loads(raw)
        if data.get('success') and data.get('data'):
            pool = data['data'].get('pool', [])
            if pool:
                max_lb = max(s.get('lban', s.get('lb', 0)) for s in pool if isinstance(s, dict))
                return max_lb
    except:
        pass
    return 0

def get_index_data():
    """
    获取主要指数涨跌情况
    """
    indices = [
        ('1.000001', '上证指数'),
        ('0.399001', '深证成指'),
        ('0.399006', '创业板指'),
    ]
    result = []
    for secid, name in indices:
        try:
            url = f'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58&klt=101&fqt=1&beg=&end=20500101&lmt=2'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.eastmoney.com'})
            resp = urllib.request.urlopen(req, timeout=8)
            klines = json.loads(resp.read().decode('utf-8')).get('data', {}).get('klines', [])
            if len(klines) >= 2:
                last = klines[-1].split(',')
                prev = klines[-2].split(',')
                cur_close = float(last[2])
                prev_close = float(prev[2])
                chg_pct = (cur_close - prev_close) / prev_close * 100
                result.append((name, cur_close, chg_pct))
        except:
            pass
    return result

def calc_sentiment_index(limit_up, limit_down, highest_board, index_chg_avg):
    """
    计算情绪指数（基于情绪周期学习手册公式）
    情绪指数 = (涨停家数*0.3 + 连板高度*10*0.2 + 赚钱效应*0.3 - 跌停家数*0.2)
    >80: 高潮期
    60-80: 发酵期
    40-60: 启动期/退潮期
    20-40: 衰退期
    <20: 冰点期
    """
    # 赚钱效应：根据指数平均涨跌幅估算（简化版）
    money_effect = min(100, max(0, 50 + index_chg_avg * 10))

    raw_score = (limit_up * 0.3 +
                 highest_board * 10 * 0.2 +
                 money_effect * 0.3 -
                 limit_down * 0.2)

    # 归一化到 0-100
    sentiment = max(0, min(100, raw_score))
    return sentiment, money_effect

def get_sentiment_phase(sentiment):
    """
    根据情绪指数判断所处阶段（情绪周期六阶段）
    """
    if sentiment >= 80:
        return '高潮期', '⚠️ 减仓/止盈，不追高'
    elif sentiment >= 60:
        return '发酵期', '✅ 加仓主升，持股待涨'
    elif sentiment >= 40:
        return '启动期或退潮期', '⚠️ 需结合其他指标判断方向'
    elif sentiment >= 20:
        return '衰退期', '❌ 减仓，等待冰点'
    else:
        return '冰点期', '🟢 观察，准备抄底'

def run_sentiment_check():
    """
    运行完整情绪检查
    """
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print('='*55)
    print(f'市场情绪检查 {now}')
    print('='*55)

    # 1. 涨停/跌停/连板
    limit_up = get_limit_up_count()
    limit_down = get_limit_down_count()
    highest_board = get_highest_board()

    print(f'涨停家数: {limit_up}')
    print(f'跌停家数: {limit_down}')
    print(f'最高连板: {highest_board}板')

    # 2. 指数涨跌
    indices = get_index_data()
    if indices:
        avg_chg = sum(x[2] for x in indices) / len(indices)
        print(f'指数平均涨跌: {avg_chg:+.2f}%')
        for name, price, chg in indices:
            arrow = '+' if chg > 0 else ''
            print(f'  {name}: {price:.2f} ({arrow}{chg:.2f}%)')
    else:
        avg_chg = 0

    print()

    # 3. 情绪指数
    sentiment, money_effect = calc_sentiment_index(limit_up, limit_down, highest_board, avg_chg)
    phase, advice = get_sentiment_phase(sentiment)

    print(f'情绪指数: {sentiment:.0f}/100')
    print(f'赚钱效应: ~{money_effect:.0f}%')
    print(f'当前阶段: {phase}')
    print(f'操作建议: {advice}')
    print()

    # 4. 阶段特征（情绪周期学习手册）
    phase_features = {
        '高潮期': '涨停>100家，连板9板+，赚钱效应>80%',
        '发酵期': '涨停50-80家，连板6-8板，赚钱效应50-60%',
        '启动期或退潮期': '涨停30-50家，连板4-5板，赚钱效应30-40%',
        '衰退期': '涨停<30家，跌停>10家，赚钱效应恶化',
        '冰点期': '涨停<20家，跌停>50家，赚钱效应极差',
    }
    print(f'阶段特征: {phase_features.get(phase, "N/A")}')
    print('='*55)

    return {
        'time': now,
        'limit_up': limit_up,
        'limit_down': limit_down,
        'highest_board': highest_board,
        'sentiment_index': sentiment,
        'money_effect': money_effect,
        'phase': phase,
        'advice': advice,
        'indices': indices,
    }

if __name__ == '__main__':
    result = run_sentiment_check()
    # Save to file
    save_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\sentiment_latest.json'
    import os
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'Saved to {save_path}')