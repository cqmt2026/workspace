#!/usr/bin/env python3
"""
AliceQuant 策略运行 CLI 入口

用法：
  # 运行回测
  python run_strategy.py --backtest --strategy pipeline --start 2026-01-01 --end 2026-06-30

  # 运行实盘信号
  python run_strategy.py --live --strategy pipeline --date 2026-07-13

  # 列出可用策略
  python run_strategy.py --list

  # 快速验证
  python run_strategy.py --validate
"""
import sys, os, argparse, json
from datetime import datetime
from typing import Optional

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK_DIR)


def list_strategies():
    """列出所有可用策略"""
    from alice_quant.strategies import PipelineStrategy, TrendStrategy, DaBanStrategy, \
        MagicFormulaStrategy, MultiFactorStrategy, PortfolioManager
    strategies = [
        ('pipeline', PipelineStrategy, 'Pipeline v2 多因子评分策略'),
        ('trend', TrendStrategy, '趋势跟踪策略'),
        ('daban', DaBanStrategy, '涨停板策略'),
        ('magic_formula', MagicFormulaStrategy, '神奇公式策略'),
        ('multifactor', MultiFactorStrategy, '多因子策略'),
        ('portfolio', PortfolioManager, '组合管理策略'),
    ]
    print('可用的策略:')
    for name, cls, desc in strategies:
        print(f'  {name:20s} {desc}')


def run_backtest(strategy_name: str, start_date: str, end_date: str,
                 codes: Optional[list] = None, params: Optional[dict] = None):
    """运行回测"""
    from alice_quant.backtest.engine import BacktestEngine
    from alice_quant.core.context import Context
    from alice_quant.core.config import ConfigManager

    print(f'开始回测: {strategy_name} @ {start_date} ~ {end_date}')

    config = ConfigManager()
    config.load()
    engine = BacktestEngine(config=config)
    context = Context(
        start_date=start_date,
        end_date=end_date,
        watch_codes=codes or [],
        is_backtesting=True,
    )

    # 选择策略
    if strategy_name == 'pipeline':
        from alice_quant.strategies import PipelineStrategy
        from alice_quant.features.store import FactorStore
        store = FactorStore()
        store.initialize()
        strategy = PipelineStrategy(params=params or {}, feature_engine=store)
    else:
        print(f'策略 {strategy_name} 尚未实现回测入口')
        return

    result = engine.run(strategy, start_date, end_date, watch_codes=context.watch_codes)
    print(result.summary())

    # 保存报告
    report_path = os.path.join(WORK_DIR, 'out_data',
                               f'backtest_{strategy_name}_{start_date}_{end_date}.html')
    result.save_report(report_path)
    print(f'报告已保存: {report_path}')


def run_live(strategy_name: str, date: str, codes: Optional[list] = None):
    """运行实盘信号"""
    from alice_quant.strategies import PipelineStrategy
    from alice_quant.features.store import FactorStore
    from scripts.data_api import DataAPI

    print(f'生成实盘信号: {strategy_name} @ {date}')

    if strategy_name == 'pipeline':
        strategy = PipelineStrategy()
        store = FactorStore()
        store.initialize()
        strategy.set_feature_store(store)

        signals = strategy.generate_signals(date, codes=codes)
        if signals:
            print(f'信号: {len(signals)} 个')
            for sig in signals[:10]:
                print(f'  {sig}')
        else:
            print('今日无信号')
    else:
        print(f'策略 {strategy_name} 尚未实现实盘入口')


def main():
    parser = argparse.ArgumentParser(description='AliceQuant 策略运行器')
    parser.add_argument('--backtest', action='store_true', help='运行回测')
    parser.add_argument('--live', action='store_true', help='运行实盘信号')
    parser.add_argument('--list', action='store_true', help='列出可用策略')
    parser.add_argument('--validate', action='store_true', help='验证环境')
    parser.add_argument('--strategy', default='pipeline', help='策略名称')
    parser.add_argument('--start', default='', help='回测开始日期')
    parser.add_argument('--end', default='', help='回测结束日期')
    parser.add_argument('--date', default='', help='信号日期')
    parser.add_argument('--codes', nargs='*', help='股票代码列表')
    parser.add_argument('--params', default='{}', help='策略参数 (JSON)')

    args = parser.parse_args()

    if args.list:
        list_strategies()
        return

    if args.validate:
        print(f'AliceQuant 环境验证 @ {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        try:
            from alice_quant.core.context import Context
            ctx = Context()
            _ = ctx.get_trading_day_count()
            print('[OK] 环境验证通过')
        except Exception as e:
            print(f'[FAIL] 初始化失败: {e}')
        return

    if args.backtest:
        if not args.start or not args.end:
            print('回测需要 --start 和 --end 参数')
            return
        codes = args.codes or None
        params = json.loads(args.params) if args.params else None
        run_backtest(args.strategy, args.start, args.end, codes, params)
        return

    if args.live:
        date = args.date or datetime.now().strftime('%Y-%m-%d')
        run_live(args.strategy, date, args.codes)
        return

    parser.print_help()


if __name__ == '__main__':
    main()