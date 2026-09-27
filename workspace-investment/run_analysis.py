# -*- coding: utf-8 -*-
"""Walk-Forward + Optimizer CLI 入口

把回测引擎 + WalkForward + Optimizer 封装为命令行。
支持 --mode backtest|walkforward|optimize。

用法:
  python run_analysis.py --strategy pipeline --mode backtest --start 2025-01-01 --end 2025-12-31
  python run_analysis.py --strategy pipeline --mode walkforward --start 2024-01-01 --end 2025-12-31
  python run_analysis.py --strategy pipeline --mode optimize --start 2024-01-01 --end 2025-12-31 --params pct_chg_min,1,3,0.5
"""
import sys, os, argparse, json
from datetime import datetime

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK_DIR)


def main():
    parser = argparse.ArgumentParser(description='回测引擎统一入口')
    parser.add_argument('--strategy', default='pipeline', help='策略名')
    parser.add_argument('--mode', default='backtest', choices=['backtest', 'walkforward', 'optimize'], help='模式')
    parser.add_argument('--start', default='2024-01-01', help='起始日期')
    parser.add_argument('--end', default='2025-12-31', help='结束日期')
    parser.add_argument('--codes', nargs='*', help='股票池（可选）')
    parser.add_argument('--initial', type=float, default=1000000, help='初始资金')
    parser.add_argument('--params', nargs='*', help='优化参数: name,min,max,step')
    parser.add_argument('--wf-train', type=int, default=120, help='WalkForward训练窗口(天)')
    parser.add_argument('--wf-val', type=int, default=30, help='WalkForward验证窗口(天)')
    parser.add_argument('--wf-step', type=int, default=30, help='WalkForward步长(天)')
    args = parser.parse_args()

    from alice_quant.core.config import ConfigManager
    from alice_quant.core.context import Context
    from alice_quant.backtest.engine import BacktestEngine

    config = ConfigManager()
    config.load()
    engine = BacktestEngine(config=config)
    context = Context(
        watch_codes=args.codes,
        start_date=args.start,
        end_date=args.end,
    )

    # 加载策略
    if args.strategy == 'pipeline':
        from alice_quant.strategies import PipelineStrategy
        from alice_quant.features.store import FactorStore
        store = FactorStore()
        store.initialize()
        strategy = PipelineStrategy(params={}, feature_engine=store)
    else:
        print(f'未知策略: {args.strategy}')
        return

    if args.mode == 'backtest':
        print(f'开始回测: {args.strategy} @ {args.start} ~ {args.end}')
        result = engine.run(strategy, args.start, args.end, watch_codes=args.codes)
        print(result.summary())

    elif args.mode == 'walkforward':
        print(f'开始Walk-Forward: {args.strategy} @ {args.start} ~ {args.end}')
        from alice_quant.backtest.walk_forward import WalkForwardEngine, WalkForwardConfig
        wf = WalkForwardEngine(WalkForwardConfig(
            train_window=args.wf_train,
            val_window=args.wf_val,
            step_size=args.wf_step,
        ))
        wf.set_dates(context.all_dates, start=args.start, end=args.end)
        wf.set_eval_fn(lambda dates, p: engine.run(strategy, p['start'], p['end'], watch_codes=args.codes))
        result = wf.run()
        print(result.summary())

    elif args.mode == 'optimize':
        print(f'开始参数优化: {args.strategy}')
        from alice_quant.backtest.optimizer import ParameterOptimizer, ParameterGrid
        if args.params:
            params = {}
            for p in args.params:
                name, lo, hi, step = p.split(',')
                params[name] = (float(lo), float(hi), float(step))
        else:
            params = {'min_score': (40, 70, 5), 'pct_chg_min': (0.5, 3, 0.5)}
        grid = ParameterGrid(params)
        opt = ParameterOptimizer()
        opt.set_grid(grid)
        opt.set_eval_fn(lambda p: engine.run(strategy, args.start, args.end, watch_codes=args.codes, initial_capital=args.initial))
        result = opt.run()
        print(result.summary())


if __name__ == '__main__':
    main()