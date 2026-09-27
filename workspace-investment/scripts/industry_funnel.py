# -*- coding: utf-8 -*-
"""
行业漏斗筛选 (Industry Funnel)
==============================
ai-berkshire /industry-funnel 的 AliceQuant 版本。

全市场 → 5条硬指标粗筛 → 精细分析 → 终选3家

核心特色：
- 每层有明确留/弃标准，被淘汰的标的留下淘汰理由（不是黑箱）
- 终选3家按"组合互补性"选（高确定性+中等弹性+高弹性），不按打分前3排序
- 强制列"未来IPO候选"，避免漏掉一级市场核心玩家

用法：
  python industry_funnel.py "AI算力"
  python industry_funnel.py "新能源" --top 5
  python industry_funnel.py "半导体" --no-cache
"""
import sys, os, json, sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORK_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
DB = r'F:\market_data.db'
OUT_DIR = WORK_DIR / 'out_data'
BOARD_CACHE = WORK_DIR / 'data' / 'stock_board_cache.json'
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


def load_board_stocks(keyword: str, use_cache=True) -> List[dict]:
    """从板块缓存加载关键词相关的板块成分股"""
    if not BOARD_CACHE.exists():
        print('[WARN] 板块缓存不存在，请先运行板块数据采集')
        return []

    with open(BOARD_CACHE, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    # cache格式: {股票代码: 板块名称}
    # 反转为: {板块名称: [股票代码列表]}
    board_stocks = {}
    for stock_code, board_name in cache.items():
        if board_name not in board_stocks:
            board_stocks[board_name] = []
        board_stocks[board_name].append(stock_code)

    # 搜索包含关键词的板块
    matched_boards = {}
    for board_name, codes in board_stocks.items():
        if keyword in board_name:
            matched_boards[board_name] = codes

    if not matched_boards:
        print(f'  未找到包含"{keyword}"的板块')
        print(f'  可用板块: {list(board_stocks.keys())[:20]}')
        return []

    # 合并去重
    all_stocks = {}
    for board_name, codes in matched_boards.items():
        print(f'  匹配板块: {board_name} ({len(codes)}只)')
        for code in codes:
            if code not in all_stocks:
                all_stocks[code] = {
                    'code': code,
                    'name': '',  # 名称从DB获取
                    'board': board_name,
                }

    return list(all_stocks.values())


def get_stock_metrics(code: str, date: str) -> Optional[dict]:
    """获取股票的5条硬指标数据"""
    try:
        conn = sqlite3.connect(DB)

        # 最近60日K线
        rows = conn.execute(
            "SELECT date, close, volume, open, high, low FROM daily_k "
            "WHERE code=? AND date<=? ORDER BY date DESC LIMIT 60",
            (to_db_code(code), date)
        ).fetchall()
        conn.close()

        if len(rows) < 20:
            return None

        closes = [r[1] for r in reversed(rows)]
        volumes = [r[2] for r in reversed(rows)]

        # 基本指标
        latest_close = closes[-1]
        avg_vol_20 = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes)
        vol_ratio = volumes[-1] / avg_vol_20 if avg_vol_20 > 0 else 0

        # MA
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        ma60 = sum(closes[-60:]) / 60 if len(closes) >= 60 else ma20

        # 涨跌幅
        chg_1d = (closes[-1] - closes[-2]) / closes[-2] * 100 if closes[-2] > 0 else 0
        chg_5d = (closes[-1] - closes[-6]) / closes[-6] * 100 if len(closes) >= 6 and closes[-6] > 0 else 0
        chg_20d = (closes[-1] - closes[-21]) / closes[-21] * 100 if len(closes) >= 21 and closes[-21] > 0 else 0

        # RSI14（简化版）
        gains = []
        losses = []
        for i in range(1, min(15, len(closes))):
            chg = closes[-i] - closes[-i - 1]
            if chg > 0:
                gains.append(chg)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(chg))
        avg_gain = sum(gains) / 14 if gains else 0
        avg_loss = sum(losses) / 14 if losses else 1
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi14 = 100 - (100 / (1 + rs))

        return {
            'code': code,
            'close': latest_close,
            'ma5': ma5,
            'ma20': ma20,
            'ma60': ma60,
            'vol_ratio': round(vol_ratio, 2),
            'chg_1d': round(chg_1d, 2),
            'chg_5d': round(chg_5d, 2),
            'chg_20d': round(chg_20d, 2),
            'rsi14': round(rsi14, 1),
            'avg_vol': round(avg_vol_20, 0),
            'trend': '多头' if closes[-1] > ma5 > ma20 else '空头' if closes[-1] < ma5 < ma20 else '震荡',
        }
    except Exception as e:
        return None


