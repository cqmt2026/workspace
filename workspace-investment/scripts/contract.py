# -*- coding: utf-8 -*-
"""
契约检查 — 启动时验证关键模块依赖完整性

设计原则：
1. 模块A依赖模块B，B不存在时A应主动报错而非静默失败
2. 每次关键脚本运行前先做契约检查
3. 契约定义在脚本顶部，便于维护

用法:
    from scripts.contract import require
    require("scripts/xxx.py", "xxx模块描述")
"""
import io
import os, sys, json, importlib
from datetime import datetime

WORK_DIR = r"C:\Users\Administrator\.openclaw\workspace\workspace-investment"
CONTRACT_LOG = os.path.join(WORK_DIR, "data", "contract_check.json")

# 定义脚本之间的依赖契约
CONTRACTS = [
    # (caller, callee, description)
    ("check_chain.py", "daily_decision_report.py", "链检查依赖日报"),
    ("check_chain.py", "daily_factor_compute.py", "链检查依赖因子计算"),
    ("check_chain.py", "daily_ic_compute.py", "链检查依赖IC计算"),
    ("check_chain.py", "si_xiang_bottom_scan.py", "链检查依赖四象共振"),
    ("close_pipeline.py", "prefilter.py", "收盘链路依赖前置过滤"),
    ("close_pipeline.py", "signal_aggregator.py", "收盘链路依赖信号聚合"),
    ("industry_research_trigger.py", "industry_funnel.py", "研报依赖漏斗筛选"),
    ("holding_alert.py", "portfolio_analysis.py", "持仓监控依赖分析模块"),
    ("strategy_scan.py", "prefilter.py", "策略扫描依赖前置过滤"),
    ("morning_brief.py", "industry_research_trigger.py", "早盘简报依赖研报"),
]

def check_all() -> list:
    """检查所有契约是否满足，返回缺失列表"""
    missing = []
    for caller, callee, desc in CONTRACTS:
        callee_path = os.path.join(WORK_DIR, "scripts", callee)
        if not os.path.exists(callee_path):
            missing.append({
                "caller": caller,
                "callee": callee,
                "description": desc,
                "status": "MISSING",
            })
    return missing

def check_module(module_name: str) -> bool:
    """检查Python模块是否可导入"""
    try:
        # 先确保脚本目录在path中
        sys.path.insert(0, WORK_DIR)
        sys.path.insert(0, os.path.join(WORK_DIR, "scripts"))
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def require(path: str, description: str = ""):
    """
    断言式检查 — 模块或文件必须存在，否则直接报错
    在脚本顶部调用
    """
    full_path = path if os.path.isabs(path) else os.path.join(WORK_DIR, path)
    if not os.path.exists(full_path):
        msg = f"❌ 契约失败: {description or path} 不存在"
        print(msg)
        raise ImportError(msg)

def log_result(missing: list):
    """记录契约检查结果"""
    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(CONTRACTS),
        "passed": len(CONTRACTS) - len(missing),
        "failed": len(missing),
        "missing": missing,
    }
    os.makedirs(os.path.dirname(CONTRACT_LOG), exist_ok=True)
    with open(CONTRACT_LOG, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result

def main():
    missing = check_all()
    result = log_result(missing)

    print(f"# 契约检查 · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"**总契约**: {result['total']} | **通过**: {result['passed']} | **失败**: {result['failed']}")
    print()
    if missing:
        print("| 调用方 | 依赖 | 说明 |")
        print("|--------|------|------|")
        for m in missing:
            print(f"| {m['caller']} | {m['callee']} | {m['description']} |")
        print("\n⚠️ **存在缺失依赖，上游脚本调用时可能失败**")
    else:
        print("✅ 全部契约满足")

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == "__main__":
    main()
