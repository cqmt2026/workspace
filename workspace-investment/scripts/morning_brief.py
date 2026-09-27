# -*- coding: utf-8 -*-
"""
晨间简报 - 全方位投资早报
2026-07-10 09:24 (周五)
"""
import sys, os, json, urllib.request, sqlite3
from datetime import datetime, date, timedelta
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
DB = r'F:\market_data.db'
OUT_DIR = os.path.join(WORKSPACE, 'out_data')
RPS_HIST = os.path.join(OUT_DIR, 'rps_history')
PORTFOLIO_PATH = os.path.join(WORKSPACE, 'data', 'portfolio.json')
os.makedirs(OUT_DIR, exist_ok=True)

today = date.today()
today_str = today.strftime('%Y%m%d')
today_fmt = today.strftime('%Y-%m-%d')
# 获取上一个交易日（不能简单减1天，要跳过周末/节假日）
conn_tmp = sqlite3.connect(DB)
prev_row = conn_tmp.execute(
    "SELECT MAX(date) FROM daily_k WHERE date < ? AND code LIKE '%.%'", (today_fmt,)
).fetchone()
prev_date = prev_row[0] if prev_row else (today - timedelta(days=1)).strftime('%Y-%m-%d')
prev_row2 = conn_tmp.execute(
    "SELECT MAX(date) FROM daily_k WHERE date < ? AND code LIKE '%.%'", (prev_date,)
).fetchone()
prev_date2 = prev_row2[0] if prev_row2 else (today - timedelta(days=2)).strftime('%Y-%m-%d')
conn_tmp.close()

lines = []

def p(s=""):
    lines.append(s)
    print(s)

# =============================================
p("=" * 66)
p(f"  📊 投资早报 | {today_fmt} 周五")
p("=" * 66)
p()

# ---- 1. 隔夜外盘 (通过 web_fetch 模拟 - 用新浪接口) ----
p("🌏 【隔夜外盘】")
try:
    # 美股指数
    us_codes = '.DJI,.IXIC,.INX'
    url = f'https://hq.sinajs.cn/list=gb_{us_codes.replace(".","").replace(",",",gb_")}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn'})
    resp = urllib.request.urlopen(req, timeout=8)
    raw = resp.read().decode('gbk')
    for line in raw.strip().split('\n'):
        if '~' not in line and '=' not in line:
            continue
        p(f"  {line[:120]}")
except Exception as e:
    p(f"  美股行情获取失败: {e}")

# 用新浪国际指数API
try:
    url = 'https://hq.sinajs.cn/list=hf_DJI,hf_IXIC,hf_INX,hf_CL,hf_GC,hf_SI,hf_USDCNY'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn'})
    resp = urllib.request.urlopen(req, timeout=8)
    raw = resp.read().decode('gbk')
    p("  外盘(新浪):")
    for line in raw.strip().split('\n'):
        if not line.strip():
            continue
        p(f"  {line.strip()[:150]}")
except Exception as e:
    p(f"  外盘(新浪)失败: {e}")

# 备用外盘数据：尝试腾讯接口（期货/外汇可用，美股指数不可用）
p()
p("🌐 【备用外盘(期货/外汇)】")
try:
    # 腾讯API不支持美股指数(gb_*)，只支持期货(hf_*)和外汇
    us_codes = 'hf_CL,hf_GC,hf_SI,hf_USDCNY'
    url = f'https://qt.gtimg.cn/q={us_codes}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=8)
    raw = resp.read().decode('gbk', errors='replace')
    found = False
    for line in raw.strip().split(';\n'):
        if not line.strip() or 'none_match' in line:
            continue
        if '=' not in line or '~' not in line:
            continue
        parts = line.split('=')
        if len(parts) < 2:
            continue
        vals = parts[1].strip('"').split('~')
        if len(vals) >= 15:
            name = vals[13] if len(vals) > 13 else '未知'
            price = vals[3] if vals[3] else '?'
            chg = vals[1] if vals[1] else '?'
            chg_pct = vals[2] if vals[2] else '?'
            p(f"  {name}: {price} ({chg} / {chg_pct}%)")
            found = True
    if not found:
        p("  (期货/外汇数据暂无)")
except Exception as e:
    p(f"  (备用外盘获取失败: {e})")
p()

