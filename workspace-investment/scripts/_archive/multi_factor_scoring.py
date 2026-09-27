# -*- coding: utf-8 -*-
"""多因子趋势选股模型 v3.0 - 完整版"""
import io
import requests, re, json, math, ssl, urllib.request, time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 数据源降级工具
try:
    from src.data_source import fetch_with_fallback
    HAS_DATA_SOURCE = True
except ImportError:
    HAS_DATA_SOURCE = False

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
EM_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Referer': 'https://finance.eastmoney.com/'}

# ==================== 工具函数 ====================

def get_tencent_quote(code, market):
    mkt = 'sz' if market == 0 else 'sh'
    url = f'https://qt.gtimg.cn/q={mkt}{code}'
    try:
        r = requests.get(url, timeout=5)
        content = r.text.strip()
        if '="' in content:
            content = content.split('="')[1].rstrip('";')
        fields = content.split('~')
        if len(fields) > 50:
            return {
                'price': float(fields[3]) if fields[3] else 0,
                'pre_close': float(fields[4]) if fields[4] else 0,
                'chg_pct': float(fields[32]) if fields[32] else 0,
                'vol_ratio': float(fields[49]) if fields[49] else 0,
            }
    except:
        pass
    return None

def get_kline(code, market, days=250):
    """获取日K线数据。主：push2his；降级：腾讯ifzq。"""
    secid = f'{market}.{code}'
    em_url = (f'https://push2his.eastmoney.com/api/qt/stock/kline/get'
              f'?fields1=f1,f2,f3,f4,f5,f6'
              f'&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61'
              f'&ut=fa5fd1943c7b386f172d6893dbfba10b&klt=101&fqt=1'
              f'&secid={secid}&beg=0&end=20500101')
    
    # 腾讯ifzq前复权接口（降级备选）
    mkt = 'sh' if market == 1 else 'sz'
    tencent_url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={mkt}{code},day,2019-01-01,2050-01-01,500,qfq'
    
    # 优先尝试东方财富
    data = None
    if HAS_DATA_SOURCE:
        data = fetch_with_fallback(em_url, [tencent_url], headers=EM_HEADERS, timeout=12)
    else:
        try:
            r = requests.get(em_url, timeout=10, headers=EM_HEADERS)
            data = r.text
        except:
            pass
    
    if data:
        try:
            d = json.loads(data)
            klines = []
            raw_bars = None
            if d.get('data') and d['data'].get('klines'):
                raw_bars = d['data']['klines'][-days:]
            elif 'qfqday' in data or 'klines' in data:  # 腾讯格式
                stock_data = d.get('data', {}).get(f'{mkt}{code}', {})
                raw_bars = (stock_data.get('qfqday') or stock_data.get('day', []))[-days:]
            if raw_bars:
                for kl in raw_bars:
                    if isinstance(kl, list) and len(kl) >= 6:
                        klines.append({'date': kl[0], 'open': float(kl[1]), 'high': float(kl[2]),
                                       'low': float(kl[4]), 'close': float(kl[3]), 'vol': float(kl[5])})
                    elif isinstance(kl, str):
                        p = kl.split(',')
                        if len(p) >= 6:
                            klines.append({'date': p[0], 'open': float(p[1]), 'high': float(p[2]),
                                           'low': float(p[3]), 'close': float(p[4]), 'vol': float(p[5])})
                return klines
        except:
            pass
    return None

def get_money_flow(code, market):
    """获取5日主力净流入（亿元）。降级：push2失败时返回None（不计入评分）。"""
    secid = f'{market}.{code}'
    url = (f'https://push2.eastmoney.com/api/qt/stock/fflow/kline/get'
           f'?lmt=0&klt=1&fields1=f1,f2,f3,f7'
           f'&fields2=f51,f52,f53,f54,f55,f56'
           f'&ut=fa5fd1943c7b386f172d6893dbfba10b&secid={secid}')
    data = fetch_with_fallback(url, [], headers=EM_HEADERS, timeout=8) if HAS_DATA_SOURCE else None
    if data is None:
        try:
            r = requests.get(url, timeout=8, headers=EM_HEADERS)
            data = r.text
        except:
            return None  # 降级：失败不返回0（避免拉低评分），返回None由调用方处理
    try:
        d = json.loads(data)
        if d.get('data') and d['data'].get('klines'):
            total = 0
            for kl in d['data']['klines'][-5:]:
                parts = kl.split(',')
                if len(parts) >= 2 and parts[1]:
                    total += float(parts[1])
            return total / 100000000
    except:
        pass
    return None

