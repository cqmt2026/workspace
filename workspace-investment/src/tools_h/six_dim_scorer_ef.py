# -*- coding: utf-8 -*-
"""
六维选股评分器 v3.0（腾讯+东方财富API版）
功能：对持仓/自选股进行六维评分：政策+题材+情绪+量价+技术+周期
"""
import json
import urllib.request
import datetime
import os

SEP = "=" * 55

# ======== 静态板块映射（更可靠）=======
SECTOR_MAP = {
    '600549': {'sector': '有色金属', 'industry': '稀土', 'concept': '稀土 钨'},
    '000539': {'sector': '电力', 'industry': '火力发电', 'concept': '电力 粤港澳'},
}

# ======== 数据获取 ========

def get_rt_tencent(code, market):
    """腾讯实时行情（更可靠）"""
    mkt_map = {'1': 'sh', '0': 'sz'}
    mkt = mkt_map.get(market, 'sz')
    url = 'https://qt.gtimg.cn/q=' + mkt + code
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.qq.com'})
    resp = urllib.request.urlopen(req, timeout=8)
    raw = resp.read().decode('gbk', errors='replace')
    parts = raw.split('~')
    if len(parts) < 40:
        return {'name': '', 'price': 0, 'prev_close': 0, 'chg_pct': 0,
                'high': 0, 'low': 0, 'open': 0, 'vol': 0}
    cur = float(parts[3]) if parts[3] else 0
    prev = float(parts[4]) if parts[4] else cur
    chg_pct = float(parts[32]) if parts[32] else 0
    return {
        'name': parts[1],
        'price': cur,
        'prev_close': prev,
        'chg_pct': chg_pct,
        'high': float(parts[33]) if parts[33] else cur,
        'low': float(parts[34]) if parts[34] else cur,
        'open': float(parts[5]) if parts[5] else cur,
        'vol': float(parts[6]) if parts[6] else 0,  # 手
    }

def get_kline_ef(code, market, count=60):
    """东方财富日K线（固定取最近count个交易日）"""
    secid = market + "." + code
    # beg=20260101 强制从2026年起，确保lmt生效
    url = ("https://push2his.eastmoney.com/api/qt/stock/kline/get"
           "?secid=" + secid + "&fields1=f1,f2,f3,f4,f5,f6"
           "&fields2=f51,f52,f53,f54,f55,f56,f57,f58"
           "&klt=101&fqt=1&beg=20260101&end=20500101&lmt=" + str(count + 20))
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.eastmoney.com'})
    resp = urllib.request.urlopen(req, timeout=10)
    klines_raw = json.loads(resp.read().decode('utf-8')).get('data', {}).get('klines', [])
    result = []
    for k in klines_raw[-count:]:  # 只取最后count条
        p = k.split(',')
        result.append({
            'date': p[0], 'open': float(p[1]), 'close': float(p[2]),
            'high': float(p[3]), 'low': float(p[4]), 'vol': float(p[5])})
    return result

# ======== 六维评分 ========

def ema(data, n):
    k_val = 2/(n+1)
    r = [data[0]]
    for p in data[1:]: r.append(p*k_val + r[-1]*(1-k_val))
    return r

def calc_macd(closes):
    e12 = ema(closes, 12)
    e26 = ema(closes, 26)
    dif = [e12[i]-e26[i] for i in range(len(closes))]
    dea = ema(dif, 9)
    hist = [2*(dif[i]-dea[i]) for i in range(len(dif))]
    return dif, dea, hist

def score_policy(sector, industry, concept):
    hot = {
        'AI': 20, '人工智能': 20, '算力': 19, '大模型': 19,
        '芯片': 18, '半导体': 18, '光刻机': 18,
        '新能源': 16, '光伏': 16, '风电': 16,
        '锂电池': 16, '固态电池': 16,
        '稀土': 17, '有色金属': 15, '钨': 16,
        '医药': 14, '创新药': 14,
        '军工': 14, '航天': 14,
        '电力': 13, '电网': 12,
        '银行': 10, '券商': 11,
        '房地产': 6, '基建': 8,
        '消费': 12, '家电': 10,
        '储能': 14, '充电桩': 12,
    }
    text = (sector + " " + industry + " " + concept).lower()
    for kw, s in hot.items():
        if kw.lower() in text:
            return s, kw + "(政策支持)"
    return 10, "一般"

def score_topic(sector, industry, concept, name):
    hot = {
        'AI': 15, '人工智能': 15, '算力': 14,
        '芯片': 13, '半导体': 13,
        '新能源': 12, '锂电池': 12,
        '稀土': 14, '有色': 12, '钨': 14,
        '机器人': 11, '无人机': 11,
        '低空经济': 13, '商业航天': 12,
        '医药': 10, '疫苗': 10,
        '电力': 11, '电网': 11,
        '固态电池': 13, '储能': 12,
        '粤港澳': 10, '大湾区': 10,
    }
    text = (sector + " " + industry + " " + concept + " " + name).lower()
    for kw, s in hot.items():
        if kw.lower() in text:
            return s, kw + "(热点题材)"
    return 7, "一般题材"

def score_sentiment(klines):
    """情绪维（20分）：近20日涨停频率 + 趋势强度"""
    if len(klines) < 20:
        return 10, '数据不足'
    closes = [k['close'] for k in klines]
    chg_pct = (closes[-1] - closes[-2]) / closes[-2] * 100 if len(closes) >= 2 else 0
    up_days = sum(1 for i in range(1, min(21, len(closes)))
                  if (closes[i] - closes[i-1]) / closes[i-1] > 0.09)
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    trend = (ma5 - ma20) / ma20 * 100
    base = 10
    if up_days >= 3: base += 5
    elif up_days >= 1: base += 2
    if trend > 5: base += 3
    elif trend < -5: base -= 3
    if chg_pct > 5: base += 2
    note = "近20日涨停%d次 趋势%+.1f%%" % (up_days, trend)
    return min(20, max(0, base)), note

