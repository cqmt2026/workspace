"""
路径配置模块 - 所有子系统路径统一管理
版本: V1.0
最后更新: 2026-06-07

使用方式:
  from path_config import WORKSPACE_MATH, WORKSPACE_INVESTMENT, ...

所有路径必须通过本模块引用，禁止硬编码
"""

import os
import io

# ========== 根目录 ==========
ROOT = r"C:\Users\Administrator\.openclaw\workspace"

# ========== 主工作目录 ==========
WORKSPACE = ROOT

# ========== 子系统目录 ==========
WORKSPACE_NOVEL = os.path.join(WORKSPACE, "workspace-novel")
WORKSPACE_INVESTMENT = os.path.join(WORKSPACE, "workspace-investment")
WORKSPACE_SOCIAL = os.path.join(WORKSPACE, "workspace-social")
WORKSPACE_MATH = os.path.join(WORKSPACE, "workspace-math")
WORKSPACE_WEIXIN = os.path.join(WORKSPACE, "workspace-weixin")

# ========== 投资子系统关键路径 ==========
INVESTMENT_DATA = os.path.join(WORKSPACE_INVESTMENT, "data")
INVESTMENT_SCRIPTS = os.path.join(WORKSPACE_INVESTMENT, "scripts")
INVESTMENT_MODELS = os.path.join(WORKSPACE_INVESTMENT, "models")
INVESTMENT_OUTPUTS = os.path.join(WORKSPACE_INVESTMENT, "outputs")
INVESTMENT_KB = os.path.join(WORKSPACE_INVESTMENT, "memory", "L2-核心", "知识库")

# 数据库（注意：是workspace\workspace-investment\data，不是workspace-investment\data）
MARKET_DB = os.path.join(WORKSPACE_INVESTMENT, "data", "market_data.db")
FINANCIAL_DATA = os.path.join(WORKSPACE_INVESTMENT, "data", "financial")

# ========== 数学动画子系统关键路径 ==========
MATH_PRODUCTION = os.path.join(WORKSPACE_MATH, "production")
MATH_MEDIA = os.path.join(WORKSPACE_MATH, "media")
MATH_AUDIO = os.path.join(WORKSPACE_MATH, "L3-音频")
MATH_VIDEOS = os.path.join(WORKSPACE_MATH, "media", "videos")
MATH_SCRIPTS = os.path.join(WORKSPACE_MATH, "scripts")
MATH_OUTPUT = os.path.join(WORKSPACE_MATH, "output")  # 成品输出

# ========== 小说子系统关键路径 ==========
NOVEL_PROJECT = os.path.join(WORKSPACE_NOVEL, "项目三：都市重生")
NOVEL_KB = os.path.join(WORKSPACE_NOVEL, "创作系统", "L2-工具", "03-知识库")

# ========== 验证函数 ==========
def verify_paths():
    """验证所有关键路径是否存在，返回缺失的路径列表"""
    paths = {
        "ROOT": ROOT,
        "WORKSPACE_MATH": WORKSPACE_MATH,
        "WORKSPACE_INVESTMENT": WORKSPACE_INVESTMENT,
        "WORKSPACE_NOVEL": WORKSPACE_NOVEL,
        "WORKSPACE_SOCIAL": WORKSPACE_SOCIAL,
        "MARKET_DB": MARKET_DB,
        "FINANCIAL_DATA": FINANCIAL_DATA,
    }
    missing = []
    for name, path in paths.items():
        if not os.path.exists(path):
            missing.append(f"{name}: {path}")
    return missing

def get_workspace_math_output(subdir=""):
    """获取数学动画成品路径"""
    if subdir:
        return os.path.join(MATH_OUTPUT, subdir)
    return MATH_OUTPUT

def get_investment_db():
    """获取投资数据库路径（带验证）"""
    if not os.path.exists(MARKET_DB):
        raise FileNotFoundError(f"数据库不存在: {MARKET_DB}")
    return MARKET_DB

# ========== 测试 ==========
if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print("=" * 50)
    print("Path Config Verification")
    print("=" * 50)
    missing = verify_paths()
    if missing:
        print("Missing paths:")
        for m in missing:
            print(f"  [ERROR] {m}")
    else:
        print("[OK] All paths verified")
    print("=" * 50)