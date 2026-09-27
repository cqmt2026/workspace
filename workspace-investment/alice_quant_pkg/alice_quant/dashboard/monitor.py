"""系统监控 - Cron任务/数据/性能/健康检查"""
from typing import Dict, List, Optional, Any
from datetime import datetime


class SystemMonitor:
    """系统监控器"""

    def __init__(self, config=None, logger=None):
        self._config = config
        self._logger = logger
        self._task_history: List[dict] = []
        self._health_checks: List[dict] = []

    def record_task(self, name: str, status: str, duration: float,
                    error: Optional[str] = None):
        """记录任务执行

        Args:
            name: 任务名
            status: 状态 (success/failed/timeout)
            duration: 耗时(秒)
            error: 错误信息
        """
        record = {
            'name': name,
            'status': status,
            'duration': duration,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        self._task_history.append(record)

        if status == 'failed' and self._logger:
            self._logger.error(f"任务失败: {name}", duration=duration, error=error)

    def get_task_stats(self, name: Optional[str] = None,
                       last_n: int = 100) -> dict:
        """获取任务统计"""
        tasks = self._task_history[-last_n:]
        if name:
            tasks = [t for t in tasks if t['name'] == name]

        total = len(tasks)
        failed = sum(1 for t in tasks if t['status'] == 'failed')
        avg_duration = sum(t['duration'] for t in tasks) / total if total > 0 else 0

        return {
            'total': total,
            'failed': failed,
            'success_rate': (total - failed) / total if total > 0 else 1.0,
            'avg_duration': avg_duration,
        }

    def health_check(self) -> dict:
        """健康检查

        Returns:
            健康检查报告
        """
        checks = []
        status = 'healthy'

        # 检查配置
        if self._config:
            missing = self._config.validate(['data.db_path'])
            if missing:
                checks.append({'name': 'config', 'status': 'warning', 'message': f'缺失配置: {missing}'})
            else:
                checks.append({'name': 'config', 'status': 'ok'})

        # 检查日志
        checks.append({'name': 'logger', 'status': 'ok'})

        # 综合状态
        if any(c['status'] == 'error' for c in checks):
            status = 'error'
        elif any(c['status'] == 'warning' for c in checks):
            status = 'warning'

        report = {
            'status': status,
            'checks': checks,
            'timestamp': datetime.now().isoformat()
        }
        self._health_checks.append(report)
        return report