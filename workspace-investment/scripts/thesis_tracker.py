# -*- coding: utf-8 -*-
"""
投资论文追踪 (Thesis Tracker)
=============================
ai-berkshire /thesis-tracker 的 AliceQuant 版本。

买入后持续跟踪投资逻辑是否被证伪。

核心机制：
1. 每只持仓有"投资论文"——买入理由的核心假设
2. 定期检查假设是否仍然成立
3. 区分"事实变化"vs"估值变化"vs"措辞变化"
4. 论文被证伪 → 卖出信号，不管盈亏

用法：
  python thesis_tracker.py                    # 检查所有持仓
  python thesis_tracker.py sh688556           # 检查单只
  python thesis_tracker.py --init             # 初始化论文文件
  python thesis_tracker.py --drift sh688556   # 检测论文漂移
"""
import sys, os, json, sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORK_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
DB = r'F:\market_data.db'
PORTFOLIO = WORK_DIR / 'data' / 'portfolio.json'
THESIS_DIR = WORK_DIR / 'data' / 'theses'
OUT_DIR = WORK_DIR / 'out_data'
os.makedirs(THESIS_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

def to_db_code(code):
    code = code.strip().replace('.','')
    if code.startswith('sh'): return f'sh.{code[2:]}'
    elif code.startswith('sz'): return f'sz.{code[2:]}'
    elif code.startswith('6') or code.startswith('68'): return f'sh.{code}'
    elif code.startswith('0') or code.startswith('3'): return f'sz.{code}'
    return code


# 预定义的默认论文模板（常见A股投资逻辑）
DEFAULT_THESES = {
    'growth_turnaround': {
        'name': '成长反转',
        'assumptions': [
            '行业周期见底，订单开始恢复',
            '公司产能利用率回升',
            '毛利率触底回升',
        ],
        'kill_conditions': [
            '连续2季营收同比下滑',
            '产能利用率持续低于60%',
            '毛利率创3年新低',
        ],
    },
    'value_defensive': {
        'name': '价值防御',
        'assumptions': [
            '现金流稳定，分红可持续',
            '估值处于历史低位（PE<15）',
            '行业格局稳定，龙头地位稳固',
        ],
        'kill_conditions': [
            '分红率下降超过50%',
            'PE跌破历史5%分位（可能是价值陷阱）',
            '市占率连续2年下滑',
        ],
    },
    'momentum_breakout': {
        'name': '动量突破',
        'assumptions': [
            '行业出现催化剂（政策/技术/事件）',
            '资金持续流入，量价配合',
            '技术面突破关键阻力位',
        ],
        'kill_conditions': [
            '催化剂证伪（政策落空/技术失败）',
            '连续3日放量下跌',
            '跌破突破位-3%',
        ],
    },
}


def load_portfolio() -> List[dict]:
    """加载持仓"""
    if not PORTFOLIO.exists():
        return []
    with open(PORTFOLIO, 'r', encoding='utf-8') as f:
        pf = json.load(f)
    return pf.get('holdings', [])


def load_thesis(code: str) -> Optional[dict]:
    """加载论文文件"""
    path = THESIS_DIR / f'{code}.json'
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_thesis(code: str, thesis: dict):
    """保存论文文件"""
    path = THESIS_DIR / f'{code}.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(thesis, f, ensure_ascii=False, indent=2)


def init_theses():
    """初始化所有持仓的论文文件"""
    holdings = load_portfolio()
    if not holdings:
        print('当前无持仓，无需初始化')
        return

    for h in holdings:
        code = h.get('code', '')
        name = h.get('name', '')
        buy_price = h.get('buy_price', 0)

        existing = load_thesis(code)
        if existing:
            print(f'  ⏭️ {name}({code}) 已有论文，跳过')
            continue

        # 创建默认论文
        thesis = {
            'code': code,
            'name': name,
            'buy_price': buy_price,
            'buy_date': h.get('buy_date', ''),
            'thesis_type': 'growth_turnaround',  # 默认
            'thesis_name': '成长反转',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'core_assumptions': DEFAULT_THESES['growth_turnaround']['assumptions'][:],
            'kill_conditions': DEFAULT_THESES['growth_turnaround']['kill_conditions'][:],
            'checks_history': [],
            'status': 'active',
        }

        save_thesis(code, thesis)
        print(f'  ✅ {name}({code}) 论文已创建')

    print(f'\n论文目录: {THESIS_DIR}')


def get_current_data(code: str, date: str = None) -> Optional[dict]:
    """获取当前市场数据用于论文检查"""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')

    try:
        conn = sqlite3.connect(DB)
        rows = conn.execute(
            "SELECT date, close, volume, open, high, low FROM daily_k "
            "WHERE code=? AND date<=? ORDER BY date DESC LIMIT 30",
            (to_db_code(code), date)
        ).fetchall()
        conn.close()

        if not rows:
            return None

        closes = [r[1] for r in reversed(rows)]
        volumes = [r[2] for r in reversed(rows)]

        return {
            'latest_close': closes[-1],
            'latest_date': rows[0][0],
            'ma5': sum(closes[-5:]) / 5 if len(closes) >= 5 else closes[-1],
            'ma20': sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1],
            'avg_vol': sum(volumes[-5:]) / 5 if len(volumes) >= 5 else volumes[-1],
            'latest_vol': volumes[-1],
            'pnl_from_buy': 0,  # 需要外部传入buy_price
        }
    except:
        return None


