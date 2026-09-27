#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
监控告警系统 V1.0

功能:
- 工作流异常监控
- 自动重试机制
- 告警报告生成
- 邮件/微信通知（可选）

作者：房地产自媒体团队
版本：V1.0
创建时间：2026-04-08
"""

import io
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

# 添加日志系统
sys.path.append(str(Path(__file__).parent.parent / 'bank' / '房产专业' / 'scripts'))
from logger import logger


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"           # 信息
    WARNING = "warning"     # 警告
    ERROR = "error"         # 错误
    CRITICAL = "critical"   # 严重


class MonitorSystem:
    """监控告警系统"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / 'data' / '监控数据'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.alert_log_file = self.data_dir / 'alert_log.json'
        self.config_file = Path(__file__).parent.parent / 'config' / 'monitor_config.json'
        
        # 加载配置
        self.config = self._load_config()
        
        # 告警记录
        self.alerts = []
        
        logger.info("监控告警系统 V1.0 初始化完成")
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            "retry": {
                "max_retries": 3,
                "retry_delay": 60,  # 秒
                "exponential_backoff": True
            },
            "thresholds": {
                "hotspots_min": 5,      # 最少热点数
                "topics_min": 3,        # 最少选题数
                "article_wordcount_min": 1500,  # 最少字数
                "article_wordcount_max": 4000,  # 最多字数
                "ai_score_max": 30      # AI 化最高分
            },
            "alerts": {
                "enabled": True,
                "email_enabled": False,
                "wechat_enabled": False,
                "daily_summary": True
            },
            "notifications": {
                "email": [],
                "wechat": []
            }
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        
        return default_config
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        logger.info(f"配置文件已保存：{self.config_file}")
    
    def add_alert(self, level: AlertLevel, module: str, message: str, details: Optional[Dict] = None):
        """
        添加告警
        
        Args:
            level: 告警级别
            module: 模块名称
            message: 告警消息
            details: 详细信息
        """
        alert = {
            "id": len(self.alerts) + 1,
            "level": level.value,
            "module": module,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "acknowledged": False,
            "resolved": False
        }
        
        self.alerts.append(alert)
        
        # 日志输出
        log_func = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical
        }.get(level, logger.info)
        
        log_func(f"[告警] {module}: {message}")
        
        # 严重告警立即通知
        if level == AlertLevel.CRITICAL:
            self._send_immediate_alert(alert)
    
    def _send_immediate_alert(self, alert: Dict):
        """发送紧急告警"""
        logger.critical(f"🚨 紧急告警：{alert['module']} - {alert['message']}")
        
        # TODO: 实现邮件/微信通知
        if self.config['alerts'].get('email_enabled'):
            self._send_email_alert(alert)
        
        if self.config['alerts'].get('wechat_enabled'):
            self._send_wechat_alert(alert)
    
    def _send_email_alert(self, alert: Dict):
        """发送邮件告警"""
        # TODO: 实现邮件发送
        logger.info(f"[邮件告警] {alert['message']}")
    
    def _send_wechat_alert(self, alert: Dict):
        """发送微信告警"""
        # TODO: 实现微信通知
        logger.info(f"[微信告警] {alert['message']}")
    
    def check_workflow_step(self, step_name: str, result: Dict) -> bool:
        """
        检查工作流步骤
        
        Args:
            step_name: 步骤名称
            result: 执行结果
        
        Returns:
            是否通过检查
        """
        thresholds = self.config['thresholds']
        
        if step_name == '热点采集':
            return self._check_hotspots(result, thresholds)
        elif step_name == '选题生成':
            return self._check_topics(result, thresholds)
        elif step_name == '自动创作':
            return self._check_article(result, thresholds)
        elif step_name == '质量检查':
            return self._check_quality(result, thresholds)
        elif step_name == '发布':
            return self._check_publish(result)
        else:
            return True
    
    def _check_hotspots(self, result: Dict, thresholds: Dict) -> bool:
        """检查热点采集"""
        hotspots_count = result.get('hotspots_count', 0)
        
        if hotspots_count == 0:
            self.add_alert(
                AlertLevel.CRITICAL,
                '热点采集',
                '热点采集失败，未获取到任何热点',
                {'result': result}
            )
            return False
        
        if hotspots_count < thresholds['hotspots_min']:
            self.add_alert(
                AlertLevel.WARNING,
                '热点采集',
                f'热点数量不足：{hotspots_count} < {thresholds["hotspots_min"]}',
                {'hotspots_count': hotspots_count}
            )
            return False
        
        logger.info(f"热点采集检查通过：{hotspots_count} 条")
        return True
    
    def _check_topics(self, result: Dict, thresholds: Dict) -> bool:
        """检查选题生成"""
        topics_count = result.get('topics_count', 0)
        
        if topics_count == 0:
            self.add_alert(
                AlertLevel.ERROR,
                '选题生成',
                '选题生成失败，未生成任何选题',
                {'result': result}
            )
            return False
        
        if topics_count < thresholds['topics_min']:
            self.add_alert(
                AlertLevel.WARNING,
                '选题生成',
                f'选题数量不足：{topics_count} < {thresholds["topics_min"]}',
                {'topics_count': topics_count}
            )
            return False
        
        logger.info(f"选题生成检查通过：{topics_count} 个")
        return True
    
    def _check_article(self, result: Dict, thresholds: Dict) -> bool:
        """检查文章创作"""
        word_count = result.get('word_count', 0)
        
        if word_count == 0:
            self.add_alert(
                AlertLevel.ERROR,
                '自动创作',
                '文章创作失败，字数为 0',
                {'result': result}
            )
            return False
        
        if word_count < thresholds['article_wordcount_min']:
            self.add_alert(
                AlertLevel.WARNING,
                '自动创作',
                f'文章字数不足：{word_count} < {thresholds["article_wordcount_min"]}',
                {'word_count': word_count}
            )
            return False
        
        if word_count > thresholds['article_wordcount_max']:
            self.add_alert(
                AlertLevel.INFO,
                '自动创作',
                f'文章字数过多：{word_count} > {thresholds["article_wordcount_max"]}',
                {'word_count': word_count}
            )
        
        logger.info(f"文章创作检查通过：{word_count} 字")
        return True
    
    def _check_quality(self, result: Dict, thresholds: Dict) -> bool:
        """检查质量检查"""
        passed = result.get('passed', False)
        issues = result.get('issues', [])
        
        if not passed:
            self.add_alert(
                AlertLevel.ERROR,
                '质量检查',
                f'质量检查未通过：{len(issues)} 个问题',
                {'issues': issues}
            )
            return False
        
        ai_score = result.get('ai_score', 0)
        if ai_score > thresholds['ai_score_max']:
            self.add_alert(
                AlertLevel.WARNING,
                '质量检查',
                f'AI 化程度偏高：{ai_score} > {thresholds["ai_score_max"]}',
                {'ai_score': ai_score}
            )
            return False
        
        logger.info("质量检查通过")
        return True
    
    def _check_publish(self, result: Dict) -> bool:
        """检查发布"""
        success = result.get('success', False)
        error = result.get('error')
        
        if not success:
            self.add_alert(
                AlertLevel.ERROR,
                '发布',
                f'发布失败：{error}',
                {'result': result}
            )
            return False
        
        logger.info("发布成功")
        return True
    
    def retry_with_backoff(self, func, max_retries: int = None, base_delay: int = None, *args, **kwargs):
        """
        带指数退避的重试机制
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            base_delay: 基础延迟（秒）
            *args, **kwargs: 函数参数
        
        Returns:
            函数返回值
        """
        if max_retries is None:
            max_retries = self.config['retry']['max_retries']
        if base_delay is None:
            base_delay = self.config['retry']['retry_delay']
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    # 计算延迟时间
                    if self.config['retry']['exponential_backoff']:
                        delay = base_delay * (2 ** attempt)
                    else:
                        delay = base_delay
                    
                    logger.warning(f"执行失败，{delay}秒后重试 ({attempt + 1}/{max_retries}): {e}")
                    
                    import time
                    time.sleep(delay)
                else:
                    logger.error(f"重试{max_retries}次后仍然失败：{e}")
        
        # 所有重试都失败
        self.add_alert(
            AlertLevel.CRITICAL,
            '重试机制',
            f'函数执行失败，已重试{max_retries}次',
            {'function': func.__name__, 'error': str(last_exception)}
        )
        
        raise last_exception
    
    def save_alerts(self):
        """保存告警记录"""
        # 读取现有记录
        existing_alerts = []
        if self.alert_log_file.exists():
            with open(self.alert_log_file, 'r', encoding='utf-8') as f:
                existing_alerts = json.load(f)
        
        # 合并新告警
        existing_alerts.extend(self.alerts)
        
        # 只保留最近 30 天的告警
        cutoff_date = datetime.now() - timedelta(days=30)
        existing_alerts = [
            a for a in existing_alerts
            if datetime.strptime(a['timestamp'], '%Y-%m-%d %H:%M:%S') > cutoff_date
        ]
        
        # 保存
        with open(self.alert_log_file, 'w', encoding='utf-8') as f:
            json.dump(existing_alerts, f, ensure_ascii=False, indent=2)
        
        logger.info(f"告警记录已保存：{self.alert_log_file}")
    
    def generate_daily_summary(self) -> str:
        """生成每日告警汇总"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 筛选今日告警
        today_alerts = [
            a for a in self.alerts
            if a['timestamp'].startswith(today)
        ]
        
        if not today_alerts:
            return f"# 监控日报 - {today}\n\n✅ 今日无告警\n"
        
        # 按级别统计
        stats = {
            'info': 0,
            'warning': 0,
            'error': 0,
            'critical': 0
        }
        
        for alert in today_alerts:
            stats[alert['level']] += 1
        
        report = f"""# 监控日报 - {today}

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 告警统计

