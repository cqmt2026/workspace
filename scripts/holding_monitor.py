#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票持仓监控脚本 - 检查持仓盈亏并推送告警

用法：
    python holding_monitor.py --holdings holdings.json
    python holding_monitor.py --holdings holdings.json --threshold 5.0
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            Path(__file__).parent.parent / 'logs' / 'holding_monitor.log',
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)

# 配置
DEFAULT_THRESHOLD = 5.0  # 默认盈亏告警阈值（%）
DEFAULT_HOLDINGS_FILE = Path(__file__).parent.parent / 'workspace-investment' / 'data' / 'holdings.json'


class HoldingMonitor:
    """持仓监控器"""
    
    def __init__(self, holdings_file: str, threshold: float = DEFAULT_THRESHOLD):
        self.holdings_file = Path(holdings_file)
        self.threshold = threshold
        self.holdings: List[Dict] = []
        self.alerts: List[Dict] = []
    
    def load_holdings(self) -> bool:
        """加载持仓数据
        
        Returns:
            bool: 是否成功加载
        """
        if not self.holdings_file.exists():
            logger.error(f"持仓文件不存在: {self.holdings_file}")
            return False
        
        try:
            with open(self.holdings_file, 'r', encoding='utf-8') as f:
                self.holdings = json.load(f)
            
            if not self.holdings:
                logger.warning("持仓列表为空")
                return False
            
            logger.info(f"加载持仓成功，共{len(self.holdings)}只股票")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"持仓文件格式错误: {e}")
            return False
        except Exception as e:
            logger.error(f"加载持仓失败: {e}")
            return False
    
    def calculate_pnl(self, holding: Dict) -> Dict:
        """计算单只股票的盈亏
        
        Args:
            holding: 持仓信息
            
        Returns:
            dict: 包含盈亏信息的字典
        """
        try:
            cost_price = float(holding.get('cost_price', 0))
            current_price = float(holding.get('current_price', 0))
            shares = int(holding.get('shares', 0))
            
            if cost_price <= 0 or current_price <= 0 or shares <= 0:
                return {
                    'code': holding.get('code', 'unknown'),
                    'error': '价格或股数无效'
                }
            
            pnl_amount = (current_price - cost_price) * shares
            pnl_percent = (current_price - cost_price) / cost_price * 100
            
            return {
                'code': holding.get('code', 'unknown'),
                'name': holding.get('name', ''),
                'cost_price': cost_price,
                'current_price': current_price,
                'shares': shares,
                'pnl_amount': pnl_amount,
                'pnl_percent': pnl_percent,
                'status': '盈利' if pnl_amount > 0 else '亏损'
            }
        except (ValueError, TypeError) as e:
            return {
                'code': holding.get('code', 'unknown'),
                'error': f'数据解析错误: {e}'
            }
    
    def check_alerts(self) -> List[Dict]:
        """检查盈亏告警
        
        Returns:
            list: 触发告警的持仓列表
        """
        self.alerts = []
        
        for holding in self.holdings:
            result = self.calculate_pnl(holding)
            
            if 'error' in result:
                logger.warning(f"{result['code']}: {result['error']}")
                continue
            
            pnl_percent = result['pnl_percent']
            
            # 触发告警条件：亏损超过阈值 或 盈利超过阈值
            if pnl_percent <= -self.threshold or pnl_percent >= self.threshold:
                result['alert_type'] = '亏损告警' if pnl_percent < 0 else '盈利告警'
                self.alerts.append(result)
                logger.info(
                    f"触发告警: {result['code']} {result['name']} "
                    f"{result['status']} {pnl_percent:.2f}%"
                )
        
        return self.alerts
    
    def generate_report(self) -> str:
        """生成监控报告
        
        Returns:
            str: 报告文本
        """
        lines = []
        lines.append("=" * 50)
        lines.append("持仓监控报告")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 50)
        lines.append("")
        
        if not self.holdings:
            lines.append("⚠️ 无持仓数据")
            return "\n".join(lines)
        
        # 汇总统计
        total_pnl = sum(
            h.get('pnl_amount', 0) for h in self.alerts
        ) if self.alerts else 0
        
        lines.append(f"持仓总数: {len(self.holdings)}只")
        lines.append(f"告警数量: {len(self.alerts)}只")
        lines.append(f"告警阈值: ±{self.threshold}%")
        lines.append("")
        
        # 告警详情
        if self.alerts:
            lines.append("【告警明细】")
            for alert in self.alerts:
                lines.append(
                    f"  {alert['code']} {alert['name']} "
                    f"{alert['status']} {alert['pnl_percent']:.2f}% "
                    f"(盈亏: {alert['pnl_amount']:.2f}元)"
                )
            lines.append("")
        
        # 全部持仓
        lines.append("【全部持仓】")
        for holding in self.holdings:
            result = self.calculate_pnl(holding)
            if 'error' not in result:
                alert_mark = " ⚠️" if result in self.alerts else ""
                lines.append(
                    f"  {result['code']} {result['name']} "
                    f"{result['status']} {result['pnl_percent']:.2f}%{alert_mark}"
                )
        
        lines.append("")
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    def send_alert(self, alerts: List[Dict]) -> bool:
        """发送告警（预留接口）
        
        Args:
            alerts: 告警列表
            
        Returns:
            bool: 是否发送成功
        """
        if not alerts:
            logger.info("无告警，无需推送")
            return True
        
        # TODO: 接入微信/Telegram推送
        logger.warning(f"告警推送功能待实现，当前仅记录日志: {len(alerts)}条告警")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="股票持仓监控脚本",
        epilog="""
示例：
  python holding_monitor.py --holdings holdings.json
  python holding_monitor.py --holdings holdings.json --threshold 3.0
  python holding_monitor.py --auto  (自动从投资系统加载持仓)
        """
    )
    parser.add_argument(
        '--holdings', '-i',
        default=str(DEFAULT_HOLDINGS_FILE),
        help='持仓文件路径 (默认: %s)' % DEFAULT_HOLDINGS_FILE
    )
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=DEFAULT_THRESHOLD,
        help='盈亏告警阈值 (默认: %s percent)' % DEFAULT_THRESHOLD
    )
    parser.add_argument(
        '--auto', '-a',
        action='store_true',
        help='自动从投资系统加载持仓'
    )
    parser.add_argument(
        '--report', '-r',
        action='store_true',
        help='输出完整报告'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='静默模式，只输出告警'
    )
    
    args = parser.parse_args()
    
    try:
        # 创建监控器
        monitor = HoldingMonitor(args.holdings, args.threshold)
        
        # 加载持仓
        if not monitor.load_holdings():
            print("[ERROR] 加载持仓失败", file=sys.stderr)
            sys.exit(1)
        
        # 检查告警
        alerts = monitor.check_alerts()
        
        # 输出结果
        if args.report:
            report = monitor.generate_report()
            print(report)
        elif not args.quiet:
            if alerts:
                print(f"⚠️ 触发告警: {len(alerts)}只")
                for alert in alerts:
                    print(
                        f"  {alert['code']} {alert['name']} "
                        f"{alert['status']} {alert['pnl_percent']:.2f}%"
                    )
            else:
                print("[OK] 无告警")
        
        # 发送告警
        if alerts and not args.quiet:
            monitor.send_alert(alerts)
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {e}", file=sys.stderr)
        logger.exception("执行异常")
        sys.exit(1)


if __name__ == '__main__':
    main()
