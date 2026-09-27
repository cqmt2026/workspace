# -*- coding: utf-8 -*-
"""
Quant ML Framework - 入口脚本
用法:
    python main.py                    # 使用默认配置
    python main.py --exp my_experiment  # 自定义实验名
    python main.py --config path/to/config.yaml  # 指定配置文件
"""
import os, sys, io, argparse
from pathlib import Path

# Fix GBK encoding on Windows
if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

import yaml
from src.training import Trainer


def load_config(config_path: str = None) -> dict:
    """加载YAML配置"""
    if config_path is None:
        config_path = SCRIPT_DIR / 'configs' / 'config.yaml'
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 解析相对路径（相对于项目根目录）
    base = SCRIPT_DIR
    for key in ['data', 'model', 'training', 'evaluation', 'paths']:
        if key in config and isinstance(config[key], dict):
            for k, v in config[key].items():
                if isinstance(v, str) and v and not v.startswith('/') and ':\\' not in v:
                    # 相对路径 -> 绝对路径
                    resolved = (base / v).resolve()
                    config[key][k] = str(resolved)

    return config


def main():
    parser = argparse.ArgumentParser(description='Quant ML Framework')
    parser.add_argument('--config', '-c', default=None, help='配置文件路径')
    parser.add_argument('--exp', '-e', default=None, help='实验名称')
    parser.add_argument('--data', '-d', default=None, help='数据源pickle路径')
    args = parser.parse_args()

    config = load_config(args.config)

    # 命令行参数覆盖配置
    if args.exp:
        exp_name = args.exp
    else:
        exp_name = f"run_{int(__import__('time').time())}"

    if args.data:
        config['data']['source_pickle'] = args.data

    trainer = Trainer(config, experiment_name=exp_name)
    results = trainer.run()

    print(f"\n最终结果: AUC={results['auc']:.4f}, 评级={results['rating']}")
    return results


if __name__ == '__main__':
    main()