# ---- 2. 市场宽度 ----
p("📏 【市场宽度】")
conn = sqlite3.connect(DB)
try:
    # 涨停数据
    zt_today = conn.execute("SELECT COUNT(*) FROM daily_zt WHERE trade_date=?", (today_fmt,)).fetchone()[0] or 0
    zt_prev = conn.execute("SELECT COUNT(*) FROM daily_zt WHERE trade_date=?", (prev_date,)).fetchone()[0] or 0
    zt_prev2 = conn.execute("SELECT COUNT(*) FROM daily_zt WHERE trade_date=?", (prev_date2,)).fetchone()[0] or 0

    # 个股涨跌统计 (从daily_k取最近两日)
    prev_close = conn.execute(
        "SELECT code, close FROM daily_k WHERE date=? AND code LIKE '%.%'", (prev_date,)
    ).fetchall()

    # 涨跌家数 (昨天 vs 前天)
    up, down, flat = 0, 0, 0
    for code, close in prev_close:
        prev2_close = conn.execute(
            "SELECT close FROM daily_k WHERE code=? AND date=?", (code, prev_date2)
        ).fetchone()
        if prev2_close:
            chg = (close - prev2_close[0]) / prev2_close[0] * 100
            if chg > 0: up += 1
            elif chg < 0: down += 1
            else: flat += 1

    p(f"  涨停家数: 昨{zt_prev}家 | 前{zt_prev2}家 | 今(盘中){zt_today}")
    p(f"  涨跌家数(昨): 涨{up}家 跌{down}家 平{flat}家")
    p(f"  上涨比例: {up/(up+down+flat)*100:.1f}%" if (up+down+flat) > 0 else "  上涨比例: N/A")

    # 连板统计
    try:
        lb = conn.execute(
            "SELECT name, code, lb_count FROM daily_zt WHERE trade_date=? AND lb_count>=2 ORDER BY lb_count DESC LIMIT 10",
            (prev_date,)
        ).fetchall()
        if lb:
            p(f"  连板梯队: {' | '.join([f'{n}({c[-6:]}) {l}b' for n,c,l in lb[:8]])}")
    except:
        pass
except Exception as e:
    p(f"  市场宽度获取失败: {e}")
conn.close()
p()

# ---- 3. 指数行情 ----
p("📈 【指数行情】")
import akshare as ak
indices = [
    ('sh000001', '上证指数'),
    ('sz399001', '深证成指'),
    ('sz399006', '创业板指'),
    ('sh000688', '科创50'),
    ('sh000016', '上证50'),
    ('sh000300', '沪深300'),
    ('sh000905', '中证500'),
]
for code, name in indices:
    try:
        df = ak.stock_zh_index_daily(symbol=code)
        df['date'] = df['date'].astype(str)
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else last
        chg_d = round((last['close'] - prev['close']) / prev['close'] * 100, 2)
        emoji = '🟢' if chg_d >= 0 else '🔴'
        vol_b = last['volume'] / 1e8
        p(f"  {emoji} {name}: {last['close']:.1f} ({chg_d:+.2f}%) 量{vol_b:.1f}亿")
    except Exception as e:
        p(f"  ⚠️ {name}: {e}")
p()

# ---- 4. 板块RPS ----
# 核心原则：不允许用旧数据填充。交易日当天RPS未采集时，明确标注数据缺失。
p("🏷️ 【板块RPS TOP10】")
rps_file = os.path.join(RPS_HIST, f"RPS_board_{today_str}.json")
if os.path.exists(rps_file):
    with open(rps_file, encoding='utf-8') as f:
        rps_data = json.load(f)
    boards = rps_data.get('rps_data', [])
    if boards:
        sorted_rps5 = sorted(boards, key=lambda x: x.get('rps_5d', 0), reverse=True)
        p(f"  {'板块':<12} {'RPS5':>6} {'RPS10':>6} {'RPS20':>6} {'涨幅':>7}")
        p(f"  {'-'*40}")
        for item in sorted_rps5[:10]:
            n = item.get('name','')
            r5 = item.get('rps_5d', 0)
            r10 = item.get('rps_10d', 0)
            r20 = item.get('rps_20d', 0)
            ret5 = item.get('returns', {}).get('5', 0)
            p(f"  {n:<12} {r5:>6.1f} {r10:>6.1f} {r20:>6.1f} {ret5:>+6.2f}%")
        p(f"\n  RPS5 BOTTOM5:")
        for item in sorted_rps5[-5:]:
            n = item.get('name','')
            r5 = item.get('rps_5d', 0)
            p(f"  {n:<12} RPS5={r5:>5.1f}")
    else:
        p("  (RPS文件存在但数据为空)")
