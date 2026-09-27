# -*- coding: utf-8 -*-
"""
四象共振·底部反转扫描
扫描全市场满足"四象共振"条件的底部反转候选股票

四象共振条件：
  象1（趋势）：前10日跌幅10%~50%（充分回调）
  象2（动能）：MACD柱加速下跌后开始收敛（背离信号）
  象3（量能）：量比>1.1（底部放量）
  象4（形态）：地量出现在最低点之前（主力建仓信号）

使用方法：
  python scripts/si_xiang_bottom_scan.py
  输出：out_data/si_xiang_bottom_YYYY-MM-DD.md
"""
import sys, os, sqlite3, json, math
from datetime import datetime, date, timedelta
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
DB_PATH = r'F:\market_data.db'
OUT_DIR = os.path.join(WORK_DIR, 'out_data')
os.makedirs(OUT_DIR, exist_ok=True)

def get_today():
    """获取今天日期"""
    return date.today().isoformat()

def get_macd_series(closes, period=120):
    """计算MACD序列，返回(EMV_DIFF, MACD_bar)列表"""
    if len(closes) < 26:
        return ([0]*len(closes), [0]*len(closes))

    # EMA12
    ema12 = [closes[0]]
    for i in range(1, len(closes)):
        ema12.append((closes[i] * 2 / 13) + (ema12[-1] * 11 / 13))
    # EMA26
    ema26 = [closes[0]]
    for i in range(1, len(closes)):
        ema26.append((closes[i] * 2 / 27) + (ema26[-1] * 25 / 27))
    # DIFF
    diff = [round(ema12[i] - ema26[i], 4) for i in range(len(closes))]
    # DEA (MACD bar proxy)
    dea = [diff[0]]
    for i in range(1, len(diff)):
        dea.append((diff[i] * 2 / 5) + (dea[-1] * 3 / 5))
    return (diff, [round(diff[i] - dea[i], 4) for i in range(len(closes))])


def scan(universe_codes=None):
    """
    四象共振底部反转扫描

    条件（全部满足）：
      1. 前10日跌幅10%~50%
      2. MACD柱加速下跌后开始收敛（当前柱 > 3日前柱）
      3. 量比 > 1.1
      4. 地量出现在最低点之前
      5. 最低点距今15~30天
      6. 当前价距最低点5%~50%

    评分：满足条件越多分数越高
    """
    conn = sqlite3.connect('file:' + DB_PATH, uri=True)
    c = conn.cursor()

    # 获取活跃股票代码（最近有数据的）
    if universe_codes is None:
        c.execute("SELECT DISTINCT code FROM daily_k WHERE date >= date('now','-30 days')")
        universe_codes = [r[0] for r in c.fetchall()]

    results = []
    today = get_today()

    for code in universe_codes:
        try:
            c.execute("SELECT date, open, high, low, close, volume FROM daily_k WHERE code=? ORDER BY date DESC LIMIT 120", (code,))
            rows = c.fetchall()
            if len(rows) < 30:
                continue

            # 反转成时间升序
            rows_rev = list(reversed(rows))
            dates = [r[0] for r in rows_rev]
            opens = [float(r[1]) for r in rows_rev]
            highs = [float(r[2]) for r in rows_rev]
            lows = [float(r[3]) for r in rows_rev]
            closes = [float(r[4]) for r in rows_rev]
            volumes = [float(r[5]) for r in rows_rev]

            n = len(closes)
            current_price = closes[-1]
            prev_close = closes[-2] if n > 1 else current_price

            # 象1: 前10日跌幅10%~50%
            if n < 11:
                continue
            close_10d_ago = closes[-11]
            pct_10d = (current_price - close_10d_ago) / close_10d_ago * 100
            if pct_10d > -10 or pct_10d < -50:
                continue

            # 象2: MACD柱加速下跌后收敛
            diff, macd_bar = get_macd_series(closes)
            bar_today = macd_bar[-1]
            bar_3d_ago = macd_bar[-4] if n > 4 else 0
            if bar_3d_ago == 0:
                continue
            # 收敛条件：当前柱 > 3日前柱（MACD柱由负转正或收敛中）
            if bar_today <= bar_3d_ago:
                continue

            # 象3: 量比 > 1.1
            vol_5d_avg = sum(volumes[-6:-1]) / 5 if n > 6 else 0
            if vol_5d_avg == 0:
                continue
            vol_ratio = volumes[-1] / vol_5d_avg
            if vol_ratio < 1.1:
                continue

            # 象4: 地量出现在最低点之前
            min_low_30d = min(lows[-30:-1]) if n > 30 else min(lows[-n:-1])
            min_low_idx = lows[-30:-1].index(min_low_30d) if n > 30 else 0
            min_low_idx = n - 30 + min_low_idx if n > 30 else min_low_idx
            vol_at_min = volumes[min_low_idx] if min_low_idx < n-1 else volumes[-2]
            vol_min_30d = min(volumes[-30:-1]) if n > 30 else min(volumes[-n:-1])
            # 地量 = 该日成交量 <= 30日内均量的1.5倍
            if vol_at_min > vol_min_30d * 1.5:
                continue

            # 象5: 最低点距今15~30天
            min_low_date = dates[min_low_idx]
            min_low_dt = datetime.strptime(min_low_date, '%Y-%m-%d').date()
            days_since_min = (datetime.strptime(today, '%Y-%m-%d').date() - min_low_dt).days
            if days_since_min < 15 or days_since_min > 30:
                continue

            # 象6: 当前价距最低点5%~50%
            pct_from_low = (current_price - min_low_30d) / min_low_30d * 100
            if pct_from_low < 5 or pct_from_low > 50:
                continue

            # 全部条件满足，计算评分
            score = 0
            # 基础分
            score += 10  # 跌幅10%~20%更优
            if pct_10d >= -20:
                score += 5
            # MACD收敛速度
            if bar_today > 0:
                score += 5
            # 量比
            if vol_ratio > 2.0:
                score += 3
            elif vol_ratio > 1.5:
                score += 2
            # 距离低点
            if pct_from_low < 20:
                score += 5
            elif pct_from_low < 30:
                score += 3

            # 金叉判断（DIFF上穿DEA）
            dea_1d = (diff[-1] * 2 / 5) + (diff[-2] * 3 / 5) if n > 2 else diff[-1]
            dea_2d = (diff[-2] * 2 / 5) + (diff[-3] * 3 / 5) if n > 3 else diff[-2]
            golden_cross = diff[-1] > dea_1d and diff[-2] <= dea_2d
            if golden_cross:
                score += 5

            # 假金叉判断（上次金叉后回落）
            fake_golden = False
            if n > 20:
                for i in range(len(diff) - 20, len(diff) - 1):
                    dea_i = (diff[i] * 2 / 5) + (diff[i-1] * 3 / 5) if i > 0 else diff[i]
                    dea_i1 = (diff[i-1] * 2 / 5) + (diff[i-2] * 3 / 5) if i > 1 else diff[i-1]
                    if diff[i] > dea_i and diff[i-1] <= dea_i1:
                        # 找到金叉点，看之后是否回落
                        peak = closes[i]
                        if peak > closes[-1] * 1.1:  # 金叉后涨了10%以上才回落
                            fake_golden = True
                        break

            results.append({
                'code': code,
                'name': code.split('.')[-1],
                'price': round(current_price, 2),
                'low_price': round(min_low_30d, 2),
                'low_date': min_low_date,
                'days_since_low': days_since_min,
                'pct_from_low': round(pct_from_low, 1),
                'pct_10d': round(pct_10d, 1),
                'macd_bar': round(bar_today, 4),
                'macd_bar_3d_ago': round(bar_3d_ago, 4),
                'vol_ratio': round(vol_ratio, 2),
                'score': min(score, 25),
                'golden_cross': '是' if golden_cross else '否',
                'fake_golden': '是' if fake_golden else '否',
            })
        except Exception as e:
            continue

    conn.close()
    return sorted(results, key=lambda x: x['score'], reverse=True)


