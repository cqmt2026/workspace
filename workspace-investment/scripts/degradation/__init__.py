# -*- coding: utf-8 -*-
"""
降级模块 — 为所有关键数据源定义降级路径

核心原则（来自用户）：
> 数据是整个系统的基础，允许报错但不允许伪造或利用过时的数据来填充

降级策略只有三种合法选择：
  1. RAISE    — 报错，明确告知数据不可用，上游必须处理异常
  2. SKIP     — 跳过该步骤，不计算该部分，输出标记为"数据缺失"
  3. CACHED_TODAY_ONLY — 仅使用今天已缓存的数据（必须确认是今天产生的）

❌ 禁止的降级策略：
  - 用昨天/前天的数据假装是今天的（伪造）
  - 用历史均值填充缺失数据（伪造）
  - 静默返回None让下游自己瞎猜（隐式伪造）
"""
import os, json
from datetime import datetime, date
from typing import Optional, List, Dict, Any

WORK_DIR = r"C:\Users\Administrator\.openclaw\workspace\workspace-investment"
LOG_DIR = os.path.join(WORK_DIR, "data")
os.makedirs(LOG_DIR, exist_ok=True)
FALLBACK_LOG = os.path.join(LOG_DIR, "fallback_events.json")

class DataMissingError(Exception):
    """数据缺失异常 — 明确表示数据不可用，不伪造"""
    def __init__(self, source: str, fallback_attempts: List[str], message: str = ""):
        self.source = source
        self.fallback_attempts = fallback_attempts
        self.message = message or f"{source} 数据不可用，已尝试: {', '.join(fallback_attempts)}"
        super().__init__(self.message)


class DataFallback:
    """
    数据源降级管理器
    
    降级链格式:
    [
        {"type": "raise", "reason": "主源不可用，阻断流程"},
        {"type": "skip", "reason": "跳过该步骤"},
        {"type": "cached_today", "path": "...", "reason": "仅使用今天已缓存的数据"},
    ]
    """

    FALLBACK_CHAINS = {
        "tencent_realtime": {
            "name": "腾讯实时行情",
            "critical": True,  # 关键数据源，不允许跳过
            "fallbacks": [
                {"type": "raise", "reason": "实时行情不可用，持仓监控阻断"},
            ],
            "max_retries": 2,
            "timeout_sec": 10,
        },
        "rps_board": {
            "name": "板块RPS数据",
            "critical": False,  # 非关键，可以跳过
            "fallbacks": [
                {"type": "skip", "reason": "RPS数据不可用，跳过板块分析"},
            ],
            "max_retries": 2,
            "timeout_sec": 60,
        },
        "xinTeng_news": {
            "name": "金十快讯",
            "critical": False,
            "fallbacks": [
                {"type": "skip", "reason": "快讯不可用，跳过新闻推送"},
            ],
            "max_retries": 2,
            "timeout_sec": 15,
        },
        "mx_search": {
            "name": "妙想搜索",
            "critical": False,
            "fallbacks": [
                {"type": "skip", "reason": "MX搜索不可用，跳过舆情分析"},
            ],
            "max_retries": 1,
            "timeout_sec": 15,
        },
        "industry_funnel": {
            "name": "行业漏斗/研报",
            "critical": False,
            "fallbacks": [
                {"type": "skip", "reason": "研报生成失败，不影响其他流程"},
            ],
            "max_retries": 1,
            "timeout_sec": 30,
        },
    }

    @classmethod
    def get_chain(cls, name: str) -> Optional[Dict[str, Any]]:
        return cls.FALLBACK_CHAINS.get(name)

    @classmethod
    def handle_fallback(cls, name: str, error_msg: str = "") -> Optional[Any]:
        """
        处理数据源不可用的降级逻辑
        
        返回:
          - None: 跳过（非关键数据源）
          - 抛出 DataMissingError: 关键数据源不可用，阻断流程
        """
        chain = cls.get_chain(name)
        if not chain:
            # 未配置降级链的数据源，默认跳过
            return None

        # 记录降级事件
        cls._log_event(name, error_msg)

        if not chain.get("critical", False):
            # 非关键数据源：跳过，返回None
            return None
        else:
            # 关键数据源：报错阻断
            raise DataMissingError(
                source=chain["name"],
                fallback_attempts=[f["type"] for f in chain["fallbacks"]],
                message=error_msg or f"{chain['name']} 数据不可用"
            )

    @staticmethod
    def _log_event(source_name: str, error_msg: str):
        event = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": source_name,
            "action": "fallback",
            "detail": error_msg,
        }
        log = []
        if os.path.exists(FALLBACK_LOG):
            try:
                with open(FALLBACK_LOG, "r", encoding="utf-8") as f:
                    log = json.load(f)
            except:
                pass
        log.append(event)
        if len(log) > 200:
            log = log[-200:]
        with open(FALLBACK_LOG, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

    @classmethod
    def get_recent_events(cls, hours: int = 24) -> List[Dict]:
        """获取最近N小时的降级事件"""
        log = []
        if os.path.exists(FALLBACK_LOG):
            with open(FALLBACK_LOG, "r", encoding="utf-8") as f:
                log = json.load(f)
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=hours)
        return [e for e in log if datetime.strptime(e["timestamp"], "%Y-%m-%d %H:%M:%S") >= cutoff]