def get_margin_balance(code, market):
    """获取融资占市值比。降级：push2失败时返回None。"""
    secid = f'{market}.{code}'
    url = f'https://push2.eastmoney.com/api/qt/stock/get?fields=f47,f48,f49,f50&secid={secid}'
    data = fetch_with_fallback(url, [], headers=EM_HEADERS, timeout=6) if HAS_DATA_SOURCE else None
    if data is None:
        try:
            r = requests.get(url, timeout=6, headers=EM_HEADERS)
            data = r.text
        except:
            return None
    try:
        d = json.loads(data)
        if d.get('data'):
            data = d['data']
            rz_ratio = data.get('f50', 0) / 100 if data.get('f50') else 0
            return rz_ratio
    except:
        pass
    return None

def get_announcements(code, market, count=30):
    secid = f'{market}.{code}'
    url = f'https://np-anotice-stock.eastmoney.com/api/security/ann?sr=-1&page_size={count}&page_index=1&ann_type=SHA%2CSZA&stock_list={secid}'
    try:
        r = requests.get(url, timeout=8)
        d = r.json()
        if d.get('data') and d['data'].get('list'):
            return d['data']['list']
    except:
        pass
    return []

def get_market_news(count=80):
    news = []
    # 东财快讯
    url = f'https://newsapi.eastmoney.com/kuaixun/v1/getlist_126_ajaxResult_{count}_1_.html'
    try:
        r = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.eastmoney.com'})
        m = re.search(r'ajaxResult=(.+)', r.text)
        if m:
            d = json.loads(m.group(1))
            for item in d.get('LivesList', []):
                news.append({'title': item.get('title', ''), 'source': '东财'})
    except:
        pass
    # 新浪财经
    url2 = f'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&num={count}&versionNumber=1.2.4&encode=utf-8'
    try:
        r = requests.get(url2, timeout=8)
        d = r.json()
        if d.get('result') and d['result'].get('data'):
            for item in d['result']['data']:
                news.append({'title': item.get('title', ''), 'source': '新浪'})
    except:
        pass
    return news

# ==================== 技术指标 ====================

def calc_ma(closes, period):
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period

def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    if len(gains) < period:
        return None
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def calc_macd(closes):
    if len(closes) < 26:
        return None, None
    ema12 = sum(closes[:12]) / 12
    k = 2 / 13
    for price in closes[12:]:
        ema12 = price * k + ema12 * (1 - k)
    ema26 = sum(closes[:26]) / 26
    k = 2 / 27
    for price in closes[26:]:
        ema26 = price * k + ema26 * (1 - k)
    dif = ema12 - ema26
    dea = dif * 0.8
    macd = (dif - dea) * 2
    return dif, macd

def calc_bollinger(closes, period=20):
    if len(closes) < period:
        return None, None, None
    recent = closes[-period:]
    mid = sum(recent) / period
    variance = sum((c - mid) ** 2 for c in recent) / period
    std = math.sqrt(variance)
    return mid + 2 * std, mid, mid - 2 * std

# ==================== 舆情分析 ====================

CATEGORY_PATTERNS = {
    '政策': ['政策', '证监会', '银保监', '央行', '财政部', '工信部', '发改委', '监管'],
    '业绩': ['业绩', '营收', '净利润', '增长', '下滑', '盈利', '亏损', '季报', '年报'],
    '订单': ['订单', '签约', '中标', '合同', '供货', '交付'],
    '产品': ['产品', '新品', '上市', '发布', '量产', '迭代'],
    '合作': ['合作', '并购', '收购', '重组', '增持', '回购'],
    '风险': ['问询函', '监管函', '处罚', '调查', '警示函', '整改'],
}

SENTIMENT_PATTERNS = {
    '利好': ['增长', '盈利', '超预期', '中标', '签约', '合作', '回购', '增持', '新品', '突破', '创新高', '订单', '政策支持', '补贴', '产能扩张'],
    '利空': ['下降', '亏损', '下滑', '减持', '处罚', '调查', '问询函', '预警', '业绩预减', '商誉减值', '诉讼', '终止'],
}

def classify_news(title):
    text = title.lower()
    cat = '其他'
    for c, patterns in CATEGORY_PATTERNS.items():
        if any(p.lower() in text for p in patterns):
            cat = c
            break
    sent = '中性'
    for s, patterns in SENTIMENT_PATTERNS.items():
        if any(p.lower() in text for p in patterns):
            sent = s
            break
    return cat, sent

