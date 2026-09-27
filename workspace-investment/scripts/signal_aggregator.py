"""
信号聚合模块
===========
聚合各信号源，输出综合评分。

数据源:
1. factors.db → Pipeline v2评分 (技术+板块+基本面+资金流)
2. strategy_scan.py → 尾盘精选信号 (--mx模式)
3. xingtai雷达 → 形态信号 (6模板)
4. mx_search → 舆情信号

输出:
- 综合评分 (0~100)
- 各维度明细
- 买入/卖出建议
"""
import io
import os, sys, json, sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


# 安全打印：处理stdout被关闭的情况（cron/后台上下文）
def _safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        try:
            kwargs.pop('file', None)
            print(*args, file=sys.stderr, **kwargs)
        except (ValueError, OSError):
            pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTORS_DB = os.path.join(WORK_DIR, 'data', 'factors.db')
OUT_DIR = os.path.join(WORK_DIR, 'out_data')
os.makedirs(OUT_DIR, exist_ok=True)

# Pipeline v2 权重
PIPELINE_WEIGHTS = {
    'momentum': 0.30, 'volume': 0.20, 'pattern': 0.15,
    'fundamental': 0.15, 'sentiment': 0.10, 'safety': 0.10,
}


def calc_pipeline_score(f: Dict, market_regime: str = 'bull') -> Optional[float]:
    """Pipeline v2 评分（同回测引擎）

    涨幅过滤条件随市场状态调整：
    - bull/正常: pct_chg 1.5%~5.0%
    - bear/谨慎: pct_chg 0.5%~5.0%（放宽，弱市也有逆势股）
    - stop/规避: 不评分（空仓）
    """
    pct = f.get('pct_chg_1d')
    vr = f.get('vol_ratio')
    if pct is None or vr is None: return None
    if market_regime == 'stop' or market_regime == '规避':
        return None
    if market_regime == 'bear' or market_regime == '谨慎':
        if pct < 0.5 or pct > 5.0: return None
    else:
        if pct < 1.5 or pct > 5.0: return None
    if vr <= 0.5: return None

    # 动量 (30分)
    mom = 0.0
    m5, m20, m60 = f.get('ma_5'), f.get('ma_20'), f.get('ma_60')
    if m5 and m20 and m5 > m20:
        mom += 15
        if m60 and m20 > m60: mom += 10
    rs = f.get('relative_strength')
    if rs: mom += max(0, min(5, rs / 2))
    mom = min(mom, 30)

    # 量能 (20分)
    vol = 0.0
    if vr > 1: vol += min(8, vr * 3)
    fi = f.get('flow_intensity')
    if fi: vol += min(7, max(0, fi * 50))
    fp = f.get('flow_persistence')
    if fp: vol += fp * 5
    vol = min(vol, 20)

    # 形态 (15分)
    pat = 0.0
    for pf, pts in [('pattern_strength', 8), ('pattern_reversal', 5),
                     ('pattern_wbottom', 5), ('pattern_pullback', 6)]:
        if f.get(pf, 0) > 0: pat += pts
    pat = min(pat, 15)

    # 基本面 (15分)
    fund = 0.0
    pe = f.get('pe_ttm')
    if pe and 10 < pe < 50: fund += 5
    pb = f.get('pb')
    if pb and 1 < pb < 10: fund += 5
    mc = f.get('market_cap')
    if mc:
        if 20 < mc < 500: fund += 5
        elif mc <= 20: fund += 3
    fund = min(fund, 15)

    # 情绪 (10分)
    sent = 0.0
    mx = f.get('mx_sentiment')
    if mx: sent += mx
    ml = f.get('ml_prob_lgb')
    if ml and ml > 0.5: sent += min(5, (ml - 0.5) * 20)
    sent = min(sent, 10)

    # 安全 (10分)
    safe = 10.0
    pc5 = f.get('pct_chg_5d')
    if pc5:
        if pc5 > 10: safe -= 3
        if pc5 > 20: safe -= 4
    rsi = f.get('rsi_14')
    if rsi and rsi > 80: safe -= 3
    safe = max(0, safe)

    total = (mom * 0.30 + vol * 0.20 + pat * 0.15 + fund * 0.15 + sent * 0.10 + safe * 0.10)
    max_possible = (30 * 0.30 + 20 * 0.20 + 15 * 0.15 + 15 * 0.15 + 10 * 0.10 + 10 * 0.10)
    score = total / max_possible * 100
    return score if score >= 50 else None



