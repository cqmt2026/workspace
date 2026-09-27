"""
8层风控系统
"""
import sqlite3
from datetime import datetime, timedelta

DB = r'F:\market_data.db'

class RiskControl:
    def __init__(self):
        self.con = sqlite3.connect(DB)
        self.risks = []  # 记录触发的风险
        self.reverse_check = None  # 芒格式逆向检验结果
    
    def close(self):
        self.con.close()
    
    def check_all(self, code, date):
        """执行所有风控检查"""
        self.risks = []
        self.reverse_check = None
        
        # 加载股票历史数据
        end_date = date
        start_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=90)).strftime('%Y-%m-%d')
        
        q = f"""
        SELECT date, close, high, volume
        FROM daily_k
        WHERE code = '{code}' AND date <= '{date}' AND date >= '{start_date}'
        ORDER BY date
        """
        df = self.con.execute(q).fetchall()
        
        if len(df) < 5:
            self.risks.append(("数据不足", 100))
            return False
        
        # 转换为列表方便处理
        dates = [row[0] for row in df]
        closes = [row[1] for row in df]
        highs = [row[2] for row in df]
        volumes = [row[3] for row in df]
        
        # 第1层：ST/北交所排除（已在选股时排除）
        # 第2层：连续涨停排除
        if self._check_consecutive_limit_up(closes, highs):
            return False
        
        # 第3层：大盘环境判断（需要和市场指数对比）
        # 第4层：仓位控制（需要持仓数据）
        # 第5层：止损线检查
        if self._check_stop_loss(closes):
            return False
        
        # 第6层：盈利保护检查
        if self._check_profit_protection(closes):
            return False
        
        # 第7层：集中度风控（需要持仓数据）
        # 第8层：手动复核（返回待确认）
        
        # 第9层：芒格式逆向检验（新增）
        self._munger_reverse_check(code, date, closes, volumes)
        
        return True
    
    def _munger_reverse_check(self, code, date, closes, volumes):
        """第9层：芒格式逆向检验
        
        强制思考失败场景："什么情况下这家公司/这只股票会死"
        列出具体情景和概率，而不是泛泛地说"存在风险"。
        """
        checks = []
        
        # 1. 量能枯竭：连续缩量（成交量连续3天低于20日均量）
        if len(volumes) >= 23:
            vol_20ma = sum(volumes[-23:-3]) / 20 if len(volumes) >= 23 else sum(volumes) / len(volumes)
            recent_vols = volumes[-3:]
            if all(v > 0 and v < vol_20ma * 0.5 for v in recent_vols):
                checks.append({
                    'scenario': '量能枯竭（连续3日缩量至20日均量50%以下）',
                    'probability': '高' if vol_20ma > 0 else '未知',
                    'impact': '流动性枯竭，难以及时止损',
                    'action': '减少仓位，增加观察频次',
                })
        
        # 2. 趋势反转：收盘价连续3日低于MA20
        if len(closes) >= 23:
            ma20 = sum(closes[-23:-3]) / 20
            if all(c < ma20 for c in closes[-3:]):
                checks.append({
                    'scenario': '趋势反转（连续3日收盘价低于MA20）',
                    'probability': '中-高',
                    'impact': '中期趋势走坏，可能进入下跌通道',
                    'action': '严格止损，不加仓',
                })
        
        # 3. 高位放量滞涨：价格高位，成交量放大但涨幅有限
        if len(closes) >= 5 and len(volumes) >= 5:
            recent_closes = closes[-5:]
            recent_vols = volumes[-5:]
            price_range = max(recent_closes) - min(recent_closes)
            avg_price = sum(recent_closes) / 5
            if avg_price > 0 and price_range / avg_price < 0.03:  # 窄幅震荡
                avg_vol = sum(recent_vols) / 5
                if avg_vol > 0 and recent_vols[-1] > avg_vol * 1.5:  # 放量
                    checks.append({
                        'scenario': '高位放量滞涨（窄幅震荡+量能放大）',
                        'probability': '中',
                        'impact': '主力出货迹象，可能见顶',
                        'action': '减仓观察，不追高',
                    })
        
        # 4. 加速下跌：连续跌幅加大
        if len(closes) >= 5:
            chgs = [(closes[i] - closes[i-1]) / closes[i-1] * 100 for i in range(-4, 0) if closes[i-1] > 0]
            if len(chgs) >= 3 and all(c < 0 for c in chgs):
                if len(chgs) >= 3 and chgs[-1] < chgs[-2] < chgs[-3]:  # 跌幅扩大
                    checks.append({
                        'scenario': '加速下跌（连续跌幅扩大）',
                        'probability': '高',
                        'impact': '恐慌性抛售，短期难以止跌',
                        'action': '立即止损，不抄底',
                    })
        
        # 5. 估值泡沫检查（从基本面角度）
        # 简单检查：过去90天涨幅超过100%
        if len(closes) >= 60 and closes[0] > 0:
            total_chg = (closes[-1] - closes[0]) / closes[0] * 100
            if total_chg > 100:
                checks.append({
                    'scenario': '估值泡沫（90日涨幅超100%）',
                    'probability': '中',
                    'impact': '获利盘巨大，回调风险高',
                    'action': '逐步止盈，不宜追高',
                })
        
        # 6. 综合结论
        if checks:
            worst = max(checks, key=lambda x: {'高': 3, '中-高': 2.5, '中': 2, '低': 1}.get(x['probability'], 0))
            self.reverse_check = {
                'passed': len(checks) == 0,
                'risk_count': len(checks),
                'worst_scenario': worst['scenario'],
                'worst_probability': worst['probability'],
                'worst_action': worst['action'],
                'details': checks,
            }
            self.risks.append((f"逆向检验: {worst['scenario']} (概率:{worst['probability']})", 80))
        else:
            self.reverse_check = {
                'passed': True,
                'risk_count': 0,
                'worst_scenario': '无显著失败情景',
                'worst_probability': '低',
                'worst_action': '维持现有策略',
                'details': [],
            }
    
    def _check_consecutive_limit_up(self, closes, highs):
        """第2层：连续涨停检查"""
        # 近3日内有涨停
        limit_up_count = 0
        for i in range(-3, 0):
            if i >= -len(closes):
                prev_close = closes[i-1] if i > 0 else closes[i]
                if prev_close > 0:
                    change = (highs[i] - prev_close) / prev_close * 100
                    if change >= 9.5:  # 涨停
                        limit_up_count += 1
        
        if limit_up_count >= 2:
            self.risks.append(("连续涨停", 80))
            return True
        return False
    
    def _check_stop_loss(self, closes):
        """第5层：止损线检查（-5%）"""
        if len(closes) < 2:
            return False
        
        # 从最高点回落超过5%
        max_close = max(closes[:-1])  # 不含今日
        today_close = closes[-1]
        
        if max_close > 0:
            drop = (today_close - max_close) / max_close * 100
            if drop <= -5:
                self.risks.append(("触及止损线", 90))
                return True
        return False
    
    def _check_profit_protection(self, closes):
        """第6层：盈利保护检查（+8%强制止盈）"""
        if len(closes) < 2:
            return False
        
        # 从最低点上涨超过8%
        min_close = min(closes[:-5] if len(closes) > 5 else closes[:-1])  # 5日前最低点
        today_close = closes[-1]
        
        if min_close > 0:
            rise = (today_close - min_close) / min_close * 100
            if rise >= 8:
                self.risks.append(("触及止盈线", 85))
                return True
        return False
    
    def filter_stocks(self, codes, date):
        """批量过滤股票，返回通过的股票"""
        passed = []
        for code in codes:
            if self.check_all(code, date):
                passed.append(code)
        return passed
    
    def get_risks(self):
        """获取触发的风险"""
        return self.risks


