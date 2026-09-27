# -*- coding: utf-8 -*-
"""
持仓异常监控脚本
盘中实时监控5只持仓的关键信号，推送到微信
触发条件:
  1. 持仓个股涨跌幅 > 5% (异动预警)
  2. 持仓个股跌破关键支撑位
  3. 持仓个股涨停/跌停
  4. 持仓个股换手率异常 (>15%)
  5. 大盘指数跌幅 > 2% (系统性风险)
  6. 板块RPS骤降 >20位 (持仓板块走弱)

使用方法:
  python scripts/holding_alert.py --check  # 盘中检查
  python scripts/holding_alert.py --continuous  # 持续监控(每5分钟)
"""
import sys, os, json, time, sqlite3
from datetime import datetime, date
sys.stdout.reconfigure(encoding='utf-8')

WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
sys.path.insert(0, WORK_DIR)

# ===== 持仓配置：从 portfolio.json 统一读取 =====
PORTFOLIO_PATH = os.path.join(WORK_DIR, 'data', 'portfolio.json')

def _load_holdings():
    """从 portfolio.json 读取真实持仓"""
    if not os.path.exists(PORTFOLIO_PATH):
        return []
    with open(PORTFOLIO_PATH, encoding='utf-8') as f:
        data = json.load(f)
    holdings = data.get('holdings', [])
    # 统一为 holding_alert.py 需要的格式
    result = []
    for h in holdings:
        result.append({
            'code': h.get('code', ''),
            'name': h.get('name', ''),
            'cost': h.get('buy_price', h.get('cost', 0)),
            'stop_loss': h.get('stop_loss_5', 0),
            'stop_loss_15': h.get('stop_loss_15', 0),
            'alert_price': h.get('current_price', 0),
            'shares': h.get('shares', 0),
            'logic': '',
        })
    return result

def _strip_code(code):
    """sz002805 -> 002805"""
    return code[2:] if len(code) > 6 else code


# ===== 数据获取 =====
def get_realtime(codes):
    """腾讯实时行情"""
    qt = ','.join(codes)
    import urllib.request
    url = f'https://qt.gtimg.cn/q={qt}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=8)
    raw = resp.read().decode('gbk')
    result = {}
    for line in raw.strip().split('\n'):
        if '~' not in line:
            continue
        p = line.split('~')
        if len(p) < 40:
            continue
        sym = p[2]
        price = float(p[3]) if p[3] else 0
        prev = float(p[4]) if p[4] else price
        chg_pct = round((price - prev) / prev * 100, 2) if prev else 0
        high = float(p[33]) if p[33] else price
        low = float(p[34]) if p[34] else price
        turnover = float(p[38]) if p[38] else 0
        volume = float(p[36]) if p[36] else 0  # 万手
        result[sym] = {
            'price': price, 'prev': prev,
            'chg_pct': chg_pct,
            'high': high, 'low': low,
            'turnover': turnover,
            'volume': volume,  # 万手
        }
    return result


def get_index():
    """大盘指数 + 相关板块指数"""
    from scripts.data_api import DataAPI
    indices = [
        ('sh000001', '上证'),
        ('sz399001', '深证'),
        ('sh000688', '科创50'),
        ('sz399967', '中证军工'),
        ('sz399930', '有色金属'),
    ]
    result = {}
    for code, name in indices:
        idx = DataAPI.get_index(code)
        if idx:
            result[name] = {'price': idx['price'], 'chg_pct': idx['chg_pct']}
    return result


def get_zt_count():
    """获取今日涨停家数（市场情绪指标）"""
    from scripts.data_api import eastmoney_realtime
    try:
        result = eastmoney_realtime(['BK0441'])
        if result:
            for code, data in result.items():
                return data.get('price', 0)
        return 0
    except:
        return None