def analyze_sentiment(keywords):
    """分析舆情"""
    news = get_market_news(80)
    pos = neg = cat_count = industry_news = 0
    risk_signals = []
    categories = {}

    for item in news:
        title = item.get('title', '')
        cat, sent = classify_news(title)
        categories[cat] = categories.get(cat, 0) + 1

        if sent == '利好':
            pos += 1
        elif sent == '利空':
            neg += 1

        # 行业/个股相关
        if any(kw.lower() in title.lower() for kw in keywords):
            industry_news += 1

        # 风险
        if cat == '风险':
            risk_signals.append(title[:50])

    # 评分
    score = 5
    if pos > neg * 2:
        score += 3
    elif neg > pos * 2:
        score -= 3
    if industry_news >= 5:
        score += 2
    elif industry_news >= 2:
        score += 1
    score -= min(len(risk_signals) * 2, 4)
    score = max(0, min(10, score))

    return {
        'score': score,
        'pos': pos,
        'neg': neg,
        'industry_news': industry_news,
        'risk_signals': risk_signals[:3],
        'categories': categories,
        'sentiment': '偏利好' if pos > neg * 2 else '偏利空' if neg > pos * 2 else '中性'
    }

# ==================== 完整分析 ====================

def analyze(code, market, name, keywords):
    result = {
        'code': code, 'market': '沪' if market == 1 else '深',
        'name': name, 'keywords': keywords,
        'sections': {},
        'total_score': 0,
        'details': []
    }

    # 数据获取
    quote = get_tencent_quote(code, market)
    klines = get_kline(code, market, 250)
    if not quote or not klines:
        result['error'] = '数据获取失败'
        return result

    closes = [k['close'] for k in klines]
    price = quote['price']
    chg_pct = quote['chg_pct']
    vol_ratio = quote['vol_ratio']
    result['price'] = price
    result['chg_pct'] = chg_pct
    result['vol_ratio'] = vol_ratio

    score = 0

    # ========== 技术面 (40分) ==========
    tech_score = 0
    tech_details = []

    ma5 = calc_ma(closes, 5)
    ma10 = calc_ma(closes, 10)
    ma20 = calc_ma(closes, 20)
    ma60 = calc_ma(closes, 60)

    # 均线多头
    if ma5 and ma10 and ma20:
        if ma5 > ma10 > ma20:
            tech_score += 15
            tech_details.append('✅均线多头(+15)')
        elif ma5 > ma10:
            tech_score += 8
            tech_details.append('⚠️MA5>MA10(+8)')

    # RSI
    rsi = calc_rsi(closes, 14)
    if rsi:
        if 30 <= rsi <= 70:
            tech_score += 10
            tech_details.append(f'✅RSI={rsi:.0f}(+10)')
        elif rsi < 30:
            tech_score += 5
            tech_details.append(f'⚠️RSI超卖={rsi:.0f}(+5)')

    # MACD
    dif, macd = calc_macd(closes)
    if dif and macd is not None:
        if dif > 0 and macd > 0:
            tech_score += 10
            tech_details.append('✅MACD多头(+10)')
        elif dif > 0:
            tech_score += 5
            tech_details.append('⚠️DIF>0(+5)')

    # 量比
    if 1.2 <= vol_ratio <= 2.0:
        tech_score += 5
        tech_details.append(f'✅量比={vol_ratio}(+5)')
    elif vol_ratio > 0.5:
        tech_score += 2
        tech_details.append(f'⚠️量比={vol_ratio}(+2)')

    result['sections']['技术面'] = {'score': tech_score, 'max': 40, 'details': tech_details}
    score += tech_score

    # ========== 布林带 (5分) ==========
    bb_up, bb_mid, bb_low = calc_bollinger(closes)
    bb_score = 0
    bb_details = []
    if bb_up and bb_low:
        bw = (bb_up - bb_low) / bb_mid * 100 if bb_mid else 0
        if bw < 5:
            bb_score = 5
            bb_details.append(f'✅布林带收口({bw:.1f}%)(+5)')

    result['sections']['布林带'] = {'score': bb_score, 'max': 5, 'details': bb_details}
    score += bb_score

    # ========== 均线支撑 (5分) ==========
    ma_score = 0
    ma_details = []
    if ma60 and price > ma60:
        ma_score = 5
        ma_details.append(f'✅MA60支撑({ma60:.2f})上方(+5)')

    result['sections']['均线支撑'] = {'score': ma_score, 'max': 5, 'details': ma_details}
    score += ma_score

    # ========== 资金面 (20分) ==========
    money_score = 0
    money_details = []

    main_net_5d = get_money_flow(code, market)
    if main_net_5d is not None:
        if main_net_5d > 0:
            money_score += 15
            money_details.append(f'东财5日主力净流入{main_net_5d:.2f}亿(+15)')
        elif main_net_5d > -1:
            money_score += 8
            money_details.append(f'东财5日主力小幅流出{main_net_5d:.2f}亿(+8)')
        else:
            money_score += 2
            money_details.append(f'东财5日主力净流出{main_net_5d:.2f}亿(+2)')
    elif klines and len(klines) >= 5:
        # 东财不可用时的降级：用换手率和量比代理资金面
        today_vol = klines[-1].get('vol', 0)
        avg_vol_5d = sum(k.get('vol', 0) for k in klines[-5:]) / 5
        vol_ratio = today_vol / avg_vol_5d if avg_vol_5d > 0 else 0
        # 量比打分 (0-10)
        if vol_ratio >= 2.0:
            vol_proxy_score = 10
        elif vol_ratio >= 1.5:
            vol_proxy_score = 7
        elif vol_ratio >= 1.2:
            vol_proxy_score = 5
        elif vol_ratio >= 0.8:
            vol_proxy_score = 3
        else:
            vol_proxy_score = 1
        money_score += vol_proxy_score
        money_details.append(f'量比{vol_ratio:.2f}x(换手率代理,+{vol_proxy_score})')

    result['sections']['资金面'] = {'score': money_score, 'max': 20, 'details': money_details}
    score += money_score

    # ========== 融资融券 (10分) ==========
    margin_score = 0
    margin_details = []
    rz_ratio = get_margin_balance(code, market)
    if rz_ratio is not None:
        if rz_ratio > 20:
            margin_score = 3
            margin_details.append(f'东财融资占比高{rz_ratio:.1f}%(+3)')
        elif rz_ratio > 10:
            margin_score = 7
            margin_details.append(f'东财融资活跃{rz_ratio:.1f}%(+7)')
        elif rz_ratio > 0:
            margin_score = 5
            margin_details.append(f'东财融资正常{rz_ratio:.1f}%(+5)')
        else:
            margin_score = 2
            margin_details.append(f'东财无融资数据(+2)')
    elif quote and quote.get('turnover', 0) > 0:
        # 东财不可用时的降级：用换手率代理（换手率高=交易活跃=资金关注）
        turnover = quote['turnover']
        if turnover >= 10:
            margin_score = 7
        elif turnover >= 5:
            margin_score = 5
        elif turnover >= 2:
            margin_score = 3
        else:
            margin_score = 1
        margin_details.append(f'换手率{turnover:.1f}%代理融资活跃(+{margin_score})')
    else:
        margin_details.append('无融资数据(+0)')

    result['sections']['融资融券'] = {'score': margin_score, 'max': 10, 'details': margin_details}
    score += margin_score

    # ========== 风险公告 (10分) ==========
    risk_score = 0
    risk_details = []
    anns = get_announcements(code, market, 50)
    risk_kw = ['问询函', '监管函', '处罚', '警示函', '整改', '立案']
    high_risk = [a.get('title', '')[:40] for a in anns if any(kw in a.get('title', '') for kw in risk_kw)]
    if not high_risk:
        risk_score = 10
        risk_details.append('✅无风险公告(+10)')
    else:
        risk_score = 0
        risk_details.append(f'🔴{len(high_risk)}条风险公告(+0)')

    result['sections']['风险公告'] = {'score': risk_score, 'max': 10, 'details': risk_details}
    score += risk_score

    # ========== 舆情 (10分) ==========
    sent = analyze_sentiment(keywords)
    sent_details = []
    if sent['industry_news'] >= 5:
        sent_details.append(f'行业舆情{sent["industry_news"]}条(+2)')
    elif sent['industry_news'] >= 1:
        sent_details.append(f'行业舆情{sent["industry_news"]}条(+1)')
    if sent['risk_signals']:
        sent_details.append(f'风险信号{len(sent["risk_signals"])}条(-{min(len(sent["risk_signals"])*2,4)})')
    sent_details.append(f'{sent["sentiment"]}({sent["pos"]}利好/{sent["neg"]}利空)')

    result['sections']['舆情'] = {'score': sent['score'], 'max': 10, 'details': sent_details}
    result['sentiment_detail'] = sent
    score += sent['score']

    # ========== MXSearch舆情 (10分) ==========
    mx_score = 0
    mx_details = []
    try:
        from mx_signal_loader import get_mx_sentiment
        mx_sig = get_mx_sentiment(code)
        if mx_sig:
            mx_score = mx_sig.get('mx_sentiment_score', 0)
            mx_details.append(f"MX信号:{mx_sig.get('name','')} score={mx_score}")
            if mx_sig.get('has_positive'):
                mx_details.append(f"正面关键词: {mx_sig.get('keywords',{}).get('positive',[])[:3]}")
            if mx_sig.get('has_negative'):
                mx_details.append(f"负面关键词: {mx_sig.get('keywords',{}).get('negative',[])[:3]}")
        else:
            mx_details.append('无MX舆情信号')
    except Exception as e:
        mx_details.append(f'MX信号读取失败: {e}')

    result['sections']['MX舆情'] = {'score': mx_score, 'max': 10, 'details': mx_details}
    score += mx_score

    # ========== ML因子 (10分) - Plan A ==========
    try:
        from ml_factor_loader import get_ml_prob, prob_to_score
        ml_prob = get_ml_prob(code)
        if ml_prob is not None:
            ml_score = prob_to_score(ml_prob)
            ml_details = [f'P(上涨)={ml_prob:.3f} -> {ml_score:.1f}分']
        else:
            ml_score = 0
            ml_details = ['无ML信号(模型未训练或股票不在池内)']
    except Exception:
        ml_score = 0
        ml_details = ['ML因子加载失败']
    result['sections']['ML信号'] = {'score': ml_score, 'max': 10, 'details': ml_details}
    result['ml_prob'] = ml_prob
    score += ml_score

    result['total_score'] = score
    return result

