"""统一日志管理器

支持结构化日志（JSON格式）、多级别、多输出、告警推送。
所有模块通过此管理器写日志，统一格式和输出。
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler


class Logger:
    """统一日志管理器"""

    def __init__(self, config=None):
        self._config = config
        self._logger = logging.getLogger('alice_quant')
        self._logger.setLevel(logging.DEBUG)

        # 防止重复添加handler
        if self._logger.handlers:
            return

        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # 文件输出
        log_dir = self._get_log_dir()
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            file_handler = RotatingFileHandler(
                filename=os.path.join(log_dir, f'alice_quant_{datetime.now().strftime("%Y%m%d")}.log'),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=30,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs):
        """DEBUG级别日志"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """INFO级别日志"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """WARNING级别日志"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """ERROR级别日志"""
        self._log(logging.ERROR, message, **kwargs)
        self._push_alert('ERROR', message, **kwargs)

    def critical(self, message: str, **kwargs):
        """CRITICAL级别日志"""
        self._log(logging.CRITICAL, message, **kwargs)
        self._push_alert('CRITICAL', message, **kwargs)

    def structured_log(self, event_type: str, data: Dict[str, Any], level: str = 'info'):
        """结构化日志（JSON格式）

        Args:
            event_type: 事件类型 (backtest/trade/data_update/training/risk)
            data: 事件数据
            level: 日志级别
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'data': data
        }
        log_method = getattr(self, level.lower(), self.info)
        log_method(json.dumps(log_entry, ensure_ascii=False))

    def get_logs(self, date: Optional[str] = None,
                 level: Optional[str] = None,
                 module: Optional[str] = None) -> list:
        """查询日志（简化版，实际应用中应接入日志分析系统）

        Args:
            date: 日期 (YYYY-MM-DD)
            level: 日志级别
            module: 模块名

        Returns:
            日志条目列表
        """
        log_dir = self._get_log_dir()
        if not log_dir:
            return []

        logs = []
        log_file = os.path.join(log_dir, f'alice_quant_{date or datetime.now().strftime("%Y%m%d")}.log')
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if level and level.upper() not in line:
                        continue
                    if module and module not in line:
                        continue
                    logs.append(line)
        return logs

    def _log(self, level: int, message: str, **kwargs):
        """内部日志方法"""
        extra = ''
        if kwargs:
            extra = ' | ' + ' '.join(f'{k}={v}' for k, v in kwargs.items())
        self._logger.log(level, f"{message}{extra}")

    def _push_alert(self, level: str, message: str, **kwargs):
        """推送告警（预留，后续接入微信推送）

        Args:
            level: 告警级别
            message: 告警消息
            kwargs: 额外信息
        """
        # TODO: 接入微信推送
        # if self._config:
        #     weixin = self._config.get('alert.weixin', None)
        #     if weixin:
        #         push_to_weixin(level, message)
        pass

    def _get_log_dir(self) -> Optional[str]:
        """获取日志目录"""
        if self._config:
            log_dir = self._config.get('logger.log_dir', None)
            if log_dir:
                return log_dir
        # 默认路径
        base_dir = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base_dir, 'data', 'logs')