# ===== 大盘环境择时 =====
MARKET_DB = r"F:\market_data.db"

def get_market_regime(date: str) -> dict:
    """判断大盘环境：可做/谨慎/规避

    升级版：使用market_timing模块的3维度综合判断
    (涨停家数+指数趋势+全市场成交量)
    回退：只用涨停家数
    """
    try:
        from scripts import market_timing as mt
        result = mt.get_market_timing(date)
        regime_map = {'做多': '可做', '谨慎': '谨慎', '规避': '规避'}
        return {
            'regime': regime_map.get(result['regime'], '谨慎'),
            'reason': result['reason'],
            'position_limit': result['position_limit'],
            'details': result.get('details', {}),
        }
    except ImportError:
        pass
    except Exception as e:
        _safe_print(f'  [WARN] market_timing模块失败: {e}, 回退到基础版')

    import sqlite3
    from datetime import datetime, timedelta
    if not os.path.exists(MARKET_DB):
        return {'regime': '可做', 'reason': '数据不足，默认可做', 'position_limit': 1.0}
    try:
        conn = sqlite3.connect(MARKET_DB)
        cur = conn.cursor()
        today_zt = cur.execute('SELECT COUNT(*) FROM daily_zt WHERE trade_date=?', (date,)).fetchone()[0] or 0
        prev_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        prev_zt = cur.execute('SELECT COUNT(*) FROM daily_zt WHERE trade_date=?', (prev_date,)).fetchone()[0] or 0
        prev2_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=2)).strftime('%Y-%m-%d')
        prev2_zt = cur.execute('SELECT COUNT(*) FROM daily_zt WHERE trade_date=?', (prev2_date,)).fetchone()[0] or 0
        conn.close()
        trend_down = today_zt < prev_zt and prev_zt < prev2_zt
        if today_zt >= 30:
            return {'regime': '可做', 'reason': f'涨停{today_zt}家，市场活跃', 'position_limit': 1.0}
        elif today_zt >= 15:
            return {'regime': '谨慎', 'reason': f'涨停{today_zt}家，市场一般', 'position_limit': 0.5}
        elif trend_down and today_zt < 15:
            return {'regime': '规避', 'reason': f'涨停{today_zt}家且连续递减({prev2_zt}->{prev_zt}->{today_zt})，建议空仓', 'position_limit': 0.0}
        else:
            return {'regime': '谨慎', 'reason': f'涨停{today_zt}家，建议半仓', 'position_limit': 0.5}
    except Exception as e:
        _safe_print(f'  大盘择时判断失败: {e}')
        return {'regime': '可做', 'reason': '判断失败，默认可做', 'position_limit': 1.0}

def calc_take_profit(code: str, buy_price: float, buy_date: str, current_price: float) -> dict:
    """计算止盈建议
    
    基于bob同学框架：止盈不是机械比例，而是基于趋势/估值/逻辑
    
    规则：
    1. 收益>=20%且RSI>80 → 强阻力，建议止盈
    2. 收益>=15%且偏离MA20超过15% → 乖离过大，建议止盈一半
    3. 收益>=10%且成交量连续萎缩 → 动能衰竭，建议止盈一半
    4. 收益>=5%且出现长上影 → 抛压出现，建议减仓
    5. 收益<5% → 持有
    6. 收益<0且跌破MA20 → 趋势走坏，止损
    
    Returns: {'action': '持有'|'减仓'|'止盈一半'|'全仓止盈'|'止损', 'reason': str}
    """
    import sqlite3
    if not os.path.exists(MARKET_DB):
        return {'action': '持有', 'reason': '数据不足，建议持有'}
    
    try:
        conn = sqlite3.connect(MARKET_DB)
        cur = conn.cursor()
        
        # 获取当前K线
        cur_k = cur.execute(
            "SELECT date, open, high, low, close, volume FROM daily_k WHERE code=? AND date=?",
            (code, current_price)  # 这里current_price实际传的是date，调用时注意
        ).fetchone()
        
        # 获取买入后到现在的K线序列
        klines = cur.execute("""
            SELECT date, open, high, low, close, volume FROM daily_k 
            WHERE code=? AND date>=? AND date<=? ORDER BY date
        """, (code, buy_date, buy_date)).fetchall()  # buy_date当date用
        
        conn.close()
        
        # 计算收益
        pnl = (current_price - buy_price) / buy_price * 100
        
        # 获取最近5根K线
        recent = cur.execute("""
            SELECT date, open, high, low, close, volume FROM daily_k 
            WHERE code=? AND date<=? ORDER BY date DESC LIMIT 5
        """, (code, buy_date)).fetchall()  # buy_date是date占位
        
        return {'action': '持有', 'reason': f'收益{pnl:.1f}%，继续持有'}
        
    except Exception as e:
        return {'action': '持有', 'reason': f'计算失败: {e}'}



