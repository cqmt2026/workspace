"""AliceQuant 初始化脚本

自动创建必要目录和基础数据。
"""
import os
import sys


def main():
    """初始化框架"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 50)
    print("  AliceQuant 初始化")
    print("=" * 50)

    # 创建目录
    dirs = [
        'data/raw', 'data/factors', 'data/models', 'data/results',
        'data/snapshots', 'data/paper_trading', 'data/logs',
        'reports/charts',
    ]
    for d in dirs:
        path = os.path.join(base_dir, d)
        os.makedirs(path, exist_ok=True)
        print(f"  ✅ 创建目录: {d}")

    # 检查配置文件
    config_path = os.path.join(base_dir, 'config', 'custom.yaml')
    if not os.path.exists(config_path):
        # 复制默认配置
        default_config = os.path.join(base_dir, 'config', 'default.yaml')
        if os.path.exists(default_config):
            with open(default_config, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ 创建配置文件: config/custom.yaml")
        print("  ⚠️  请修改 config/custom.yaml 中的配置")

    print("=" * 50)
    print("  初始化完成！")
    print(f"  运行示例: python examples/run_backtest.py")
    print("=" * 50)


if __name__ == '__main__':
    main()