def run_risk_check(codes, date):
    """运行风控检查"""
    rc = RiskControl()
    passed = rc.filter_stocks(codes, date)
    risks = rc.get_risks()
    rc.close()
    return passed, risks


def run_reverse_check(code, date):
    """单独运行逆向检验（芒格式）
    
    独立执行，不走全风控链，确保逆向检验始终能被触发。
    
    返回: dict with passed/worst_scenario/probability/details
    """
    rc = RiskControl()
    
    # 直接从DB加载历史数据（不走check_all的提前返回逻辑）
    start_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=90)).strftime('%Y-%m-%d')
    q = f"""
    SELECT date, close, high, volume
    FROM daily_k
    WHERE code = '{code}' AND date <= '{date}' AND date >= '{start_date}'
    ORDER BY date
    """
    df = rc.con.execute(q).fetchall()
    
    if len(df) < 5:
        rc.close()
        return {'passed': True, 'risk_count': 0, 'worst_scenario': '数据不足', 'worst_probability': '未知', 'worst_action': '无', 'details': []}
    
    dates = [row[0] for row in df]
    closes = [row[1] for row in df]
    highs = [row[2] for row in df]
    volumes = [row[3] for row in df]
    
    # 直接调用逆向检验
    rc._munger_reverse_check(code, date, closes, volumes)
    result = rc.reverse_check
    rc.close()
    return result or {'passed': True, 'risk_count': 0, 'worst_scenario': '无显著风险', 'worst_probability': '低', 'worst_action': '维持现有策略', 'details': []}