| 级别 | 数量 |
|------|------|
| 🚨 严重 | {stats['critical']} |
| ❌ 错误 | {stats['error']} |
| ⚠️ 警告 | {stats['warning']} |
| ℹ️ 信息 | {stats['info']} |
| **合计** | **{len(today_alerts)}** |

---

## 📋 告警详情

"""
        
        # 按模块分组
        modules = {}
        for alert in today_alerts:
            module = alert['module']
            if module not in modules:
                modules[module] = []
            modules[module].append(alert)
        
        for module, alerts in modules.items():
            report += f"### {module}\n\n"
            for alert in alerts:
                emoji = {'critical': '🚨', 'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}.get(alert['level'], '•')
                report += f"- {emoji} [{alert['level'].upper()}] {alert['message']}\n"
                report += f"  - 时间：{alert['timestamp']}\n"
            report += "\n"
        
        report += "---\n\n*报告由监控告警系统自动生成*\n"
        
        # 保存报告
        report_file = self.data_dir / f'daily_alert_summary_{today}.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"监控日报已保存：{report_file}")
        return report
    
    def get_unresolved_alerts(self) -> List[Dict]:
        """获取未解决的告警"""
        return [a for a in self.alerts if not a['resolved']]
    
    def acknowledge_alert(self, alert_id: int):
        """确认告警"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                logger.info(f"告警 {alert_id} 已确认")
                return
        logger.warning(f"未找到告警 {alert_id}")
    
    def resolve_alert(self, alert_id: int):
        """解决告警"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['resolved'] = True
                logger.info(f"告警 {alert_id} 已解决")
                return
        logger.warning(f"未找到告警 {alert_id}")


# 全局监控实例
monitor = MonitorSystem()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='监控告警系统')
    parser.add_argument('--summary', action='store_true', help='生成每日告警汇总')
    parser.add_argument('--status', action='store_true', help='显示监控状态')
    parser.add_argument('--unresolved', action='store_true', help='显示未解决告警')
    parser.add_argument('--config', action='store_true', help='显示配置')
    
    args = parser.parse_args()
    
    if args.summary:
        report = monitor.generate_daily_summary()
        print(report)
    elif args.status:
        print("监控告警系统状态")
        print("=" * 60)
        print(f"告警记录数：{len(monitor.alerts)}")
        print(f"未解决告警：{len(monitor.get_unresolved_alerts())}")
        print(f"配置文件：{monitor.config_file.exists()}")
        print("=" * 60)
    elif args.unresolved:
        unresolved = monitor.get_unresolved_alerts()
        if unresolved:
            print("未解决的告警:")
            for alert in unresolved:
                print(f"  [{alert['level']}] {alert['module']}: {alert['message']}")
        else:
            print("✅ 无未解决告警")
    elif args.config:
        print("监控配置:")
        print(json.dumps(monitor.config, indent=2, ensure_ascii=False))
    else:
        parser.print_help()
    
    # 保存告警记录
    monitor.save_alerts()


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()
