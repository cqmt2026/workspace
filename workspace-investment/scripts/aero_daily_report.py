#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
商业航天每日分析报告 - 优化版
=============================
优化点：
1. 单次获取全市场行情，避免重复调用
2. 修正资金流向 market 参数
3. 并行新闻搜索减少等待时间
4. 增加超时时间到 600s
5. 实时打印进度，便于排查
"""

import io
import sys
import os
import json
import subprocess
import concurrent.futures
from datetime import datetime, timedelta
from pathlib import Path

# ---------- 路径设置 ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(os.path.dirname(SCRIPT_DIR))
OUT_DIR = os.path.join(WORKSPACE, "out_data")
os.makedirs(OUT_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(WORKSPACE, "scripts"))
sys.path.insert(0, WORKSPACE)

try:
    import akshare as ak
except ImportError:
    ak = None

MX_SEARCH_PY = os.path.join(
    os.environ.get("NPM_PREFIX", r"C:\Users\Administrator\AppData\Roaming\npm"),
    "node_modules", "openclaw", "skills", "mx-search", "mx_search.py"
)
MX_DATA_PY = os.path.join(
    os.environ.get("NPM_PREFIX", r"C:\Users\Administrator\AppData\Roaming\npm"),
    "node_modules", "openclaw", "skills", "mx-data", "mx_data.py"
)

# 商业航天核心股票（精简版，只保留核心标的）
AERO_CORE_STOCKS = [
    ("000768", "中航西飞"),
    ("600893", "航发动力"),
    ("600760", "中航沈飞"),
    ("002179", "中航光电"),
    ("688122", "西部超导"),
    ("300699", "光威复材"),
    ("688002", "睿创微纳"),
    ("600118", "中国卫星"),
    ("600879", "航天电子"),
    ("688543", "天智航"),
]

AERO_KEYWORDS = ["商业航天", "卫星互联网", "火箭发射", "低轨卫星"]


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
        print(f"[WARN] mx_search.py not found")
        return None
    cmd = [sys.executable, MX_SEARCH_PY, query]
    if output_dir:
        cmd.append(output_dir)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45,
                                encoding="utf-8", errors="replace")
        return result.stdout
    except Exception as e:
        print(f"[WARN] mx_search failed: {e}")
        return None


def run_mx_data(query, output_dir=None):
    """运行 mx-data 获取金融数据"""
    if not os.path.exists(MX_DATA_PY):
        print(f"[WARN] mx_data.py not found")
        return None
    cmd = [sys.executable, MX_DATA_PY, query]
    if output_dir:
        cmd.append(output_dir)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45,
                                encoding="utf-8", errors="replace")
        return result.stdout
    except Exception as e:
        print(f"[WARN] mx_data failed: {e}")
        return None


def get_market_data():
    """获取全市场行情数据（一次性获取）"""
    print("\n[1] 获取全市场行情...")
    if not ak:
        print("  [SKIP] akshare未安装")
        return None
    try:
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            print(f"  [OK] 获取到 {len(df)} 只股票行情")
            return df
    except Exception as e:
        print(f"  [ERROR] {e}")
    return None


def get_sector_data(market_df):
    """从行情数据中提取商业航天板块数据"""
    print("\n" + "=" * 60)
    print("[2] 商业航天板块行情概览")
    print("=" * 60)

    trading_date = get_trading_date()
    keywords = ['航天', '卫星', '火箭', '北斗']

    # 行业板块
    try:
        if ak:
            industry_df = ak.stock_board_industry_name_em()
            if industry_df is not None and not industry_df.empty:
                aero_ind = industry_df[
                    industry_df['板块名称'].str.contains('航天|卫星|火箭|北斗', na=False)
                ]
                if not aero_ind.empty:
                    print(f"\n行业板块 ({len(aero_ind)} 个):")
                    for _, row in aero_ind.iterrows():
                        print(f"  {row.get('板块名称','')}: 涨跌幅={row.get('涨跌幅','')}% | 成交额={row.get('成交额','')}")
    except Exception as e:
        print(f"  [INFO] 行业板块: {e}")

    # 概念板块
    try:
        if ak:
            concept_df = ak.stock_board_concept_name_em()
            if concept_df is not None and not concept_df.empty:
                aero_conc = concept_df[
                    concept_df['板块名称'].str.contains('航天|卫星|火箭|北斗|低轨|商业航天', na=False)
                ]
                if not aero_conc.empty:
                    print(f"\n概念板块 ({len(aero_conc)} 个):")
                    for _, row in aero_conc.iterrows():
                        print(f"  {row.get('板块名称','')}: 涨跌幅={row.get('涨跌幅','')}% | 领涨={row.get('领涨股票','')}")
    except Exception as e:
        print(f"  [INFO] 概念板块: {e}")

    # 从全市场行情中提取商业航天股票
    if market_df is not None:
        mask = market_df['名称'].apply(
            lambda x: any(kw in str(x) for kw in keywords)
        )
        aero_stocks = market_df[mask]
        if not aero_stocks.empty:
            print(f"\n商业航天概念股 ({len(aero_stocks)} 只):")
            for _, row in aero_stocks.iterrows():
                print(f"  {row.get('名称','')}({row.get('代码','')}): "
                      f"最新价={row.get('最新价','')} | "
                      f"涨跌幅={row.get('涨跌幅','')}% | "
                      f"成交额={row.get('成交额','')}")

    # 涨停分析
    try:
        if ak:
            zt_df = ak.stock_zt_pool_em(date=trading_date)
            if zt_df is not None and not zt_df.empty:
                aero_zt = zt_df[zt_df['名称'].apply(
                    lambda x: any(kw in str(x) for kw in keywords)
                )]
                if not aero_zt.empty:
                    print(f"\n商业航天涨停股 ({len(aero_zt)} 家):")
                    for _, row in aero_zt.iterrows():
                        print(f"  {row.get('名称','')}({row.get('代码','')}): {row.get('涨跌幅','')}%")
                else:
                    print("\n商业航天今日无涨停股")
    except Exception as e:
        print(f"  [INFO] 涨停数据: {e}")

    # 跌停分析
    try:
        if ak:
            dt_df = ak.stock_zt_pool_dtgc_em(date=trading_date)
            if dt_df is not None and not dt_df.empty:
                aero_dt = dt_df[dt_df['名称'].apply(
                    lambda x: any(kw in str(x) for kw in keywords)
                )]
                if not aero_dt.empty:
                    print(f"\n商业航天跌停股 ({len(aero_dt)} 家):")
                    for _, row in aero_dt.iterrows():
                        print(f"  {row.get('名称','')}({row.get('代码','')}): {row.get('涨跌幅','')}%")
                else:
                    print("\n商业航天今日无跌停股")
    except Exception as e:
        print(f"  [INFO] 跌停数据: {e}")


def get_stock_quotes(market_df):
    """获取重点股票行情"""
    print("\n" + "=" * 60)
    print("[3] 重点股票行情")
    print("=" * 60)

    if market_df is None:
        print("  [SKIP] 无行情数据")
        return

    for code, name in AERO_CORE_STOCKS:
        try:
            row = market_df[market_df['代码'] == code]
            if not row.empty:
                r = row.iloc[0]
                print(f"  {r.get('名称','')}( {code}): 最新价={r.get('最新价','')} | "
                      f"涨跌幅={r.get('涨跌幅','')}% | "
                      f"成交额={r.get('成交额','')}")
        except Exception as e:
            print(f"  [INFO] {name}: {e}")


def get_main_flow(market_df):
    """获取主力资金流向"""
    print("\n" + "=" * 60)
    print("[4] 主力资金流向（TOP 5）")
    print("=" * 60)

    for code, name in AERO_CORE_STOCKS[:5]:
        try:
            if ak:
                market = "sz" if code.startswith(("0", "3")) else "sh"
                flow = ak.stock_individual_fund_flow(stock=name, market=market)
                if flow is not None and not flow.empty:
                    latest = flow.iloc[-1]
                    net_in = latest.get('主力净流入-净额', '')
                    net_pct = latest.get('主力净流入-净占比', '')
                    print(f"  {name}({code}): 主力净流入={net_in} | 占比={net_pct}")
        except Exception as e:
            print(f"  [INFO] {name}: {e}")


def fetch_news_parallel():
    """并行搜索新闻"""
    print("\n" + "=" * 60)
    print("[5] 商业航天新闻与政策")
    print("=" * 60)

    def search_one(kw):
        print(f"  [搜索] {kw} ...")
        output = run_mx_search(f"{kw} 最新新闻 政策", OUT_DIR)
        if output:
            lines = output.strip().split('\n')
            # 只取前3条
            count = 0
            for line in lines:
                if line.strip().startswith('{') or line.strip().startswith('['):
                    continue
                if line.strip():
                    print(f"    {line[:120]}")
                    count += 1
                    if count >= 3:
                        break
        else:
            print(f"    [无法获取]")

    # 并行执行4个搜索
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(search_one, kw) for kw in AERO_KEYWORDS]
        for future in concurrent.futures.as_completed(futures, timeout=120):
            try:
                future.result()
            except Exception as e:
                print(f"  [ERROR] 搜索线程: {e}")


def fetch_financials_parallel():
    """并行获取财务数据"""
    print("\n" + "=" * 60)
    print("[6] 重点公司财务摘要")
    print("=" * 60)

    financial_queries = [
        "中航西飞 净利润 营收 最新财报",
        "航发动力 净利润 营收 最新财报",
        "中航沈飞 净利润 营收 最新财报",
        "西部超导 净利润 营收 最新财报",
    ]

    def fetch_one(q):
        print(f"  [查询] {q.split()[0]} ...")
        output = run_mx_data(q, OUT_DIR)
        if output:
            lines = output.strip().split('\n')
            for line in lines[:5]:
                print(f"    {line}")
        else:
            print(f"    [无法获取]")

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(fetch_one, q) for q in financial_queries]
        for future in concurrent.futures.as_completed(futures, timeout=120):
            try:
                future.result()
            except Exception as e:
                print(f"  [ERROR] 财务查询: {e}")


def generate_report():
    """生成最终报告"""
    print("\n" + "=" * 60)
    print("[7] 报告生成")
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
        "一、板块行情概览 - 请查看上方板块数据",
        "",
        "二、主力资金流向 - 请查看上方资金流向数据",
        "",
        "三、重点股票行情 - 请查看上方行情数据",
        "",
        "四、新闻与政策 - 请查看上方新闻数据",
        "",
        "五、财务摘要 - 请查看上方财务数据",
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

    start = datetime.now()

    # 第一步：获取全市场行情（关键优化：只获取一次）
    market_df = get_market_data()

    try:
        get_sector_data(market_df)
    except Exception as e:
        print(f"[ERROR] 板块数据: {e}")

    try:
        get_stock_quotes(market_df)
    except Exception as e:
        print(f"[ERROR] 行情数据: {e}")

    try:
        get_main_flow(market_df)
    except Exception as e:
        print(f"[ERROR] 资金流向: {e}")

    try:
        fetch_news_parallel()
    except Exception as e:
        print(f"[ERROR] 新闻搜索: {e}")

    try:
        fetch_financials_parallel()
    except Exception as e:
        print(f"[ERROR] 财务数据: {e}")

    try:
        generate_report()
    except Exception as e:
        print(f"[ERROR] 报告生成: {e}")

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n[完成] 耗时: {elapsed:.1f}s")
    print("[完成] 商业航天每日分析报告执行完毕")


if __name__ == '__main__':
    main()
