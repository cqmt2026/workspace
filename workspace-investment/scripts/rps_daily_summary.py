# -*- coding: utf-8 -*-
"""
RPS每日收盘全覆盖报告
每天16:10自动运行，输出：
  1. TOP20/BOTTOM20板块排行
  2. 各板块7日RPS变动走势（ASCII表格）
  3. 排名异动板块（较昨日变动>10位）
  4. MA5趋势状态（强势/弱势/震荡）
  5. 全市场情绪评分
  6. 个股异动（较昨日排名骤升/骤降 TOP15）
输出: out_data/RPS_daily_summary_YYYY-MM-DD.md + .json
"""
import io
import os
import sys
import json
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
OUT_DIR = WORK_DIR + r'\out_data'
HIST_DIR = OUT_DIR + r'\rps_history'
DATA_DIR = WORK_DIR + r'\data'


def load_history(days=7):
    """加载最近N日的板块RPS历史（新格式：fetch_board_rps.py输出）"""
    files = sorted([f for f in os.listdir(HIST_DIR)
                    if f.startswith('RPS_board_') and f.endswith('.json')])
    files = files[-days:]
    history = []
    for fname in files:
        with open(os.path.join(HIST_DIR, fname), encoding='utf-8') as f:
            d = json.load(f)
        # 新格式: d['boards'] = [{code, name, change_pct, rps_5d, ...}]
        data = {}
        # 支持旧格式(boards)和新格式(rps_data)
        board_list = d.get('rps_data') or d.get('boards', [])
        for r in board_list:
            code = str(r.get('board_code', r.get('code', '')))
            data[code] = {
                'board_code': code,
                'board_name': r.get('name', ''),
                'change_pct': r.get('change_pct', 0),
                'rps': r.get('rps_5d', r.get('rps', 0)),  # RPS5为核心
            }
        history.append({'date': d['date'], 'data': data})
    return history


def load_today_board_rps(today_str):
    """加载今日收盘板块RPS（新格式：rps_history/RPS_board_YYYYMMDD.json）"""
    today_file = os.path.join(HIST_DIR, f'RPS_board_{today_str}.json')
    if os.path.exists(today_file):
        with open(today_file, encoding='utf-8') as f:
            d = json.load(f)
        data = {}
        for r in d.get('boards', []):
            code = str(r.get('code', ''))
            data[code] = {
                'board_code': code,
                'board_name': r.get('name', ''),
                'change_pct': r.get('change_pct', 0),
                'rps': r.get('rps_5d', 0),
            }
        return data, '申万90(rps_history)'
    # 回退到历史
    hist_files = sorted([f for f in os.listdir(HIST_DIR)
                        if f.startswith('RPS_board_') and f.endswith('.json')])
    if hist_files:
        latest = hist_files[-1]
        with open(os.path.join(HIST_DIR, latest), encoding='utf-8') as f:
            d = json.load(f)
        actual_date = d.get('date', today_str)
        source = f'历史回退({actual_date})'
        data = {}
        board_list = d.get('rps_data') or d.get('boards', [])
        for r in board_list:
            code = str(r.get('board_code', r.get('code', '')))
            data[code] = {
                'board_code': code,
                'board_name': r.get('name', ''),
                'change_pct': r.get('change_pct', 0),
                'rps': r.get('rps_5d', r.get('rps', 0)),
            }
        return data, source
    return {}, '无数据'


def load_stock_history(days=2):
    """加载最近N日的个股RPS历史（对比用）"""
    files = sorted([f for f in os.listdir(OUT_DIR)
                    if f.startswith('RPS_stock_') and f.endswith('.json')])
    files = files[-days:]
    history = []
    for fname in files:
        fpath = OUT_DIR + '\\' + fname
        with open(fpath, encoding='utf-8') as f:
            d = json.load(f)
        history.append({
            'date': d['date'],
            'data': {str(s['code']): s for s in d.get('stocks_rps', [])}
        })
    return history


