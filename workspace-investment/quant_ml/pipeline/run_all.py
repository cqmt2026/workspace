# -*- coding: utf-8 -*-
"""
幻方量化链路复现 — 总控脚本
一键跑通全链路：数据 → Ridge/IC → LightGBM/分层 → 多模型对比 → 滚动训练

对应视频8周计划：
  第1步：数据管道（已有）
  第2步：Ridge + IC分析 → pipeline/ridge_ic_analysis.py
  第3步：LightGBM滚动训练 → pipeline/rolling_train.py
  第4步：多模型对比 → pipeline/model_compare.py
  第5步：分层收益分析 → pipeline/layer_return_analysis.py
  第6步：完整回测（已有）

用法：
    python pipeline/run_all.py                    # 全链路
    python pipeline/run_all.py --fast             # 快速测试
    python pipeline/run_all.py --skip-ic          # 跳过IC分析
"""
import os, sys, io, time, argparse, subprocess
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def run_script(name: str, script: str, args: list = None):
    """运行脚本并计时"""
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始: {name}")
    print(f"  脚本: {script}")
    print(f"{'='*60}")

    t0 = time.time()
    cmd = [sys.executable, script]
    if args:
        cmd.extend(args)

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)

    elapsed = time.time() - t0

    # 打印输出
    if result.stdout:
        print(result.stdout[:2000])  # 只显示前2000字符
    if result.returncode != 0 and result.stderr:
        print(f"错误: {result.stderr[:1000]}")

    status = "✅" if result.returncode == 0 else "❌"
    print(f"\n{status} {name} 完成 | 耗时: {elapsed:.1f}s | 返回码: {result.returncode}")
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description='量化链路全流程')
    parser.add_argument('--fast', action='store_true', help='快速模式（小样本）')
    parser.add_argument('--skip-ic', action='store_true', help='跳过IC分析')
    parser.add_argument('--skip-compare', action='store_true', help='跳过模型对比')
    args = parser.parse_args()

    pipeline_dir = PROJECT_ROOT / 'pipeline'
    fast_args = ['--fast'] if args.fast else []

    print(f"\n{'★'*30}")
    print(f"  幻方量化链路复现 — 全流程")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  模式: {'快速' if args.fast else '完整'}")
    print(f"{'★'*30}")

    results = []

    # Step 1: Ridge IC分析
    if not args.skip_ic:
        results.append((
            'Ridge IC分析',
            run_script('Ridge IC分析', str(pipeline_dir / 'ridge_ic_analysis.py'), ['--n_lookahead', '10'])
        ))

    # Step 2: 分层收益分析
    results.append((
        '分层收益分析',
        run_script('分层收益分析', str(pipeline_dir / 'layer_return_analysis.py'), ['--n_layers', '10'] + fast_args)
    ))

    # Step 3: 多模型对比
    if not args.skip_compare:
        results.append((
            '多模型对比',
            run_script('多模型对比', str(pipeline_dir / 'model_compare.py'), fast_args)
        ))

    # Step 4: 滚动训练
    results.append((
        '滚动训练',
        run_script('滚动训练', str(pipeline_dir / 'rolling_train.py'), fast_args + ['--window', '120', '--step', '20'])
    ))

    # Step 5: 快速检验（已有LightGBM模型）
    results.append((
        '现有LightGBM评估',
        run_script('现有LightGBM', str(PROJECT_ROOT / 'main.py'), [])
    ))

    # 汇总
    print(f"\n{'='*60}")
    print(f"📊 链路执行汇总")
    print(f"{'='*60}")
    for name, ok in results:
        print(f"  {'✅' if ok else '❌'} {name}")

    n_ok = sum(1 for _, ok in results if ok)
    n_total = len(results)
    print(f"\n  通过率: {n_ok}/{n_total}")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


if __name__ == '__main__':
    main()