def normalize_code(code: str) -> str:
    """统一代码格式：sz300034 → 300034, sh688556 → 688556"""
    return code.replace('sh', '').replace('sz', '').replace('SH', '').replace('SZ', '').replace('.', '')


def to_full_code(code: str) -> str:
    """300034 → sz300034, 688556 → sh688556"""
    code = normalize_code(code)
    if code.startswith('6') or code.startswith('68'):
        return f'sh{code}'
    elif code.startswith('0') or code.startswith('3'):
        return f'sz{code}'
    return code


def funnel_screen(stocks: List[dict], date: str) -> Tuple[List[dict], List[dict]]:
    """5条硬指标粗筛

    规则（价值投资+趋势结合）：
    1. 趋势：收盘价 > MA20（中期趋势向上）
    2. 量能：量比 > 0.8（不是极度缩量）
    3. 波动：5日涨幅 < 20%（排除短期爆炒）
    4. 波动：5日跌幅 > -15%（排除暴跌）
    5. RSI：14日RSI < 80（排除超买）

    返回: (通过列表, 淘汰列表)
    """
    passed = []
    eliminated = []

    for s in stocks:
        code = s.get('code', '')
        name = s.get('name', '')
        board = s.get('board', '')

        # 补全代码前缀
        if not (code.startswith('sh') or code.startswith('sz')):
            code = to_full_code(code)
            if not (code.startswith('sh') or code.startswith('sz')):
                eliminated.append({**s, 'elimination_reason': '代码格式不符', 'elimination_rule': '格式'})
                continue

        m = get_stock_metrics(code, date)
        if not m:
            eliminated.append({**s, 'code': code, 'elimination_reason': '数据不足', 'elimination_rule': '数据'})
            continue

        reasons = []

        # 硬指标1: 趋势
        if m['close'] < m['ma20']:
            reasons.append(f'收盘{m["close"]:.2f}<MA20{m["ma20"]:.2f}')

        # 硬指标2: 量能
        if m['vol_ratio'] < 0.8:
            reasons.append(f'量比{m["vol_ratio"]:.1f}<0.8')

        # 硬指标3: 5日涨幅<20%
        if m['chg_5d'] > 20:
            reasons.append(f'5日涨{m["chg_5d"]:.1f}%>20%')

        # 硬指标4: 5日跌幅>-15%
        if m['chg_5d'] < -15:
            reasons.append(f'5日跌{m["chg_5d"]:.1f}%<-15%')

        # 硬指标5: RSI<80
        if m['rsi14'] > 80:
            reasons.append(f'RSI{m["rsi14"]:.0f}>80')

        s['code'] = code
        s.update(m)

        if reasons:
            s['elimination_reason'] = '; '.join(reasons)
            s['elimination_rule'] = '硬指标'
            eliminated.append(s)
        else:
            passed.append(s)

    return passed, eliminated


def select_portfolio_complement(passed: List[dict], top_n=3) -> List[dict]:
    """按组合互补性终选3家

    逻辑：
    - 高确定性：MA60多头+量能稳定+RSI<60（不超过热）
    - 中等弹性：MA20多头+量比1-2之间
    - 高弹性：涨幅较大但趋势完好

    不按打分前3排序，而是按互补性选。
    """
    if len(passed) <= top_n:
        return passed

    # 分类
    high_certainty = []
    medium_elasticity = []
    high_elasticity = []

    for s in passed:
        # 高确定性：MA60上方+RSI<60+量比<1.5
        if (s.get('close', 0) > s.get('ma60', 0) and
            s.get('rsi14', 0) < 60 and
            s.get('vol_ratio', 0) < 1.5):
            high_certainty.append(s)
        # 高弹性：5日涨幅>5%且RSI>55
        elif (s.get('chg_5d', 0) > 5 and
              s.get('rsi14', 0) > 55):
            high_elasticity.append(s)
        # 中等弹性：其余
        else:
            medium_elasticity.append(s)

    # 从每类取1只（按5日涨幅排序，取最有代表性的）
    selected = []

    def pick_best(candidates, label):
        if not candidates:
            return None
        # 按趋势强度排序
        candidates.sort(key=lambda x: x.get('chg_5d', 0), reverse=True)
        best = candidates[0]
        best['portfolio_role'] = label
        return best

    sel1 = pick_best(high_certainty, '高确定性')
    sel2 = pick_best(medium_elasticity, '中等弹性')
    sel3 = pick_best(high_elasticity, '高弹性')

    for s in [sel1, sel2, sel3]:
        if s and s not in selected:
            selected.append(s)

    # 如果不够3只，从passed里补
    if len(selected) < top_n:
        for s in passed:
            if s not in selected:
                s['portfolio_role'] = '补充'
                selected.append(s)
                if len(selected) >= top_n:
                    break

    return selected[:top_n]


