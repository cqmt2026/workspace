# -*- coding: utf-8 -*-
"""
ML预测结果→factors.db 桥接脚本

从 ml_latest_prob.pkl（全市场预测）读取概率，写入 factors.db 的 ml_prob_lgb 因子。
20:00 ML训练完成后自动执行（由 Cron 触发 run_ml_predict.py 后调用此脚本）。
"""
import io
import sys, os, sqlite3, pickle
from datetime import datetime

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(WORK_DIR))

FACTORS_DB = os.path.join(WORK_DIR, 'data', 'factors.db')
# 全市场预测文件（训练器输出）
ML_PROB_PATH = os.path.join(WORK_DIR, 'ml_latest_prob.pkl')
# 持仓预测文件（run_ml_predict.py 输出）
HOLDINGS_PROB_PATH = os.path.join(WORK_DIR, 'ml_holdings_prob.pkl')


def write_ml_factors(prob_dict: dict, date: str, source: str = 'lgbm_unified'):
    """将ML概率写入factors.db

    Args:
        prob_dict: {code: prob} 格式
        date: 日期 (YYYY-MM-DD)
        source: 模型来源标识
    """
    if not prob_dict:
        print(f'  [ML桥接] 无数据，跳过')
        return 0

    factor_name = 'ml_prob_lgb'
    os.makedirs(os.path.dirname(FACTORS_DB), exist_ok=True)
    conn = sqlite3.connect(FACTORS_DB, timeout=30)
    conn.execute("""CREATE TABLE IF NOT EXISTS factors (
        date TEXT, code TEXT, factor_name TEXT, value REAL,
        updated_at TEXT DEFAULT (datetime('now')),
        PRIMARY KEY (date, code, factor_name)
    )""")

    n = 0
    cursor = conn.cursor()
    for code, prob in prob_dict.items():
        if not isinstance(prob, (int, float)) or prob < 0 or prob > 1:
            continue
        # code 标准化：确保 factors.db 中格式统一
        std_code = code
        if '.' not in std_code and std_code.isdigit():
            if std_code.startswith('6') or std_code.startswith('688'):
                std_code = f'sh.{std_code}'
            elif std_code.startswith('3') or std_code.startswith('0'):
                std_code = f'sz.{std_code}'
            else:
                continue  # 无法识别，跳过

        try:
            cursor.execute(
                "INSERT OR REPLACE INTO factors VALUES (?,?,?,?,datetime('now'))",
                (date, std_code, factor_name, round(prob, 4))
            )
            n += 1
        except Exception:
            pass

    conn.commit()
    conn.close()
    print(f'  [ML桥接] 写入 {n} 条 {factor_name} 因子（来源: {source}）')
    return n


def main():
    """主入口"""
    today = datetime.now().strftime('%Y-%m-%d')

    print(f'=== ML预测→factors.db 桥接 @ {today} ===')

    total = 0

    # 1. 全市场预测（优先）
    if os.path.exists(ML_PROB_PATH):
        try:
            with open(ML_PROB_PATH, 'rb') as f:
                data = pickle.load(f)
            if isinstance(data, dict):
                total += write_ml_factors(data, today, 'lgbm_unified')
            elif isinstance(data, list):
                # unified_train 可能输出 list of tuples
                prob_dict = {}
                for item in data:
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        prob_dict[str(item[0])] = float(item[1])
                total += write_ml_factors(prob_dict, today, 'lgbm_unified')
            print(f'  全市场: {len(data) if isinstance(data, dict) else len(data)} 只')
        except Exception as e:
            print(f'  [WARN] 全市场预测加载失败: {e}')
    else:
        print(f'  [INFO] 全市场预测文件不存在: {ML_PROB_PATH}')

    # 2. 持仓预测（补充）
    if os.path.exists(HOLDINGS_PROB_PATH):
        try:
            with open(HOLDINGS_PROB_PATH, 'rb') as f:
                data = pickle.load(f)
            if isinstance(data, dict):
                total += write_ml_factors(data, today, 'holdings')
                print(f'  持仓: {len(data)} 只')
        except Exception as e:
            print(f'  [WARN] 持仓预测加载失败: {e}')

    print(f'  [ML桥接] 合计写入 {total} 条')


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()