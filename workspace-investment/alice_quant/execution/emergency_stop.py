"""紧急停止开关"""
from typing import Optional, Callable
from ..core.exceptions import EmergencyStopError


class EmergencyStop:
    """紧急停止开关

    一键停止所有交易，支持自动触发。
    """

    def __init__(self, logger=None):
        self._logger = logger
        self._is_stopped = False
        self._stop_reason = ''
        self._handlers: list = []

    def trigger(self, reason: str = '手动触发'):
        """触发紧急停止

        Args:
            reason: 停止原因
        """
        self._is_stopped = True
        self._stop_reason = reason

        # 执行所有处理器
        for handler in self._handlers:
            try:
                handler(reason)
            except Exception as e:
                if self._logger:
                    self._logger.error(f"紧急停止处理器异常", error=str(e))

        if self._logger:
            self._logger.critical(f"紧急停止", reason=reason)

    def auto_trigger(self, condition: Callable[[], bool], reason: str):
        """自动触发

        Args:
            condition: 条件函数，返回True时触发
            reason: 触发原因
        """
        try:
            if condition():
                self.trigger(reason)
        except Exception as e:
            if self._logger:
                self._logger.error(f"自动停止检测异常", error=str(e))

    def register_handler(self, handler: Callable[[str], None]):
        """注册停止处理器

        Args:
            handler: 接收reason的回调函数
        """
        self._handlers.append(handler)

    def resume(self):
        """恢复"""
        self._is_stopped = False
        self._stop_reason = ''
        if self._logger:
            self._logger.info("紧急停止已恢复")

    @property
    def is_stopped(self) -> bool:
        return self._is_stopped

    @property
    def stop_reason(self) -> str:
        return self._stop_reason