def compute_ma5(history, board_codes):
    """计算MA5"""
    ma5 = {}
    for code in board_codes:
        vals = []
        for h in history:
            if code in h['data'] and h['data'][code].get('rps') is not None:
                vals.append(h['data'][code]['rps'])
        if len(vals) >= 5:
            ma5[code] = round(sum(vals[-5:]) / 5, 2)
        elif len(vals) >= 2:
            ma5[code] = round(sum(vals) / len(vals), 2)
    return ma5


def arrow(delta, threshold=5):
    """返回涨跌箭头"""
    if delta is None:
        return '→'
    if delta > threshold:
        return '↑'
    elif delta < -threshold:
        return '↓'
    return '→'


def gen_table_row(code, name, history, days=7):
    """生成单板块7日RPS走势行"""
    cells = [code[:8], name[:8]]
    date_vals = []
    for h in history[-days:]:
        rps = h['data'].get(code, {}).get('rps', None)
        date_vals.append(rps)

    for v in date_vals:
        if v is not None:
            cells.append('%5.1f' % v)
        else:
            cells.append('  N/A')

    ma_vals = [v for v in date_vals if v is not None]
    if len(ma_vals) >= 5:
        ma5 = round(sum(ma_vals[-5:]) / 5, 2)
        cells.append('%5.1f' % ma5)
    elif len(ma_vals) >= 2:
        ma5 = round(sum(ma_vals) / len(ma_vals), 1)
        cells.append('%5.1f*' % ma5)
    else:
        cells.append('  N/A')

    if len(ma_vals) >= 2 and ma_vals[-1] is not None and ma_vals[0] is not None:
        delta = ma_vals[-1] - ma_vals[0]
        cells.append(arrow(delta, 5))
    else:
        cells.append('→')

    return '| ' + ' | '.join(cells) + ' |'


