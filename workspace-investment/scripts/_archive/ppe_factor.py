# -*- coding: utf-8 -*-
"""
PPE周期编码因子 (Position-Period-Encoding)
==========================================
将个股所在的行业板块周期位置编码为评分因子。

PPE核心逻辑：
  1. 板块周期定位：用RPS历史数据判断板块所处的4个周期阶段
     - 上升期 (RPS_5d > 80, RPS_5d > RPS_10d): +8分
     - 高潮期 (RPS_5d > 80, RPS_5d <= RPS_10d): +5分
     - 筑底期 (RPS_5d < 30, RPS_5d > RPS_10d): +3分
     - 衰退期 (RPS_5d < 30, RPS_5d <= RPS_10d): -5分
     - 中间期: +0分
  2. 个股位置编码：个股涨幅 vs 板块涨幅（相对强度）
     - 相对强度 = 个股5日涨幅 - 板块5日涨幅
     - >+3%: +3分  |  >+0%: +1分  |  >-3%: 0分  |  <=-3%: -2分
  3. 综合PPE = 周期得分 + 位置得分 (范围 -7 ~ +13)

数据来源：
  - out_data/rps_history/ 下的 RPS_board_*.json 文件（每日采集）
  - 个股日K线从DB读取
"""

import json
import os
import sqlite3
from datetime import datetime, date, timedelta

WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
HIST_DIR = os.path.join(WORK_DIR, 'out_data', 'rps_history')
DB = r'F:\market_data.db'

# ============================================================
# 板块周期定位
# ============================================================

# 股票代码到申万板块名称的映射（缓存文件）
STOCK_BOARD_CACHE = os.path.join(WORK_DIR, 'data', 'stock_board_cache.json')