else:
    p(f"  (数据缺失 — 今日RPS尚未采集，收盘后16:10自动生成)")
p()

# ---- 5. 个股RPS ----
p("🔍 【个股RPS TOP10】")
try:
    # 从DB读取个股每日涨幅
    conn2 = sqlite3.connect(DB)
    # daily_k表没有name和zdf列，用close计算涨跌幅
    rows = conn2.execute(
        "SELECT code, close FROM daily_k WHERE date=? AND code LIKE '%.%' ORDER BY rowid DESC LIMIT 100",
        (prev_date,)
    ).fetchall()
    if rows:
        # 计算每个code昨日的涨跌幅（与前一日比较）
        prev2 = (today - timedelta(days=2)).strftime('%Y-%m-%d')
        gains = []
        for code, close in rows:
            prev_row = conn2.execute(
                "SELECT close FROM daily_k WHERE code=? AND date=?", (code, prev2)
            ).fetchone()
            if prev_row:
                zdf = (close - prev_row[0]) / prev_row[0] * 100
                gains.append((code, zdf))
        gains.sort(key=lambda x: x[1], reverse=True)
        p("  (昨日涨幅TOP10)")
        for code, zdf in gains[:10]:
            code_short = code[3:] if '.' in code else code
            p(f"  🟢 {code_short} 涨幅{zdf:+.2f}%")
    else:
        p("  (个股日线数据未更新)")
    conn2.close()
except Exception as e:
    p(f"  个股RPS获取失败: {e}")
p()

# ---- 6. 持仓监控 ----
p("📋 【持仓监控】")
try:
    sys.path.insert(0, os.path.join(WORKSPACE, 'scripts'))
    # 直接读取portfolio.json
    if os.path.exists(PORTFOLIO_PATH):
        with open(PORTFOLIO_PATH, encoding='utf-8') as f:
            pf = json.load(f)
        holdings = pf.get('holdings', [])
        if holdings:
            p(f"  {'名称':<10}{'代码':<8}{'成本':>8}{'现价':>8}{'涨跌':>7}{'浮盈':>8}{'仓位':>6}")
            p(f"  {'-'*60}")
            total_pnl = 0
            total_cost = 0
            for h in holdings:
                code = h.get('code','')
                name = h.get('name','')
                cost = h.get('entry_price', h.get('buy_price', h.get('cost', 0)))
                shares = h.get('shares', 0)
                # 获取实时价（通过统一接口）
                try:
                    from data_api import DataAPI
                    # 标准化code：002837 -> sz.002837, 601888 -> sh.601888
                    std_code = f'sz.{code}' if code.startswith(('0', '3')) else f'sh.{code}'
                    rt = DataAPI.get_realtime([code])
                    if rt and std_code in rt:
                        price = rt[std_code]['price']
                        chg = round(rt[std_code]['chg_pct'], 2)
                    else:
                        price = cost
                        chg = 0
                except:
                    price = cost
                    chg = 0
                pnl = round((price - cost) * shares, 2)
                pnl_pct = round((price-cost)/cost*100, 2) if cost else 0
                pos_value = price * shares
                total_pnl += pnl
                total_cost += cost * shares
                emoji = '🟢' if pnl >= 0 else '🔴'
                pnl_pct_display = round((price-cost)/cost*100, 2) if cost else 0
                p(f"  {emoji} {name:<8} {code[-6:]:<8} {cost:>8.2f} {price:>8.2f} {chg:>+6.2f}% {pnl:>+8.2f} ({pnl_pct_display:+.1f}%) {pos_value:>8.0f}")
            p(f"  {'-'*60}")
            p(f"  总市值: {total_cost+total_pnl:.2f} | 总浮盈: {total_pnl:+.2f} ({round(total_pnl/total_cost*100,2) if total_cost else 0:+.2f}%)")
        else:
            p("  空仓")
    else:
        p("  (持仓文件未找到)")
except Exception as e:
    p(f"  持仓获取失败: {e}")
p()

# ---- 7. 大盘择时 ----
p("🎯 【大盘择时】")
timing = {'regime': '未知', 'market': '未知', 'position_limit': 0, 'reason': '数据采集失败', 'details': {'zt_score': 0, 'idx_score': 0, 'vol_score': 0, 'total_score': 0}}
try:
    sys.path.insert(0, os.path.join(WORKSPACE, 'scripts'))
    from market_timing import get_market_timing
    timing = get_market_timing(today_fmt)
    d = timing['details']
    emoji = '🟢' if timing['regime'] == '做多' else '🟡' if timing['regime'] == '谨慎' else '🔴'
    p(f"  {emoji} 判定: {timing['regime']} | 仓位上限: {timing['position_limit']*100:.0f}%")
    p(f"  理由: {timing['reason']}")
    p(f"  评分: 情绪{d['zt_score']} + 趋势{d['idx_score']} + 量能{d['vol_score']} = {d['total_score']}/6")
