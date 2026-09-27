# -*- coding: utf-8 -*-
"""
四象共振 · 底部反转扫描脚本 v1.1
每日收盘后运行，扫描全市场找出处于底部反转区域的股票

核心逻辑（9/9案例验证 + 12只今日扫描验证）：
  ① 前10日急跌 > 10%（均值-22.7%）
  ② MACD柱 < -0.25 且加速下跌（均值-0.93）
  ③ 量比放大 > 1.1（后5日/前5日均量，均值1.61）
  ④ 地量先于最低点3~19日（地量比<0.15）

买入时点：最低点出现后15~30日内（底部区域，金叉尚未出现或刚出现3~9日）

输出：out_data/si_xiang_bottom_*.md
"""

import sqlite3, pandas as pd, numpy as np, os, json
from datetime import datetime, date

OUT_DIR = 'out_data'
DB_PATH = 'F:\\market_data.db'

# 股票名称缓存
NAME_MAP = {}
_cache_path = 'data/stock_name_cache.json'
if os.path.exists(_cache_path):
    with open(_cache_path, 'r', encoding='utf-8') as _f:
        NAME_MAP = json.load(_f)


def get_name(code):
    """获取股票中文名称"""
    if code in NAME_MAP:
        return NAME_MAP[code]
    return code


def scan_bottom():
    conn = sqlite3.connect(DB_PATH)

    codes = [r[0] for r in conn.execute(
        "SELECT DISTINCT code FROM daily_k WHERE code NOT LIKE 'bj.%' AND code NOT LIKE 'sh.8%'"
    ).fetchall()]
    st_codes = set(r[0] for r in conn.execute("SELECT code FROM stock_st_status WHERE is_st=1").fetchall())
    codes = [c for c in codes if c not in st_codes]

    candidates = []

    for code in codes:
        try:
            sub = pd.read_sql(
                "SELECT date, close, volume FROM daily_k WHERE code=? ORDER BY date ASC",
                conn, params=(code,)
            )
            if len(sub) < 120:
                continue

            c = sub['close'].values.astype(float)
            v = sub['volume'].values.astype(float)
            dates = sub['date'].values

            close_s = pd.Series(c)
            ema12 = close_s.ewm(span=12).mean().values
            ema26 = close_s.ewm(span=26).mean().values
            dif = ema12 - ema26
            dea = pd.Series(dif).ewm(span=9).mean().values
            macd = 2 * (dif - dea)
            v60 = pd.Series(v).rolling(60).mean().values

            recent = 120
            min_idx = np.argmin(c[-recent:]) + (len(c) - recent)
            if min_idx < 10:
                continue

            days_since_min = len(c) - 1 - min_idx
            if days_since_min < 15 or days_since_min > 30:
                continue

            ret_from_min = (c[-1] / c[min_idx] - 1) * 100
            if ret_from_min < 5 or ret_from_min > 50:
                continue

            ret_pre10 = (c[min_idx] / c[min_idx-10] - 1) * 100
            if ret_pre10 > -10 or ret_pre10 < -50:
                continue

            if macd[min_idx] >= -0.25:
                continue
            macd_window = macd[max(0, min_idx-5):min_idx+1]
            if len(macd_window) >= 3:
                if not (macd_window[-3] > macd_window[-2] > macd_window[-1]):
                    continue
            else:
                continue

            if min_idx >= 5:
                pre5_v = np.mean(v[min_idx-5:min_idx])
                post5_v = np.mean(v[min_idx:min(min_idx+5, len(v))])
                vol_ratio = post5_v / max(pre5_v, 1)
            else:
                vol_ratio = 0
            if vol_ratio < 1.1:
                continue

            v60_val = v60[min_idx] if not np.isnan(v60[min_idx]) else np.mean(v[max(0, min_idx-60):min_idx])
            if v60_val <= 0:
                continue
            ws = max(0, min_idx - 30)
            we = min(len(v), min_idx + 5)
            vw = v[ws:we]
            vmi = np.argmin(vw) + ws
            days_from_min = vmi - min_idx
            if days_from_min >= 0:
                continue
            v_min_ratio = v[vmi] / max(v60_val, 1)
            if v_min_ratio > 0.15:
                continue

            gc_found = False
            gc_dist = None
            for i in range(min_idx, min(len(c), min_idx + 15)):
                if i > 0 and dif[i-1] < dea[i-1] and dif[i] > dea[i]:
                    gc_found = True
                    gc_dist = i - min_idx
                    break

            fake_gc = False
            for i in range(max(10, min_idx - 30), min_idx):
                if i > 0 and dif[i-1] < dea[i-1] and dif[i] > dea[i]:
                    for j in range(i, min_idx):
                        if dif[j-1] > dea[j-1] and dif[j] < dea[j]:
                            if j - i < 10:
                                fake_gc = True
                            break

            lookback = min(240, min_idx)
            if lookback >= 60:
                low_60 = np.min(c[min_idx-lookback:min_idx])
                high_60 = np.max(c[min_idx-lookback:min_idx])
                range_pct = (high_60 / low_60 - 1) * 100
            else:
                range_pct = 999

            candidates.append({
                'code': code,
                'name': get_name(code),
                'price': round(c[-1], 2),
                'min_price': round(c[min_idx], 2),
                'min_date': dates[min_idx],
                'days_since': days_since_min,
                'ret_from_min': round(ret_from_min, 1),
                'ret_pre10': round(ret_pre10, 1),
                'macd_col': round(macd[min_idx], 3),
                'vol_ratio': round(vol_ratio, 2),
                'v_min_ratio': round(v_min_ratio, 3),
                'days_from_min': days_from_min,
                'gc_found': gc_found,
                'gc_dist': gc_dist,
                'fake_gc': fake_gc,
                'range_pct': round(range_pct, 1),
            })

        except Exception:
            continue

    conn.close()

    for c in candidates:
        score = 0
        if c['ret_pre10'] < -35: score += 3
        elif c['ret_pre10'] < -25: score += 2
        elif c['ret_pre10'] < -15: score += 1

        if c['macd_col'] < -3.0: score += 3
        elif c['macd_col'] < -1.5: score += 2
        elif c['macd_col'] < -0.5: score += 1

        if c['vol_ratio'] > 2.5: score += 3
        elif c['vol_ratio'] > 1.8: score += 2
        elif c['vol_ratio'] > 1.2: score += 1

        if c['v_min_ratio'] < 0.02: score += 2
        elif c['v_min_ratio'] < 0.08: score += 1

        if c['gc_found'] and c['gc_dist'] <= 8: score += 3
        elif c['gc_found'] and c['gc_dist'] <= 12: score += 2
        elif c['gc_found'] and c['gc_dist'] <= 15: score += 1

        if c['fake_gc']: score -= 2

        if 0 < c['range_pct'] < 50: score += 1
        if 10 < c['ret_from_min'] < 35: score += 1

        c['score'] = score

    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates


def output_report(candidates):
    os.makedirs(OUT_DIR, exist_ok=True)
    today_str = date.today().isoformat()
    out_path = os.path.join(OUT_DIR, f'si_xiang_bottom_{today_str}.md')

    lines = []
    lines.append('# 四象共振 · 底部反转扫描 v1.1')
    lines.append(f'**扫描时间**: {today_str} {datetime.now().strftime("%H:%M")}')
    lines.append('**条件**: 前10日跌10~50% + MACD柱加速下跌 + 量比>1.1 + 地量先于最低点 + 底部距今15~30日 + 距低5~50%')
    lines.append('')
    lines.append(f'**结果**: 共 {len(candidates)} 只')
    lines.append('')

    if not candidates:
        lines.append('**无符合条件的股票**')
    else:
        lines.append('## Top 20')
        lines.append('')
        cols = '| # | 代码 | 名称 | 当前价 | 最低价 | 最低日 | 距低% | 前10日% | MACD柱 | 量比 | 地量比 | 金叉 | 假金叉 | 评分 |'
        sep = '|---|------|------|--------|--------|--------|-------|---------|--------|------|--------|------|--------|------|'
        lines.append(cols)
        lines.append(sep)

        for i, c in enumerate(candidates[:20]):
            gc_str = f'{c["gc_dist"]}日后' if c['gc_found'] else '未'
            fake_str = '是' if c['fake_gc'] else '否'
            lines.append(
                f"| {i+1} | {c['code']} | {c['name']} | {c['price']} | {c['min_price']} | {c['min_date']} "
                f"| {c['ret_from_min']}% | {c['ret_pre10']}% | {c['macd_col']} "
                f"| {c['vol_ratio']} | {c['v_min_ratio']} | {gc_str} | {fake_str} | {c['score']} |"
            )

        lines.append('')
        lines.append('## 全部候选')
        lines.append('')
        for c in candidates:
            gc_str = f'金叉{c["gc_dist"]}日后' if c['gc_found'] else '未金叉'
            fake_str = ' 假金叉' if c['fake_gc'] else ''
            lines.append(
                f"- {c['code']} {c['name']}: 底{c['min_price']}({c['min_date']}) "
                f"距低{c['ret_from_min']}% 前10日{c['ret_pre10']}% MACD柱{c['macd_col']} "
                f"量比{c['vol_ratio']} 地量比{c['v_min_ratio']} {gc_str}{fake_str} 评分{c['score']}"
            )

    content = '\n'.join(lines)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'报告: {out_path}')
    print(f'共 {len(candidates)} 只')
    return out_path


if __name__ == '__main__':
    print('四象共振·底部反转扫描 v1.1')
    print(f'数据库: {DB_PATH}')
    print()

    result = scan_bottom()
    out = output_report(result)

    print()
    print('=== Top 10 ===')
    for i, c in enumerate(result[:10]):
        gc_str = f'金叉{c["gc_dist"]}日后' if c['gc_found'] else '未金叉'
        fake_str = ' 假金叉' if c['fake_gc'] else ''
        print(f'{i+1}. {c["code"]} {c["name"]}: 底{c["min_price"]}({c["min_date"]}) '
              f'距低{c["ret_from_min"]}% 前10日{c["ret_pre10"]}% '
              f'MACD柱{c["macd_col"]} 量比{c["vol_ratio"]} {gc_str}{fake_str} 评分{c["score"]}')