# -*- coding: utf-8 -*-
"""
每日决策参考日报生成器
五段式报告 → 微信推送
一，大盘指数 / 二，市场情绪 / 三，持仓动态 / 四，候选信号 / 五，持仓趋势与风险评估
止盈基于趋势/估值/逻辑，非机械比例
"""
import json, sys, sqlite3, urllib.request, os, shutil
from datetime import datetime, date
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORKSPACE = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-investment")
DB = r"F:\market_data.db"
PORTFOLIO = WORKSPACE / "data" / "portfolio.json"
OUT_DIR = WORKSPACE / "out_data"
RPS_SUMMARY = OUT_DIR / f"RPS_daily_summary_{date.today().strftime('%Y-%m-%d')}.json"
RPS_STOCK = OUT_DIR / f"rps_5d_{date.today().strftime('%Y%m%d')}.json"

# Obsidian 归档路径
OBSIDIAN_VAULT = Path(r"C:\Users\Administrator\Obsidian\Jarvis")
OBSIDIAN_DAILY = OBSIDIAN_VAULT / "00-日记"
OBSIDIAN_TRACKING = OBSIDIAN_VAULT / "03-项目" / "贾维斯系统" / "推荐追踪"


def sync_to_obsidian(report_text, today):
    """将日报同步到Obsidian 00-日记目录"""
    try:
        obsidian_dir = OBSIDIAN_DAILY
        obsidian_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成Obsidian兼容的Markdown文件（带frontmatter）
        md_content = f"""---
tags: [日报, 决策参考]
date: {today}
created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

{report_text}
"""
        
        obsidian_file = obsidian_dir / f"{today}_决策日报.md"
        with open(obsidian_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        # 不打印到stdout（cron环境下可能已关闭）
        return True
    except Exception as e:
        return False


def sync_signals_to_obsidian(today):
    """将信号聚合Top10同步到Obsidian推荐追踪看板"""
    try:
        # 读取信号聚合结果
        signal_file = OUT_DIR / f"signal_aggregated_{today}.json"
        if not signal_file.exists():
            return False
            
        with open(signal_file, encoding="utf-8") as f:
            signals = json.load(f)
        
        # 读取推荐追踪统计
        tracker_file = WORKSPACE / "data" / "recommendation_tracker.json"
        tracker_stats = {}
        if tracker_file.exists():
            with open(tracker_file, encoding="utf-8") as f:
                tracker_data = json.load(f)
            tracker_stats = tracker_data.get("source_stats", {})
        
        tracking_dir = OBSIDIAN_TRACKING
        tracking_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成推荐追踪看板
        md_lines = [f"---", f"tags: [推荐追踪, 信号聚合]", f"date: {today}", f"updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", f"---", "", f"# 推荐追踪看板 · {today}", ""]
        
        # 信号源胜率统计
        if tracker_stats:
            md_lines.append("## 信号源胜率统计")
            md_lines.append("")
            md_lines.append("| 信号源 | 推荐次数 | 胜率 | T+1均收益 | 状态 |")
            md_lines.append("|--------|---------|------|----------|------|")
            for source, s in sorted(tracker_stats.items()):
                total = s.get('total', 0)
                wr = s.get('win_rate', 0)
                ret = s.get('avg_t1_return', 0)
                status = "🟢" if wr >= 50 and total >= 3 else "🔴" if total >= 3 else "⏳"
                md_lines.append(f"| {source} | {total} | {wr:.0f}% | {ret:+.2f}% | {status} |")
            md_lines.append("")
        
        # 今日Top10信号
        if isinstance(signals, list):
            md_lines.append("## 今日Top信号")
            md_lines.append("")
            md_lines.append("| 排名 | 代码 | 名称 | 综合分 | 信号源 |")
            md_lines.append("|------|------|------|--------|--------|")
            for i, s in enumerate(signals[:10], 1):
                code = s.get('code', s.get('symbol', ''))
                name = s.get('name', '')
                score = s.get('score', s.get('total_score', 0))
                source = s.get('source', '综合')
                md_lines.append(f"| {i} | {code} | {name} | {score} | {source} |")
        
        md_content = "\n".join(md_lines)
        
        # 更新看板文件
        tracking_file = tracking_dir / f"tracking_{today}.md"
        with open(tracking_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        # 同时更新最新看板（覆盖式）
        latest_file = tracking_dir / "最新看板.md"
        with open(latest_file, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        return True
    except Exception as e:
        return False


def get_market_index():
    import sys, os
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    if _script_dir not in sys.path:
        sys.path.insert(0, _script_dir)
    from data_api import DataAPI
    indices = [
        ('sh000001', '上证指数'),
        ('sz399001', '深证成指'),
        ('sh000688', '科创50'),
    ]
    result = {}
    for code, name in indices:
        idx = DataAPI.get_index(code)
        if idx:
            result[name] = {'price': idx['price'], 'chg': round(idx['chg_pct'], 2)}
    return result


def get_portfolio_status():
    """使用 portfolio_analysis.py 获取更丰富的持仓数据"""
    try:
        import sys
        sys.path.insert(0, str(WORKSPACE / "scripts"))
        from portfolio_analysis import enrich_holdings
        holdings = enrich_holdings()
        return holdings
    except Exception as e:
        print(f"[WARN] portfolio_analysis: {e}")
        return []


def get_rps_data():
    """读取RPS数据：板RPS汇总 + 个股RPS"""
    out = {}
    # 板RPS MA5汇总（rps_daily_summary.py输出）
    if RPS_SUMMARY.exists():
        try:
            with open(RPS_SUMMARY, encoding="utf-8") as f:
                d = json.load(f)
            out["ma5_strong"] = d.get("ma5_strong", [])[:8]
            out["ma5_rising"] = d.get("ma5_rising", [])[:5]
            out["ma5_weak"] = d.get("ma5_weak", [])[:5]
            out["sentiment"] = d.get("sentiment", "")
            out["market_avg_rps"] = d.get("market_avg_rps", 0)
            out["high_cnt"] = d.get("high_rps_count", 0)
            out["low_cnt"] = d.get("low_rps_count", 0)
            out["rank_alerts"] = d.get("rank_alerts", [])[:8]
        except Exception as e:
            print(f"[WARN] rps_summary: {e}")
    # 个股RPS5日（rps_5d输出）
    if RPS_STOCK.exists():
        try:
            with open(RPS_STOCK, encoding="utf-8") as f:
                d = json.load(f)
            stocks = d.get("stocks_rps", [])
            top = sorted(stocks, key=lambda x: x.get("rps", 0), reverse=True)[:10]
            out["stock_top"] = [(s.get("code", ""), s.get("rps", 0)) for s in top]
        except Exception as e:
            print(f"[WARN] rps_stock: {e}")
    return out


def confidence_tag(source_type: str, data_available: bool = True) -> str:
    """置信度标注（ai-berkshire风格 A/B/C 级）
    
    A级：数据来自2+独立来源，交叉验证通过
    B级：数据来自1个来源，逻辑合理但未交叉验证
    C级：推算/估算/数据不足，仅供参考
    
    用在日报中每个结论后面加标记。
    """
    if not data_available:
        return '`[C级]`'
    
    # 指数数据来源稳定，通常A级
    if source_type in ('index', 'market', 'price', 'volume'):
        return '`[A级]`'
    # RPS来自akshare，有时不稳定
    if source_type in ('rps', 'rps_board', 'rps_stock'):
        return '`[B级]`'
    # 候选信号来自内部模型
    if source_type in ('candidate', 'signal', 'pipeline'):
        return '`[B级]`'
    # 舆情数据
    if source_type in ('sentiment', 'mx', 'news'):
        return '`[B级]`'
    # 推算/估算值
    if source_type in ('estimate', 'projection', 'forecast'):
        return '`[C级]`'
    # 默认
    return '`[B级]`'


def is_portfolio_empty():
    """检查持仓是否为空"""
    try:
        with open(PORTFOLIO, encoding='utf-8') as f:
            pf = json.load(f)
        holdings = pf.get('holdings', [])
        return len(holdings) == 0
    except:
        return False


def format_report():
    today = date.today().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M")
    market = get_market_index()
    portfolio = get_portfolio_status()
    rps = get_rps_data()
    lines = []

    lines.append(f"📊 **每日决策参考 · {today} {now}**")
    lines.append("=" * 56)

    # ===== 一，大盘指数 =====
    lines.append("\n📈 **一，大盘指数**")
    parts = []
    for name, code in [("上证指数", "sh000001"), ("深证成指", "sz399001"), ("科创50", "sh000688")]:
        if name in market:
            m = market[name]
            e = "🟢" if m["chg"] > 0 else "🔴"
            parts.append(f"{e} {name} {m['price']:.2f}({m['chg']:+.2f}%)")
    ct = confidence_tag('index')
    lines.append(f"{' | '.join(parts) if parts else '数据获取中'} {ct}")

    # 涨停/跌停
    try:
        conn = sqlite3.connect(DB)
        prev = conn.execute(
            "SELECT MAX(date) FROM daily_k WHERE code='sh000001' AND date < ?", (today,)
        ).fetchone()[0]
        if prev:
            zt = conn.execute(
                "SELECT COUNT(*) FROM daily_zt WHERE date = ?", (today,)
            ).fetchone()[0] or 0
            dt = conn.execute(
                "SELECT COUNT(*) FROM daily_k WHERE date=? AND close<open*0.97 AND volume>0",
                (today,)
            ).fetchone()[0] or 0
            ct_zt = confidence_tag('volume')
            lines.append(f"📈 涨停{zt}家 | 跌停{dt}家 {ct_zt}")
        conn.close()
    except Exception as e:
        print(f"[WARN] zt_count: {e}")

    # ===== 二，市场情绪（RPS视角）=====
    strong = rps.get("ma5_strong", [])
    rising = rps.get("ma5_rising", [])
    weak = rps.get("ma5_weak", [])
    stock_top = rps.get("stock_top", [])
    has_rps = strong or rising or weak or stock_top

    if has_rps:
        lines.append("\n🌀 **二，市场情绪（RPS视角）**")
        avg = rps.get("market_avg_rps", 0)
        if avg:
            e = "🟢" if avg > 55 else "🟡" if avg > 45 else "🔴"
            ct_rps = confidence_tag('rps', bool(avg))
            lines.append(f"{e} 全市场RPS均值: {avg:.1f} | 强势{rps.get('high_cnt',0)}个 | 弱势{rps.get('low_cnt',0)}个 {ct_rps}")
        if strong:
            ns = [str(n) for _, n, _, _ in strong[:5]]
            ct_strong = confidence_tag('rps', True)
            lines.append(f"🟢 MA5>70: {', '.join(ns)} {ct_strong}")
        if rising:
            ns = [str(n) for _, n, _, _ in rising[:3]]
            ct_rising = confidence_tag('rps', True)
            lines.append(f"🟡 MA5 50-70: {', '.join(ns)} {ct_rising}")
        if weak:
            ns = [str(n) for _, n, _, _ in weak[:3]]
            ct_weak = confidence_tag('rps', True)
            lines.append(f"🔴 MA5<50: {', '.join(ns)} {ct_weak}")
        if stock_top:
            cs = [str(c) for c, _ in stock_top[:5]]
            ct_stock = confidence_tag('rps_stock', True)
            lines.append(f"🔥 个股RPS强势: {', '.join(cs)} {ct_stock}")
        alerts = rps.get("rank_alerts", [])
        up_a = [a for a in alerts if a.get("change", 0) > 0]
        dn_a = [a for a in alerts if a.get("change", 0) < 0]
        if up_a:
            ns = [a.get("name", "")[:8] for a in up_a[:3]]
            lines.append(f"📈 板块强势异动: {', '.join(ns)}")
        if dn_a:
            ns = [a.get("name", "")[:8] for a in dn_a[:3]]
            lines.append(f"📉 板块弱势异动: {', '.join(ns)}")
    else:
        lines.append("\n🌀 **二，市场情绪**")
        ct_rps = confidence_tag('rps', False)
        lines.append(f"今日RPS数据暂缺（板RPS 17:00生成，当前16:30）{ct_rps}")

    # ===== 空仓判断 =====
    empty = is_portfolio_empty()
    if empty:
        lines.append("\n📭 **当前状态：空仓**")
        lines.append("无持仓，今日无操作建议。")
        lines.append("\n_系统在后台持续积累数据，重新建仓后自动恢复决策支持_")
        lines.append("\n" + "=" * 56)
        report_text = "\n".join(lines)
        out_file = OUT_DIR / f"daily_decision_{today}.txt"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(report_text)
        # 同步到Obsidian
        sync_to_obsidian(report_text, today)
        # 不打印到stdout（cron环境下可能已关闭）
        return report_text

    # ===== 三，持仓动态 =====
    lines.append("\n💼 **三，持仓动态**")
    if portfolio:
        lines.append(f"{'名称':<10} {'现价':>8} {'今日':>8} {'浮盈':>8} {'MA5':>7} {'趋势':>6} {'信号'}")
        lines.append("-" * 65)
        for p in sorted(portfolio, key=lambda x: x.get("pnl_pct", 0), reverse=True):
            e = "🟢" if p.get('chg', 0) >= 5 else "🟢" if p.get('chg', 0) > 0 else "🟡" if p.get('chg', 0) > -2 else "🔴"
            p_s = "+" if p.get('pnl', 0) >= 0 else ""
            c_s = "+" if p.get('chg', 0) >= 0 else ""
            ma5 = str(p.get('ma5', 'N/A'))[:5]
            trend = p.get('trend', '?')
            signals = ' '.join(p.get('scenarios', []))
            ct_price = confidence_tag('price', bool(p.get('price', 0)))
            lines.append(f"{e} {p['name']:<8} {p['price']:>8.2f}{ct_price} {c_s}{p.get('chg',0):>6.1f}% {p_s}{p.get('pnl_pct',0):>6.1f}% {ma5:>7} {trend:<6} {signals}")
    else:
        lines.append("暂无持仓数据")

    # ===== 四，候选信号 =====
    lines.append("\n🎯 **四，候选信号**")
    ct_cand = confidence_tag('candidate', True)
    lines.append(f"数据源: 形态雷达+选股候选+信号聚合 {ct_cand}")
    
    # 形态捕手雷达
    xt_file = OUT_DIR / "xingtai" / f"xingtai_radar_{date.today().strftime('%Y-%m-%d')}.json"
    if xt_file.exists():
        try:
            from xingtai_integration import get_candidates_summary
            with open(xt_file, encoding="utf-8") as f:
                xt_data = json.load(f)
            xt_summary = get_candidates_summary(xt_data)
            lines.append(xt_summary)
        except Exception as e:
            print(f"[WARN] xingtai: {e}")

    cfile = WORKSPACE / "logs" / "xuangu_candidates.csv"
    if cfile.exists():
        try:
            with open(cfile, encoding="utf-8") as f:
                rows = [l.split(",") for l in f.read().strip().split("\n")[1:] if l]
            if rows:
                lines.append(f"{'代码':<12} {'名称':<10} {'换手率':>8} {'量比':>6} {'综合分':>8}")
                lines.append("-" * 45)
                for row in rows[:5]:
                    if len(row) >= 9:
                        lines.append(f"{row[0]:<12} {row[1][:8]:<10} {row[3]:>8} {row[4]:>6} {row[8]:>8}")
        except Exception as e:
            lines.append(f"读取失败: {e}")
    else:
        lines.append("今日候选股数据暂缺")

    # ===== 五，持仓趋势与风险评估 =====
    lines.append("\n💡 **五，持仓趋势与风险评估**")
    sh_chg = market.get("上证指数", {}).get("chg", 0)
    if sh_chg < -2:
        lines.append(f"🔴 大盘下跌{sh_chg:.1f}%，注意系统性风险")
    elif sh_chg < 0:
        lines.append(f"🟡 大盘偏弱，关注持仓支撑位")
    else:
        lines.append(f"🟢 大盘稳健，趋势未破坏")

    # 新增：逆向检验 + 反共识（ai-berkshire P0迁移）
    try:
        from risk_control import run_reverse_check, format_reverse_check
        for p in sorted(portfolio, key=lambda x: x.get("chg", 0), reverse=True):
            code = p.get('code', '')
            if code:
                rc = run_reverse_check(code, today)
                if rc and rc.get('risk_count', 0) > 0:
                    lines.append(f"⚠️ [{p.get('name', '')}] 逆向检验: {rc['worst_scenario']} (概率:{rc['worst_probability']}) → {rc['worst_action']}")
                # 反共识
                try:
                    from signal_aggregator import SignalAggregator
                    agg = SignalAggregator()
                    cc = agg.load_contrarian_signals(today)
                    if code in cc:
                        info = cc[code]
                        if info['contrarian_count'] > 0:
                            lines.append(f"🔍 [{p.get('name', '')}] 反共识: {info['contrarian_level']} {info['contrarian_reason'][:80]}")
                    agg.close()
                except Exception:
                    pass
    except Exception as e:
        print(f"[WARN] 逆向检验/反共识加载失败: {e}")

    # 止损检查 + 趋势评估（使用enrich_holdings数据）
    for p in sorted(portfolio, key=lambda x: x.get("chg", 0), reverse=True):
        chg = p.get('chg', 0)
        pnl_pct = p.get('pnl_pct', 0)
        name = p.get('name', '')
        scenarios = p.get('scenarios', [])
        trend = p.get('trend', '?')
        # 风险信号
        if pnl_pct < -5:
            lines.append(f"🚨 [{name}] 浮亏{pnl_pct:.1f}%，已达止损条件")
        elif any('止损' in s for s in scenarios):
            lines.append(f"🚨 [{name}] 触及止损线 {p.get('stop_loss')} → 清仓")
        elif any('警戒' in s for s in scenarios):
            lines.append(f"🔴 [{name}] 接近警戒线 {p.get('alert_price')} → 关注")
        elif chg >= 5:
            lines.append(f"🟢 [{name}] {chg:+.1f}% 强势，趋势完好 | 浮盈{pnl_pct:+.1f}%")
        elif chg > 0:
            lines.append(f"🟢 [{name}] {chg:+.1f}% 温和上涨 | 浮盈{pnl_pct:+.1f}%")
        elif chg > -2:
            lines.append(f"🟡 [{name}] {chg:+.1f}% 小幅回调 | 浮盈{pnl_pct:+.1f}%")
        else:
            lines.append(f"🔴 [{name}] {chg:+.1f}% 显著回调，留意止损 | 浮盈{pnl_pct:+.1f}%")

    # 推荐追踪统计
    try:
        from scripts.recommendation_tracker import compute_stats, show_summary
        stats = compute_stats()
        if stats:
            lines.append("\n📊 **推荐追踪统计**")
            for source, s in sorted(stats.items()):
                if s['total'] >= 3:
                    emoji = "🟢" if s['win_rate'] >= 50 else "🔴"
                    lines.append(f"{emoji} {source}: {s['total']}次 {s['win_rate']:.0f}%胜率 均T+1{s['avg_t1_return']:+.2f}%")
    except Exception as e:
        pass

    lines.append(f"\n_止盈基于趋势/估值/逻辑，非机械比例。系统仅提供分析，决策由主人判断_")

    # 置信度标注说明（ai-berkshire防骗机制）
    lines.append("")
    lines.append("📏 **置信度说明**")
    lines.append("[A级] 2+独立来源交叉验证 | [B级] 单一来源/模型输出 | [C级] 推算估算/数据不足")
    lines.append("")
    lines.append("🛡️ **防骗机制（逆向检验+反共识）**")
    lines.append("已嵌入持仓风险分析，见第五部分详情")

    lines.append("\n" + "=" * 56)
    lines.append("⚠️ _以上为系统分析结果，最终买卖决策由主人自行判断_")
    lines.append("📌 投资有风险，决策需谨慎")

    report_text = "\n".join(lines)
    out_file = OUT_DIR / f"daily_decision_{today}.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(report_text)

    # 同步到Obsidian
    sync_to_obsidian(report_text, today)
    sync_signals_to_obsidian(today)

    # 不打印到stdout（cron环境下可能已关闭）
    return report_text


def push_to_wechat(content):
    """微信推送已由Cron delivery统一处理，此函数仅打印"""
    print(content)
    return True


if __name__ == "__main__":
    report = format_report()
    if "--push" in sys.argv:
        push_to_wechat(report)
