# -*- coding: utf-8 -*-
"""
姣忔棩娑ㄨ穼鍋滀釜鑲″垎鏋愯剼鏈?========================
鍔熻兘锛?1. 娑ㄥ仠鏉垮垎鏋愶紙琛屼笟/杩炴澘/鎴愪氦棰濓級
2. 璺屽仠鏉垮垎鏋愶紙琛屼笟/鎭愭厡绋嬪害锛?3. 鎯呯华鍒ゆ柇锛堟定璺屽仠姣旓級
4. 鐑偣鏉垮潡璇嗗埆
5. 鍐欏叆daily_zt琛ㄤ緵涓嬫父浣跨敤

娉ㄦ剰锛?  鏈剼鏈笉鍐欏叆daily_zt琛紙鐢眂ollect_daily_zt_kline.py璐熻矗鍐欏叆zt_kline锛?  浣嗘湰鑴氭湰鏄痙aily_zt琛ㄧ殑鏁版嵁鏉ユ簮涔嬩竴鈥斺€旈€氳繃akshare鑾峰彇娑ㄥ仠鏁版嵁
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
    """鑾峰彇鏈€杩戜氦鏄撴棩锛堝悜鍓嶈拷婧級锛岃繑鍥瀁YYY-MM-DD鏍煎紡"""
    today = date_cls.today()
    for i in range(7):
        d = today - timedelta(days=i)
        if d.weekday() < 5:
            return d.strftime('%Y-%m-%d')


def write_zt_to_db(date_str, zt_data):
    """灏嗘定鍋滄暟鎹啓鍏aily_zt琛?""
    import sqlite3
    if not os.path.exists(DB_PATH):
        print(f"[DB] 鏁版嵁搴撲笉瀛樺湪: {DB_PATH}")
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # 纭繚琛ㄥ瓨鍦?        c.execute("""
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
            raw_code = str(row.get('浠ｇ爜', '')).strip()
            name = str(row.get('鍚嶇О', '')).strip()
            close_price = float(row.get('鏈€鏂颁环', row.get('鏀剁洏浠?, 0)))
            chg_pct = float(row.get('娑ㄨ穼骞?, row.get('pct_chg', 0)))
            # 鏍囧噯鍖栦唬鐮佹牸寮忥細绾暟瀛?鈫?sh.600xxx / sz.000xxx / sz.300xxx / sh.688xxx
            if raw_code.startswith('6') or raw_code.startswith('9'):
                code = 'sh.' + raw_code
            else:
                code = 'sz.' + raw_code
            try:
                c.execute("""
                    INSERT OR REPLACE INTO daily_zt
                    (code, name, trade_date, close_price, open_price, zt_type, chg_pct)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (code, name, date_str, close_price, 0, '娑ㄥ仠', chg_pct))
                saved += 1
            except Exception:
                pass
        conn.commit()
        conn.close()
        print(f"[DB] 鍐欏叆daily_zt: {saved}鏉?)
    except Exception as e:
        print(f"[DB] 鍐欏叆澶辫触: {e}")


def analyze_daily(date=None):
    """姣忔棩娑ㄨ穼鍋滃垎鏋?""
    if date is None:
        date = get_trading_date()
    
    # akshare瑕佹眰YYYYMMDD鏍煎紡锛屽唴閮ㄧ粺涓€杞崲
    ak_date = date.replace('-', '')  # 2026-07-13 -> 20260713
    
    result_lines = []
    def p(text):
        print(text)
        result_lines.append(text)
    
    p("=" * 60)
    p(f"姣忔棩娑ㄨ穼鍋滃垎鏋?{date}")
    p("=" * 60)
    
    # ========== 娑ㄥ仠鏉?==========
    p("")
    p("[1] 娑ㄥ仠鏉垮垎鏋?)
    p("-" * 40)
    
    zt = ak.stock_zt_pool_em(date=ak_date)
    if zt is None or len(zt) == 0:
        p("娑ㄥ仠鏁版嵁鑾峰彇澶辫触鎴栦粖鏃ユ棤娑ㄥ仠")
        # 淇濆瓨绌虹粨鏋?        _save_file(date, "\n".join(result_lines))
        return
    
    p(f"娑ㄥ仠鎬绘暟: {len(zt)}瀹?)
    
    # 鍐欏叆daily_zt琛?    write_zt_to_db(date, zt)
    
    # 琛屼笟鍒嗗竷
    if '鎵€灞炶涓? in zt.columns:
        sector = zt.groupby('鎵€灞炶涓?).size().sort_values(ascending=False)
        p("")
        p("娑ㄥ仠琛屼笟鍒嗗竷:")
        for s, c in sector.head(10).items():
            bar = "鈻? * min(c, 30)
            p(f"  {s:12s}: {c:2d}瀹?{bar}")
    
    # 杩炴澘鑲?    if '杩炴澘鏁? in zt.columns:
        lianban = zt[zt['杩炴澘鏁?] >= 2]
        p("")
        p(f"杩炴澘鑲?{len(lianban)}瀹?:")
        for _, row in lianban.sort_values('杩炴澘鏁?, ascending=False).head(5).iterrows():
            p(f"  {row['鍚嶇О']}: {row['杩炴澘鏁?]}杩炴澘")
    
    # 鎴愪氦棰漈op5
    if '鎴愪氦棰? in zt.columns:
        p("")
        p("鎴愪氦棰漈op5:")
        top5 = zt.nlargest(5, '鎴愪氦棰?)
        for _, row in top5.iterrows():
            amt = row['鎴愪氦棰?] / 1e8
            p(f"  {row['鍚嶇О']}: {amt:.2f}浜?)
    
    # ========== 璺屽仠鏉?==========
    p("")
    p("[2] 璺屽仠鏉垮垎鏋?)
    p("-" * 40)
    
    dt_count = 0
    try:
        dt = ak.stock_zt_pool_dtgc_em(date=ak_date)
        if dt is not None:
            p(f"璺屽仠鎬绘暟: {len(dt)}瀹?)
            if '鎵€灞炶涓? in dt.columns:
                sector_dt = dt.groupby('鎵€灞炶涓?).size().sort_values(ascending=False)
                p("")
                p("璺屽仠琛屼笟鍒嗗竷:")
                for s, c in sector_dt.head(5).items():
                    p(f"  {s:12s}: {c:2d}瀹?)
            dt_count = len(dt)
    except Exception as e:
        p(f"璺屽仠鏁版嵁鑾峰彇澶辫触: {e}")
    
    # ========== 鎯呯华鍒ゆ柇 ==========
    p("")
    p("[3] 鎯呯华鍒ゆ柇")
    p("-" * 40)
    
    zt_count = len(zt)
    ratio = zt_count / max(dt_count, 1)
    
    p(f"娑ㄨ穼鍋滄瘮: {zt_count} : {dt_count} = {ratio:.2f}")
    
    if ratio > 3:
        sentiment = "鏋佸害璐┆"
        level = "馃敶"
    elif ratio > 2:
        sentiment = "璐┆"
        level = "馃煚"
    elif ratio > 1:
        sentiment = "鍋忓"
        level = "馃煝"
    elif ratio > 0.5:
        sentiment = "涓€?
        level = "馃煛"
    elif ratio > 0.3:
        sentiment = "鍋忕┖"
        level = "馃煚"
    else:
        sentiment = "鎭愭厡"
        level = "馃敶"
    
    p(f"甯傚満鎯呯华: {level} {sentiment}")
    
    # ========== 鐑偣鏉垮潡 ==========
    p("")
    p("[4] 浠婃棩鐑偣鏉垮潡")
    p("-" * 40)
    
    if '鎵€灞炶涓? in zt.columns:
        hot_sectors = sector.head(5)
        p("鐑偣娑ㄥ仠鏉垮潡:")
        for s, c in hot_sectors.items():
            p(f"  {s}: {c}瀹舵定鍋?)
    
    p("")
    p("=" * 60)
    
    # 淇濆瓨缁撴灉
    _save_file(date, "\n".join(result_lines))

    # 鍐欏叆Supermemory
    _save_to_memory(result_lines, date)


def _save_to_memory(lines, date):
    """灏嗗垎鏋愮粨鏋滃啓鍏upermemory鎶曡祫搴?""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'memory'))
        from memory_tools import MemoryTools
        mt = MemoryTools()
        # 鎻愬彇鍏抽敭淇℃伅锛堟定鍋?璺屽仠鏁伴噺銆佹澘鍧椼€佹儏缁級
        summary = '\n'.join(lines[:30])  # 鍓?0琛屾憳瑕?        mt.save_memory(
            f"娑ㄥ仠鍒嗘瀽 {date}:\n{summary}",
            category='daily',
            domain='investment'
        )
        print(f"[memory] 宸插啓鍏upermemory")
    except ImportError:
        print(f"[memory] 璺宠繃锛坢emory_tools涓嶅彲鐢級")
    except Exception as e:
        print(f"[memory] 鍐欏叆澶辫触: {e}")


def _save_file(date, content):
    """淇濆瓨鍒嗘瀽缁撴灉鍒版枃浠?""
    today = datetime.now().strftime("%Y%m%d")
    out_file = os.path.join(OUT_DIR, f"zt_analysis_{today}.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[淇濆瓨] {out_file}")


if __name__ == '__main__':
    date_arg = None
    for arg in sys.argv[1:]:
        if not arg.startswith('--'):
            date_arg = arg
            break
    analyze_daily(date_arg)
