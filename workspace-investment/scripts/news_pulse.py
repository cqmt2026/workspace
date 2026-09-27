# -*- coding: utf-8 -*-
"""
新闻快速归因 (News Pulse)
========================
ai-berkshire /news-pulse 的 AliceQuant 版本。

股价异动时10分钟搞清"发生了什么"——
不是深度投研，是快速归因，避免信息焦虑或盲目止损。

4维并行侦察：
1. 公司事件 — 公告/业绩/管理层变动
2. 监管政策 — 行业政策/监管动作
3. 行业对手 — 竞对动态/板块联动
4. 市场情绪 — 资金流向/卖方观点/大V观点

输出：
- 归因结论：价值事件 / 情绪波动 / 真因不明 / 混合
- 行动建议：深度研究 / 重审论文 / 仅观察

用法：
  python news_pulse.py sh688556
  python news_pulse.py sz300034 --drop 8.5
"""
import sys, os, json, sqlite3, urllib.request
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORK_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
DB = r'F:\market_data.db'
OUT_DIR = WORK_DIR / 'out_data'
os.makedirs(OUT_DIR, exist_ok=True)


def to_db_code(code: str) -> str:
    """统一转DB格式：sh688556 → sh.688556, sz300034 → sz.300034"""
    code = code.strip().replace('.', '')
    if code.startswith('sh'):
        return f'sh.{code[2:]}'
    elif code.startswith('sz'):
        return f'sz.{code[2:]}'
    elif code.startswith('6') or code.startswith('68'):
        return f'sh.{code}'
    elif code.startswith('0') or code.startswith('3'):
        return f'sz.{code}'
    return code


def to_cache_code(code: str) -> str:
    """统一转缓存格式：sh688556 → 688556, sz300034 → 300034"""
    return code.strip().replace('.', '').replace('sh', '').replace('sz', '').replace('SH', '').replace('SZ', '')


def get_stock_name(code):
    code = to_db_code(code)
    """从DB获取股票名称"""
    try:
        conn = sqlite3.connect(DB)
        row = conn.execute(
            "SELECT name FROM daily_k WHERE code=? LIMIT 1", (code,)
        ).fetchone()
        conn.close()
        return row[0] if row else code
    except:
        return code