def score_vol_price(klines):
    """量价维（20分）：量价配合分析"""
    if len(klines) < 20:
        return 10, '数据不足'
    vols = [k['vol'] for k in klines]
    closes = [k['close'] for k in klines]
    avg_vol = sum(vols[:-1]) / max(1, len(vols[:-1]))
    today_vol = vols[-1]
    vol_ratio = today_vol / avg_vol if avg_vol > 0 else 1
    price_chg = (closes[-1] - closes[-2]) / closes[-2] if closes[-2] > 0 else 0
    vol_chg = (vols[-1] - vols[-2]) / vols[-2] if vols[-2] > 0 else 0
    score = 10
    if 0.8 <= vol_ratio <= 2.0: score += 3
    elif vol_ratio > 3: score -= 2
    elif vol_ratio < 0.5: score += 1
    if price_chg > 0 and vol_chg > 0: score += 3
    elif price_chg > 0 and vol_chg < 0: score -= 1
    elif price_chg < 0 and vol_chg < 0: score += 2
    elif price_chg < 0 and vol_chg > 0: score -= 3
    note = "量比%.1fx" % vol_ratio
    return min(20, max(0, score)), note

def score_technical(klines):
    """技术维（15分）：均线多头/MACD"""
    if len(klines) < 60:
        return 7, '数据不足60日'
    closes = [k['close'] for k in klines]
    ma5 = sum(closes[-5:]) / 5
    ma10 = sum(closes[-10:]) / 10
    ma20 = sum(closes[-20:]) / 20
    ma60 = sum(closes[-60:]) / 60
    cur = closes[-1]
    dif, dea, hist = calc_macd(closes)
    score = 7
    if ma5 > ma10 > ma20: score += 4
    elif ma5 > ma10: score += 2
    elif ma5 < ma10 < ma20: score -= 2
    if dif[-1] > 0 and hist[-1] > 0: score += 2
    elif dif[-1] < 0: score -= 1
    if cur > ma20: score += 1
    if cur > ma60: score += 1
    else: score -= 1
    note = "MA5=%.2f MA20=%.2f MA60=%.2f DIF=%+.3f" % (ma5, ma20, ma60, dif[-1])
    return min(15, max(0, score)), note

def score_cycle(klines):
    """周期维（10分）：相对历史位置"""
    if len(klines) < 60:
        return 5, '数据不足'
    highs = [k['high'] for k in klines]
    lows = [k['low'] for k in klines]
    cur = klines[-1]['close']
    high60 = max(highs[-60:])
    low60 = min(lows[-60:])
    range_pct = (cur - low60) / (high60 - low60) * 100 if high60 > low60 else 50
    score = 5
    if range_pct > 80: score -= 2
    elif range_pct < 20: score += 3
    elif range_pct > 50: score += 1
    note = "60日位置%.0f%%" % range_pct
    return min(10, max(0, score)), note

def six_dim_score(code, market, name=''):
    stock_sector = SECTOR_MAP.get(code, {'sector': '', 'industry': '', 'concept': ''})
    print("\n" + SEP)
    print(name + " (" + market + "." + code + ") 六维评分")
    print(SEP)
    rt = get_rt_tencent(code, market)
    print("现价: %.2f  昨收: %.2f  涨跌幅: %+.2f%%" % (rt['price'], rt['prev_close'], rt['chg_pct']))
    klines = get_kline_ef(code, market, 60)
    print("K线数据: %d条 (%s ~ %s)" % (len(klines), klines[0]['date'], klines[-1]['date']))
    print("板块: %s | 行业: %s | 概念: %s" % (
        stock_sector['sector'], stock_sector['industry'], stock_sector['concept']))
    p1, n1 = score_policy(stock_sector['sector'], stock_sector['industry'], stock_sector['concept'])
    p2, n2 = score_topic(stock_sector['sector'], stock_sector['industry'], stock_sector['concept'], rt['name'])
    p3, n3 = score_sentiment(klines)
    p4, n4 = score_vol_price(klines)
    p5, n5 = score_technical(klines)
    p6, n6 = score_cycle(klines)
    total = p1 + p2 + p3 + p4 + p5 + p6
    print("  政策维(20): %2d  %s" % (p1, n1))
    print("  题材维(15): %2d  %s" % (p2, n2))
    print("  情绪维(20): %2d  %s" % (p3, n3))
    print("  量价维(20): %2d  %s" % (p4, n4))
    print("  技术维(15): %2d  %s" % (p5, n5))
    print("  周期维(10): %2d  %s" % (p6, n6))
    print("  " + ("=" * 30))
    print("  综合总分(100): %d/100" % total)
    rating = 'A+' if total >= 85 else 'A' if total >= 75 else 'B+' if total >= 65 else 'B' if total >= 55 else 'C'
    print("  评级: %s" % rating)
    return total, rating, {'p1': p1, 'p2': p2, 'p3': p3, 'p4': p4, 'p5': p5, 'p6': p6}

if __name__ == '__main__':
    stocks = [('600549', '1', '厦门钨业'), ('000539', '0', '粤电力A')]
    results = []
    for code, mkt, name in stocks:
        total, rating, detail = six_dim_score(code, mkt, name)
        results.append({
            'code': code, 'market': mkt, 'name': name,
            'total': total, 'rating': rating, 'detail': detail})
    save_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\data\stock_score_latest.json'
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump({
            'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            'stocks': results
        }, f, ensure_ascii=False, indent=2)
    print("\n结果已保存到 " + save_path)