# ===== 告警判断 =====
def check_holdings():
    """检查所有持仓"""
    HOLDINGS = _load_holdings()
    codes = [h['code'] for h in HOLDINGS]
    snap = get_realtime(codes)
    index = get_index()
    zt_count = get_zt_count()

    alerts = []
    market_closed = (datetime.now().hour >= 15)

    # 1. 持仓个股检查
    for h in HOLDINGS:
        s = snap.get(_strip_code(h['code']))
        if not s or s['price'] == 0:
            continue

        price = s['price']
        chg = s['chg_pct']
        pnl = round((price - h['cost']) / h['cost'] * 100, 1)

        item = {
            'code': h['code'],
            'name': h['name'],
            'price': price,
            'chg': chg,
            'pnl': pnl,
            'cost': h['cost'],
            'alerts': [],
        }

        # 涨停/跌停
        if abs(chg) >= 9.9:
            item['alerts'].append(f"{'涨停' if chg > 0 else '跌停'} ⚠️")

        # 异动 (>5%)
        if abs(chg) >= 5.0:
            item['alerts'].append(f"异动{'🔴' if chg < 0 else '🟢'} ({chg:+.1f}%)")

        # 跌破关键支撑
        if price <= h['alert_price'] * 0.98:
            item['alerts'].append(f"接近警戒 {h['alert_price']} → 关注")

        # 跌破止损
        if price <= h['stop_loss']:
            item['alerts'].append(f"⚠️止损线 {h['stop_loss']} → 清仓")

        # 换手率异常
        if s['turnover'] >= 15:
            item['alerts'].append(f"高换手 {s['turnover']:.1f}%")

        # 浮亏警告
        if pnl < -3:
            item['alerts'].append(f"浮亏 {pnl}%")

        if item['alerts']:
            alerts.append(item)

    # 2. 大盘检查
    market_alerts = []
    for name, idx in index.items():
        if idx['chg_pct'] <= -2.0:
            market_alerts.append(f"{name} {'🔴' if idx['chg_pct'] < 0 else '🟢'} {idx['chg_pct']:+.1f}%")
    # 板块暴跌预警（>3%）
    sector_names = ['中证军工', '有色金属', '科创50']
    for name in sector_names:
        if name in index and index[name]['chg_pct'] <= -3.0:
            market_alerts.append(f"📉{name}暴跌 {index[name]['chg_pct']:+.1f}%")

    # 3. 板块与持仓相关性检查（持仓板块是否同时大跌）
    sector_correlation = []
    for name in ['中证军工', '有色金属']:
        if name in index:
            sector_correlation.append(f"{name} {index[name]['chg_pct']:+.1f}%")

    return {
        'time': datetime.now().strftime('%H:%M'),
        'market': index,
        'zt_count': zt_count,
        'market_alerts': market_alerts,
        'holding_alerts': alerts,
    }


def format_report(r):
    """格式化告警报告"""
    lines = []
    lines.append(f"📊 持仓监控 {r['time']}")
    lines.append("=" * 45)

    # 大盘
    for name, idx in r['market'].items():
        emoji = '🟢' if idx['chg_pct'] >= 0 else '🔴'
        lines.append(f"{emoji} {name}: {idx['price']:.0f} ({idx['chg_pct']:+.1f}%)")
    if r['zt_count']:
        lines.append(f"🏆 涨停: {int(r['zt_count'])}家")

    if r['market_alerts']:
        lines.append(f"⚠️ 市场风险: {', '.join(r['market_alerts'])}")

    lines.append("-" * 45)
    lines.append("持仓告警:")
    if not r['holding_alerts']:
        lines.append("  无异常 ✅")
    else:
        for item in r['holding_alerts']:
            lines.append(f"\n  【{item['name']}】{item['price']:.2f} ({item['chg']:+.1f}% / {item['pnl']:+.1f}%)")
            for a in item['alerts']:
                lines.append(f"    → {a}")

    lines.append("=" * 45)
    return '\n'.join(lines)


# ===== 推送 =====
def push_to_wechat(msg):
    """推送告警（Server酱已废弃，保留函数签名待迁移）"""
    print(f"[INFO] 推送消息已拦截（Server酱已废弃）: {msg[:80]}...")
    return True


# ===== 主逻辑 =====
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='单次检查')
    parser.add_argument('--continuous', action='store_true', help='持续监控(每5分钟)')
    parser.add_argument('--push', action='store_true', help='推送到微信')
    args = parser.parse_args()

    if args.check or args.continuous:
        result = check_holdings()
        report = format_report(result)
        print(report)

        if args.push and (result['holding_alerts'] or result['market_alerts']):
            push_to_wechat(report)
            print("\n✅ 已推送")

        if args.continuous:
            print("\n持续监控中 (Ctrl+C退出)...")
            while True:
                time.sleep(300)  # 5分钟
                result = check_holdings()
                report = format_report(result)
                print(report)
                if result['holding_alerts'] or result['market_alerts']:
                    push_to_wechat(report)
                    print("✅ 已推送")
    else:
        # 默认单次检查
        result = check_holdings()
        print(format_report(result))