def generate_report(today_str, board_rps_today, source, history, ma5, stock_history=None):
    """生成完整报告"""
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    trade_date = today_str

    sorted_boards = sorted(board_rps_today.values(),
                           key=lambda x: x.get('rps', 0), reverse=True)

    name_map = {str(b['board_code']): str(b['board_name']) for b in sorted_boards}

    days = min(len(history), 7)
    date_headers = [h['date'][5:] for h in history[-days:]]
    header_row = '| 板块代码 | 板块名称 | ' + ' | '.join([d for d in date_headers]) + ' | MA5  | 趋势 |'
    sep_row = '|----------|----------|' + '-|'.join(['-----' for _ in range(days)]) + '-|------|-----|'

    top_ma5 = sorted(ma5.items(), key=lambda x: x[1] or 0, reverse=True)[:30]
    table_rows = []
    for code, ma5_val in top_ma5:
        name = name_map.get(code, code)
        table_rows.append(gen_table_row(code, name, history, days))

    rank_changes = []
    if len(history) >= 2:
        today_boards = {str(b['board_code']): b for b in board_rps_today.values()}
        yest_boards = history[-2]['data']
        for code, today_b in today_boards.items():
            yest_b = yest_boards.get(code)
            if yest_b:
                yest_rank = yest_b.get('rank', 0)
                today_rank = today_b.get('rank', 0)
                if yest_rank > 0 and today_rank > 0:
                    change = yest_rank - today_rank
                    if abs(change) >= 10:
                        rank_changes.append({
                            'code': code,
                            'name': name_map.get(code, code),
                            'yest_rank': yest_rank,
                            'today_rank': today_rank,
                            'change': change,
                            'yest_rps': yest_b.get('rps', 0),
                            'today_rps': today_b.get('rps', 0),
                        })
        rank_changes.sort(key=lambda x: abs(x['change']), reverse=True)

    # --- 个股异动 ---
    stock_changes = []
    if stock_history and len(stock_history) >= 2:
        stock_latest = stock_history[-1]['data']
        stock_yest = stock_history[-2]['data']
        for code, s_latest in stock_latest.items():
            s_yest = stock_yest.get(code)
            if s_yest:
                r25 = s_yest.get('rank', 0)
                r26 = s_latest.get('rank', 0)
                if r25 > 0 and r26 > 0:
                    change = r25 - r26
                    rps25 = s_yest.get('rps', 0)
                    rps26 = s_latest.get('rps', 0)
                    rps_chg = rps26 - rps25
                    if abs(change) >= 15 or abs(rps_chg) >= 20:
                        stock_changes.append({
                            'code': code,
                            'name': s_latest.get('name', '?'),
                            'rank25': r25,
                            'rank26': r26,
                            'change': change,
                            'rps25': rps25,
                            'rps26': rps26,
                            'rps_chg': rps_chg,
                            'chg_pct': s_latest.get('change_pct', 0),
                        })
        stock_changes.sort(key=lambda x: abs(x['change']), reverse=True)

    strong_ma5 = []
    rising_ma5 = []
    weak_ma5 = []
    for code, ma5_val in ma5.items():
        if ma5_val is None:
            continue
        name = name_map.get(code, code)
        today_rps = board_rps_today.get(code, {}).get('rps', 0)
        if ma5_val > 70:
            strong_ma5.append((code, name, ma5_val, today_rps))
        elif ma5_val >= 50:
            rising_ma5.append((code, name, ma5_val, today_rps))
        else:
            weak_ma5.append((code, name, ma5_val, today_rps))

    strong_ma5.sort(key=lambda x: x[2], reverse=True)
    rising_ma5.sort(key=lambda x: x[2], reverse=True)
    weak_ma5.sort(key=lambda x: x[2])

    all_rps = [b.get('rps', 0) for b in board_rps_today.values() if b.get('rps') is not None]
    avg_rps = round(sum(all_rps) / len(all_rps), 2) if all_rps else 0
    high_rps_count = len([r for r in all_rps if r >= 70])
    low_rps_count = len([r for r in all_rps if r <= 30])

    lines = []
    lines.append('# 📊 板块RPS每日收盘报告')
    lines.append('')
    lines.append('**交易日期**: ' + trade_date + '  |  **生成时间**: ' + now_str + '  |  **数据源**: ' + source)
    lines.append('**覆盖板块**: ' + str(len(board_rps_today)) + '个 申万二级行业  |  **历史积累**: ' + str(len(history)) + '天')
    lines.append('')

    sentiment_emoji = '🟢' if avg_rps >= 55 else ('🟡' if avg_rps >= 45 else '🔴')
    sentiment_text = '偏强' if avg_rps >= 55 else ('偏弱' if avg_rps < 45 else '中性')
    lines.append('---')
    lines.append('')
    lines.append('## 一、全市场情绪评分')
    lines.append('')
    lines.append('| 指标 | 数值 |')
    lines.append('|------|------|')
    lines.append('| 全市场平均RPS | **' + str(avg_rps) + '** |')
    lines.append('| 强势板块数（RPS>=70） | ' + str(high_rps_count) + ' 个 |')
    lines.append('| 弱势板块数（RPS<=30） | ' + str(low_rps_count) + ' 个 |')
    lines.append('| 市场情绪 | ' + sentiment_emoji + ' ' + sentiment_text + ' |')
    lines.append('')

    lines.append('---')
    lines.append('')
    lines.append('## 二、板块RPS排行榜')
    lines.append('')
    lines.append('### 🔝 TOP20 强势板块')
    lines.append('')
    lines.append('| Rank | 板块代码 | 板块名称 | RPS | 涨幅% |')
    lines.append('|------|----------|----------|-----|------|')
    for i, b in enumerate(sorted_boards[:20], 1):
        name = b.get('board_name', '?')
        code = str(b.get('board_code', '?'))
        rps = b.get('rps', 0)
        chg = b.get('change_pct', 0)
        lines.append('| ' + str(i) + ' | ' + code + ' | ' + name + ' | ' + ('%.2f' % rps) + ' | ' + ('%+.2f%%' % chg) + ' |')

    lines.append('')
    lines.append('### 🔻 BOTTOM20 弱势板块')
    lines.append('')
    lines.append('| Rank | 板块代码 | 板块名称 | RPS | 涨幅% |')
    lines.append('|------|----------|----------|-----|------|')
    for i, b in enumerate(sorted_boards[-20:], len(sorted_boards) - 19):
        name = b.get('board_name', '?')
        code = str(b.get('board_code', '?'))
        rps = b.get('rps', 0)
        chg = b.get('change_pct', 0)
        lines.append('| ' + str(i) + ' | ' + code + ' | ' + name + ' | ' + ('%.2f' % rps) + ' | ' + ('%+.2f%%' % chg) + ' |')

    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 三、各板块7日RPS走势（TOP30 by MA5）')
    lines.append('')
    lines.append('> 注：MA5标注*表示数据不足5日，趋势箭头基于7日变化')
    lines.append('')
    lines.append(header_row)
    lines.append(sep_row)
    for row in table_rows:
        lines.append(row)

    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 四、排名异动板块（较昨日变动>=10位）')
    lines.append('')
    if rank_changes:
        lines.append('| 板块名称 | 昨日排名 | 今日排名 | 变动 | 昨日RPS | 今日RPS |')
        lines.append('|----------|---------|---------|------|---------|---------|')
        for item in rank_changes[:15]:
            sign = '+' if item['change'] > 0 else ''
            lines.append('| ' + item['name'] + ' | ' + str(item['yest_rank']) + ' | ' + str(item['today_rank']) + ' | ' + sign + str(item['change']) + ' | ' + ('%.1f' % item['yest_rps']) + ' | ' + ('%.1f' % item['today_rps']) + ' |')
    else:
        lines.append('无排名变动超过10位的板块')

    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 五、MA5趋势状态分类')
    lines.append('')
    strong_names = ', '.join([n for _, n, _, _ in strong_ma5[:5]])
    rising_names = ', '.join([n for _, n, _, _ in rising_ma5[:5]])
    weak_names = ', '.join([n for _, n, _, _ in weak_ma5[:5]])
    lines.append('| 分类 | 数量 | 代表板块 |')
    lines.append('|------|------|----------|')
    lines.append('| 🟢 MA5>70 强势 | ' + str(len(strong_ma5)) + '个 | ' + strong_names + ' |')
    lines.append('| 🟡 MA5 50-70 上升中 | ' + str(len(rising_ma5)) + '个 | ' + rising_names + ' |')
    lines.append('| 🔴 MA5<50 弱势 | ' + str(len(weak_ma5)) + '个 | ' + weak_names + ' |')
    lines.append('')
    lines.append('> MA5>70：短期强势，持续关注  |  MA5 50-70：动能有起色，关注拐点  |  MA5<50：弱势，谨慎 |')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 六、个股异动排行（较昨日排名骤变 TOP15）')
    lines.append('')
    if stock_changes:
        lines.append('**排名骤升（强势爆发）**：')
        lines.append('')
        lines.append('| Code | 名称 | 排名变化 | RPS变化 | 今日涨幅 |')
        lines.append('|------|------|---------|---------|---------|')
        for c in [x for x in stock_changes if x['change'] > 0][:10]:
            sign = '+' if c['change'] > 0 else ''
            rps_sign = '+' if c['rps_chg'] > 0 else ''
            lines.append('| ' + c['code'] + ' | ' + c['name'] + ' | ' + sign + str(c['change']) + ' | ' + rps_sign + ('%.1f' % c['rps_chg']) + ' | ' + ('%+.2f%%' % c['chg_pct']) + ' |')
        lines.append('')
        lines.append('**排名骤降（风险警示）**：')
        lines.append('')
        lines.append('| Code | 名称 | 排名变化 | RPS变化 | 今日跌幅 |')
        lines.append('|------|------|---------|---------|---------|')
        for c in [x for x in stock_changes if x['change'] < 0][:10]:
            sign = '+' if c['change'] > 0 else ''
            rps_sign = '+' if c['rps_chg'] > 0 else ''
            lines.append('| ' + c['code'] + ' | ' + c['name'] + ' | ' + sign + str(c['change']) + ' | ' + rps_sign + ('%.1f' % c['rps_chg']) + ' | ' + ('%+.2f%%' % c['chg_pct']) + ' |')
    else:
        lines.append('无个股排名异动数据')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('*本报告由投资系统自动生成  |  数据源：东财/THS  |  公式：RPS=(1-排名/板块数)×100*')

    report_md = '\n'.join(lines)

    report_json = {
        'date': trade_date,
        'timestamp': now_str,
        'source': source,
        'total_boards': len(board_rps_today),
        'history_days': len(history),
        'market_avg_rps': avg_rps,
        'high_rps_count': high_rps_count,
        'low_rps_count': low_rps_count,
        'sentiment': sentiment_text,
        'top20': [{'code': str(b['board_code']), 'name': b['board_name'],
                   'rps': b['rps'], 'chg': b['change_pct']} for b in sorted_boards[:20]],
        'bottom20': [{'code': str(b['board_code']), 'name': b['board_name'],
                      'rps': b['rps'], 'chg': b['change_pct']} for b in sorted_boards[-20:]],
        'rank_alerts': rank_changes[:15],
        'ma5_strong': strong_ma5[:10],
        'ma5_rising': rising_ma5[:10],
        'ma5_weak': weak_ma5[:10],
        'stock_alerts': stock_changes[:15],
    }

    return report_md, report_json