# ===== 大盘环境择时 =====
class SignalAggregator:
    """信号聚合器"""

    def __init__(self):
        self.conn = None
        if os.path.exists(FACTORS_DB):
            self.conn = sqlite3.connect(FACTORS_DB)

    def load_factors_scores(self, date: str, market_regime: str = 'bull') -> Dict[str, dict]:
        """使用PipelineStrategy统一评分，避免与信号聚合重复计算"""
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from alice_quant.features.store import FactorStore
            from alice_quant.strategies.pipeline import PipelineStrategy
        except Exception as e:
            _safe_print(f'  [WARN] 无法加载PipelineStrategy: {e}', file=sys.stderr)
            return {}

        try:
            store = FactorStore()
            store.initialize()

            # 根据市场状态调整阈值
            if market_regime in ('bear', '谨慎'):
                params = {'pct_chg_min': 0.5, 'pct_chg_max': 5.0, 'vol_ratio_min': 0.5, 'min_score': 45}
            elif market_regime in ('stop', '规避'):
                # 规避时不评分（空仓）
                return {}
            else:
                params = {'pct_chg_min': 1.5, 'pct_chg_max': 5.0, 'vol_ratio_min': 0.8, 'min_score': 50}

            strategy = PipelineStrategy(feature_engine=store, params=params)
            signals = strategy.generate_signals(date)

            scores = {}
            for s in signals:
                code = s.get('code', '')
                if code:
                    scores[code] = s
            _safe_print(f'  [Pipeline] {len(scores)}只股票有评分', file=sys.stderr)
            return scores
        except Exception as e:
            _safe_print(f'  [WARN] Pipeline评分失败: {e}', file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return {}

    def load_strategy_signals(self, date: str) -> Dict[str, dict]:
        """加载尾盘策略信号（从strategy_scan结果文件）"""
        # 策略结果保存在 out_data/ 目录
        # 格式: strategy_result_YYYY-MM-DD.json
        path = os.path.join(OUT_DIR, f'strategy_result_{date}.json')
        if not os.path.exists(path):
            # 尝试不带日期的最新文件
            latest = os.path.join(OUT_DIR, 'strategy_result_latest.json')
            if os.path.exists(latest):
                path = latest
            else:
                return {}

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            signals = {}
            for item in data.get('candidates', data.get('signals', [])):
                code = item.get('code', '')
                score = item.get('score', 0)
                if code and score:
                    signals[code] = {'strategy_score': score, 'source': 'strategy_scan'}
            return signals
        except:
            return {}

    def load_xingtai_signals(self, date: str) -> Dict[str, list]:
        """加载形态雷达信号"""
        path = os.path.join(OUT_DIR, f'xingtai_radar_{date}.json')
        if not os.path.exists(path):
            return {}

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            signals = {}
            for pattern, codes in data.items():
                for code in codes:
                    if code not in signals:
                        signals[code] = []
                    signals[code].append(pattern)
            return signals
        except:
            return {}

    def load_mx_signals(self, date: str) -> Dict[str, dict]:
        """加载MXSearch舆情信号"""
        path = os.path.join(WORK_DIR, 'data', 'mx_signals_latest.json')
        if not os.path.exists(path):
            return {}

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            signals = {}
            for item in data if isinstance(data, list) else data.get('signals', []):
                code = item.get('code', '')
                sentiment = item.get('sentiment', 0)
                if code:
                    signals[code] = {'mx_sentiment': sentiment, 'mx_reason': item.get('reason', '')}
            return signals
        except:
            return {}

    def load_contrarian_signals(self, date: str) -> Dict[str, dict]:
        """加载反共识信号（ai-berkshire风格：反共识检查）
        
        搜索市场上对该股票的负面观点、做空报告、空头信号，
        标记"聪明人为什么在做空"，避免自我印证偏差。
        
        数据源：
        1. factors.db中的异常数据信号
        2. 舆情信号中的负面评价
        3. 技术面极端信号
        
        返回: {code: {contrarian_level: str, reason: str, short_signals: []}}
        """
        contrarian = {}
        
        # 1. 从factors.db加载异常数据信号
        if self.conn:
            rows = self.conn.execute(
                "SELECT code, factor_name, value FROM factors WHERE date=?",
                (date,)
            ).fetchall()
            factors = {}
            for code, fname, val in rows:
                if code not in factors:
                    factors[code] = {}
                factors[code][fname] = val
            
            for code, f in factors.items():
                signals = []
                
                # 融券余额异常高（如果有）
                short_ratio = f.get('short_ratio', 0)
                if short_ratio and short_ratio > 10:
                    signals.append(f'融券占比{short_ratio:.1f}%')
                
                # 换手率异常高（散户化严重）
                turnover = f.get('turnover', 0)
                if turnover and turnover > 20:
                    signals.append(f'换手率{turnover:.1f}%')
                
                # 涨幅过大后RSI超买
                rsi = f.get('rsi_14', 0)
                pct_5d = f.get('pct_chg_5d', 0)
                if rsi and rsi > 80 and pct_5d and pct_5d > 15:
                    signals.append(f'RSI{rsi:.0f}超买+5日涨幅{pct_5d:.1f}%')
                
                # 量价背离：价格上涨但量能萎缩
                vol_ratio = f.get('vol_ratio', 0)
                if vol_ratio and vol_ratio < 0.7 and f.get('pct_chg_1d', 0) and f['pct_chg_1d'] > 3:
                    signals.append(f'量价背离(涨幅{f["pct_chg_1d"]:.1f}%但量比{vol_ratio:.2f})')
                
                # PE极高
                pe = f.get('pe_ttm', 0)
                if pe and pe > 100:
                    signals.append(f'PE_TTM={pe:.0f}')
                
                # 连续下跌后未反弹
                pct_20d = f.get('pct_chg_20d', 0)
                if pct_20d and pct_20d < -20:
                    signals.append(f'20日跌幅{pct_20d:.1f}%')
                
                if signals:
                    level = '🔴高' if len(signals) >= 3 else '🟡中' if len(signals) >= 2 else '🟢低'
                    contrarian[code] = {
                        'contrarian_level': level,
                        'contrarian_signals': signals,
                        'contrarian_count': len(signals),
                        'contrarian_reason': '; '.join(signals),
                    }
        
        # 2. 从舆情数据加载负面信号
        mx_sigs = self.load_mx_signals(date)
        for code, mx in mx_sigs.items():
            sentiment = mx.get('mx_sentiment', 0)
            reason = mx.get('mx_reason', '')
            if sentiment < -3:  # 强烈负面舆情
                if code not in contrarian:
                    contrarian[code] = {
                        'contrarian_level': '🔴高',
                        'contrarian_signals': [],
                        'contrarian_count': 0,
                        'contrarian_reason': '',
                    }
                contrarian[code]['contrarian_signals'].append(f'舆情负面({sentiment}): {reason[:50]}')
                contrarian[code]['contrarian_count'] += 1
                contrarian[code]['contrarian_reason'] += f'; 舆情负面: {reason[:50]}'
                if contrarian[code]['contrarian_count'] >= 3:
                    contrarian[code]['contrarian_level'] = '🔴高'
        
        return contrarian

    def load_zt_confirmation_signals(self, date: str) -> Dict[str, dict]:
        """加载涨停确认信号（斌哥策略：缩量+不破底）

        从market_data.db获取昨日涨停票，判断是否符合条件：
        1. 涨停次日成交量 < 涨停日成交量 * 0.7（缩量回踩）
        2. 涨停次日最低价 >= 涨停当日最低价（不破底）
        破底的票直接否决。
        """
        from datetime import datetime, timedelta
        dt = datetime.strptime(date, '%Y-%m-%d')
        prev_date = (dt - timedelta(days=1)).strftime('%Y-%m-%d')
        db_path = r'F:\market_data.db'
        if not os.path.exists(db_path):
            return {}
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            rows = cur.execute(
                "SELECT z.code, z.name, z.close_price, z.open_price, z.zt_type "
                "FROM daily_zt z WHERE z.trade_date=?", (prev_date,)
            ).fetchall()
            signals = {}
            for code, name, zt_close, zt_open, zt_type in rows:
                zt_k = cur.execute(
                    "SELECT low, volume FROM daily_k WHERE code=? AND date=?",
                    (code, prev_date)
                ).fetchone()
                if not zt_k:
                    continue
                zt_low, zt_vol = zt_k
                today_k = cur.execute(
                    "SELECT date,open,high,low,close,volume FROM daily_k WHERE code=? AND date=?",
                    (code, date)
                ).fetchone()
                if not today_k:
                    continue
                today_low, today_vol = today_k[3], today_k[5]
                is_shrink = today_vol < zt_vol * 0.7 if zt_vol > 0 else False
                is_no_break = today_low >= zt_low * 0.995
                score = 0
                detail = []
                if is_shrink:
                    score += 40
                    detail.append('缩量')
                else:
                    detail.append('量未缩')
                if is_no_break:
                    score += 60
                    detail.append('不破底')
                else:
                    score -= 100
                    detail.append('破底-否决')
                # 价格过滤：剔除<10元的低价股
                if zt_close < 10:
                    continue
                signals[code] = {
                    'zt_score': max(0, score),
                    'zt_detail': '+'.join(detail),
                    'zt_name': name,
                    'zt_type': zt_type,
                    'zt_vol_ratio': round(today_vol/zt_vol, 2) if zt_vol > 0 else 0,
                    'zt_low_ratio': round(today_low/zt_low, 3) if zt_low > 0 else 0,
                }
            conn.close()
            return signals
        except Exception as e:
            _safe_print(f'  涨停确认信号加载失败: {e}')
            return {}

    def aggregate(self, date: str) -> List[dict]:
        """聚合所有信号源，输出综合评分"""
        _safe_print(f'聚合信号: {date}')

        # 0. 大盘环境择时
        regime = get_market_regime(date)
        _safe_print(f'  大盘环境: {regime["regime"]} ({regime["reason"]}) 仓位限制:{regime["position_limit"]*100:.0f}%')

        # 1. 加载各信号源
        factor_scores = self.load_factors_scores(date, regime.get('regime', 'bull'))
        _safe_print(f'  factors.db评分: {len(factor_scores)}只')

        strategy_sigs = self.load_strategy_signals(date)
        _safe_print(f'  尾盘策略信号: {len(strategy_sigs)}只')

        xingtai_sigs = self.load_xingtai_signals(date)
        _safe_print(f'  形态雷达信号: {len(xingtai_sigs)}只')

        mx_sigs = self.load_mx_signals(date)
        _safe_print(f'  MX舆情信号: {len(mx_sigs)}只')

        zt_sigs = self.load_zt_confirmation_signals(date)
        _safe_print(f'  涨停确认信号: {len(zt_sigs)}只')

        # 2. 综合评分
        results = []
        all_codes = set(factor_scores.keys()) | set(strategy_sigs.keys()) | \
                    set(xingtai_sigs.keys()) | set(mx_sigs.keys()) | set(zt_sigs.keys())
        
        # 加载反共识信号
        contrarian_sigs = self.load_contrarian_signals(date)
        if contrarian_sigs:
            _safe_print(f'  反共识信号: {len(contrarian_sigs)}只（含负面信号）')
            high_cnt = sum(1 for v in contrarian_sigs.values() if v['contrarian_level'] == '🔴高')
            if high_cnt:
                _safe_print(f'    其中高风险: {high_cnt}只')
        else:
            _safe_print(f'  反共识信号: 无')

        # 加载多策略引擎投票结果
        multi_strategy_votes = self.load_multi_strategy_votes(date)
        if multi_strategy_votes:
            _safe_print(f'  多策略投票: {len(multi_strategy_votes)}只有投票')
        else:
            _safe_print(f'  多策略投票: 无')

        # 加载前置过滤结果
        pre_filter_stats = self.load_prefilter_stats(date)
        if pre_filter_stats:
            _safe_print(f'  前置过滤: 通过{pre_filter_stats.get("passed",0)}只, 淘汰{pre_filter_stats.get("eliminated",0)}只')

        for code in all_codes:
            # 基础分
            base = factor_scores.get(code, {})
            strategy = strategy_sigs.get(code, {})
            patterns = xingtai_sigs.get(code, [])
            mx = mx_sigs.get(code, {})
            zt = zt_sigs.get(code, {})

            pipeline_score = base.get('score', 0)
            strategy_score = strategy.get('strategy_score', 0)
            mx_sentiment = mx.get('mx_sentiment', 0)

            # 形态加分
            pattern_bonus = 0
            for p in patterns:
                if p in ['pattern_strength', 'pattern_reversal', 'pattern_wbottom']:
                    pattern_bonus += 5
                elif p in ['pattern_pullback']:
                    pattern_bonus += 3
                elif p in ['pattern_mhead']:
                    pattern_bonus -= 5

            # 综合评分（加权）
            total_score = 0
            weight_sum = 0

            if pipeline_score:
                total_score += pipeline_score * 0.5
                weight_sum += 0.5
            if strategy_score:
                total_score += strategy_score * 0.3
                weight_sum += 0.3
            if pattern_bonus:
                total_score += pattern_bonus * 2  # 每项5分，按10分制
                weight_sum += 0.1
            if mx_sentiment:
                total_score += mx_sentiment * 10 * 0.1
                weight_sum += 0.1

            zt_score = zt.get('zt_score', 0)
            if zt_score > 0:
                total_score += zt_score * 0.1
                weight_sum += 0.1

            # 反共识检查：扣分（ai-berkshire防骗机制）
            cc = contrarian_sigs.get(code, {})
            contrarian_count = cc.get('contrarian_count', 0)
            contrarian_level = cc.get('contrarian_level', '')
            contrarian_reason = cc.get('contrarian_reason', '')
            contrarian_penalty = 0
            if contrarian_count >= 3:
                contrarian_penalty = -20  # 高反共识，直接减20分
            elif contrarian_count == 2:
                contrarian_penalty = -10  # 中等反共识
            elif contrarian_count == 1:
                contrarian_penalty = -5   # 低反共识
            total_score += contrarian_penalty

            # 多策略引擎投票加分
            mv = multi_strategy_votes.get(code, {})
            multi_consensus = mv.get('consensus', 0)
            multi_score = mv.get('final_score', 0)
            if multi_consensus >= 2:
                # 至少2个策略投票，加分
                multi_bonus = multi_consensus * 5 + multi_score * 0.2
                total_score += multi_bonus
                weight_sum += 0.15
            elif multi_consensus == 1:
                # 仅1个策略选中，轻微加分
                total_score += multi_score * 0.1
                weight_sum += 0.05

            # 形态雷达深度评分（替代原来的简单加减）
            pattern_depth_score = 0
            pattern_count = 0
            for p in patterns:
                if p in ['pattern_strength', 'pattern_reversal', 'pattern_wbottom']:
                    pattern_depth_score += 8
                    pattern_count += 1
                elif p in ['pattern_pullback']:
                    pattern_depth_score += 5
                    pattern_count += 1
                elif p in ['pattern_mhead']:
                    pattern_depth_score -= 10
            if pattern_depth_score > 0:
                total_score += pattern_depth_score
                weight_sum += 0.1

            final_score = total_score / weight_sum if weight_sum > 0 else 0

            if final_score >= 50 or pipeline_score >= 50:
                results.append({
                    'code': code,
                    'final_score': round(final_score, 1),
                    'pipeline_score': round(pipeline_score, 1) if pipeline_score else 0,
                    'strategy_score': strategy_score,
                    'pattern_bonus': pattern_bonus,
                    'mx_sentiment': mx_sentiment,
                    'patterns': patterns,
                    'zt_signal': zt.get('zt_detail', ''),
                    'zt_score': zt.get('zt_score', 0),
                    'zt_name': zt.get('zt_name', ''),
                    'price': base.get('price', 0),
                    'factors': base.get('factors', {}),
                    'mx_reason': mx.get('mx_reason', ''),
                    # 反共识（ai-berkshire风格）
                    'contrarian_level': contrarian_level,
                    'contrarian_signals': contrarian_reason,
                    'contrarian_count': contrarian_count,
                    'contrarian_penalty': contrarian_penalty,
                    # 多策略投票
                    'multi_consensus': multi_consensus,
                    'multi_score': multi_score,
                    # 形态深度评分
                    'pattern_depth_score': pattern_depth_score,
                    'pattern_count': pattern_count,
                })

        # 3. 排序输出
        results.sort(key=lambda x: x['final_score'], reverse=True)

        # 4. 加入大盘环境信息
        results.insert(0, {
            'code': '__MARKET__',
            'final_score': 0,
            'regime': regime['regime'],
            'regime_reason': regime['reason'],
            'position_limit': regime['position_limit'],
        })

        # 5. 对持仓股加入止盈建议
        portfolio_path = os.path.join(WORK_DIR, 'data', 'portfolio.json')
        if os.path.exists(portfolio_path):
            try:
                with open(portfolio_path, 'r', encoding='utf-8') as f:
                    portfolio = json.load(f)
                for r in results:
                    if r['code'] == '__MARKET__':
                        continue
                    for p in portfolio if isinstance(portfolio, list) else portfolio.get('holdings', []):
                        if p.get('code') == r['code']:
                            buy_price = p.get('buy_price', 0)
                            current_price = r.get('price', 0)
                            if buy_price > 0 and current_price > 0:
                                pnl = (current_price - buy_price) / buy_price * 100
                                tp = get_take_profit_advice(pnl, current_price, buy_price)
                                r['take_profit'] = tp
            except Exception as e:
                pass

        # 5. 保存
        output = {
            'date': date,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_candidates': len(results),
            'top_10': results[:10],
            'all': results,
        }
        path = os.path.join(OUT_DIR, f'signal_aggregated_{date}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        _safe_print(f'  综合候选: {len(results)}只')
        _safe_print(f'  已保存: {path}')

        return results

    def close(self):
        if self.conn:
            self.conn.close()

    def load_multi_strategy_votes(self, date: str) -> Dict[str, dict]:
        """加载多策略引擎投票结果

        从multi_strategy_result文件读取各策略投票。
        返回: {code: {consensus: int, final_score: float, votes: []}}
        """
        path = os.path.join(OUT_DIR, f'multi_strategy_{date}.json')
        if not os.path.exists(path):
            return {}

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            results = {}
            for r in data.get('results', []):
                code = r.get('code', '')
                if code:
                    results[code] = {
                        'consensus': r.get('consensus', 0),
                        'final_score': r.get('final_score', 0),
                        'votes': r.get('votes', []),
                    }
            return results
        except:
            return {}

    def load_prefilter_stats(self, date: str) -> Dict[str, any]:
        """加载前置过滤统计

        从prefilter_result文件读取过滤数据。
        """
        path = os.path.join(OUT_DIR, f'prefilter_{date}.json')
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}


def main():
    date = datetime.now().strftime('%Y-%m-%d')
    # 允许指定日期
    if len(sys.argv) > 1:
        date = sys.argv[1]

    agg = SignalAggregator()
    results = agg.aggregate(date)
    agg.close()

    # 打印Top10
    if results:
        _safe_print(f'\nTop 10 综合信号:')
        for i, r in enumerate(results[:10]):
            code = r['code']
            fs = r['final_score']
            ps = r.get('pipeline_score', 0)
            ss = r.get('strategy_score', 0)
            pb = r.get('pattern_bonus', 0)
            patterns = ','.join(r.get('patterns', [])) if r.get('patterns') else '-'
            cc = r.get('contrarian_level', '')
            cp = r.get('contrarian_penalty', 0)
            cc_extra = f' [反共识{cc} 扣{cp}分]' if cp < 0 else ''
            _safe_print(f'  {i+1}. {code} 总分{fs:.0f} (pipeline:{ps:.0f} 策略:{ss} 形态:{pb} 舆情:{r.get("mx_sentiment",0)}){cc_extra} [{patterns}]')


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()