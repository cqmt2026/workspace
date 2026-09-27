# -*- coding: utf-8 -*-
"""
交易结果追踪器
==============
每天09:10运行，检查pending决策，计算参考收益，推送主人确认

逻辑:
  1. 加载 decisions.json 中所有 pending 决策
  2. 获取每只股票的最新收盘价（腾讯API）
  3. 计算参考收益（现价 vs 成本）
  4. 推送微信给主人，等待确认结果
  5. 主人回复「确认 ID 结果」→ 标记结果

Cron: 每天 09:10 (INV-Trade-Result-Tracker)
"""
import io
import sys, os, json, urllib.request
from datetime import datetime, date, timedelta
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
DECISIONS_FILE = os.path.join(WORK_DIR, 'data', 'decisions.json')
DB = r'F:\market_data.db'


def load_pending():
    if not os.path.exists(DECISIONS_FILE):
        return []
    try:
        with open(DECISIONS_FILE, encoding='utf-8') as f:
            data = json.load(f)
        return [r for r in data.get('records', []) if r.get('result') == 'pending']
    except:
        return []


def get_realtime_price(code):
    """实时行情（通过统一接口）"""
    from scripts.data_api import DataAPI
    try:
        rt = DataAPI.get_realtime([code])
        if rt:
            for k, v in rt.items():
                return v['price']
        return None
    except:
        return None


def get_db_t1_price(code, buy_date):
    """从DB获取T+1日收盘价"""
    try:
        import sqlite3
        conn = sqlite3.connect(DB)
        # 找buy_date之后的第一条数据
        cur = conn.cursor()
        cur.execute(
            'SELECT date, close FROM daily_k WHERE code=? AND date>? ORDER BY date ASC LIMIT 1',
            (code, buy_date[:10])
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return {'date': row[0], 'price': row[1]}
    except:
        pass
    return None


def calc_pnl(buy_price, current_price):
    if not buy_price or not current_price:
        return None
    return round((current_price - buy_price) / buy_price * 100, 2)


def build_tracker_report(pending):
    """构建追踪报告"""
    if not pending:
        return None

    lines = []
    lines.append("📊 **持仓结果追踪 · 待确认**")
    lines.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 50)
    lines.append(f"{'ID':<4} {'名称':<8} {'买入价':>7} {'现价':>7} {'浮盈':>7} {'操作':<6} {'持仓天数'}")
    lines.append("-" * 55)

    today = datetime.now()
    rows = []

    for r in pending:
        code = r.get('code', '')
        name = r.get('name', code)
        buy_price = r.get('price')
        action = r.get('action', '')

        # 持仓天数
        try:
            buy_dt = datetime.fromisoformat(r.get('timestamp', ''))
            days = (today - buy_dt).days
        except:
            days = '?'

        # 实时价格
        snap = get_realtime_price(code)
        current_price = snap['price'] if snap else None
        chg_pct = snap['chg_pct'] if snap else None

        # 计算浮盈
        pnl = calc_pnl(buy_price, current_price) if buy_price and current_price else None

        pnl_str = f"{pnl:+.2f}%" if pnl is not None else 'N/A'
        try:
            price_str = f"{float(buy_price):.2f}" if buy_price else 'N/A'
        except:
            price_str = str(buy_price) if buy_price else 'N/A'
        try:
            current_str = f"{float(current_price):.2f}" if current_price else 'N/A'
        except:
            current_str = str(current_price) if current_price else 'N/A'
        chg_str = f"({chg_pct:+.1f}%)" if chg_pct is not None else ''
        action_cn = {'buy': '买入', 'sell': '卖出', 'watch': '观望'}.get(action, action)

        lines.append(
            f"{r['id']:<4} {name[:7]:<8} {price_str:>7} {current_str:>7} {pnl_str:>7} {action_cn:<6} {days}天"
        )
        rows.append({
            'id': r['id'], 'code': code, 'name': name,
            'buy_price': buy_price, 'current_price': current_price,
            'pnl': pnl, 'action': action, 'days': days
        })

    lines.append("=" * 50)
    lines.append("📝 **结果确认格式**（回复我）:")
    lines.append("  确认 3 成功   → ID=3盈利了")
    lines.append("  确认 3 失败   → ID=3亏损了")
    lines.append("  确认 3 保本   → ID=3不赚不亏")
    lines.append("")
    lines.append("⏳ pending决策将持续追踪，直到您确认结果")

    return '\n'.join(lines), rows


def push_to_wechat(msg):
    """微信推送已由Cron delivery统一处理，此函数仅打印"""
    print(msg)
    return True


def main():
    pending = load_pending()
    print(f"[结果追踪] 待确认决策: {len(pending)}条")

    if not pending:
        print("无pending决策，跳过")
        return

    report, rows = build_tracker_report(pending)
    print(report)

    # 推送到微信
    pushed = push_to_wechat(report)
    if pushed:
        print("\n✅ 已推送到微信，等待主人确认结果")
    else:
        print("\n⚠️ 微信推送失败，请手动确认pending决策")


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()
