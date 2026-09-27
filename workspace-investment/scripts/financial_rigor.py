# -*- coding: utf-8 -*-
"""
财务精度计算 (Financial Rigor)
==============================
ai-berkshire financial_rigor.py 的 AliceQuant 版本。

所有关键计算使用 Python decimal.Decimal（精确十进制），不用 float。
提供反向验算能力，防止金融计算中出现浮点数误差。

LLM心算不可靠——市值单位港币亿/人民币亿搞混、PE算错一个小数点，
都可能导致错误投资决策。0.1+0.2要等于0.3，在金融场景里不是玩笑。

用法：
  python financial_rigor.py
  from financial_rigor import verify_market_cap, calc_pe, D

  # 反向验算市值
  verify_market_cap(11.28, 930_000_000, 10_490_400_000)  # 高测股份

  # 精确计算PE
  calc_pe(11.28, 0.45)  # 股价/每股收益
"""
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Optional, Dict, List, Tuple


class D:
    """精确十进制工具类，替代float"""

    @staticmethod
    def to_decimal(value, places: int = 4) -> Decimal:
        """转为精确Decimal，支持字符串/数字"""
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, str):
            return Decimal(value.strip())
        raise TypeError(f"Cannot convert {type(value)} to Decimal")

    @staticmethod
    def quantize(value, places: int = 4) -> Decimal:
        """四舍五入到指定位数"""
        if places == 0:
            return value.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        fmt = '0.' + '0' * places
        return value.quantize(Decimal(fmt), rounding=ROUND_HALF_UP)


def safe_div(a, b, places: int = 6) -> Decimal:
    """安全除法，避免除零"""
    d_a = D.to_decimal(a)
    d_b = D.to_decimal(b)
    if d_b == 0:
        return Decimal('0')
    return D.quantize(d_a / d_b, places)


def verify_market_cap(
    price: float,
    shares_total: int,
    reported_cap: float,
    tolerance: float = 0.02,
    currency: str = 'CNY'
) -> Dict:
    """反向验算市值

    市值 = 股价 × 总股本
    如果偏差超过容差，告警——可能是单位搞混了。

    真实案例：分析腾讯时，市值单位在港币亿和人民币亿之间搞混。

    Args:
        price: 股价
        shares_total: 总股本
        reported_cap: 报告中的市值
        tolerance: 允许偏差（默认2%）
        currency: 币种（CNY/HKD/USD）

    Returns:
        {'passed': bool, 'calc_cap': Decimal, 'reported_cap': Decimal,
         'deviation': Decimal, 'deviation_pct': Decimal, 'warning': str or None}
    """
    d_price = D.to_decimal(price)
    d_shares = D.to_decimal(shares_total)
    d_reported = D.to_decimal(reported_cap)

    calc_cap = d_price * d_shares

    if d_reported == 0:
        return {
            'passed': False,
            'calc_cap': calc_cap,
            'reported_cap': d_reported,
            'deviation': Decimal('0'),
            'deviation_pct': Decimal('0'),
            'warning': '报告市值为0',
        }

    deviation = calc_cap - d_reported
    deviation_pct = safe_div(deviation, d_reported, 6)

    tolerance_d = D.to_decimal(tolerance)
    passed = abs(deviation_pct) <= tolerance_d

    warning = None
    if not passed:
        # 尝试币种转换
        if currency == 'CNY':
            # 假设可能是港币，汇率约0.9
            hk_cap = calc_cap * Decimal('0.9')
            hk_dev = safe_div(hk_cap - d_reported, d_reported, 6)
            if abs(hk_dev) <= tolerance_d:
                warning = f'可能单位混淆：报告市值疑似港币({calc_cap.quantize(Decimal("1")):.0f} vs 报告{d_reported:.0f})'
            else:
                warning = f'偏差{deviation_pct * 100:.2f}%，超出容差{tolerance*100:.0f}%'
        else:
            warning = f'偏差{deviation_pct * 100:.2f}%，超出容差{tolerance*100:.0f}%'

    return {
        'passed': passed,
        'calc_cap': calc_cap,
        'reported_cap': d_reported,
        'deviation': deviation,
        'deviation_pct': deviation_pct,
        'warning': warning,
    }


def calc_pe(price: float, eps: float) -> Dict:
    """精确计算PE"""
    d_price = D.to_decimal(price)
    d_eps = D.to_decimal(eps)

    if d_eps == 0:
        return {'pe': None, 'note': 'EPS为0，无法计算PE'}
    if d_eps < 0:
        return {'pe': None, 'note': f'EPS为负({d_eps})，PE无意义'}

    pe = D.quantize(d_price / d_eps, 4)
    return {
        'pe': float(pe),
        'note': f'PE = {d_price} / {d_eps} = {pe}',
    }