class DynamicStopLoss:
    """动态止盈止损

    核心规则：
    - 静态止损：买入价的5%，永远有效作为兜底
    - 动态止损：浮盈每增加5%，止损线上移2%（只上移不下移）
    - 止盈触发：加速上涨或高位放量滞涨时触发部分/全部减仓

    用法：
        dsl = DynamicStopLoss(buy_price=18.40, shares=1000, current_price=20.19)
        result = dsl.evaluate()
        print(result['action'])  # '持有' / '减仓1/3' / '减仓1/2' / '清仓'
    """

    def __init__(self, buy_price: float, shares: int, current_price: float,
                 name: str = '', code: str = '',
                 volume: float = 0, avg_volume: float = 0):
        self.buy_price = buy_price
        self.shares = shares
        self.current_price = current_price
        self.name = name
        self.code = code
        self.volume = volume
        self.avg_volume = avg_volume

    def calc_dynamic_stop(self) -> dict:
        """计算动态止损线

        规则：
        - 浮盈0%：静态止损 = 买入价 * 0.95
        - 浮盈+5%：止损上移至买入价 * 0.96
        - 浮盈+10%：止损上移至买入价 * 0.97
        - 浮盈+15%：止损上移至买入价 * 0.98
        - 浮盈+20%+：止损上移至买入价 * 0.99
        """
        pnl_pct = (self.current_price - self.buy_price) / self.buy_price * 100
        static_stop = round(self.buy_price * 0.95, 2)

        # 动态上移：浮盈每+5%，止损上移买入价的2%
        shift = 0
        if pnl_pct >= 5:
            shift = 1  # 止损上移1%
        if pnl_pct >= 10:
            shift = 2
        if pnl_pct >= 15:
            shift = 3
        if pnl_pct >= 20:
            shift = 4
        if pnl_pct >= 30:
            shift = 5

        dynamic_stop = round(self.buy_price * (0.95 + shift * 0.01), 2)
        # 动态止损不得低于静态止损
        dynamic_stop = max(dynamic_stop, static_stop)
        # 动态止损不得高于当前价格
        dynamic_stop = min(dynamic_stop, self.current_price * 0.97)

        return {
            'pnl_pct': round(pnl_pct, 2),
            'static_stop': static_stop,
            'dynamic_stop': dynamic_stop,
            'shift_level': shift,
        }

    def check_take_profit(self) -> dict:
        """检查止盈信号

        触发条件：
        1. 单日涨幅 > 7% 且量比 > 2 → 加速上涨，减仓1/3
        2. 高位放量滞涨 → 减仓1/2
        3. 累计涨幅 > 30% → 至少减仓1/3
        4. 跌破动态止损 → 清仓
        """
        pnl_pct = (self.current_price - self.buy_price) / self.buy_price * 100
        signals = []

        # 条件1：加速上涨
        if self.avg_volume > 0 and self.volume > 0:
            vol_ratio = self.volume / self.avg_volume
        else:
            vol_ratio = 0

        if vol_ratio > 2 and pnl_pct > 7:
            signals.append({
                'signal': '加速上涨',
                'detail': f'量比{vol_ratio:.1f} 当日涨幅超阈值',
                'action': '减仓1/3',
            })

        # 条件2：高位放量滞涨
        if pnl_pct > 15 and vol_ratio > 1.5 and pnl_pct < 18:
            # 涨幅有限但放量
            signals.append({
                'signal': '高位放量滞涨',
                'detail': f'浮盈{pnl_pct:.1f}% 量比{vol_ratio:.1f}',
                'action': '减仓1/2',
            })

        # 条件3：累计涨幅过大
        if pnl_pct > 30:
            signals.append({
                'signal': '累计涨幅过大',
                'detail': f'浮盈{pnl_pct:.1f}% > 30%',
                'action': '减仓1/3',
            })

        # 条件4：盈利保护（浮盈>20%后回撤>5%）
        # 这个需要历史最高价，暂时放后面做

        return signals

    def evaluate(self) -> dict:
        """综合评估止盈止损"""
        stop_info = self.calc_dynamic_stop()
        tp_signals = self.check_take_profit()

        pnl_pct = stop_info['pnl_pct']
        dynamic_stop = stop_info['dynamic_stop']

        # 判定行动
        if self.current_price <= dynamic_stop:
            action = '清仓'
            reason = f'触发动态止损({dynamic_stop})'
        elif tp_signals:
            # 取最严重的止盈信号
            worst = tp_signals[0]
            action = worst['action']
            reason = worst['signal'] + ': ' + worst['detail']
        elif pnl_pct < -5:
            action = '清仓'
            reason = f'触发静态止损({stop_info["static_stop"]})'
        else:
            action = '持有'
            reason = f'动态止损{dynamic_stop} 浮盈{pnl_pct:.1f}%'

        return {
            'code': self.code,
            'name': self.name,
            'action': action,
            'reason': reason,
            'pnl_pct': pnl_pct,
            'buy_price': self.buy_price,
            'current_price': self.current_price,
            'static_stop': stop_info['static_stop'],
            'dynamic_stop': dynamic_stop,
            'take_profit_signals': tp_signals,
        }