# ==================== 打印报告 ====================

def print_report(r):
    if 'error' in r:
        print(f"\n{r['code']} {r['error']}")
        return

    print(f"\n{'='*65}")
    print(f" {r['name']}({r['code']}) {'='*40}")
    print(f"{'='*65}")
    print(f" 现价:{r['price']:.2f} | 涨幅:{r['chg_pct']:.2f}% | 量比:{r['vol_ratio']:.2f}")
    print(f"\n{'维度':<10} {'得分':>6}/{'满分':>4}  说明")
    print(f" {'-'*60}")

    for section, data in r['sections'].items():
        bar = '█' * (data['score'] * 20 // data['max']) + '░' * (20 - data['score'] * 20 // data['max'])
        print(f" {section:<10} {data['score']:>5}/{data['max']:<4} [{bar}]")
        for d in data.get('details', []):
            print(f"   • {d}")

    print(f" {'-'*60}")
    total_max = sum(v['max'] for v in r['sections'].values())
    print(f" {'总分':<10} {r['total_score']:>5}/{total_max}")

    if r['sentiment_detail'].get('industry_news'):
        cats = r['sentiment_detail'].get('categories', {})
        if cats:
            cat_str = ' '.join([f'{k}[{v}]' for k, v in sorted(cats.items(), key=lambda x: -x[1])])
            print(f" 消息分布: {cat_str}")

    print(f" {'-'*65}")

def score_to_level(score):
    # 110分制：75分约等于原100分的75th percentile
    if score >= 82:  # ~75%
        return '⭐强烈推荐'
    elif score >= 66:  # ~60%
        return '✅关注'
    elif score >= 50:  # ~45%
        return '⚠️观察'
    else:
        return '❌不关注'

# ==================== 主函数 ====================

def main():
    print("="*65)
    print(" 多因子趋势选股模型 v3.0 - 完整版")
    print("="*65)

    stocks = [
        ('600549', 1, '厦门钨业', ['厦门钨业', '钨', '稀土', '有色金属']),
        ('300492', 0, '华图山鼎', ['华图山鼎', '建筑设计', '工程咨询']),
    ]

    results = []
    for code, mkt, name, keywords in stocks:
        r = analyze(code, mkt, name, keywords)
        results.append(r)
        print_report(r)

    print("\n" + "="*65)
    print(" 评分标准: 75+强烈推荐 60+关注 45+观察 45以下不关注")
    print(" 维度: 技术面(40) 布林带(5) 均线支撑(5) 资金面(20) 融资融券(10) 风险公告(10) 舆情(10) ML信号(10)")
    print("="*65)

    # 简评
    print("\n【综合简评】")
    for r in results:
        if 'error' in r:
            continue
        level = score_to_level(r['total_score'])
        print(f" {r['name']}: {r['total_score']}分 {level}")

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()