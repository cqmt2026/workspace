"""资金流因子计算器

从 scripts/smart_money_factor.py 移植，简化并注册为框架标准因子。

因子列表：
  - flow_intensity: 5日资金强度
  - flow_persistence: 10日资金持续性
  - price_confirmation: 价量确认
  - impact_efficiency: 冲击效率
  - smart_money_score: 综合评分

数据源：
  - 优先：东财fflow/daykline API (HTTP)
  - 降级：DB K线数据估算

注意：资金流API在非交易时段只返回1天数据，需降级处理。
"""
import numpy as np
import pandas as pd
import requests
import sqlite3
from typing import Optional, Dict, Any

# 东财API配置
EM_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'http://finance.eastmoney.com/'
}
DB_PATH = r'F:\market_data.db'


class MoneyFlowFactors:
    """资金流因子计算器"""

    @staticmethod
    def get_eastmoney_secid(code: str) -> str:
        """统一code为东财secid格式"""
        c = code.replace('sh.', '').replace('sz.', '').replace('bj.', '')
        for prefix in ('sh', 'sz', 'bj'):
            if c.startswith(prefix) and len(c) > len(prefix) and c[len(prefix):len(prefix)+1].isdigit():
                c = c[len(prefix):]
                break
        return f'1.{c}' if c.startswith('6') or c.startswith('688') or c.startswith('689') else f'0.{c}'

    @staticmethod
    def _normalize_code(code: str) -> str:
        """统一code为sh.XXXXXX/sz.XXXXXX"""
        if '.' in code:
            return code
        if code.startswith('sh') or code.startswith('sz') or code.startswith('bj'):
            return code[:2] + '.' + code[2:]
        if code.startswith('6') or code.startswith('688') or code.startswith('689'):
            return 'sh.' + code
        return 'sz.' + code

    @staticmethod
    def fetch_flow_api(code: str, days: int = 15) -> list:
        """从东财API获取资金流数据"""
        secid = MoneyFlowFactors.get_eastmoney_secid(code)
        urls = [
            f'http://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get?secid={secid}&fields1=f1,f2,f3,f7,f8,f9&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60&lmt={days}',
            f'http://push2.eastmoney.com/api/qt/stock/fflow/daykline/get?secid={secid}&fields1=f1,f2,f3,f7,f8,f9&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60&lmt={days}',
        ]
        try:
            raw_klines = []
            for url in urls:
                try:
                    resp = requests.get(url, headers=EM_HEADERS, timeout=8)
                    data = resp.json()
                    if data.get('data') and data['data'].get('klines'):
                        klines = data['data']['klines']
                        if len(klines) > len(raw_klines):
                            raw_klines = klines
                except Exception:
                    continue
            if not raw_klines:
                return []
            results = []
            for k in raw_klines:
                parts = k.split(',')
                dt = parts[0]
                main_net = float(parts[1]) if parts[1] else 0
                big_net = float(parts[4]) if len(parts) > 4 and parts[4] else 0
                super_big_net = float(parts[5]) if len(parts) > 5 and parts[5] else 0
                active = big_net + super_big_net
                main_pct = float(parts[6]) if len(parts) > 6 and parts[6] else 0
                amount = abs(main_net / main_pct * 100) if main_pct != 0 else 0
                results.append({
                    'date': dt, 'active_buy_sell': active,
                    'amount': amount, 'main_net': main_net,
                })
            return results
        except Exception:
            return []

    @staticmethod
    def get_db_klines(code: str, days: int = 30) -> list:
        """从本地DB获取日K线（降级用）"""
        db_code = MoneyFlowFactors._normalize_code(code)
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.execute("""
                SELECT date, close, volume FROM daily_k
                WHERE code = ? ORDER BY date DESC LIMIT ?
            """, (db_code, days))
            rows = cur.fetchall()
            conn.close()
            results = [{'date': r[0], 'close': r[1], 'volume': r[2]} for r in reversed(rows)]
            return results
        except Exception:
            return []

    @staticmethod
    def estimate_flow_from_klines(klines: list, api_flows: list) -> list:
        """用K线数据估算缺失日期的资金流（降级）"""
        api_dates = {f['date'] for f in api_flows}
        merged = list(api_flows)
        for i, k in enumerate(klines):
            if k['date'] not in api_dates:
                est_amount = k['volume'] * 100
                est_active = 0
                if i > 0:
                    prev = klines[i - 1]
                    chg = (k['close'] - prev['close']) / prev['close'] if prev['close'] > 0 else 0
                    vol_ratio = k['volume'] / max(prev['volume'], 1) if prev['volume'] > 0 else 1
                    if chg > 0.005:
                        est_active = est_amount * (0.05 + 0.10 * min(vol_ratio - 1, 3) / 3)
                    elif chg < -0.005:
                        est_active = -est_amount * (0.05 + 0.10 * min(vol_ratio - 1, 3) / 3)
                    else:
                        est_active = est_amount * 0.02 * (1 if chg > 0 else -1)
                merged.append({
                    'date': k['date'], 'active_buy_sell': est_active,
                    'amount': est_amount, 'main_net': 0, '_estimated': True,
                })
        merged.sort(key=lambda x: x['date'])
        return merged[-15:]

    @staticmethod
    def flow_intensity(code: str, df: pd.DataFrame = None) -> float:
        """5日资金强度

        公式: sum(5日主动买卖净额) / sum(5日成交额)
        范围: [-1, 1]，正值=净流入
        """
        flows = MoneyFlowFactors.fetch_flow_api(code, 15)
        if not flows:
            klines = MoneyFlowFactors.get_db_klines(code, 20)
            if len(klines) < 5:
                return 0.0
            flows = MoneyFlowFactors.estimate_flow_from_klines(klines, [])

        recent = flows[-5:]
        total_active = sum(f['active_buy_sell'] for f in recent)
        total_amount = sum(f['amount'] for f in recent)
        if total_amount <= 0:
            return 0.0
        return max(-1.0, min(1.0, total_active / total_amount))

    @staticmethod
    def flow_persistence(code: str, df: pd.DataFrame = None) -> float:
        """10日资金持续性

        公式: 10日内净主动买入天数 / 10
        范围: [0, 1]
        """
        flows = MoneyFlowFactors.fetch_flow_api(code, 15)
        if not flows:
            klines = MoneyFlowFactors.get_db_klines(code, 20)
            if len(klines) < 10:
                return 0.0
            flows = MoneyFlowFactors.estimate_flow_from_klines(klines, [])

        recent = flows[-10:]
        if len(recent) < 5:
            return 0.0
        pos_days = sum(1 for f in recent if f['active_buy_sell'] > 0)
        return pos_days / len(recent)

    @staticmethod
    def price_confirmation(code: str, df: pd.DataFrame = None) -> float:
        """价量确认

        公式: 资金方向与价格方向一致的天数占比
        范围: [0, 1]，1=完全一致
        """
        flows = MoneyFlowFactors.fetch_flow_api(code, 15)
        klines = MoneyFlowFactors.get_db_klines(code, 30)

        if not flows or not klines:
            return 0.5

        # 合并
        if len(flows) < 5:
            flows = MoneyFlowFactors.estimate_flow_from_klines(klines, flows)

        kline_by_date = {k['date']: k for k in klines}
        score = 0
        count = 0

        for f in flows[-10:]:
            k = kline_by_date.get(f['date'])
            if not k:
                continue
            # 找前一个交易日
            prev_close = None
            for k2 in reversed(klines):
                if k2['date'] < f['date']:
                    prev_close = k2['close']
                    break
            if prev_close is None:
                continue

            ret = (k['close'] - prev_close) / prev_close
            flow_dir = 1 if f['active_buy_sell'] > 0 else (-1 if f['active_buy_sell'] < 0 else 0)
            price_dir = 1 if ret > 0.005 else (-1 if ret < -0.005 else 0)

            if flow_dir == price_dir and flow_dir != 0:
                score += 1
            elif flow_dir == 1 and price_dir <= 0:
                score -= 1
            elif flow_dir == -1 and price_dir == 1:
                score -= 0.5
            count += 1

        if count == 0:
            return 0.5
        max_possible = count * 2
        min_possible = -count
        if max_possible <= min_possible:
            return 0.5
        return max(0.0, min(1.0, (score - min_possible) / (max_possible - min_possible)))

    @staticmethod
    def impact_efficiency(code: str, df: pd.DataFrame = None) -> float:
        """冲击效率

        公式: 5日收益率 / |5日资金强度|
        范围: [-2, 2]，正值=资金推动有效
        """
        flows = MoneyFlowFactors.fetch_flow_api(code, 15)
        klines = MoneyFlowFactors.get_db_klines(code, 15)

        if len(klines) < 6:
            return 0.0

        ret_5d = (klines[-1]['close'] - klines[-6]['close']) / klines[-6]['close'] if klines[-6]['close'] > 0 else 0

        if not flows or len(flows) < 5:
            return 0.0

        recent = flows[-5:]
        total_active = sum(f['active_buy_sell'] for f in recent)
        total_amount = sum(f['amount'] for f in recent)
        intensity = total_active / total_amount if total_amount > 0 else 0

        if abs(intensity) < 0.0001:
            return 0.0
        ie = ret_5d / abs(intensity)
        return max(-2.0, min(2.0, ie))

    @staticmethod
    def smart_money_score(code: str, df: pd.DataFrame = None) -> float:
        """SmartMoney综合评分

        组合: 方向分 * 持续性 * 价格确认 * 冲击效率
        范围: [0, 100]
        """
        intensity = MoneyFlowFactors.flow_intensity(code, df)
        persistence = MoneyFlowFactors.flow_persistence(code, df)
        confirmation = MoneyFlowFactors.price_confirmation(code, df)
        ie = MoneyFlowFactors.impact_efficiency(code, df)

        direction_score = min(1.0, abs(intensity) * 20)
        impact_norm = max(0.0, min(1.0, (ie + 2) / 4))

        raw = direction_score * persistence * confirmation * impact_norm * 100
        return max(0.0, min(100.0, raw))