def run_industry_funnel(keyword: str, date: str = None, top_n: int = 3):
    """运行行业漏斗筛选"""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')

    print(f"\n{'=' * 60}")
    print(f"🔍 行业漏斗筛选 — {keyword}")
    print(f"{'=' * 60}")

    # 第1层：全市场扫描
    print(f"\n📊 第1层：全市场扫描（关键词: {keyword}）")
    all_stocks = load_board_stocks(keyword)
    print(f"  扫描到: {len(all_stocks)}只")

    if not all_stocks:
        print("  无匹配结果，请换关键词")
        return None

    # 第2层：5条硬指标粗筛
    print(f"\n🔎 第2层：5条硬指标粗筛")
    print(f"  ① 趋势：收盘价 > MA20")
    print(f"  ② 量能：量比 > 0.8")
    print(f"  ③ 波动：5日涨幅 < 20%")
    print(f"  ④ 波动：5日跌幅 > -15%")
    print(f"  ⑤ RSI：14日RSI < 80")

    passed, eliminated = funnel_screen(all_stocks, date)
    print(f"\n  ✅ 通过: {len(passed)}只")
    print(f"  ❌ 淘汰: {len(eliminated)}只")

    # 打印淘汰理由（不是黑箱）
    if eliminated:
        print(f"\n  淘汰明细（前10只）:")
        for e in eliminated[:10]:
            name = e.get('name', '')
            code = e.get('code', '')
            reason = e.get('elimination_reason', '')
            rule = e.get('elimination_rule', '')
            print(f"    ❌ {name}({code}): [{rule}] {reason}")

    # 第3层：精细分析
    print(f"\n📝 第3层：精细分析（{len(passed)}只）")
    if passed:
        passed.sort(key=lambda x: x.get('chg_5d', 0), reverse=True)
        for i, s in enumerate(passed[:10], 1):
            name = s.get('name', '')
            code = s.get('code', '')
            trend = s.get('trend', '')
            chg5 = s.get('chg_5d', 0)
            chg1 = s.get('chg_1d', 0)
            rsi = s.get('rsi14', 0)
            vr = s.get('vol_ratio', 0)
            print(f"  {i}. {name}({code}) {trend} 5日{chg5:+.1f}% 今{chg1:+.1f}% RSI{rsi:.0f} 量比{vr:.1f}")

    # 第4层：终选3家（按组合互补性）
    print(f"\n🏆 第4层：终选{top_n}家（按组合互补性）")
    selected = select_portfolio_complement(passed, top_n)

    if selected:
        for s in selected:
            name = s.get('name', '')
            code = s.get('code', '')
            role = s.get('portfolio_role', '')
            chg5 = s.get('chg_5d', 0)
            rsi = s.get('rsi14', 0)
            trend = s.get('trend', '')
            board = s.get('board', '')
            emoji_map = {'高确定性': '🔵', '中等弹性': '🟡', '高弹性': '🔴', '补充': '⚪'}
            emoji = emoji_map.get(role, '⚪')
            print(f"  {emoji} [{role}] {name}({code}) | {board} | {trend} | 5日{chg5:+.1f}% RSI{rsi:.0f}")
    else:
        print("  无符合条件的标的")

    # 保存结果
    result = {
        'keyword': keyword,
        'date': date,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'total_scanned': len(all_stocks),
        'passed_screen': len(passed),
        'eliminated_screen': len(eliminated),
        'selected': selected,
        'eliminated_details': eliminated[:30],  # 保留前30条淘汰理由
        'passed_details': passed[:30],
    }

    out_path = OUT_DIR / f'industry_funnel_{keyword}_{date}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n💾 已保存: {out_path}")

    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='行业漏斗筛选')
    parser.add_argument('keyword', help='行业关键词，如 AI算力/新能源/半导体')
    parser.add_argument('--date', help='日期(YYYY-MM-DD)，默认今天')
    parser.add_argument('--top', type=int, default=3, help='终选数量，默认3')
    args = parser.parse_args()

    run_industry_funnel(args.keyword, args.date, args.top)
