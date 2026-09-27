"""形态因子计算器

从 skills/xingtai-catcher 提取形态特征，注册为框架标准因子。

因子列表（二值因子 0/1）：
  - pattern_strength: 强趋势延续
  - pattern_reversal: 底部反转
  - pattern_wbottom: W底
  - pattern_pullback: 趋势回踩
  - pattern_consolidation: 震荡整理
  - pattern_mhead: M头（预警信号）

数据来源：
  - 形态捕手AI引擎 (xingtai_search.py 子进程调用)
  - 每日收盘后生成雷达结果

注意：形态识别依赖AI模型，计算较慢。
建议只在收盘后计算，不作为盘中因子。
"""
import subprocess
import json
import os
import sys
import re
import io
from typing import Optional, List, Dict, Any
from datetime import date

WORK_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SCRIPT = os.path.join(WORK_DIR, 'skills', 'xingtai-catcher', 'scripts', 'xingtai_search.py')
OUT_DIR = os.path.join(WORK_DIR, 'out_data', 'xingtai')

# 形态名称到因子名的映射
PATTERN_MAP = {
    '强趋势延续': 'pattern_strength',
    '底部反转': 'pattern_reversal',
    'W底': 'pattern_wbottom',
    '趋势回踩': 'pattern_pullback',
    '震荡整理': 'pattern_consolidation',
    'M头': 'pattern_mhead',
}


class PatternFactors:
    """形态因子计算器"""

    # 缓存：当日雷达结果
    _radar_cache: Optional[dict] = None

    @staticmethod
    def _run_radar() -> dict:
        """执行全部6模板形态扫描（首次调用时）"""
        if PatternFactors._radar_cache is not None:
            return PatternFactors._radar_cache

        today = date.today().isoformat()

        # 先尝试读已保存的雷达文件
        cached_file = os.path.join(OUT_DIR, f'xingtai_radar_{today}.json')
        if os.path.exists(cached_file):
            try:
                with open(cached_file, 'r', encoding='utf-8') as f:
                    PatternFactors._radar_cache = json.load(f)
                return PatternFactors._radar_cache
            except Exception:
                pass

        # 执行扫描
        results = {}
        for name in PATTERN_MAP:
            candidates = PatternFactors._search_single(name)
            results[name] = candidates

        PatternFactors._radar_cache = results

        # 缓存到文件
        os.makedirs(OUT_DIR, exist_ok=True)
        try:
            with open(cached_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return results

    @staticmethod
    def _search_single(template: str, top_n: int = 5) -> list:
        """执行单个模板搜索"""
        cmd = [
            sys.executable, str(SCRIPT),
            "text", template,
            "--universe", "stock",
            "--timeframe", "1d",
            "--window-bars", "120",
            "--top-n", str(top_n),
            "--print"
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=30, cwd=str(WORK_DIR),
                                    encoding='utf-8', errors='replace')
            output = (result.stdout or '') + (result.stderr or '')
            return PatternFactors._parse_output(output)
        except Exception:
            return []

    @staticmethod
    def _parse_output(output: str) -> list:
        """解析 xingtai_search.py 输出"""
        candidates = []
        for line in output.split('\n'):
            line = line.strip()
            m = re.match(r'(\d+)\.\s+(\S+?)\s+(\d{6}|\*?[A-Z]+\d+?)，评分\s+([\d.]+)', line)
            if m:
                candidates.append({
                    'rank': int(m.group(1)),
                    'name': m.group(2).strip(),
                    'code': m.group(3).strip(),
                    'score': float(m.group(4)),
                })
        return candidates

    @staticmethod
    def _check_pattern(code: str, pattern_name: str) -> bool:
        """检查股票是否出现在特定形态的候选列表中"""
        clean_code = code.replace('sh.', '').replace('sz.', '').replace('bj.', '')
        results = PatternFactors._run_radar()
        candidates = results.get(pattern_name, [])
        for c in candidates:
            c_code = c.get('code', '')
            if c_code == clean_code or c_code == code:
                return c.get('score', 0) >= 60  # 60分以上才算有效信号
        return False

    @staticmethod
    def pattern_strength(code: str, df=None) -> float:
        """强趋势延续信号 (0/1)"""
        return 1.0 if PatternFactors._check_pattern(code, '强趋势延续') else 0.0

    @staticmethod
    def pattern_reversal(code: str, df=None) -> float:
        """底部反转信号 (0/1)"""
        return 1.0 if PatternFactors._check_pattern(code, '底部反转') else 0.0

    @staticmethod
    def pattern_wbottom(code: str, df=None) -> float:
        """W底信号 (0/1)"""
        return 1.0 if PatternFactors._check_pattern(code, 'W底') else 0.0

    @staticmethod
    def pattern_pullback(code: str, df=None) -> float:
        """趋势回踩信号 (0/1)"""
        return 1.0 if PatternFactors._check_pattern(code, '趋势回踩') else 0.0

    @staticmethod
    def pattern_consolidation(code: str, df=None) -> float:
        """震荡整理信号 (0/1)"""
        return 1.0 if PatternFactors._check_pattern(code, '震荡整理') else 0.0

    @staticmethod
    def pattern_mhead(code: str, df=None) -> float:
        """M头预警信号 (0/1)"""
        return 1.0 if PatternFactors._check_pattern(code, 'M头') else 0.0

    @staticmethod
    def clear_cache():
        """清空缓存"""
        PatternFactors._radar_cache = None