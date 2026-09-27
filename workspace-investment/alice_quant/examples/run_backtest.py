"""回测运行示例

使用方法:
  python examples/run_backtest.py
  python examples/run_backtest.py --strategy pipeline --start 2019-01-01 --end 2024-12-31
"""
import argparse
import sys
import os

# 将项目根目录加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from alice_quant.core.config import ConfigManager
from alice_quant.core.logger import Logger


def main():
    parser = argparse.ArgumentParser(description='运行回测')
    parser.add_argument('--strategy', default='pipeline', help='策略名称')
    parser.add_argument('--start', default='2019-01-01', help='开始日期')
    parser.add_argument('--end', default='2024-12-31', help='结束日期')
    parser.add_argument('--capital', default=1000000, type=float, help='初始资金')
    args = parser.parse_args()

    # 1. 加载配置
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'custom.yaml')
    config = ConfigManager()
    config.load(config_path)

    # 2. 初始化日志
    logger = Logger(config)
    logger.info(f"回测开始", strategy=args.strategy, start=args.start, end=args.end)

    # 3. 加载策略
    logger.info(f"加载策略: {args.strategy}")

    # 4. 运行回测 (待实现)
    logger.info("回测引擎待实现 - 此示例仅验证框架初始化")

    # 5. 输出结果
    logger.info("回测完成")

    print(f"""
{'='*50}
  回测配置:
    策略: {args.strategy}
    区间: {args.start} ~ {args.end}
    资金: {args.capital:,.0f} 元
{'='*50}
  注意: 此示例仅验证框架初始化，实际回测功能待实现。
  请等待后续 Phase 完成。
{'='*50}
""")


if __name__ == '__main__':
    main()