def check_thesis(code: str, date: str = None) -> dict:
    """检查论文是否仍成立

    返回: {
        thesis_still_valid: bool,
        assumptions: [{assumption, status, evidence}],
        kill_signals: [{condition, triggered, evidence}],
        overall_status: '成立' | '警惕' | '证伪',
        action: '持有' | '减仓观察' | '清仓',
    }
    """
    thesis = load_thesis(code)
    if not thesis:
        return {
            'code': code,
            'thesis_still_valid': False,
            'error': '未找到论文文件，请先运行 --init',
            'overall_status': '未知',
            'action': '初始化论文',
        }

    if not date:
        date = datetime.now().strftime('%Y-%m-%d')

    name = thesis.get('name', code)
    buy_price = thesis.get('buy_price', 0)

    # 获取数据
    data = get_current_data(code, date)
    if not data:
        return {
            'code': code,
            'name': name,
            'thesis_still_valid': True,
            'assumptions': [],
            'kill_signals': [],
            'overall_status': '数据不足',
            'action': '观察',
        }

    current_price = data['latest_close']
    pnl = (current_price - buy_price) / buy_price * 100 if buy_price > 0 else 0

    # 检查核心假设
    assumptions = []
    for a in thesis.get('core_assumptions', []):
        status = '未知'
        evidence = '无法自动验证，需人工确认'

        # 尝试自动验证部分假设
        if 'MA' in a or '均线' in a or '趋势' in a:
            if data['latest_close'] > data['ma20']:
                status = '成立'
                evidence = f'收盘{current_price:.2f}>MA20{data["ma20"]:.2f}'
            else:
                status = '失效'
                evidence = f'收盘{current_price:.2f}<MA20{data["ma20"]:.2f}'
        elif '量' in a or '资金' in a:
            vol_ratio = data['latest_vol'] / data['avg_vol'] if data['avg_vol'] > 0 else 1
            if vol_ratio > 0.8:
                status = '成立'
                evidence = f'量比{vol_ratio:.1f}'
            else:
                status = '失效'
                evidence = f'量比{vol_ratio:.1f}（缩量）'
        elif '估值' in a or 'PE' in a:
            status = '未知'
            evidence = '估值需外部数据验证'

        assumptions.append({
            'assumption': a,
            'status': status,
            'evidence': evidence,
        })

    # 检查否决条件
    kill_signals = []
    for k in thesis.get('kill_conditions', []):
        triggered = False
        evidence = '未触发'

        if '跌破' in k or '破' in k:
            # 简化：如果浮亏>10%，认为趋势相关否决条件可能触发
            if pnl < -10:
                triggered = True
                evidence = f'浮亏{pnl:.1f}%'
        elif '下滑' in k or '下降' in k or '减少' in k:
            if pnl < -5:
                triggered = True
                evidence = f'浮亏{pnl:.1f}%，可能存在业绩下滑'

        kill_signals.append({
            'condition': k,
            'triggered': triggered,
            'evidence': evidence,
        })

    # 综合判断
    failed_assumptions = sum(1 for a in assumptions if a['status'] == '失效')
    triggered_kills = sum(1 for k in kill_signals if k['triggered'])

    if triggered_kills > 0:
        overall = '证伪'
        action = '清仓'
        still_valid = False
    elif failed_assumptions >= 2:
        overall = '警惕'
        action = '减仓观察'
        still_valid = True  # 还没死
    else:
        overall = '成立'
        action = '持有'
        still_valid = True

    # 记录检查历史
    check_record = {
        'date': date,
        'price': current_price,
        'pnl_pct': round(pnl, 2),
        'overall_status': overall,
        'failed_assumptions': failed_assumptions,
        'triggered_kills': triggered_kills,
    }

    thesis['checks_history'].append(check_record)
    thesis['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    save_thesis(code, thesis)

    return {
        'code': code,
        'name': name,
        'buy_price': buy_price,
        'current_price': current_price,
        'pnl_pct': round(pnl, 2),
        'thesis_name': thesis.get('thesis_name', ''),
        'thesis_still_valid': still_valid,
        'assumptions': assumptions,
        'kill_signals': kill_signals,
        'overall_status': overall,
        'action': action,
        'check_date': date,
    }


def detect_drift(code: str) -> Optional[dict]:
    """检测论文漂移

    对比最近两次检查，区分：
    - 事实变化：假设从成立→失效（真实变化）
    - 估值变化：价格变了但假设不变（只是市场波动）
    - 措辞变化：同样的信号，解读不同（自我欺骗）
    """
    thesis = load_thesis(code)
    if not thesis:
        return None

    history = thesis.get('checks_history', [])
    if len(history) < 2:
        return {'code': code, 'drift_type': '数据不足', 'detail': '需要至少2次检查'}

    recent = history[-1]
    prev = history[-2]

    drifts = []

    # 1. 事实变化：状态从成立→证伪
    if recent['overall_status'] != prev['overall_status']:
        drifts.append({
            'type': '事实变化',
            'detail': f"状态从'{prev['overall_status']}'变为'{recent['overall_status']}'",
            'severity': '高' if recent['overall_status'] == '证伪' else '中',
        })

    # 2. 估值变化：价格变化>5%但假设不变
    price_chg = abs(recent.get('pnl_pct', 0) - prev.get('pnl_pct', 0))
    if price_chg > 5 and recent['failed_assumptions'] == prev['failed_assumptions']:
        drifts.append({
            'type': '估值变化',
            'detail': f"盈亏变动{price_chg:.1f}%但假设未变，可能是市场波动",
            'severity': '低',
        })

    # 3. 措辞变化：假设数变化但结论不变
    if recent['failed_assumptions'] != prev['failed_assumptions'] and recent['overall_status'] == prev['overall_status']:
        drifts.append({
            'type': '措辞变化',
            'detail': f"失效假设从{prev['failed_assumptions']}变为{recent['failed_assumptions']}，但结论未变——注意是否在自我说服",
            'severity': '中',
        })

    if not drifts:
        drifts.append({'type': '无漂移', 'detail': '最近两次检查结论一致', 'severity': '无'})

    return {'code': code, 'name': thesis.get('name', ''), 'drifts': drifts}


def format_check_result(result: dict) -> str:
    """格式化检查结果"""
    lines = []
    code = result.get('code', '')
    name = result.get('name', code)
    status = result.get('overall_status', '未知')
    action = result.get('action', '未知')

    status_emoji = {'成立': '✅', '警惕': '⚠️', '证伪': '🔴', '数据不足': '❓', '未知': '❓'}
    lines.append(f"\n{status_emoji.get(status, '❓')} **{name}({code}) 论文检查**")
    lines.append(f"  状态: {status} | 建议: {action}")
    lines.append(f"  买入价: {result.get('buy_price', 0):.2f} | 现价: {result.get('current_price', 0):.2f} | 浮盈: {result.get('pnl_pct', 0):+.1f}%")

    assumptions = result.get('assumptions', [])
    if assumptions:
        lines.append(f"\n  📋 核心假设:")
        for a in assumptions:
            emoji = '✅' if a['status'] == '成立' else '❌' if a['status'] == '失效' else '❓'
            lines.append(f"    {emoji} {a['assumption']}")
            lines.append(f"       证据: {a['evidence']}")

    kill_signals = result.get('kill_signals', [])
    if kill_signals:
        lines.append(f"\n  🔫 否决条件:")
        for k in kill_signals:
            emoji = '🔴' if k['triggered'] else '🟢'
            lines.append(f"    {emoji} {k['condition']}")
            if k['triggered']:
                lines.append(f"       ⚡ 已触发: {k['evidence']}")

    return '\n'.join(lines)


def run_check_all(date: str = None):
    """检查所有持仓论文"""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')

    holdings = load_portfolio()
    if not holdings:
        print('当前无持仓')
        return

    print(f"\n{'=' * 60}")
    print(f"📋 投资论文追踪 — {date}")
    print(f"{'=' * 60}")

    results = []
    for h in holdings:
        code = h.get('code', '')
        result = check_thesis(code, date)
        results.append(result)
        print(format_check_result(result))

    # 汇总
    print(f"\n{'=' * 60}")
    print(f"📊 汇总:")
    valid = sum(1 for r in results if r.get('overall_status') == '成立')
    warning = sum(1 for r in results if r.get('overall_status') == '警惕')
    invalidated = sum(1 for r in results if r.get('overall_status') == '证伪')
    print(f"  ✅ 成立: {valid} | ⚠️ 警惕: {warning} | 🔴 证伪: {invalidated}")

    if invalidated > 0:
        print(f"\n  ⚠️ 证伪持仓需立即处理！论文被证伪=卖出信号")

    # 保存
    output = {
        'date': date,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'results': results,
        'summary': {'valid': valid, 'warning': warning, 'invalidated': invalidated},
    }
    out_path = OUT_DIR / f'thesis_check_{date}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n💾 已保存: {out_path}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='投资论文追踪')
    parser.add_argument('code', nargs='?', help='股票代码（不填则检查所有持仓）')
    parser.add_argument('--init', action='store_true', help='初始化论文文件')
    parser.add_argument('--drift', action='store_true', help='检测论文漂移')
    parser.add_argument('--date', help='日期(YYYY-MM-DD)')
    args = parser.parse_args()

    if args.init:
        init_theses()
    elif args.drift and args.code:
        result = detect_drift(args.code)
        if result:
            print(f"\n📊 论文漂移检测 — {result.get('name', args.code)}")
            for d in result.get('drifts', []):
                severity_emoji = {'高': '🔴', '中': '🟡', '低': '🟢', '无': '✅'}
                print(f"  {severity_emoji.get(d['severity'], '❓')} [{d['type']}] {d['detail']}")
    elif args.code:
        result = check_thesis(args.code, args.date)
        print(format_check_result(result))
    else:
        run_check_all(args.date)