def main():
    today = datetime.now().strftime('%Y-%m-%d')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    md_file = OUT_DIR + '\\RPS_daily_summary_' + today + '.md'
    json_file = OUT_DIR + '\\RPS_daily_summary_' + today + '.json'

    print('=' * 60)
    print('RPS每日收盘报告 - ' + timestamp)
    print('=' * 60)

    print('[1/3] 加载今日板块RPS数据...')
    board_rps_today, source = load_today_board_rps(today)
    print('  覆盖: ' + str(len(board_rps_today)) + '个板块（' + source + '）')

    if not board_rps_today:
        print('  今日数据不存在，跳过')
        return

    print('[2/3] 加载历史数据...')
    history = load_history(days=7)
    print('  历史积累: ' + str(len(history)) + '天')

    print('[3/4] 加载个股RPS历史...')
    stock_history = load_stock_history(days=2)
    print('  个股历史: ' + str(len(stock_history)) + '天')

    print('[4/4] 生成报告...')
    board_codes = list(board_rps_today.keys())
    ma5 = compute_ma5(history, board_codes)
    print('  MA5有效板块: ' + str(len(ma5)) + '个')

    report_md, report_json = generate_report(today, board_rps_today, source, history, ma5, stock_history)

    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(report_md)
    print('  Markdown: ' + md_file)

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report_json, f, ensure_ascii=False, indent=2)
    print('  JSON: ' + json_file)

    print()
    print('--- 报告摘要 ---')
    print('全市场平均RPS: ' + str(report_json['market_avg_rps']))
    print('强势板块数: ' + str(report_json['high_rps_count']) + '个')
    print('弱势板块数: ' + str(report_json['low_rps_count']) + '个')
    print('MA5强势: ' + str(len(report_json['ma5_strong'])) + '个')
    print('MA5上升中: ' + str(len(report_json['ma5_rising'])) + '个')
    print('MA5弱势: ' + str(len(report_json['ma5_weak'])) + '个')
    print('排名异动: ' + str(len(report_json['rank_alerts'])) + '个板块')
    print('个股异动: ' + str(len(report_json['stock_alerts'])) + '只')
    print('=' * 60)

    return report_md, report_json


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()