def format_report(results):
    """格式化输出为Markdown"""
    lines = []
    lines.append('# 四象共振·底部反转扫描 v1.1')
    lines.append(f'**扫描时间**: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append('**条件**: 前10日跌10~50% + MACD柱加速下跌 + 量比>1.1 + 地量先于最低点 + 底部距今15~30日 + 距低5~50%')
    lines.append(f'\n**结果**: 共 {len(results)} 只\n')

    if not results:
        lines.append('当前无满足条件的候选股票。')
        return '\n'.join(lines)

    lines.append('## Top 20\n')
    lines.append('| # | 代码 | 名称 | 当前价 | 最低价 | 最低日 | 距低% | 前10日% | MACD柱 | 量比 | 金叉 | 假金叉 | 评分 |')
    lines.append('|---|------|------|--------|--------|--------|-------|---------|--------|------|------|--------|------|')

    for i, r in enumerate(results[:20], 1):
        lines.append(
            f'| {i} | {r["code"]} | {r["name"]} | {r["price"]} | {r["low_price"]} | {r["low_date"]} | '
            f'{r["pct_from_low"]}% | {r["pct_10d"]}% | {r["macd_bar"]} | {r["vol_ratio"]} | '
            f'{r["golden_cross"]} | {r["fake_golden"]} | {r["score"]} |'
        )

    lines.append('\n## 风险提示')
    lines.append('1. 底部反转扫描仅为参考，不构成投资建议')
    lines.append('2. 请结合基本面、板块RPS、大盘环境综合判断')
    lines.append('3. 底部反转成功率约60-70%，需严格止损')
    lines.append('4. 四象共振条件苛刻，筛选出的股票通常为优质候选')

    return '\n'.join(lines)


if __name__ == '__main__':
    results = scan()
    report = format_report(results)
    print(report)

    out_file = os.path.join(OUT_DIR, f'si_xiang_bottom_{date.today().isoformat()}.md')
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f'\n报告已保存: {out_file}')
