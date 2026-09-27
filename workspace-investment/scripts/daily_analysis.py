# -*- coding: utf-8 -*-
"""
每日涨跌停个股分析脚本
========================
功能：
1. 涨停板分析（行业/连板/成交额）
2. 跌停板分析（行业/恐慌程度）
3. 情绪判断（涨跌停比）
4. 热点板块识别
5. 写入daily_zt表供下游使用

注意：
  本脚本不写入daily_zt表（由collect_daily_zt_kline.py负责写入zt_kline）
  但本脚本是daily_zt表的数据来源之一——通过akshare获取涨停数据
"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import akshare as ak
from datetime import date as date_cls, datetime, timedelta

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(WORK_DIR, "out_data")
os.makedirs(OUT_DIR, exist_ok=True)

DB_PATH = r'F:\market_data.db'


def get_trading_date():
    """获取最近交易日（向前追溯），返回YYYY-MM-DD格式"""
    today = date_cls.today()
    for i in range(7):
        d = today - timedelta(days=i)
        if d.weekday() < 5:
            return d.strftime('%Y-%m-%d')


def write_zt_to_db(date_str, zt_data):
    """将涨停数据写入daily_zt表"""
    import sqlite3
    if not os.path.exists(DB_PATH):
        print(f"[DB] 数据库不存在: {DB_PATH}")
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # 确保表存在
        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_zt (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT,
                trade_date TEXT NOT NULL,
                close_price REAL,
                open_price REAL,
                zt_type TEXT,
                chg_pct REAL,
                UNIQUE(code, trade_date)
            )
        """)
        saved = 0
        for _, row in zt_data.iterrows():
            raw_code = str(row.get('代码', '')).strip()
            name = str(row.get('名称', '')).strip()
            close_price = float(row.get('最新价', row.get('收盘价', 0)))
            chg_pct = float(row.get('涨跌幅', row.get('pct_chg', 0)))
            # 标准化代码格式：纯数字 → sh.600xxx / sz.000xxx / sz.300xxx / sh.688xxx
            if raw_code.startswith('6') or raw_code.startswith('9'):
                code = 'sh.' + raw_code
            else:
                code = 'sz.' + raw_code
            try:
                c.execute("""
                    INSERT OR REPLACE INTO daily_zt
                    (code, name, trade_date, close_price, open_price, zt_type, chg_pct)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (code, name, date_str, close_price, 0, '涨停', chg_pct))
                saved += 1
            except Exception:
                pass
        conn.commit()
        conn.close()
        print(f"[DB] 写入daily_zt: {saved}条")
    except Exception as e:
        print(f"[DB] 写入失败: {e}")


def analyze_daily(date=None):
    """每日涨跌停分析"""
    if date is None:
        date = get_trading_date()
    
    # akshare要求YYYYMMDD格式，内部统一转换
    ak_date = date.replace('-', '')  # 2026-07-13 -> 20260713
    
    result_lines = []
    def p(text):
        print(text)
        result_lines.append(text)
    
    p("=" * 60)
    p(f"每日涨跌停分析 {date}")
    p("=" * 60)
    
    # ========== 涨停板 ==========
    p("")
    p("[1] 涨停板分析")
    p("-" * 40)
    
    zt = ak.stock_zt_pool_em(date=ak_date)
    if zt is None or len(zt) == 0:
        p("涨停数据获取失败或今日无涨停")
        # 保存空结果
        _save_file(date, "\n".join(result_lines))
        return
    
    p(f"涨停总数: {len(zt)}家")
    
    # 写入daily_zt表
    write_zt_to_db(date, zt)
    
    # 行业分布
    if '所属行业' in zt.columns:
        sector = zt.groupby('所属行业').size().sort_values(ascending=False)
        p("")
        p("涨停行业分布:")
        for s, c in sector.head(10).items():
            bar = "█" * min(c, 30)
            p(f"  {s:12s}: {c:2d}家 {bar}")
    
    # 连板股
    if '连板数' in zt.columns:
        lianban = zt[zt['连板数'] >= 2]
        p("")
        p(f"连板股({len(lianban)}家):")
        for _, row in lianban.sort_values('连板数', ascending=False).head(5).iterrows():
            p(f"  {row['名称']}: {row['连板数']}连板")
    
    # 成交额Top5
    if '成交额' in zt.columns:
        p("")
        p("成交额Top5:")
        top5 = zt.nlargest(5, '成交额')
        for _, row in top5.iterrows():
            amt = row['成交额'] / 1e8
            p(f"  {row['名称']}: {amt:.2f}亿")
    
    # ========== 跌停板 ==========
    p("")
    p("[2] 跌停板分析")
    p("-" * 40)
    
    dt_count = 0
    try:
        dt = ak.stock_zt_pool_dtgc_em(date=ak_date)
        if dt is not None:
            p(f"跌停总数: {len(dt)}家")
            if '所属行业' in dt.columns:
                sector_dt = dt.groupby('所属行业').size().sort_values(ascending=False)
                p("")
                p("跌停行业分布:")
                for s, c in sector_dt.head(5).items():
                    p(f"  {s:12s}: {c:2d}家")
            dt_count = len(dt)
    except Exception as e:
        p(f"跌停数据获取失败: {e}")
    
    # ========== 情绪判断 ==========
    p("")
    p("[3] 情绪判断")
    p("-" * 40)
    
    zt_count = len(zt)
    ratio = zt_count / max(dt_count, 1)
    
    p(f"涨跌停比: {zt_count} : {dt_count} = {ratio:.2f}")
    
    if ratio > 3:
        sentiment = "极度贪婪"
        level = "🔴"
    elif ratio > 2:
        sentiment = "贪婪"
        level = "🟠"
    elif ratio > 1:
        sentiment = "偏多"
        level = "🟢"
    elif ratio > 0.5:
        sentiment = "中性"
        level = "🟡"
    elif ratio > 0.3:
        sentiment = "偏空"
        level = "🟠"
    else:
        sentiment = "恐慌"
        level = "🔴"
    
    p(f"市场情绪: {level} {sentiment}")
    
    # ========== 热点板块 ==========
    p("")
    p("[4] 今日热点板块")
    p("-" * 40)
    
    if '所属行业' in zt.columns:
        hot_sectors = sector.head(5)
        p("热点涨停板块:")
        for s, c in hot_sectors.items():
            p(f"  {s}: {c}家涨停")
    
    p("")
    p("=" * 60)
    
    # 保存结果
    _save_file(date, "\n".join(result_lines))

    # 写入Supermemory
    _save_to_memory(result_lines, date)


def _save_to_memory(lines, date):
    """将分析结果写入Supermemory投资库"""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'memory'))
        from memory_tools import MemoryTools
        mt = MemoryTools()
        # 提取关键信息（涨停/跌停数量、板块、情绪）
        summary = '\n'.join(lines[:30])  # 前30行摘要
        mt.save_memory(
            f"涨停分析 {date}:\n{summary}",
            category='daily',
            domain='investment'
        )
        print(f"[memory] 已写入Supermemory")
    except ImportError:
        print(f"[memory] 跳过（memory_tools不可用）")
    except Exception as e:
        print(f"[memory] 写入失败: {e}")


def _save_file(date, content):
    """保存分析结果到文件"""
    today = datetime.now().strftime("%Y%m%d")
    out_file = os.path.join(OUT_DIR, f"zt_analysis_{today}.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[保存] {out_file}")


if __name__ == '__main__':
    date_arg = None
    for arg in sys.argv[1:]:
        if not arg.startswith('--'):
            date_arg = arg
            break
    analyze_daily(date_arg)