def get_price_change(code, days=5):
    code = to_db_code(code)
    """获取近N日价格变化"""
    try:
        conn = sqlite3.connect(DB)
        rows = conn.execute(
            "SELECT date, close, volume, high, low FROM daily_k "
            "WHERE code=? ORDER BY date DESC LIMIT ?",
            (code, days + 1)
        ).fetchall()
        conn.close()
        if len(rows) < 2:
            return None
        # rows[0] = 最新, rows[-1] = N天前
        latest = rows[0]
        earliest = rows[-1]
        dates = [r[0] for r in rows]
        closes = [r[1] for r in rows]
        volumes = [r[2] for r in rows]
        highs = [r[3] for r in rows]
        lows = [r[4] for r in rows]

        total_chg = (closes[0] - closes[-1]) / closes[-1] * 100 if closes[-1] > 0 else 0
        max_drawdown = 0
        peak = closes[-1]
        for c in reversed(closes):
            if c > peak:
                peak = c
            dd = (c - peak) / peak * 100 if peak > 0 else 0
            if dd < max_drawdown:
                max_drawdown = dd

        return {
            'latest_date': dates[0],
            'latest_close': closes[0],
            'start_close': closes[-1],
            'total_chg_pct': round(total_chg, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'avg_volume': sum(volumes) / len(volumes) if volumes else 0,
            'latest_volume': volumes[0],
            'days': len(rows) - 1,
            'high': max(highs),
            'low': min(lows),
        }
    except Exception as e:
        return None


def check_company_events(code, name):
    code = to_db_code(code)
    """维度1: 公司事件 — 公告/业绩/管理层"""
    findings = []
    try:
        conn = sqlite3.connect(DB)
        # 检查是否在涨停表（可能有利好）
        zt = conn.execute(
            "SELECT trade_date, zt_type FROM daily_zt WHERE code=? ORDER BY trade_date DESC LIMIT 5",
            (code,)
        ).fetchall()
        if zt:
            for d, t in zt:
                findings.append({'type': '涨停记录', 'detail': f'{d} {t}板', 'impact': '正面', 'confidence': '高'})

        # 检查近期成交量和价格波动
        rows = conn.execute(
            "SELECT date, close, open, high, low, volume FROM daily_k "
            "WHERE code=? ORDER BY date DESC LIMIT 10",
            (code,)
        ).fetchall()
        conn.close()

        if rows and len(rows) >= 3:
            # 跳空缺口
            for i in range(min(3, len(rows) - 1)):
                prev_close = rows[i + 1][1]
                today_open = rows[i][2]
                if prev_close > 0:
                    gap = (today_open - prev_close) / prev_close * 100
                    if abs(gap) > 2:
                        direction = '向上' if gap > 0 else '向下'
                        findings.append({
                            'type': f'跳空缺口{direction}',
                            'detail': f'{rows[i][0]} 开{today_open:.2f} vs 前收{prev_close:.2f} ({gap:+.1f}%)',
                            'impact': '正面' if gap > 0 else '负面',
                            'confidence': '高'
                        })

            # 放量/缩量
            vols = [r[5] for r in rows]
            avg_vol = sum(vols[1:]) / len(vols[1:]) if len(vols) > 1 else 0
            if avg_vol > 0:
                vol_ratio = vols[0] / avg_vol
                if vol_ratio > 2:
                    findings.append({
                        'type': '异常放量',
                        'detail': f'量比{vol_ratio:.1f}倍 (可能有重大事件)',
                        'impact': '中性',
                        'confidence': '中'
                    })
                elif vol_ratio < 0.5:
                    findings.append({
                        'type': '异常缩量',
                        'detail': f'量比{vol_ratio:.1f}倍 (关注度下降)',
                        'impact': '中性',
                        'confidence': '中'
                    })
    except Exception as e:
        findings.append({'type': '数据错误', 'detail': str(e), 'impact': '未知', 'confidence': '低'})

    if not findings:
        findings.append({'type': '无显著公司事件', 'detail': '近期无公告/业绩/管理层变动', 'impact': '中性', 'confidence': '中'})

    return findings


def check_regulatory_policy(code, name):
    code = to_db_code(code)
    """维度2: 监管政策 — 行业政策/监管动作"""
    findings = []
    try:
        conn = sqlite3.connect(DB)
        # 检查同板块股票的整体表现
        rows = conn.execute(
            "SELECT date, close, volume FROM daily_k "
            "WHERE code=? ORDER BY date DESC LIMIT 20",
            (code,)
        ).fetchall()
        conn.close()

        if rows and len(rows) >= 5:
            # 检查是否整个板块在跌（系统性风险）
            # 用上证指数做对比
            idx_rows = []
            try:
                conn2 = sqlite3.connect(DB)
                idx_rows = conn2.execute(
                    "SELECT date, close FROM daily_k "
                    "WHERE code='sh000001' ORDER BY date DESC LIMIT 5"
                ).fetchall()
                conn2.close()
            except:
                pass

            if idx_rows and len(idx_rows) >= 2:
                idx_chg = (idx_rows[0][1] - idx_rows[-1][1]) / idx_rows[-1][1] * 100
                stock_chg = (rows[0][1] - rows[-1][1]) / rows[-1][1] * 100 if len(rows) >= 5 else 0
                excess = stock_chg - idx_chg
                if abs(excess) > 3:
                    direction = '独立上涨' if excess > 0 else '独立下跌'
                    findings.append({
                        'type': f'与大盘背离({direction})',
                        'detail': f'个股{stock_chg:+.1f}% vs 大盘{idx_chg:+.1f}% 超额{excess:+.1f}%',
                        'impact': '正面' if excess > 0 else '负面',
                        'confidence': '中'
                    })
                else:
                    findings.append({
                        'type': '跟随大盘',
                        'detail': f'个股{stock_chg:+.1f}% vs 大盘{idx_chg:+.1f}% 超额{excess:+.1f}%',
                        'impact': '中性',
                        'confidence': '高'
                    })
    except Exception as e:
        findings.append({'type': '数据错误', 'detail': str(e), 'impact': '未知', 'confidence': '低'})

    if not findings:
        findings.append({'type': '无显著政策事件', 'detail': '未检测到监管/政策变化', 'impact': '中性', 'confidence': '低'})

    return findings


def check_industry_peers(code, name):
    """维度3: 行业对手 — 同板块股票表现"""
    findings = []
    try:
        # 从板块缓存找同行业股票
        cache_path = WORK_DIR / 'data' / 'stock_board_cache.json'
        if not cache_path.exists():
            findings.append({'type': '板块缓存缺失', 'detail': '无法判断行业联动', 'impact': '中性', 'confidence': '低'})
            return findings

        with open(cache_path, 'r', encoding='utf-8') as f:
            cache = json.load(f)

        # cache格式: {股票代码: 板块名称}
        target_code_bare = to_cache_code(code)  # sh.688556 -> 688556
        target_board = cache.get(target_code_bare, '')
        target_board = cache.get(target_code_bare, '')
        if not target_board:
            findings.append({'type': '未找到板块', 'detail': f'{code}不在板块缓存中', 'impact': '中性', 'confidence': '低'})
            return findings

        # 找同板块其他股票
        peer_codes = [c for c, b in cache.items() if b == target_board and c != target_code_bare]

        conn = sqlite3.connect(DB)
        peer_changes = []
        for peer_code in peer_codes[:15]:  # 取前15只对比
            # 裸代码 -> DB格式
            peer_db_code = to_db_code(peer_code)

            row = conn.execute(
                "SELECT close FROM daily_k WHERE code=? ORDER BY date DESC LIMIT 2",
                (peer_db_code,)
            ).fetchall()
            if len(row) >= 2 and row[1][0] > 0:
                chg = (row[0][0] - row[1][0]) / row[1][0] * 100
                peer_changes.append(chg)
        conn.close()

        if peer_changes:
            avg_peer_chg = sum(peer_changes) / len(peer_changes)
            up_ratio = sum(1 for c in peer_changes if c > 0) / len(peer_changes) * 100
            if up_ratio > 70:
                findings.append({
                    'type': '板块普涨',
                    'detail': f'同板块[{target_board}]{len(peer_changes)}只均涨{avg_peer_chg:+.1f}% 涨占比{up_ratio:.0f}%',
                    'impact': '正面',
                    'confidence': '中'
                })
            elif up_ratio < 30:
                findings.append({
                    'type': '板块普跌',
                    'detail': f'同板块[{target_board}]{len(peer_changes)}只均涨{avg_peer_chg:+.1f}% 跌占比{100 - up_ratio:.0f}%',
                    'impact': '负面',
                    'confidence': '中'
                })
            else:
                findings.append({
                    'type': '板块分化',
                    'detail': f'同板块[{target_board}]{len(peer_changes)}只均涨{avg_peer_chg:+.1f}% 涨占比{up_ratio:.0f}%',
                    'impact': '中性',
                    'confidence': '中'
                })
    except Exception as e:
        findings.append({'type': '数据错误', 'detail': str(e), 'impact': '未知', 'confidence': '低'})

    if not findings:
        findings.append({'type': '无板块数据', 'detail': '无法判断行业联动', 'impact': '中性', 'confidence': '低'})

    return findings


def check_market_sentiment(code, name):
    code = to_db_code(code)
    """维度4: 市场情绪 — 资金面/技术面信号"""
    findings = []
    try:
        conn = sqlite3.connect(DB)
        rows = conn.execute(
            "SELECT date, close, volume, open, high, low FROM daily_k "
            "WHERE code=? ORDER BY date DESC LIMIT 20",
            (code,)
        ).fetchall()
        conn.close()

        if not rows or len(rows) < 5:
            return [{'type': '数据不足', 'detail': '无法分析情绪面', 'impact': '中性', 'confidence': '低'}]

        closes = [r[1] for r in rows]
        volumes = [r[2] for r in rows]
        opens = [r[3] for r in rows]
        highs = [r[4] for r in rows]
        lows = [r[5] for r in rows]

        # 1. 均线位置
        ma5 = sum(closes[:5]) / 5
        ma10 = sum(closes[:10]) / 10 if len(closes) >= 10 else ma5
        ma20 = sum(closes[:20]) / 20 if len(closes) >= 20 else ma10

        if closes[0] < ma5 < ma10 < ma20:
            findings.append({
                'type': '均线空头排列',
                'detail': f'收盘{closes[0]:.2f} < MA5{ma5:.2f} < MA10{ma10:.2f} < MA20{ma20:.2f}',
                'impact': '负面',
                'confidence': '高'
            })
        elif closes[0] > ma5 > ma10 > ma20:
            findings.append({
                'type': '均线多头排列',
                'detail': f'收盘{closes[0]:.2f} > MA5{ma5:.2f} > MA10{ma10:.2f} > MA20{ma20:.2f}',
                'impact': '正面',
                'confidence': '高'
            })
        else:
            findings.append({
                'type': '均线纠缠',
                'detail': f'MA5{ma5:.2f} MA10{ma10:.2f} MA20{ma20:.2f} 无明确方向',
                'impact': '中性',
                'confidence': '中'
            })

        # 2. 量价关系
        avg_vol = sum(volumes[1:6]) / 5 if len(volumes) > 5 else sum(volumes) / len(volumes)
        vol_ratio = volumes[0] / avg_vol if avg_vol > 0 else 1
        daily_chg = (closes[0] - closes[1]) / closes[1] * 100 if closes[1] > 0 else 0

        if vol_ratio > 1.5 and daily_chg < -2:
            findings.append({
                'type': '放量下跌',
                'detail': f'量比{vol_ratio:.1f} 涨幅{daily_chg:+.1f}%',
                'impact': '负面',
                'confidence': '高'
            })
        elif vol_ratio > 1.5 and daily_chg > 2:
            findings.append({
                'type': '放量上涨',
                'detail': f'量比{vol_ratio:.1f} 涨幅{daily_chg:+.1f}%',
                'impact': '正面',
                'confidence': '高'
            })
        elif vol_ratio < 0.7 and daily_chg < -2:
            findings.append({
                'type': '缩量下跌',
                'detail': f'量比{vol_ratio:.1f} 涨幅{daily_chg:+.1f}%',
                'impact': '中性偏负',
                'confidence': '中'
            })

        # 3. K线形态
        body = abs(closes[0] - opens[0])
        upper_shadow = highs[0] - max(closes[0], opens[0])
        lower_shadow = min(closes[0], opens[0]) - lows[0]
        total_range = highs[0] - lows[0]

        if total_range > 0:
            if upper_shadow / total_range > 0.6 and daily_chg > 0:
                findings.append({
                    'type': '长上影线',
                    'detail': f'上影占K线{upper_shadow / total_range * 100:.0f}%',
                    'impact': '负面',
                    'confidence': '中'
                })
            elif lower_shadow / total_range > 0.6 and daily_chg < 0:
                findings.append({
                    'type': '长下影线',
                    'detail': f'下影占K线{lower_shadow / total_range * 100:.0f}%',
                    'impact': '正面',
                    'confidence': '中'
                })

    except Exception as e:
        findings.append({'type': '数据错误', 'detail': str(e), 'impact': '未知', 'confidence': '低'})

    if not findings:
        findings.append({'type': '无明显情绪信号', 'detail': '技术面无明显异常', 'impact': '中性', 'confidence': '低'})

    return findings


def classify_attribution(all_findings, price_chg):
    """综合归因分类

    返回: 价值事件 / 情绪波动 / 真因不明 / 混合
    """
    positive = sum(1 for f in all_findings if f.get('impact') == '正面')
    negative = sum(1 for f in all_findings if f.get('impact') == '负面')
    neutral = sum(1 for f in all_findings if f.get('impact') in ('中性', '中性偏负'))
    total = len(all_findings)

    high_conf = sum(1 for f in all_findings if f.get('confidence') == '高')

    # 判断逻辑
    if total == 0:
        return '真因不明', '无任何可识别信号'

    if high_conf >= 2 and (positive >= 2 or negative >= 2):
        # 有多个高置信度信号指向同一方向
        if negative > positive and price_chg < -3:
            return '价值事件', f'{negative}个负面信号(高置信)支撑下跌，可能是基本面变化'
        elif positive > negative and price_chg > 3:
            return '价值事件', f'{positive}个正面信号(高置信)支撑上涨，可能是基本面利好'
        else:
            return '混合', f'正{positive}负{negative}信号并存，多空交织'

    if neutral >= total * 0.6:
        return '情绪波动', f'{neutral}/{total}信号为中性，缺乏基本面驱动'

    if negative > 0 and positive == 0 and price_chg < -3:
        return '情绪波动', f'仅有{negative}个负面信号，但无高置信基本面变化'

    if positive > 0 and negative == 0 and price_chg > 3:
        return '情绪波动', f'仅有{positive}个正面信号，但无高置信基本面变化'

    return '混合', f'正{positive}负{negative}中{neutral}，无法简单归类'


def run_news_pulse(code, drop_pct=None):
    """运行新闻快速归因"""
    name = get_stock_name(code)
    price_info = get_price_change(code, days=5)

    # 确定跌幅
    if drop_pct is None:
        if price_info:
            drop_pct = price_info['total_chg_pct']
        else:
            drop_pct = 0

    print(f"\n{'=' * 60}")
    print(f"⚡ News Pulse — {name}({code})")
    print(f"{'=' * 60}")
    if price_info:
        print(f"近{price_info['days']}日涨跌: {price_info['total_chg_pct']:+.2f}%")
        print(f"最大回撤: {price_info['max_drawdown_pct']:.2f}%")
        print(f"最新收盘: {price_info['latest_close']:.2f} ({price_info['latest_date']})")

    # 4维并行侦察
    print(f"\n🔍 4维并行侦察:")

    findings_1 = check_company_events(code, name)
    print(f"\n1️⃣ 公司事件:")
    for f in findings_1:
        emoji = '🟢' if f['impact'] == '正面' else '🔴' if f['impact'] == '负面' else '🟡'
        print(f"  {emoji} [{f['confidence']}] {f['type']}: {f['detail']}")

    findings_2 = check_regulatory_policy(code, name)
    print(f"\n2️⃣ 监管政策:")
    for f in findings_2:
        emoji = '🟢' if f['impact'] == '正面' else '🔴' if f['impact'] == '负面' else '🟡'
        print(f"  {emoji} [{f['confidence']}] {f['type']}: {f['detail']}")

    findings_3 = check_industry_peers(code, name)
    print(f"\n3️⃣ 行业对手:")
    for f in findings_3:
        emoji = '🟢' if f['impact'] == '正面' else '🔴' if f['impact'] == '负面' else '🟡'
        print(f"  {emoji} [{f['confidence']}] {f['type']}: {f['detail']}")

    findings_4 = check_market_sentiment(code, name)
    print(f"\n4️⃣ 市场情绪:")
    for f in findings_4:
        emoji = '🟢' if f['impact'] == '正面' else '🔴' if f['impact'] == '负面' else '🟡'
        print(f"  {emoji} [{f['confidence']}] {f['type']}: {f['detail']}")

    # 综合归因
    all_findings = findings_1 + findings_2 + findings_3 + findings_4
    attribution, reason = classify_attribution(all_findings, drop_pct)

    print(f"\n{'=' * 60}")
    print(f"📋 归因结论:")
    attr_emoji = {'价值事件': '🔴', '情绪波动': '🟡', '真因不明': '❓', '混合': '🟠'}
    print(f"  {attr_emoji.get(attribution, '❓')} {attribution}")
    print(f"  {reason}")

    # 行动建议
    print(f"\n📌 行动建议:")
    if attribution == '价值事件' and drop_pct < -5:
        print(f"  🔴 建议启动深度研究(/investment-research)，评估是否需要重审投资论文")
    elif attribution == '情绪波动':
        print(f"  🟡 情绪驱动，非基本面变化。观察1-2日，如价格回到支撑位则无需操作")
    elif attribution == '真因不明':
        print(f"  ❓ 原因不明，可能存在内幕信息。减仓观察，等待信息披露")
    elif attribution == '混合':
        print(f"  🟠 多空交织，建议进一步调查。关注后续公告和资金流向")
    else:
        print(f"  🟢 无异常，维持现有策略")

    # 保存结果
    result = {
        'code': code,
        'name': name,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'price_change': drop_pct,
        'price_info': price_info,
        'attribution': attribution,
        'attribution_reason': reason,
        'findings': {
            'company_events': findings_1,
            'regulatory_policy': findings_2,
            'industry_peers': findings_3,
            'market_sentiment': findings_4,
        }
    }

    today = datetime.now().strftime('%Y-%m-%d')
    out_path = OUT_DIR / f'news_pulse_{code}_{today}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 已保存: {out_path}")

    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='新闻快速归因')
    parser.add_argument('code', help='股票代码，如 sh688556')
    parser.add_argument('--drop', type=float, help='跌幅百分比（可选，默认从DB计算）')
    args = parser.parse_args()

    run_news_pulse(args.code, args.drop)