except Exception as e:
    p(f"  {e}")
p()

# ---- 8. 快讯 (金十) ----
p("⚡ 【今日快讯】")
try:
    # 动态查找最新金十文件
    jin10_dir = os.path.join(OUT_DIR)
    jin10_files = sorted([
        f for f in os.listdir(jin10_dir)
        if f.startswith('jin10_flash_') and f.endswith('.json')
    ])
    if jin10_files:
        latest_file = os.path.join(jin10_dir, jin10_files[-1])
        with open(latest_file, 'r', encoding='utf-8') as f:
            jin10_data = json.load(f)
        if jin10_data:
            for item in jin10_data[:10]:
                content = item.get('content', '')[:120]
                time_str = item.get('time', '')
                p(f"  [{time_str}] {content}")
        else:
            p("  (暂无快讯数据)")
    else:
        p("  (今日金十数据尚未采集，盘中每30分钟更新)")
except Exception as e:
    p(f"  (金十数据: {e})")

# 备用快讯
try:
    # 新浪财经头条
    url = 'https://vip.stock.finance.sina.com.cn/corp/view/vRSS_News.php?num=5'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=5)
    raw = resp.read().decode('gbk', errors='replace')
    p(f"  新浪财经: {raw[:300]}")
except:
    pass
p()

# ---- 9. 操作参考 ----
p("💡 【操作参考】")
conn3 = sqlite3.connect(DB)
try:
    # 北向资金
    try:
        north = conn3.execute("SELECT jz, value, name FROM north_money ORDER BY date DESC LIMIT 1").fetchone()
        if north:
            p(f"  北向资金: {north[0]} ({north[1]})")
    except:
        pass

    # 融资融券
    try:
        margin = conn3.execute("SELECT rzrqye FROM margin ORDER BY date DESC LIMIT 1").fetchone()
        if margin:
            p(f"  两融余额: {margin[0]/1e8:.1f}亿")
    except:
        pass
except:
    pass
conn3.close()

# 操作建议
timing_regime = timing.get('regime', '未知')
if timing is None:
    timing_regime = '未知'
    p("  ⚠️ 大盘择时数据采集失败，建议空仓观望")
elif timing_regime == '做多':
    p(f"  ✅ 环境偏多，仓位可积极。关注RPS强势板块回调低吸机会。")
elif timing_regime == '谨慎':
    p(f"  ⚠️ 谨慎为主，仓位控制50%以内。优先关注逆势强势板块。")
else:
    p(f"  🚫 规避为主，建议轻仓或空仓观望。等待企稳信号。")

p()
p("=" * 66)
p(f"  报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
p(f"  💡 盘中实时数据请使用 wind-mcp / mx-search")

# ---- 历史记忆参考（supermemory反哺） ----
p()
p("📖 【历史记忆参考】")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
    from memory_ref import recall
    # 搜索上周热点+策略信号
    r = recall([
        ('涨停', '涨停 板块 热点'),
        ('策略', '策略 信号'),
        ('市场', '市场 分析'),
    ], top_k=3, max_total=5)
    if r['count'] > 0:
        for m in r['results']:
            p(f"  [{m['_label']}] ({m['score']:.2f}) {m['text'][:80]}")
    else:
        p("  （暂无历史记忆参考）")
except Exception as e:
    p(f"  （记忆加载失败: {e}")
p()
p("=" * 66)

# 保存报告
report_file = os.path.join(OUT_DIR, f'morning_report_{today_str}.txt')
with open(report_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"\n报告已保存: {report_file}")

# 存入supermemory
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
    from memory_adapter import save_market_analysis
    summary = '早盘参考 %s: 大盘%s, 环境%s, 热点板块%s' % (
        today_str,
        timing.get('market', '未知'),
        timing_regime,
        ', '.join(hot_sectors[:3] if 'hot_sectors' in dir() else [])
    )
    save_market_analysis(summary, source='investment-morning')
    print('  [Supermemory] 已保存早盘参考')
except Exception as e:
    print('  [Supermemory] 写入失败: %s' % e)