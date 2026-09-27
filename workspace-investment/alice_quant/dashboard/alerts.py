"""告警系统"""
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    level: str                      # INFO/WARNING/ALERT/CRITICAL
    condition: Callable[[], bool]   # 触发条件
    message: str                    # 告警消息
    cooldown_minutes: int = 60      # 静默期(分钟)
    auto_resolve: bool = False      # 是否自动处置


@dataclass
class AlertEvent:
    """告警事件"""
    rule_name: str
    level: str
    message: str
    triggered_at: str
    resolved: bool = False
    resolved_at: str = ''


class AlertSystem:
    """告警系统"""

    def __init__(self, logger=None):
        self._logger = logger
        self._rules: List[AlertRule] = []
        self._events: List[AlertEvent] = []
        self._last_triggered: Dict[str, datetime] = {}

    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self._rules.append(rule)

    def check(self) -> List[AlertEvent]:
        """检查所有规则"""
        triggered = []
        now = datetime.now()

        for rule in self._rules:
            # 静默期检查
            if rule.name in self._last_triggered:
                elapsed = (now - self._last_triggered[rule.name]).total_seconds()
                if elapsed < rule.cooldown_minutes * 60:
                    continue

            try:
                if rule.condition():
                    event = AlertEvent(
                        rule_name=rule.name,
                        level=rule.level,
                        message=rule.message,
                        triggered_at=now.isoformat()
                    )
                    self._events.append(event)
                    self._last_triggered[rule.name] = now
                    triggered.append(event)

                    if self._logger:
                        log_method = getattr(self._logger, rule.level.lower(), self._logger.info)
                        log_method(f"告警: {rule.message}")

            except Exception as e:
                if self._logger:
                    self._logger.error(f"告警规则检查异常", rule=rule.name, error=str(e))

        return triggered

    def get_events(self, level: Optional[str] = None,
                   limit: int = 50) -> List[AlertEvent]:
        """获取告警事件"""
        events = self._events
        if level:
            events = [e for e in events if e.level == level]
        return events[-limit:]

    def resolve(self, rule_name: str):
        """处置告警"""
        for event in reversed(self._events):
            if event.rule_name == rule_name and not event.resolved:
                event.resolved = True
                event.resolved_at = datetime.now().isoformat()
                break

    def get_statistics(self) -> dict:
        """获取告警统计"""
        total = len(self._events)
        by_level = {}
        for event in self._events:
            by_level[event.level] = by_level.get(event.level, 0) + 1
        return {
            'total': total,
            'by_level': by_level,
            'active': sum(1 for e in self._events if not e.resolved),
        }