def run_dynamic_stop_loss(holding: dict, current_price: float = None,
                           volume: float = 0, avg_volume: float = 0) -> dict:
    """对单只持仓运行动态止盈止损"""
    dsl = DynamicStopLoss(
        buy_price=holding['buy_price'],
        shares=holding.get('shares', 0),
        current_price=current_price or holding.get('current_price', holding['buy_price']),
        name=holding.get('name', ''),
        code=holding.get('code', ''),
        volume=volume,
        avg_volume=avg_volume,
    )
    return dsl.evaluate()


def run_all_dynamic_stops(holdings: list) -> list:
    """对所有持仓运行动态止盈止损"""
    results = []
    for h in holdings:
        result = run_dynamic_stop_loss(h)
        results.append(result)
    return results


def format_dynamic_stop(result: dict) -> str:
    """格式化输出"""
    lines = []
    action = result['action']
    action_emoji = {'持有': '🟢', '减仓1/3': '🟡', '减仓1/2': '🟠', '清仓': '🔴'}
    emoji = action_emoji.get(action, '⚪')

    lines.append(f'{emoji} **{result["name"]}({result["code"]})**')
    lines.append(f'  买入: {result["buy_price"]:.2f} | 现价: {result["current_price"]:.2f} | 浮盈: {result["pnl_pct"]:+.1f}%')
    lines.append(f'  静态止损: {result["static_stop"]:.2f} | 动态止损: {result["dynamic_stop"]:.2f}')
    lines.append(f'  行动: {action} → {result["reason"]}')

    if result.get('take_profit_signals'):
        for s in result['take_profit_signals']:
            lines.append(f'  📊 止盈信号: {s["signal"]}')

    return '\n'.join(lines)


def format_reverse_check(code: str, date: str) -> str:
    """格式化逆向检验结果为可读文本"""
    rc = run_reverse_check(code, date)
    if not rc:
        return f"📋 **芒格式逆向检验 - {code}**\n数据不足，无法分析\n"
    
    lines = [f"📋 **芒格式逆向检验 - {code}**"]
    lines.append(f"结论: {'✅ 无显著风险' if rc['passed'] else '⚠️ 触发风险'}")
    lines.append(f"最坏情景: {rc['worst_scenario']}")
    lines.append(f"概率: {rc['worst_probability']}")
    lines.append(f"建议: {rc['worst_action']}")
    
    if rc['details']:
        lines.append("")
        lines.append("详细失败情景:")
        for d in rc['details']:
            emoji = '🔴' if d['probability'] in ('高', '中-高') else '🟡' if d['probability'] == '中' else '🟢'
            lines.append(f"{emoji} {d['scenario']}")
            lines.append(f"   概率: {d['probability']} | 影响: {d['impact']}")
            lines.append(f"   建议: {d['action']}")
    
    lines.append("")
    return "\n".join(lines)


if __name__ == '__main__':
    import sys
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')
    
    # 测试
    test_codes = ['sh.600000', 'sz.000001', 'sh.600519']
    passed, risks = run_risk_check(test_codes, date)
    
    print(f"风控检查 ({date}):")
    print(f"通过: {passed}")
    print(f"风险: {risks}")
    
    # 逆向检验测试
    if len(sys.argv) > 2:
        code = sys.argv[2]
        print(f"\n逆向检验 {code}:")
        print(format_reverse_check(code, date))