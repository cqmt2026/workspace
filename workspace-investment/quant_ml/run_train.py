# -*- coding: utf-8 -*-
"""
ML训练启动器（兼容后台进程）
用法: python quant_ml/run_train.py
"""
import sys, os, subprocess, time
from pathlib import Path

WORKSPACE = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
PYTHON = sys.executable

# 日志路径
LOG_DIR = WORKSPACE / 'quant_ml' / 'logs' / 'quant_ml_v1'
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / 'train_run.log'

def main():
    print(f'[{time.strftime("%H:%M:%S")}] 启动ML训练...')
    print(f'[{time.strftime("%H:%M:%S")}] 日志: {LOG_FILE}')
    
    # 用subprocess启动（完全隔离的进程，不受exec超时影响）
    log_fd = open(LOG_FILE, 'w', encoding='utf-8', buffering=1)
    proc = subprocess.Popen(
        [PYTHON, '-u', str(WORKSPACE / 'quant_ml' / 'src' / 'training' / 'trainer.py')],
        cwd=str(WORKSPACE),
        stdout=log_fd,
        stderr=subprocess.STDOUT,
        # 不继承父进程环境
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    )
    
    print(f'[{time.strftime("%H:%M:%S")}] 进程 PID={proc.pid} 已启动')
    
    # 等待完成（最多60分钟）
    try:
        retcode = proc.wait(timeout=3600)
        log_fd.close()
        
        # 读取结果
        results_file = LOG_DIR / 'results.json'
        if results_file.exists():
            import json
            with open(results_file, encoding='utf-8') as f:
                results = json.load(f)
            print(f'[{time.strftime("%H:%M:%S")}] 训练完成!')
            print(f'  AUC={results.get("auc","N/A"):.4f}')
            print(f'  val_acc={results.get("val_acc","N/A"):.4f}')
            print(f'  rating={results.get("rating","N/A")}')
            print(f'  gap={results.get("gap","N/A"):.4f}')
        else:
            print(f'[{time.strftime("%H:%M:%S")}] 警告: results.json 未生成')
            print(f'  返回码: {retcode}')
    except subprocess.TimeoutExpired:
        proc.kill()
        log_fd.close()
        print(f'[{time.strftime("%H:%M:%S")}] 训练超时（60分钟），已终止')

if __name__ == '__main__':
    main()