# -*- coding: utf-8 -*-
"""
持仓决策追踪器
主人每日下午收盘后告知买卖情况 → 记录到结构化文件
用法:
    python trade_tracker.py --add --code sz002805 --action sell --price 29.57 --reason "触发+10%清仓规则"
    python trade_tracker.py --add --code sh600186 --action sell --price 14.40 --qty 200 --reason "减仓60%"
    python trade_tracker.py --show
"""
import json, sys, sqlite3, os
from datetime import datetime, date
from pathlib import Path

WORKSPACE = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-investment")
TRADE_LOG = WORKSPACE / "data" / "trade_log.json"
PORTFOLIO = WORKSPACE / "data" / "portfolio.json"

def load_trade_log():
    if TRADE_LOG.exists():
        with open(TRADE_LOG, encoding='utf-8') as f:
            return json.load(f)
    return {"trades": [], "daily_summary": {}}

def save_trade_log(log):
    with open(TRADE_LOG, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2, default=str)

def get_cost(code):
    """从portfolio.json获取成本"""
    if not PORTFOLIO.exists():
        return None
    with open(PORTFOLIO, encoding='utf-8') as f:
        data = json.load(f)
    for h in data.get("holdings", []):
        if h["code"].lower() == code.lower():
            return h.get("cost")
    return None

def add_trade(code, action, price, qty=None, reason=""):
    """记录一笔交易"""
    log = load_trade_log()
    cost = get_cost(code)
    today = date.today().isoformat()

    trade = {
        "id": len(log["trades"]) + 1,
        "date": today,
        "code": code,
        "action": action,
        "price": float(price),
        "qty": float(qty) if qty else None,
        "cost": cost,
        "reason": reason,
        "pnl_pct": round((float(price) - cost) / cost * 100, 2) if cost and action == "sell" else None,
        "recorded_at": datetime.now().isoformat()
    }

    log["trades"].append(trade)

    # 更新当日汇总
    if today not in log["daily_summary"]:
        log["daily_summary"][today] = {"buy": 0, "sell": 0, "total_pnl": 0.0, "trades": []}
    summary = log["daily_summary"][today]
    summary["trades"].append(trade["id"])
    if action == "buy":
        summary["buy"] += 1
    elif action == "sell":
        summary["sell"] += 1
        if trade["pnl_pct"] is not None:
            summary["total_pnl"] = round(summary.get("total_pnl", 0) + trade["pnl_pct"], 2)

    save_trade_log(log)
    print(f"[记录成功] #{trade['id']} {today} {action.upper()} {code} @ {price} | 成本={cost} | 盈亏={trade['pnl_pct']}% | 理由:{reason}")
    return trade

def show_trades(days=30):
    """显示最近交易记录"""
    log = load_trade_log()
    today = date.today().isoformat()
    cutoff = (datetime.strptime(today, '%Y-%m-%d') - __import__('datetime').timedelta(days=days)).strftime('%Y-%m-%d')

    trades = [t for t in log.get("trades", []) if t["date"] >= cutoff]
    if not trades:
        print("暂无交易记录")
        return

    print(f"\n{'='*70}")
    print(f"{'日期':<12} {'代码':<12} {'操作':<6} {'价格':>8} {'股数':>8} {'成本':>8} {'盈亏%':>8} {'理由'}")
    print(f"{'-'*70}")
    for t in sorted(trades, key=lambda x: x["date"], reverse=True):
        pnl = f"{t['pnl_pct']:+.2f}%" if t.get("pnl_pct") is not None else "持仓中"
        qty = str(t.get("qty", "-"))
        cost = f"{t.get('cost', 0):.2f}" if t.get("cost") else "-"
        reason = t.get("reason", "")[:20]
        print(f"{t['date']:<12} {t['code']:<12} {t['action'].upper():<6} {t['price']:>8.2f} {qty:>8} {cost:>8} {pnl:>8} {reason}")
    print(f"{'='*70}")

    # 当日汇总
    today_summary = log.get("daily_summary", {}).get(today, {})
    print(f"\n今日汇总: 买入{today_summary.get('buy',0)}笔 卖出{today_summary.get('sell',0)}笔 累计盈亏{today_summary.get('total_pnl',0):+.2f}%")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--add", action="store_true")
    parser.add_argument("--code", type=str)
    parser.add_argument("--action", type=str, choices=["buy", "sell"])
    parser.add_argument("--price", type=float)
    parser.add_argument("--qty", type=float, default=None)
    parser.add_argument("--reason", type=str, default="")
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    if args.add:
        if not args.code or not args.action or not args.price:
            print("错误: --add 需要 --code --action --price")
            sys.exit(1)
        add_trade(args.code, args.action, args.price, args.qty, args.reason)
    elif args.show:
        show_trades(args.days)
    else:
        parser.print_help()
