"""板块动量因子计算器

从 scripts/ppe_factor.py 移植，注册为框架标准因子。

因子列表：
  - sector_phase: 板块周期阶段编码 (-5~+8)
  - sector_rps_5d: 板块5日RPS (0~100)
  - sector_rps_10d: 板块10日RPS (0~100)
  - relative_strength: 个股相对板块强度

数据来源：
  - RPS历史文件: out_data/rps_history/RPS_board_*.json
  - 板块映射: data/stock_board_cache.json
  - 个股K线: F:\\market_data.db
"""
import json
import os
import sqlite3
import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple

WORK_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
HIST_DIR = os.path.join(WORK_DIR, 'out_data', 'rps_history')
CACHE_FILE = os.path.join(WORK_DIR, 'data', 'stock_board_cache.json')
DB_PATH = r'F:\market_data.db'


class SectorFactors:
    """板块动量因子计算器"""

    # 缓存：避免每次计算都读取文件
    _rps_cache: Optional[list] = None
    _rps_date: Optional[str] = None
    _board_mapping: Optional[dict] = None

    @staticmethod
    def _load_latest_rps() -> Tuple[Optional[list], Optional[str]]:
        """加载最新的RPS板块数据"""
        if SectorFactors._rps_cache is not None:
            return SectorFactors._rps_cache, SectorFactors._rps_date

        if not os.path.exists(HIST_DIR):
            return None, None
        files = sorted([f for f in os.listdir(HIST_DIR)
                       if f.startswith('RPS_board_') and f.endswith('.json')])
        if not files:
            return None, None
        try:
            with open(os.path.join(HIST_DIR, files[-1]), 'r', encoding='utf-8') as f:
                data = json.load(f)
            SectorFactors._rps_cache = data.get('rps_data', [])
            SectorFactors._rps_date = files[-1].replace('RPS_board_', '').replace('.json', '')
            return SectorFactors._rps_cache, SectorFactors._rps_date
        except Exception:
            return None, None

    @staticmethod
    def _load_board_mapping() -> dict:
        """加载股票→板块映射"""
        if SectorFactors._board_mapping is not None:
            return SectorFactors._board_mapping
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    SectorFactors._board_mapping = json.load(f)
                return SectorFactors._board_mapping
            except Exception:
                pass
        return {}

    @staticmethod
    def _get_stock_board(code: str) -> Optional[str]:
        """获取股票所属申万板块"""
        clean = code.replace('sh.', '').replace('sz.', '').replace('bj.', '')
        mapping = SectorFactors._load_board_mapping()
        return mapping.get(clean)

    @staticmethod
    def _get_board_rps(board_name: str) -> Optional[dict]:
        """获取板块的RPS数据"""
        rps_data, _ = SectorFactors._load_latest_rps()
        if not rps_data:
            return None
        for b in rps_data:
            if b.get('name') == board_name:
                return b
        return None

    @staticmethod
    def _classify_phase(rps_5d: float, rps_10d: float) -> Tuple[str, int]:
        """板块周期分类"""
        accelerating = rps_5d > rps_10d + 5

        if rps_5d >= 80:
            return ('上升期', 8) if accelerating else ('高潮期', 5)
        elif rps_5d >= 60:
            return ('温和上升', 4) if accelerating else ('温和调整', 1)
        elif rps_5d >= 40:
            return ('筑底回暖', 2) if accelerating else ('中性整理', 0)
        elif rps_5d >= 20:
            return ('底部异动', 1) if accelerating else ('弱势整理', -2)
        else:
            return ('底部试探', -1) if accelerating else ('衰退期', -5)

    @staticmethod
    def _get_stock_ret_5d(code: str) -> float:
        """从DB获取个股5日涨幅"""
        db_code = code if '.' in code else ('sh.' + code if code.startswith('6') else 'sz.' + code)
        try:
            conn = sqlite3.connect(DB_PATH)
            rows = conn.execute("""
                SELECT date, close FROM daily_k
                WHERE code = ? ORDER BY date DESC LIMIT 6
            """, (db_code,)).fetchall()
            conn.close()
            if len(rows) < 2:
                return 0.0
            rows = list(reversed(rows))
            return (rows[-1][1] - rows[0][1]) / rows[0][1] * 100 if rows[0][1] > 0 else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def sector_phase(code: str, df: pd.DataFrame = None) -> float:
        """板块周期阶段编码

        返回编码值: -5(衰退) ~ +8(上升)
        """
        board_name = SectorFactors._get_stock_board(code)
        if not board_name:
            return 0.0
        board = SectorFactors._get_board_rps(board_name)
        if not board:
            return 0.0
        _, score = SectorFactors._classify_phase(
            board.get('rps_5d', 50), board.get('rps_10d', 50)
        )
        return float(score)

    @staticmethod
    def sector_rps_5d(code: str, df: pd.DataFrame = None) -> float:
        """板块5日RPS"""
        board_name = SectorFactors._get_stock_board(code)
        if not board_name:
            return 50.0
        board = SectorFactors._get_board_rps(board_name)
        if not board:
            return 50.0
        return float(board.get('rps_5d', 50))

    @staticmethod
    def sector_rps_10d(code: str, df: pd.DataFrame = None) -> float:
        """板块10日RPS"""
        board_name = SectorFactors._get_stock_board(code)
        if not board_name:
            return 50.0
        board = SectorFactors._get_board_rps(board_name)
        if not board:
            return 50.0
        return float(board.get('rps_10d', 50))

    @staticmethod
    def relative_strength(code: str, df: pd.DataFrame = None) -> float:
        """个股相对板块强度

        公式: 个股5日涨幅 - 板块5日涨幅 (%)
        正值=个股跑赢板块
        """
        board_name = SectorFactors._get_stock_board(code)
        if not board_name:
            return 0.0
        board = SectorFactors._get_board_rps(board_name)
        if not board:
            return 0.0
        board_ret = board.get('returns', {}).get('5', 0.0)
        stock_ret = SectorFactors._get_stock_ret_5d(code)
        return stock_ret - board_ret

    @staticmethod
    def clear_cache():
        """清空缓存（每日更新后调用）"""
        SectorFactors._rps_cache = None
        SectorFactors._rps_date = None
        SectorFactors._board_mapping = None