def calc_pb(price: float, bvps: float) -> Dict:
    """精确计算PB"""
    d_price = D.to_decimal(price)
    d_bvps = D.to_decimal(bvps)

    if d_bvps == 0:
        return {'pb': None, 'note': 'BPS为0，无法计算PB'}
    if d_bvps < 0:
        return {'pb': None, 'note': f'BPS为负({d_bvps})，PB无意义'}

    pb = D.quantize(d_price / d_bvps, 4)
    return {
        'pb': float(pb),
        'note': f'PB = {d_price} / {d_bvps} = {pb}',
    }


def calc_change(new_value: float, old_value: float) -> Dict:
    """精确计算涨跌幅"""
    d_new = D.to_decimal(new_value)
    d_old = D.to_decimal(old_value)

    if d_old == 0:
        return {'change_pct': None, 'note': '基准值为0'}

    change_pct = D.quantize(safe_div(d_new - d_old, d_old, 6) * 100, 4)
    return {
        'change_pct': float(change_pct),
        'note': f'{(d_new - d_old) / d_old * 100:.4f}%',
    }


def precise_calc(expr_parts: List[Tuple[str, float]]) -> Decimal:
    """
    精确表达式计算，替代LLM心算

    用法:
        precise_calc([('add', 0.1), ('add', 0.2)])  # = 0.3（精确）
    """
    result = Decimal('0')
    for op, val in expr_parts:
        d_val = D.to_decimal(val)
        if op == 'add':
            result += d_val
        elif op == 'sub':
            result -= d_val
        elif op == 'mul':
            result *= d_val
        elif op == 'div' and d_val != 0:
            result /= d_val
    return result


def is_equal_approx(a: float, b: float, tolerance: float = 0.01) -> bool:
    """精确比较两个数是否近似相等（避免浮点误差）"""
    d_a = D.to_decimal(a)
    d_b = D.to_decimal(b)
    d_tol = D.to_decimal(tolerance)
    return abs(d_a - d_b) <= d_tol


def precision_audit(
    price: float,
    shares: int,
    reported_market_cap: float,
    eps: float = None,
    bvps: float = None,
    currency: str = 'CNY'
) -> Dict:
    """
    综合财务精度审计

    一次跑完：市值验算 + PE + PB + 币种检查
    """
    result = {
        'inputs': {
            'price': price,
            'shares': shares,
            'reported_cap': reported_market_cap,
        },
        'market_cap_check': verify_market_cap(price, shares, reported_market_cap, currency=currency),
        'eps': eps,
        'bvps': bvps,
    }

    if eps:
        result['pe_check'] = calc_pe(price, eps)
    if bvps:
        result['pb_check'] = calc_pb(price, bvps)

    # 总体结论
    all_passed = result['market_cap_check']['passed']
    if not all_passed:
        result['overall'] = 'WARNING'
    else:
        result['overall'] = 'PASS'

    return result


def test_suite():
    """测试套件"""
    print("=" * 60)
    print("财务精度测试")
    print("=" * 60)

    # 1. 基础精度测试
    print("\n1. 基础精度: 0.1 + 0.2 == 0.3 ?")
    result = precise_calc([('add', 0.1), ('add', 0.2)])
    print(f"   Decimal结果: {result}")
    print(f"   Float结果:   {0.1 + 0.2}")
    print(f"   通过: {result == Decimal('0.3')}")

    # 2. 高测股份市值验算
    print("\n2. 高测股份市值验算:")
    # 股价11.28, 总股本约9.3亿
    cap_check = verify_market_cap(11.28, 930_000_000, 10_490_400_000)
    print(f"   计算市值: {cap_check['calc_cap']:.0f}")
    print(f"   报告市值: {cap_check['reported_cap']:.0f}")
    print(f"   偏差: {cap_check['deviation_pct'] * 100:.4f}%")
    print(f"   通过: {cap_check['passed']}")
    if cap_check['warning']:
        print(f"   警告: {cap_check['warning']}")

    # 3. PE计算
    print("\n3. PE计算测试:")
    pe = calc_pe(11.28, 0.45)
    print(f"   股价11.28 / EPS 0.45 = PE {pe['pe']}")
    pe2 = calc_pe(11.28, 0)
    print(f"   EPS为0: {pe2}")

    # 4. 涨跌幅计算
    print("\n4. 涨跌幅计算:")
    chg = calc_change(11.28, 11.98)
    print(f"   11.98 → 11.28: {chg['change_pct']}%")

    # 5. 综合审计
    print("\n5. 综合财务审计:")
    audit = precision_audit(
        price=11.28,
        shares=930_000_000,
        reported_market_cap=10_490_400_000,
        eps=0.45,
        bvps=5.2
    )
    print(f"   市值验算: {'通过' if audit['market_cap_check']['passed'] else '告警'}")
    print(f"   PE: {audit.get('pe_check', {}).get('pe', 'N/A')}")
    print(f"   PB: {audit.get('pb_check', {}).get('pb', 'N/A')}")
    print(f"   总体: {audit['overall']}")


if __name__ == '__main__':
    test_suite()
