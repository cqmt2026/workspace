#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
商业航天每日分析报告
====================
功能：
1. 商业航天板块行情概览（板块指数、涨跌幅、成交额）
2. 商业航天概念股涨跌停分析
3. 商业航天板块主力资金流向
4. 商业航天相关新闻与政策搜索
5. 重点公司基本面与财务数据摘要
6. 生成日报报告并保存到 out_data
"""

import io
import sys
import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ---------- 路径设置 ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUT_DIR = os.path.join(WORKSPACE, "out_data")
os.makedirs(OUT_DIR, exist_ok=True)

# 添加路径
sys.path.insert(0, os.path.join(WORKSPACE, "scripts"))
sys.path.insert(0, WORKSPACE)

try:
    import akshare as ak
except ImportError:
    ak = None

# 东方财富妙想脚本路径
MX_SEARCH_PY = os.path.join(
    os.environ.get("NPM_PREFIX", r"C:\Users\Administrator\AppData\Roaming\npm"),
    "node_modules", "openclaw", "skills", "mx-search", "mx_search.py"
)
MX_DATA_PY = os.path.join(
    os.environ.get("NPM_PREFIX", r"C:\Users\Administrator\AppData\Roaming\npm"),
    "node_modules", "openclaw", "skills", "mx-data", "mx_data.py"
)

# 商业航天板块相关股票代码（A股主要标的）
AERO_STOCKS = [
    ("300343", "联创电子"),
    ("300009", "安科瑞"),
    ("688543", "天智航"),
    ("688066", "航天长峰"),
    ("002413", "雷科防务"),
    ("600862", "南通科技"),
    ("000738", "航发控制"),
    ("600760", "中航沈飞"),
    ("002179", "中航光电"),
    ("601989", "中国重工"),
    ("000768", "中航西飞"),
    ("600893", "航发动力"),
    ("688599", "天海防务"),
    ("300699", "光威复材"),
    ("002421", "宏达国际电子"),
    ("688122", "西部超导"),
    ("688002", "睿创微纳"),
    ("300627", "华测导航"),
    ("688048", "长光华芯"),
    ("688137", "近岸蛋白质"),
    ("002985", "拓荆科技"),
    ("688361", "中科飞测"),
    ("688072", "拓普集团"),
    ("002049", "紫光国微"),
    ("688256", "寒武纪"),
    ("300123", " Sundray 太阳鸟"),
    ("688385", "复旦微电"),
    ("002180", "纳思达"),
    ("688172", "双乐股份"),
    ("688279", "峰岹科技"),
]

# 商业航天核心概念标签
AERO_KEYWORDS = ["商业航天", "卫星互联网", "火箭发射", "低轨卫星", "北斗导航", "航天科技", "航天科工"]


def get_trading_date():
    """获取最近交易日"""
    today = datetime.now()
    for i in range(10):
        d = today - timedelta(days=i)
        if d.weekday() < 5:
            return d.strftime("%Y%m%d")
    return today.strftime("%Y%m%d")


def run_mx_search(query, output_dir=None):
    """运行 mx-search 获取资讯"""
    if not os.path.exists(MX_SEARCH_PY):
        print(f"[WARN] mx_search.py not found: {MX_SEARCH_PY}")
        return None
    cmd = [sys.executable, MX_SEARCH_PY, query]
    if output_dir:
        cmd.append(output_dir)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                                encoding="utf-8", errors="replace")
        return result.stdout
    except Exception as e:
        print(f"[WARN] mx_search failed: {e}")
        return None


def run_mx_data(query, output_dir=None):
    """运行 mx-data 获取金融数据"""
    if not os.path.exists(MX_DATA_PY):
        print(f"[WARN] mx_data.py not found: {MX_DATA_PY}")
        return None
    cmd = [sys.executable, MX_DATA_PY, query]
    if output_dir:
        cmd.append(output_dir)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                                encoding="utf-8", errors="replace")
        return result.stdout
    except Exception as e:
        print(f"[WARN] mx_data failed: {e}")
        return None


def get_sector_data():
    """获取商业航天板块行情数据"""
    print("\n" + "=" * 60)
    print("[1] 商业航天板块行情概览")
    print("=" * 60)

    trading_date = get_trading_date()

    # 尝试获取行业板块涨幅排名
    try:
        if ak:
            # 行业板块实时行情
            industry_df = ak.stock_board_industry_name_em()
            if industry_df is not None and not industry_df.empty:
                aero_rows = industry_df[
                    industry_df['板块名称'].str.contains('航天|卫星|火箭|北斗', na=False)
                ]
                if not aero_rows.empty:
                    print(f"\n发现相关板块 ({len(aero_rows)} 个):")
                    for _, row in aero_rows.iterrows():
                        name = row.get('板块名称', '')
                        change = row.get('涨跌幅', '')
                        volume = row.get('成交额', '')
                        turnover = row.get('换手率', '')
                        print(f"  {name}: 涨跌幅={change}% | 成交额={volume} | 换手率={turnover}%")
    except Exception as e:
        print(f"[INFO] 板块数据获取: {e}")

    # 获取概念板块
    try:
        if ak:
            concept_df = ak.stock_board_concept_name_em()
            if concept_df is not None and not concept_df.empty:
                aero_concepts = concept_df[
                    concept_df['板块名称'].str.contains('航天|卫星|火箭|北斗|低轨|商业航天', na=False)
                ]
                if not aero_concepts.empty:
                    print(f"\n概念板块 ({len(aero_concepts)} 个):")
                    for _, row in aero_concepts.iterrows():
                        name = row.get('板块名称', '')
                        change = row.get('涨跌幅', '')
                        volume = row.get('成交额', '')
                        turnover = row.get('换手率', '')
                        leader = row.get('领涨股票', '')
                        leader_change = row.get('领涨-涨跌幅', '')
                        print(f"  {name}: 涨跌幅={change}% | 成交额={volume} | 领涨={leader}({leader_change}%)")
    except Exception as e:
        print(f"[INFO] 概念板块数据获取: {e}")

    # 涨停分析
    try:
        if ak:
            zt_df = ak.stock_zt_pool_em(date=trading_date)
            if zt_df is not None and not zt_df.empty:
                aero_zt = zt_df[zt_df['名称'].apply(
                    lambda x: any(kw in str(x) for kw in ['航天', '卫星', '火箭', '北斗'])
                )]
                if not aero_zt.empty:
                    print(f"\n商业航天涨停股 ({len(aero_zt)} 家):")
                    for _, row in aero_zt.iterrows():
                        print(f"  {row['名称']} ({row.get('代码', '')}): {row.get('涨跌幅', '')}%")
                else:
                    print("\n商业航天今日无涨停股")
    except Exception as e:
        print(f"[INFO] 涨停数据: {e}")

    # 跌停分析
    try:
        if ak:
            dt_df = ak.stock_zt_pool_dtgc_em(date=trading_date)
            if dt_df is not None and not dt_df.empty:
                aero_dt = dt_df[dt_df['名称'].apply(
                    lambda x: any(kw in str(x) for kw in ['航天', '卫星', '火箭', '北斗'])
                )]
                if not aero_dt.empty:
                    print(f"\n商业航天跌停股 ({len(aero_dt)} 家):")
                    for _, row in aero_dt.iterrows():
                        print(f"  {row['名称']} ({row.get('代码', '')}): {row.get('涨跌幅', '')}%")
                else:
                    print("\n商业航天今日无跌停股")
    except Exception as e:
        print(f"[INFO] 跌停数据: {e}")


def get_main_flow():
    """获取主力资金流向"""
    print("\n" + "=" * 60)
    print("[2] 商业航天概念股主力资金流向")
    print("=" * 60)

    core_stocks = [
        ("000768", "中航西飞"),
        ("600893", "航发动力"),
        ("600760", "中航沈飞"),
        ("002179", "中航光电"),
        ("688543", "天智航"),
        ("688066", "航天长峰"),
        ("002413", "雷科防务"),
        ("688122", "西部超导"),
        ("300699", "光威复材"),
        ("688002", "睿创微纳"),
    ]

    for code, name in core_stocks[:5]:
        try:
            if ak:
                flow = ak.stock_individual_fund_flow(stock=name, market="sh")
                if flow is not None and not flow.empty:
                    latest = flow.iloc[-1]
                    print(f"\n{name}({code}) 主力流向:")
                    for col in ['日期', '主力净流入-净额', '主力净流入-净占比',
                                '超大单净流入-净额', '大单净流入-净额']:
                        if col in latest.index:
                            print(f"  {col}: {latest[col]}")
        except Exception as e:
            print(f"[INFO] {name} 资金流向: {e}")


def get_stock_quotes():
    """获取重点股票实时行情"""
    print("\n" + "=" * 60)
    print("[3] 重点股票实时行情")
    print("=" * 60)

    stocks = [
        "000768", "600893", "600760", "002179", "688122",
        "300699", "688002", "688543", "002413", "600862"
    ]

    for code in stocks:
        try:
            if ak:
                df = ak.stock_zh_a_spot_em()
                if df is not None and not df.empty:
                    row = df[df['代码'] == code]
                    if not row.empty:
                        r = row.iloc[0]
                        print(f"  {r['名称']}({code}): 最新价={r.get('最新价','')} | "
                              f"涨跌幅={r.get('涨跌幅','')}% | "
                              f"成交额={r.get('成交额','')}")
        except Exception as e:
            print(f"[INFO] {code} 行情获取: {e}")


def fetch_news():
    """搜索商业航天相关新闻"""
    print("\n" + "=" * 60)
    print("[4] 商业航天新闻与政策")
    print("=" * 60)

    for kw in AERO_KEYWORDS[:4]:
        print(f"\n--- 搜索: {kw} ---")
        output = run_mx_search(f"{kw} 最新新闻 政策", OUT_DIR)
        if output:
            lines = output.strip().split('\n')
            for line in lines[:15]:
                print(f"  {line}")
        else:
            print("  [无法获取资讯]")

    # 补充网络搜索
    try:
        from web_search import web_search as ws
        for kw in AERO_KEYWORDS[:2]:
            print(f"\n--- 网络搜索: {kw} ---")
            results = ws(query=f"{kw} 商业航天 最新消息 2026", count=5)
            if results:
                for item in results[:3]:
                    title = item.get('title', '')
                    snippet = item.get('snippet', '')
                    print(f"  [{title}]")
                    print(f"    {snippet[:100]}...")
    except Exception as e:
        print(f"[INFO] 网络搜索不可用: {e}")


def fetch_financials():
    """获取重点公司财务数据"""
    print("\n" + "=" * 60)
    print("[5] 重点公司财务摘要")
    print("=" * 60)

    financial_queries = [
        "中航西飞 净利润 营收 最新财报",
        "航发动力 净利润 营收 最新财报",
        "中航沈飞 净利润 营收 最新财报",
        "西部超导 净利润 营收 最新财报",
        "光威复材 净利润 营收 最新财报",
    ]

    for q in financial_queries:
        print(f"\n--- {q} ---")
        output = run_mx_data(q, OUT_DIR)
        if output:
            lines = output.strip().split('\n')
            for line in lines[:10]:
                print(f"  {line}")
        else:
            print("  [无法获取财务数据]")


def generate_report():
    """生成最终报告"""
    print("\n" + "=" * 60)
    print("[6] 报告生成")
    print("=" * 60)

    trading_date = get_trading_date()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report_date = datetime.now().strftime("%Y年%m月%d日")

    report_lines = [
        f"{'='*60}",
        f"商业航天每日分析报告",
        f"报告时间: {report_date} {now}",
        f"交易日期: {trading_date}",
        f"{'='*60}",
        "",
        "一、板块行情概览",
        "  - 请查看上方板块数据",
        "",
        "二、主力资金流向",
        "  - 请查看上方资金流向数据",
        "",
        "三、重点股票行情",
        "  - 请查看上方行情数据",
        "",
        "四、新闻与政策",
        "  - 请查看上方新闻数据",
        "",
        "五、财务摘要",
        "  - 请查看上方财务数据",
        "",
        f"{'='*60}",
        "免责声明: 本报告由自动化工具生成，仅供参考，不构成投资建议。",
        f"生成时间: {now}",
        f"{'='*60}",
    ]

    report_text = '\n'.join(report_lines)

    out_file = os.path.join(OUT_DIR, f"aero_daily_{trading_date}.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\n[保存] {out_file}")
    print(report_text)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print(f"商业航天每日分析报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目录: {WORKSPACE}")

    try:
        get_sector_data()
    except Exception as e:
        print(f"[ERROR] 板块数据: {e}")

    try:
        get_main_flow()
    except Exception as e:
        print(f"[ERROR] 资金流向: {e}")

    try:
        get_stock_quotes()
    except Exception as e:
        print(f"[ERROR] 行情数据: {e}")

    try:
        fetch_news()
    except Exception as e:
        print(f"[ERROR] 新闻搜索: {e}")

    try:
        fetch_financials()
    except Exception as e:
        print(f"[ERROR] 财务数据: {e}")

    try:
        generate_report()
    except Exception as e:
        print(f"[ERROR] 报告生成: {e}")

    print("\n[完成] 商业航天每日分析报告执行完毕")


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()