def get_latest_rps_data():
    """获取最新的RPS板块数据"""
    if not os.path.exists(HIST_DIR):
        print("[PPE] RPS历史目录不存在")
        return None, None
    files = sorted([f for f in os.listdir(HIST_DIR) 
                    if f.startswith('RPS_board_') and f.endswith('.json')])
    if not files:
        print("[PPE] 无RPS历史文件")
        return None, None
    latest_file = files[-1]
    with open(os.path.join(HIST_DIR, latest_file), 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['rps_data'], latest_file


def classify_board_phase(board_rps: dict) -> tuple:
    """
    判断板块所处的周期阶段
    返回: (phase_name: str, phase_score: int)
    """
    rps_5d = board_rps.get('rps_5d', 50)
    rps_10d = board_rps.get('rps_10d', 50)
    
    # 趋势判断：5日RPS > 10日RPS 表示加速，反之减速
    accelerating = rps_5d > rps_10d + 5  # 5分以上才判为加速
    
    if rps_5d >= 80:
        if accelerating:
            return ('上升期', 8)   # 强势加速，最佳
        else:
            return ('高潮期', 5)   # 强势但减速，警惕
    elif rps_5d >= 60:
        if accelerating:
            return ('温和上升', 4)
        else:
            return ('温和调整', 1)
    elif rps_5d >= 40:
        if accelerating:
            return ('筑底回暖', 2)
        else:
            return ('中性整理', 0)
    elif rps_5d >= 20:
        if accelerating:
            return ('底部异动', 3)  # 从底部爬起来，信号
        else:
            return ('弱势整理', -2)
    else:
        if accelerating:
            return ('底部试探', -1)
        else:
            return ('衰退期', -5)   # 最差


def build_stock_board_mapping() -> dict:
    """
    建立股票代码→申万板块名称的映射
    返回: { '000001': '银行', '000002': '房地产', ... }
    
    使用akshare逐板块获取成分股，缓存到本地文件
    """
    if os.path.exists(STOCK_BOARD_CACHE):
        try:
            with open(STOCK_BOARD_CACHE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            print(f"[PPE] 板块映射缓存加载: {len(cache)}只股票, {len(set(cache.values()))}个板块")
            return cache
        except Exception:
            pass
    
    print("[PPE] 构建板块映射（首次较慢，后续缓存）...")
    
    # 获取RPS数据中的板块列表
    rps_data, _ = get_latest_rps_data()
    if not rps_data:
        print("[PPE] 无RPS数据，无法建立映射")
        return {}
    
    import akshare as ak
    mapping = {}
    errors = 0
    
    for i, board in enumerate(rps_data):
        board_name = board['name']
        try:
            df = ak.stock_board_industry_cons_em(symbol=board_name)
            if df is not None and not df.empty and '代码' in df.columns:
                for code in df['代码']:
                    code_str = str(code).strip()
                    # 统一为6位数字格式
                    if len(code_str) >= 6:
                        code_clean = code_str[-6:]  # 取后6位
                        if code_clean not in mapping:
                            mapping[code_clean] = board_name
            if (i + 1) % 20 == 0:
                print(f"  [PPE] 已处理 {i+1}/{len(rps_data)} 个板块")
        except Exception as e:
            errors += 1
            if errors > 5:
                continue
    
    # 缓存
    os.makedirs(os.path.dirname(STOCK_BOARD_CACHE), exist_ok=True)
    with open(STOCK_BOARD_CACHE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False)
    print(f"[PPE] 板块映射构建完成: {len(mapping)}只股票, {len(set(mapping.values()))}个板块, 缓存已保存")
    return mapping


def get_stock_board(code: str, mapping: dict = None) -> str:
    """获取股票所属申万板块"""
    # 标准化code: sh.000001 -> 000001, sz.000858 -> 000858
    clean = code.replace('sh.', '').replace('sz.', '').replace('bj.', '')
    if mapping and clean in mapping:
        return mapping[clean]
    return None


def get_board_rps_by_name(board_name: str, rps_list: list) -> dict:
    """根据板块名在RPS列表中查找"""
    for b in rps_list:
        if b['name'] == board_name:
            return b
    return None


def compute_stock_relative_strength(stock_code: str, board_name: str, rps_list: list, date_str: str = None) -> float:
    """
    计算个股相对板块的强度
    返回: 个股5日涨幅 - 板块5日涨幅
    """
    if date_str is None:
        date_str = date.today().strftime('%Y-%m-%d')
    
    # 板块5日涨幅
    board = get_board_rps_by_name(board_name, rps_list)
    if not board:
        return 0.0
    board_ret_5d = board.get('returns', {}).get('5', 0.0)
    
    # 个股5日涨幅
    clean_code = stock_code.replace('sh.', '').replace('sz.', '').replace('bj.', '')
    db_code = stock_code  # DB里是 sh.XXXXXX 格式
    
    try:
        conn = sqlite3.connect(DB)
        # 获取最近6个交易日的收盘价（多取1天算前收盘）
        rows = conn.execute("""
            SELECT date, close FROM daily_k 
            WHERE code = ? AND date <= ?
            ORDER BY date DESC LIMIT 6
        """, (db_code, date_str)).fetchall()
        conn.close()
        
        if len(rows) < 2:
            return 0.0
        
        # 按日期升序
        rows = list(reversed(rows))
        # 取最新收盘和5个交易日前的收盘（如果有）
        latest_close = rows[-1][1]
        if len(rows) >= 6:
            prev_close = rows[-6][1]
        elif len(rows) >= 2:
            # 不足6个交易日，用最早的那个
            prev_close = rows[0][1]
        else:
            return 0.0
        
        if prev_close <= 0:
            return 0.0
        
        stock_ret_5d = (latest_close - prev_close) / prev_close * 100
        return stock_ret_5d - board_ret_5d
    except Exception as e:
        print(f"  [PPE] 个股强度计算失败 {stock_code}: {e}")
        return 0.0


# ============================================================
# 主评分函数
# ============================================================

def load_ppe_data():
    """加载PPE所需的数据：板块RPS + 板块映射，返回缓存"""
    rps_data, rps_file = get_latest_rps_data()
    if not rps_data:
        print("[PPE] 无RPS数据可用，PPE评分为0")
        return None, None
    
    mapping = build_stock_board_mapping()
    return rps_data, mapping


def score_ppe(stock_code: str, rps_data: list, mapping: dict, date_str: str = None) -> dict:
    """
    对单只股票计算PPE评分
    返回: {'ppe_score': float, 'board_name': str, 'board_phase': str, 'phase_score': int,
           'relative_strength': float, 'position_score': int}
    """
    board_name = get_stock_board(stock_code, mapping)
    if not board_name:
        return {
            'ppe_score': 0,
            'board_name': '未知',
            'board_phase': '未知',
            'phase_score': 0,
            'relative_strength': 0,
            'position_score': 0,
        }
    
    board = get_board_rps_by_name(board_name, rps_data)
    if not board:
        return {
            'ppe_score': 0,
            'board_name': board_name,
            'board_phase': '未知',
            'phase_score': 0,
            'relative_strength': 0,
            'position_score': 0,
        }
    
    # 1. 板块周期定位
    phase_name, phase_score = classify_board_phase(board)
    
    # 2. 个股相对强度
    rel_strength = compute_stock_relative_strength(stock_code, board_name, rps_data, date_str)
    
    # 个股位置得分
    if rel_strength > 5:
        position_score = 5    # 大幅领涨板块
    elif rel_strength > 3:
        position_score = 3    # 明显领涨
    elif rel_strength > 0:
        position_score = 1    # 略强于板块
    elif rel_strength > -3:
        position_score = 0    # 跟随板块
    elif rel_strength > -5:
        position_score = -2   # 弱于板块
    else:
        position_score = -3   # 严重弱于板块
    
    # 3. 综合PPE
    ppe_score = phase_score + position_score
    
    return {
        'ppe_score': ppe_score,
        'board_name': board_name,
        'board_phase': phase_name,
        'phase_score': phase_score,
        'relative_strength': round(rel_strength, 2),
        'position_score': position_score,
        'board_rps_5d': board.get('rps_5d', 0),
        'board_rps_10d': board.get('rps_10d', 0),
    }


def batch_ppe_score(candidates: list, rps_data: list, mapping: dict, date_str: str = None) -> list:
    """
    批量计算候选股的PPE评分
    candidates: [{code, chg_pct, ...}, ...]
    返回: 原列表+ppe_info字段
    """
    if not rps_data or not mapping:
        for s in candidates:
            s['ppe_score'] = 0
            s['ppe_board'] = ''
            s['ppe_phase'] = ''
            s['ppe_detail'] = ''
        return candidates
    
    total = len(candidates)
    for i, s in enumerate(candidates):
        ppe = score_ppe(s.get('code', ''), rps_data, mapping, date_str)
        s['ppe_score'] = ppe['ppe_score']
        s['ppe_board'] = ppe['board_name']
        s['ppe_phase'] = ppe['board_phase']
        s['ppe_detail'] = f"板块:{ppe['board_name']} | 阶段:{ppe['board_phase']}({ppe['phase_score']:+d}) | 相对强度:{ppe['relative_strength']:+.1f}%({ppe['position_score']:+d})"
        if (i + 1) % 50 == 0:
            print(f"  [PPE] 已评分 {i+1}/{total} 只")
    
    print(f"[PPE] 批量评分完成: {total}只, 有板块: {sum(1 for s in candidates if s.get('ppe_board') and s['ppe_board'] != '未知')}")
    return candidates


if __name__ == '__main__':
    print("=" * 60)
    print("PPE周期编码因子 测试")
    print("=" * 60)
    
    rps_data, mapping = load_ppe_data()
    if not rps_data:
        print("[PPE] 数据加载失败")
        sys.exit(1)
    
    # 测试几只股票
    test_codes = ['sz.002805', 'sh.600186', 'sz.000833', 'sz.002456', 'sh.688556',
                  'sz.000858', 'sz.002415', 'sh.600519']
    print(f"\n测试股票PPE评分:")
    print(f"{'股票':<16} {'板块':<12} {'阶段':<10} {'阶段分':>6} {'相对强度':>10} {'位置分':>6} {'PPE总分':>8}")
    print("-" * 80)
    for code in test_codes:
        ppe = score_ppe(code, rps_data, mapping)
        print(f"{code:<16} {ppe['board_name']:<12} {ppe['board_phase']:<10} {ppe['phase_score']:+6d} {ppe['relative_strength']:+9.1f}% {ppe['position_score']:+6d} {ppe['ppe_score']:+8d}")
