"""
尾盘精选策略扫描 V3.0
量化筛选 + 供应链卡点验证 + MX实时数据（三重驱动）
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import sqlite3, pandas as pd, json, os, winreg
from datetime import datetime, timedelta
from pathlib import Path

# 读取MX_APIKEY（从Machine级环境变量）
def get_mx_key():
    for hive, path in [
        (winreg.HKEY_CURRENT_USER, r'Environment'),
        (winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'),
    ]:
        try:
            with winreg.OpenKey(hive, path) as h:
                val, _ = winreg.QueryValueEx(h, 'MX_APIKEY')
                if val:
                    return val
        except FileNotFoundError:
            pass
    return None

MX_KEY = get_mx_key()
print(f"[MX_APIKEY] {'已设置' + str(len(MX_KEY)) + '字符' if MX_KEY else '未设置'}")

DB = r'F:\market_data.db'
WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
ML_PROB_PATH = os.path.join(WORK_DIR, 'scripts', 'ml_latest_prob.pkl')
FIN_PKL = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\quant_ml\data\financial_features.pkl'
DB = r'F:\market_data.db'

# 预加载财务特征（现金流/净利润比等）
_fin_cache = None
def load_financial_cache():
    global _fin_cache
    if _fin_cache is not None:
        return _fin_cache
    if os.path.exists(FIN_PKL):
        import pickle
        with open(FIN_PKL, 'rb') as f:
            raw = pickle.load(f)
        _fin_cache = {}
        for k, v in raw.items():
            norm_k = k.replace('sh.', '').replace('sz.', '').replace('.', '')
            cash = v.get('经营现金净流量与净利润的比率(%)')
            _fin_cache[norm_k] = float(cash) / 100.0 if cash else 0.0
        print(f"[财务特征] 加载完成: {len(_fin_cache)} 只")
    else:
        _fin_cache = {}
    return _fin_cache

# ============================================================
# MX智能选股（妙想全市场筛选）
# ============================================================

def _code_norm(code: str) -> str:
    """xuangu格式(sz002805) → DB格式(sz.002805)"""
    code = str(code)
    if '.' not in code:
        if code.startswith('sz') and len(code) == 8:
            return f'sz.{code[2:]}'
        if code.startswith('sh') and len(code) == 8:
            return f'sh.{code[2:]}'
        if code.startswith('bj') and len(code) == 6:
            return f'bj.{code[2:]}'
    return code


def enrich_from_db(candidates: list, date: str) -> list:
    """
    对xuangu候选补充换手率（来自DB，xuangu已有数据则跳过不覆盖）
    stock_turnover最新日期2026-06-05，用最新可用日期避免查空
    """
    if not candidates:
        return candidates
    # 只对缺换手率的候选补数据
    missing = [s for s in candidates if not s.get('turnover', 0)]
    if not missing:
        return candidates
    db_codes = [_code_norm(s['code']) for s in missing]
    codes_str = ','.join(f"'{c}'" for c in db_codes)
    try:
        con = sqlite3.connect(DB)
        latest_date = pd.read_sql(
            "SELECT MAX(date) as md FROM stock_turnover", con)['md'].iloc[0]
        turn_df = pd.read_sql(
            f"SELECT code, turnover FROM stock_turnover "
            f"WHERE date = '{latest_date}' AND code IN ({codes_str})",
            con)
        con.close()
        turn_map = {str(r['code']): float(r['turnover']) for _, r in turn_df.iterrows()}
        filled = 0
        for s in missing:
            db_code = _code_norm(s['code'])
            tv = turn_map.get(db_code, 0.0)
            if tv > 0:
                s['turnover'] = tv
                filled += 1
        print(f"  [DB enrichment] 成功补充{filled}/{len(missing)}只换手率(数据日期:{latest_date})")
    except Exception as e:
        print(f"  [DB enrichment] 失败: {e}，xuangu原始数据继续")
    return candidates


def _find_date_suffix(row: dict, prefix: str) -> str:
    """动态查找row中字段的日期后缀，如'涨跌幅(%) 2026.06.22'返回'2026.06.22'"""
    for key in row.keys():
        if key.startswith(prefix + ' '):
            return key[len(prefix) + 1:]
    return ''


def screen_mx_xuangu(chg_min: float = 2.0, chg_max: float = 8.0) -> list:
    """通过妙想API全市场筛选涨幅区间股票，返回[{code, name, close, chg_pct, turnover, vol_ratio, ...}]"""
    if not MX_KEY:
        print("[xuangu] MX_APIKEY未设置")
        return []
    try:
        sys.path.insert(0, r'C:\Users\Administrator\AppData\Roaming\npm\node_modules\openclaw\skills\mx-xuangu')
        from mx_xuangu import MXSelectStock
        xuangu = MXSelectStock(api_key=MX_KEY)
        query = f"A股涨幅在{chg_min}%到{chg_max}%之间的股票"
        result = xuangu.search(query)
        rows, src, err = MXSelectStock.extract_data(result)
        if err or not rows:
            print(f"[xuangu] 筛选失败: {err}")
            return []

        # 动态获取日期后缀（xuangu数据日期不固定）
        date_suffix = _find_date_suffix(rows[0], '涨跌幅(%)')
        print(f"  [xuangu] 数据日期后缀: {date_suffix}")

        stocks = []
        for row in rows:
            # 解析字段（列名含动态日期后缀）
            code = row.get('代码', '').strip()
            name = row.get('名称', '').strip()
            # 过滤ST/*退市
            if name.startswith('*ST') or name.startswith('ST') or '退市' in name:
                continue
            # 解析涨跌幅
            chg_str = row.get(f'涨跌幅(%) {date_suffix}') if date_suffix else row.get('涨跌幅(%)')
            try: chg = float(chg_str)
            except: chg = 0.0
            # 解析最新价
            close_str = row.get(f'最新价(元) {date_suffix}') if date_suffix else row.get('最新价(元)')
            try: close = float(close_str)
            except: close = 0.0
            # 解析换手率
            turnover_str = row.get(f'换手率(%) {date_suffix}') if date_suffix else row.get('换手率(%)')
            try: turnover = float(turnover_str)
            except: turnover = 0.0
            # 解析量比
            vol_ratio_str = row.get(f'量比 {date_suffix}') if date_suffix else row.get('量比')
            try: vol_ratio = float(vol_ratio_str)
            except: vol_ratio = 0.0
            
            # 完整原始行数据
            stocks.append({
                'code': code,
                'name': name,
                'close': close,
                'chg_pct': chg,
                'turnover': turnover,
                'vol_ratio': vol_ratio,
                'raw': row,
            })
        print(f"[xuangu] 筛选{chg_min}~{chg_max}%: {len(stocks)}只（已过滤ST）")
        return stocks
    except Exception as e:
        print(f"[xuangu] 异常: {e}")
        return []


# ============================================================
# MX实时行情查询（妙想数据通道）
# ============================================================

def query_mx_realtime(symbol: str) -> dict:
    """通过妙想API查询单只股票最新行情（最近交易日），返回dict或None"""
    if not MX_KEY:
        return None
    try:
        sys.path.insert(0, r'C:\Users\Administrator\AppData\Roaming\npm\node_modules\openclaw\skills\mx-data')
        from mx_data import MXData
        client = MXData(api_key=MX_KEY)
        code = symbol.replace('sh.', '').replace('sz.', '').replace('bj.', '')
        query = f"{code} 实时的股价、涨跌幅、成交量、换手率"
        result = client.query(query)
        
        # 解析MX返回结构
        outer = result.get('data', {}) or {}
        inner = outer.get('data', {}) or {}
        sdr = inner.get('searchDataResultDTO', {}) if isinstance(inner, dict) else {}
        tables = sdr.get('dataTableDTOList', []) if isinstance(sdr, dict) else []
        if not tables:
            return None
        
        table = tables[0]
        raw = table.get('rawTable', {}) or {}
        names = table.get('nameMap', {}) or {}
        
        # dates在rawTable里面
        raw_dates = raw.get('headName', [])
        if not raw_dates:
            return None
        
        # 字段keys（排除headName本身）
        field_keys = [k for k in raw.keys() if k != 'headName']
        latest_date = raw_dates[0]
        
        d = {'date': latest_date}
        for fk in field_keys:
            fv_list = raw.get(fk, [])
            if fv_list:
                # names的value才是中文名
                fname = names.get(str(fk), str(fk))
                d[fname] = fv_list[0]
        
        def find_field(ls):
            for k, v in d.items():
                kl = k.lower() if isinstance(k, str) else ''
                if any(t in kl for t in ls):
                    try: return float(v)
                    except:
                        try: return float(v.strip('%'))
                        except: pass
            return None
        
        d['close'] = find_field(['收盘价', '最新价', '现价'])
        d['chg_pct'] = find_field(['涨跌幅'])
        d['volume'] = find_field(['成交量'])
        d['turnover'] = find_field(['换手率'])
        
        return d
    except Exception as e:
        print(f"  [MX警告] {symbol}: {e}")
        return None


# ============================================================
# 舆情关键词提取（整词匹配）
# ============================================================

POSITIVE_KW = [
    '业绩超预期', '中标', '产品突破', '技术创新', '产能扩张', '订单增长',
    '业绩预增', '净利润增长', '评级上调', '信用评级', '增持', '回购',
    '复产', '扩产', '员工持股', '股权激励', '战略合作', '全球领先',
    '订单饱满', '供货', '首发', '独家', '打破垄断', '填补空白',
    '营业收入增长', '利润增长', '市场份额', '突破', '增长', '提升',
]
NEGATIVE_KW = [
    '业绩下修', '监管问询', '减持', '风险提示', '诉讼', '商誉减值',
    '业绩预减', '净利润下降', '被立案', '召回', '造假', '停产',
    '亏损', '债务风险', '流动性紧张', '违规', '处罚', '立案调查',
    '竞争加剧', '价格战', '毛利率下降', '存货跌价', '应收款恶化',
    '大幅亏损', '持续亏损', '终止', '取消', '下降', '减少',
]
NEUTRAL_KW = ['分红', '回购', '股权激励', '高管变动', '担保', '更名',
               '发行债券', '吸收合并', '资产重组']

def is_cjk(char):
    return '\u4e00' <= char <= '\u9fff'

def whole_word_match(text, keyword):
    idx = text.find(keyword)
    while idx != -1:
        before = text[idx - 1] if idx > 0 else ' '
        after = text[idx + len(keyword)] if idx + len(keyword) < len(text) else ' '
        if not (is_cjk(before) and is_cjk(after)):
            return True
        idx = text.find(keyword, idx + 1)
    return False

def extract_keywords(title, content='') -> dict:
    full = title + ' ' + content
    pos = [kw for kw in POSITIVE_KW if whole_word_match(full, kw)]
    neg = [kw for kw in NEGATIVE_KW if whole_word_match(full, kw)]
    neu = [kw for kw in NEUTRAL_KW if whole_word_match(full, kw)]
    return {
        'positive': pos, 'negative': neg, 'neutral': neu,
        'score': len(pos) - len(neg),
        'has_positive': bool(pos), 'has_negative': bool(neg),
    }


def query_mx_news_score(symbol: str) -> dict:
    """
    通过妙想API查询个股最新资讯，返回舆情评分dict。
    包含: positive(bool), negative(bool), sentiment_score(int), keywords(list)
    """
    if not MX_KEY:
        return {'has_positive': False, 'has_negative': False, 'sentiment_score': 0, 'keywords': []}
    try:
        sys.path.insert(0, r'C:\Users\Administrator\AppData\Roaming\npm\node_modules\openclaw\skills\mx-search')
        from mx_search import MXSearch
        client = MXSearch(api_key=MX_KEY)
        code = symbol.replace('sh.', '').replace('sz.', '').replace('bj.', '')
        # 构造查询：公司名或代码 + 关键词
        result = client.search(code)  # 直接用代码搜索
        if not isinstance(result, dict):
            return {'has_positive': False, 'has_negative': False, 'sentiment_score': 0, 'keywords': []}

        raw_items = result.get('data', {}).get('data', {}).get('llmSearchResponse', {}).get('data', [])
        if not isinstance(raw_items, list):
            return {'has_positive': False, 'has_negative': False, 'sentiment_score': 0, 'keywords': []}

        # 找得分最高的一条（合并标题+内容前800字）
        best_score = 0
        best_kw = []
        for item in raw_items[:10]:  # 最多看10条
            title = item.get('title', '')
            content = item.get('content', '')[:800]
            kw_info = extract_keywords(title, content)
            s = kw_info['score']
            if s > best_score:
                best_score = s
                best_kw = kw_info['positive'] + kw_info['negative']

        return {
            'has_positive': best_score > 0,
            'has_negative': best_score < 0,
            'sentiment_score': best_score,
            'keywords': best_kw,
        }
    except Exception as e:
        return {'has_positive': False, 'has_negative': False, 'sentiment_score': 0, 'keywords': []}


def mx_enabled() -> bool:
    """检查MX通道是否可用"""
    return MX_KEY is not None

# ============================================================
# 供应链卡点知识库（从投资系统.md加载）
# ============================================================

def load_supply_chain_tiers():
    """加载S/A/B级卡点股票列表"""
    # 硬编码S/A/B级卡点（从投资系统.md提取）
    # 格式：code -> (tier, industry, bottleneck_type)
    tiers = {
        # S级
        '300750': ('S', '新能源车/锂电', '全球动力电池龙头'),
        '688981': ('S', '半导体/AI', '唯一先进制程代工'),
        '002371': ('S', '半导体/AI', '国产半导体设备'),
        '300308': ('S', '光模块/光学', '全球光模块龙头'),
        '600760': ('S', '军工', '战斗机唯一上市公司'),
        '688017': ('S', '机器人/工控', '谐波减速器龙头'),
        '300124': ('S', '机器人/工控', '工控伺服龙头'),
        
        # A级
        '688234': ('A', '半导体/AI', '碳化硅衬底'),
        '688012': ('A', '半导体/AI', 'CCP刻蚀机'),
        '301269': ('A', '半导体/AI', '国产EDA'),
        '300274': ('A', '光伏', '逆变器龙头'),
        '002812': ('A', '新能源车/锂电', '湿法隔膜'),
        '002460': ('A', '新能源车/锂电', '锂矿'),
        '002466': ('A', '新能源车/锂电', '锂矿'),
        '603259': ('A', '医药/CDMO', '全球CRDMO'),
        '002413': ('A', '军工', '军工连接器'),
        '600893': ('A', '军工', '航空发动机'),
        '600276': ('A', '医药', '创新药'),
        '002594': ('A', '新能源车/整车', '垂直整合'),
        
        # B级
        '600703': ('B', '半导体/AI', '化合物半导体'),
        '600438': ('B', '光伏', '硅料龙头'),
        '300316': ('B', '半导体/AI', '硅片设备'),
        '603799': ('B', '新能源车/锂电', '钴镍'),
        '002821': ('B', '医药/CDMO', 'CDMO'),
        '002281': ('B', '光模块/光学', '国内光模块'),
        '603083': ('B', '光模块/光学', '数通光模块'),
        '688025': ('B', '光模块/光学', '激光器'),
        '688122': ('B', '军工', '高温合金'),
        '000733': ('B', '军工', '被动器件'),
        '000739': ('B', '医药', '原料药'),
        '603986': ('B', '机器人/工控', 'MCU'),
        '300014': ('B', '新能源车/锂电', '动力电池'),
        '605398': ('B', '机器人/工控', '减速器'),
    }
    return tiers


def verify_supply_chain(code, tier_map):
    """验证股票是否是供应链卡点"""
    # A股代码处理（去掉sh/sz前缀，保留6位数字）
    clean_code = code.replace('sh.', '').replace('sz.', '').replace('sz.', '')
    if clean_code in tier_map:
        return tier_map[clean_code]
    return None


def check_risk_blacklist(code, con):
    """检查风险黑名单"""
    # 检查ST
    st = con.execute("SELECT 1 FROM stock_st_status WHERE code = ? AND is_st = 1", (code,)).fetchone()
    if st:
        return True, "ST股"
    
    # 检查北交所
    if code.startswith('bj.'):
        return True, "北交所"
    
    return False, None


# ============================================================
# 量化筛选（原有逻辑）
# ============================================================

def scan_stocks_quantitative(date=None):
    """量化筛选候选股"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    con = sqlite3.connect(DB)
    
    # 取当日数据
    df = pd.read_sql(f"SELECT code, date, close, volume FROM daily_k WHERE date = '{date}'", con)
    
    # 换手率
    turnover = pd.read_sql(f"SELECT code, turnover FROM stock_turnover WHERE date = '{date}'", con)
    df = df.merge(turnover, on='code', how='left')
    
    # 排除ST、北交所
    df = df[~df['code'].str.startswith('bj.')]
    df = df[~df['code'].str.startswith('sh.8')]
    
    st_result = con.execute("SELECT code FROM stock_st_status WHERE is_st = 1").fetchall()
    st_codes = {r[0] for r in st_result}
    df = df[~df['code'].isin(st_codes)]
    
    # 基础指标
    df['prev_close'] = df.groupby('code')['close'].shift(1)
    df = df[df['prev_close'] > 0]
    df['chg_pct'] = (df['close'] / df['prev_close'] - 1) * 100
    
    con.close()
    
    # 近3日涨幅
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 5)]
    con = sqlite3.connect(DB)
    df_3d = pd.read_sql(f"SELECT code, date, close FROM daily_k WHERE date IN {tuple(dates)}", con)
    con.close()
    
    df_3d['prev_c'] = df_3d.groupby('code')['close'].shift(1)
    df_3d['chg'] = (df_3d['close'] / df_3d['prev_c'] - 1) * 100
    
    chg_3d = {}
    for code in df['code'].unique():
        code_data = df_3d[df_3d['code'] == code].sort_values('date')
        if len(code_data) >= 3:
            chgs = code_data['chg'].iloc[-4:-1]
            chg_3d[code] = chgs.sum()
    
    df['chg_3d'] = df['code'].map(chg_3d)
    
    chg_2d = {}
    for code in df['code'].unique():
        code_data = df_3d[df_3d['code'] == code].sort_values('date')
        if len(code_data) >= 2:
            chg_2d[code] = code_data['chg'].iloc[-2]
    df['chg_1d'] = df['code'].map(chg_2d)
    
    # 量比
    con = sqlite3.connect(DB)
    vol = pd.read_sql(f"""
        SELECT code, AVG(volume) as avg_vol FROM daily_k 
        WHERE date IN {tuple(dates[:3])}
        GROUP BY code
    """, con)
    con.close()
    
    df = df.merge(vol, on='code', how='left')
    df['vol_ratio'] = df['volume'] / df['avg_vol']
    
    # 量化条件
    cond = (
        (df['chg_pct'] >= 3) & (df['chg_pct'] <= 5) &
        (df['vol_ratio'] > 1) &
        (df['chg_3d'] > 0) & (df['chg_3d'] < 10) &
        (df['chg_1d'] < 7)
    )
    
    candidates = df[cond].sort_values('chg_3d', ascending=False)
    
    return candidates


# ============================================================
# 供应链卡点验证（新增）
# ============================================================

def verify_candidates_with_supply_chain(candidates, tier_map):
    """对候选股进行供应链卡点验证"""
    results = []
    
    for _, row in candidates.iterrows():
        code = row['code']
        tier_info = verify_supply_chain(code, tier_map)
        
        if tier_info:
            tier, industry, bottleneck = tier_info
            # 查现金流/净利润比
            fin_cache = load_financial_cache()
            norm_code = str(code).replace('sh.', '').replace('sz.', '').replace('.', '')
            cash_ratio = fin_cache.get(norm_code, 0.0)
            results.append({
                'code': code,
                'close': row['close'],
                'chg_pct': row['chg_pct'],
                'vol_ratio': row['vol_ratio'],
                'chg_3d': row['chg_3d'],
                'chg_1d': row['chg_1d'],
                'turnover': row.get('turnover'),
                'supply_tier': tier,
                'industry': industry,
                'bottleneck': bottleneck,
                'supply_chain_score': 1 if tier == 'S' else 0.7 if tier == 'A' else 0.4,
                'cash_net_ratio': cash_ratio
            })
    
    return pd.DataFrame(results)


# ============================================================
# ML概率验证快照
# ============================================================
def save_ml_snapshot(df: pd.DataFrame, scan_date: str):
    """保存候选股ML概率快照，用于后续T+1验证胜率"""
    if df is None or len(df) == 0:
        return
    out_dir = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\out_data\ml_snapshots'
    os.makedirs(out_dir, exist_ok=True)
    snap_file = os.path.join(out_dir, f'ml_candidates_{scan_date.replace("-","")}.json')
    
    records = []
    for _, row in df.iterrows():
        ml_prob = float(row.get('ml_prob', 0) or 0)
        records.append({
            'code': str(row.get('code', '')),
            'name': str(row.get('name', '')),
            'chg_pct': float(row.get('chg_pct', 0) or 0),
            'ml_prob': ml_prob,
            'score': float(row.get('score', 0) or 0),
            'turnover': float(row.get('turnover', 0) or 0),
            'vol_ratio': float(row.get('vol_ratio', 0) or 0),
            'supply_tier': str(row.get('supply_tier', '')),
            'industry': str(row.get('industry', '')),
            'result': 'pending'  # 待T+1后更新
        })
    
    snap_data = {
        'date': scan_date,
        'total': len(records),
        'ml_prob_above_50': len([r for r in records if r['ml_prob'] > 0.50]),
        'ml_prob_above_55': len([r for r in records if r['ml_prob'] > 0.55]),
        'ml_prob_above_60': len([r for r in records if r['ml_prob'] > 0.60]),
        'records': records
    }
    
    with open(snap_file, 'w', encoding='utf-8') as f:
        json.dump(snap_data, f, ensure_ascii=False, indent=2)
    print(f"[ML快照] 已保存: {snap_file} ({len(records)}只候选，ML>50%有{snap_data['ml_prob_above_50']}只)")


# 主流程
# ============================================================

def load_ml_probabilities(top_n: int = 5000) -> dict:
    """加载ML概率（双模型融合），返回top_n只股票的{code: prob}

    默认返回全量（5000只），确保候选票全覆盖。
    """
    try:
        from ml_factor_loader import get_ml_prob
        # 先加载概率缓存，拿到所有有数据的股票
        from ml_factor_loader import load_latest_probabilities, load_mstnn_probabilities
        lgbm_probs = load_latest_probabilities()
        mstnn_probs = load_mstnn_probabilities()
        all_codes = set(lgbm_probs.keys()) | set(k.replace('sh.','').replace('sz.','') for k in mstnn_probs.keys())
        
        # 取双模型融合概率
        probs = {}
        for code in all_codes:
            p = get_ml_prob(code)
            if p is not None:
                probs[code] = p
        
        # 取概率最高的top_n只（默认5000=全量）
        sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:top_n]
        print(f"[ML] 双模型融合加载{len(probs)}只概率，已筛选top {len(sorted_probs)}只")
        return dict(sorted_probs)
    except Exception as e:
        print(f"[ML] 概率加载失败: {e}")
        return {}


def run_scan(date=None, use_mx=False):
    """执行扫描（量化+供应链+MX实时三重驱动）"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    version = "V3.0（量化+供应链+MX实时）" if use_mx else "V3.0（量化+供应链）"
    print("=" * 70)
    print(f"尾盘精选策略扫描 {version} {date}")
    print("=" * 70)
    
    # 加载知识库
    tier_map = load_supply_chain_tiers()
    print(f"\n[INFO] 知识库加载：{len(tier_map)} 只卡点股票（S/A/B级）")
    
    # 加载ML概率
    ml_probs = load_ml_probabilities(top_n=5000) if use_mx else {}

    # 加载因子IC状态（用于动态权重调整）
    factor_ic_weights = {}
    try:
        ic_path = os.path.join(WORK_DIR, 'out_data', f'factor_ic_{date}.json')
        if not os.path.exists(ic_path):
            # 找最近的
            for d in range(1, 10):
                test_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=d)).strftime('%Y-%m-%d')
                test_path = os.path.join(WORK_DIR, 'out_data', f'factor_ic_{test_date}.json')
                if os.path.exists(test_path):
                    ic_path = test_path
                    break
        if os.path.exists(ic_path):
            with open(ic_path, encoding='utf-8') as f:
                ic_data = json.load(f)
            for f_entry in ic_data.get('factors', []):
                status = f_entry.get('status', '')
                mean_ic = f_entry.get('mean_ic', 0)
                # active: 权重1.0, inverse: 权重0.5(取反信号弱), watch: 0.3, eliminated: 0
                if status == 'active':
                    factor_ic_weights[f_entry['factor']] = 1.0
                elif status == 'inverse':
                    factor_ic_weights[f_entry['factor']] = 0.5  # 负IC取反信号，减半权重
                elif status == 'watch':
                    factor_ic_weights[f_entry['factor']] = 0.3
                else:
                    factor_ic_weights[f_entry['factor']] = 0.0
            print(f"[IC] 因子IC权重加载: {len(factor_ic_weights)}个因子")
            active_cnt = sum(1 for v in factor_ic_weights.values() if v > 0)
            print(f"[IC] 有效因子: {active_cnt}个 (active={sum(1 for v in factor_ic_weights.values() if v>=1.0)}, inverse={sum(1 for v in factor_ic_weights.values() if v==0.5)})")
    except Exception as e:
        print(f"[IC] 因子IC权重加载失败: {e}")
        factor_ic_weights = {}

    # 加载PPE周期编码数据（板块RPS + 股票板块映射）
    ppe_rps_data = None
    ppe_mapping = None
    try:
        from ppe_factor import load_ppe_data, batch_ppe_score
        ppe_rps_data, ppe_mapping = load_ppe_data()
        if ppe_rps_data:
            print(f"[PPE] 板块RPS数据加载成功: {len(ppe_rps_data)}个板块, 映射{len(ppe_mapping)}只股票")
    except Exception as e:
        print(f"[PPE] 加载失败: {e}，跳过PPE评分")

    if use_mx and mx_enabled():
        # ===== MX智能选股通道（全市场筛选）=====
        print(f"\n[Step 1] MX智能选股（全市场筛选）...")
        # 用xuangu筛选涨幅2~8%的全市场股票
        candidates = screen_mx_xuangu(chg_min=2.0, chg_max=8.0)
        
        if not candidates:
            print("  [xuangu] 无候选，切DB模式...")
            use_mx = False
        else:
            # 叠加ML概率（支持sh./sz.前缀格式）
            if ml_probs:
                for s in candidates:
                    code = s['code']
                    prob = ml_probs.get(code, 0.0)
                    if prob == 0.0:
                        # 尝试带前缀
                        for prefix in ['sh.', 'sz.', 'bj.']:
                            prob = ml_probs.get(prefix + code, 0.0)
                            if prob > 0:
                                break
                    s['ml_prob'] = prob
            else:
                for s in candidates:
                    s['ml_prob'] = 0.0
            
            # 叠加供应链
            for s in candidates:
                tier_info = verify_supply_chain(s['code'], tier_map)
                if tier_info:
                    s['supply_tier'], s['industry'], s['bottleneck'] = tier_info
                else:
                    s['supply_tier'], s['industry'], s['bottleneck'] = '', '', ''

            # DB补充换手率（避免xuangu候选缺字段被过滤）
            candidates = enrich_from_db(candidates, date)

            # 叠加舆情信号（对top30候选查询mx-search，取前30只）
            # 预排序取top30降低API消耗
            if mx_enabled():
                candidates_sorted = sorted(candidates, key=lambda x: (
                    x.get('ml_prob', 0) * 40 +
                    min(x.get('turnover', 0) / 10.0, 1.0) * 25 +
                    {'S': 12, 'A': 7, 'B': 3}.get(x.get('supply_tier', ''), 0),
                ), reverse=True)[:30]
                print(f"\n[Step2] MX舆情信号查询（top10候选，超时5秒/只）...")
                import signal
                def _timeout_handler(signum, frame):
                    raise TimeoutError('MX API超时')
                api_calls = 0
                for s in candidates_sorted[:10]:  # 只查top10，防止OS杀进程
                    try:
                        import time
                        start_t = time.time()
                        sn = query_mx_news_score(s['code'])
                        elapsed = time.time() - start_t
                        if elapsed > 8:
                            print(f'  [舆情] {s["code"]} 超时({elapsed:.1f}s)，跳过')
                            continue
                        s['sentiment_score'] = sn.get('sentiment_score', 0)
                        s['sentiment_keywords'] = sn.get('keywords', [])
                        api_calls += 1
                    except Exception as e:
                        s.setdefault('sentiment_score', 0)
                        s.setdefault('sentiment_keywords', [])
                        print(f'  [舆情] {s["code"]} 失败: {str(e)[:50]}')
                # 对未查询的候选设默认0
                for s in candidates:
                    s.setdefault('sentiment_score', 0)
                    s.setdefault('sentiment_keywords', [])
                print(f"  [舆情] 成功{api_calls}/10只，保留全部{len(candidates)}只候选" if api_calls > 0 else f"  [舆情] API失败，保留{len(candidates)}只xuangu原始候选")
            else:
                for s in candidates:
                    s['sentiment_score'] = 0
                    s['sentiment_keywords'] = []

            # PPE周期编码评分（对候选股批量计算）
            if ppe_rps_data and ppe_mapping:
                candidates = batch_ppe_score(candidates, ppe_rps_data, ppe_mapping, date)

            # 过滤条件（2~8% + 有换手率）
            df = pd.DataFrame(candidates)
            df = df[
                (df['chg_pct'] >= 2.0) &
                (df['chg_pct'] <= 8.0) &
                (df['turnover'] >= 0)  # 允许换手率未知（xuangu原始候选chg_pct有效即可通过
            ]
            
            # 综合评分
            def score(row):
                s = 0.0
                # ML概率权重40%
                s += row.get('ml_prob', 0) * 40
                # 换手率权重25%（越高越好）
                s += min(row.get('turnover', 0) / 10.0, 1.0) * 25
                # 量比权重15%（越高越好）
                s += min(row.get('vol_ratio', 0) / 3.0, 1.0) * 15
                # 供应链加分（S/A/B降权，释放给舆情）
                tier = row.get('supply_tier', '')
                s += {'S': 12, 'A': 7, 'B': 3}.get(tier, 0)
                # 舆情信号加分（正面+15，负面-15）
                sentiment = row.get('sentiment_score', 0)
                s += sentiment * 5  # sentiment_score是整数，正面=正，负面=负
                # 月末效应（每月最后5个交易日，权重+10分）
                today = datetime.now()
                month_day = today.day
                days_in_month = (datetime(today.year, today.month + 1, 1) - timedelta(days=1)).day if today.month < 12 else 31
                days_left = days_in_month - month_day
                if days_left <= 5:
                    s += (6 - days_left) * 2  # 最后1天+10，最后5天+2
                # 现金流/净利润比（>0为正分，<-50%为负分）
                cash_ratio = row.get('cash_net_ratio', 0)
                if cash_ratio > 0.5:
                    s += 8  # 现金流健康
                elif cash_ratio < -0.5:
                    s -= 10  # 现金流异常
                # PPE周期编码因子（+0~+13分，从ppe_info获取）
                ppe_score = row.get('ppe_score', 0)
                s += ppe_score
                return s
            
            df['score'] = df.apply(score, axis=1)
            df = df.sort_values('score', ascending=False)
            
            print(f"\n{'='*70}")
            print(f"[MX智能选股候选] {len(df)} 只（评分排序）")
            print(f"{'='*70}")
            for _, row in df.head(15).iterrows():
                tier = row.get('supply_tier', '')
                tier_icon = f"[{tier}]" if tier else "   "
                ml = f"ML:{row.get('ml_prob', 0):.3f}" if row.get('ml_prob', 0) > 0 else ""
                chg = f"{row.get('chg_pct', 0):+.2f}%"
                turnover = f"换手:{row.get('turnover', 0):.2f}%"
                vr = f"量比:{row.get('vol_ratio', 0):.2f}"
                ind = row.get('industry', '')
                bot = row.get('bottleneck', '')
                name = row.get('name', '')
                sn_score = row.get('sentiment_score', 0)
                sn_icon = '📰+' if sn_score > 0 else '📰-' if sn_score < 0 else '📰~'
                sn_kw = ','.join(row.get('sentiment_keywords', [])[:3])
                ppe_str = f"PPE:{row.get('ppe_score', 0):+d}" if row.get('ppe_score', 0) != 0 else ""
                ppe_board = row.get('ppe_board', '')
                ppe_phase = row.get('ppe_phase', '')
                print(f"  {tier_icon} {row['code']} {name} {ml}")
                print(f"       涨幅:{chg} | {turnover} | {vr} | {sn_icon}{sn_score} | {ppe_str} | 分:{row.get('score', 0):.1f}")
                if ind:
                    print(f"       {ind} | {bot}")
                if ppe_board and ppe_board != '未知':
                    print(f"       [PPE] {ppe_board} - {ppe_phase}")
                if sn_kw:
                    print(f"       舆情: {sn_kw}")
            
            # 保存结果（含舆情）
            df_out = df.copy()
            df_out['sentiment_score'] = df_out.get('sentiment_score', 0)
            df_out['sentiment_keywords'] = df_out.get('sentiment_keywords', '').apply(lambda x: ','.join(x) if isinstance(x, list) else str(x))
            cols = ['code', 'name', 'chg_pct', 'turnover', 'vol_ratio', 'ml_prob',
                    'supply_tier', 'industry', 'sentiment_score', 'sentiment_keywords', 'ppe_score', 'ppe_board', 'ppe_phase', 'score']
            df_out = df_out[[c for c in cols if c in df_out.columns]]
            df_out.to_csv(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\logs\xuangu_candidates.csv',
                         index=False, encoding='utf-8-sig')
            print(f"\n  → 结果已保存（含舆情评分）")
            # 保存ML概率快照用于T+1验证
            save_ml_snapshot(df, date)

            # ─── 持仓联动检查 ───────────────────────────────────
            try:
                pf_path = os.path.join(WORK_DIR, 'data', 'portfolio.json')
                if os.path.exists(pf_path):
                    with open(pf_path, encoding='utf-8') as f:
                        portfolio = json.load(f)
                    for h in portfolio.get('holdings', []):
                        code = h.get('code', '')
                        name = h.get('name', code)
                        buy_price = h.get('buy_price', 0)
                        current_price = h.get('current_price', 0)
                        pct = h.get('profit_loss_pct', 0)
                        shares = h.get('shares', 0)
                        ml_p = ml_probs.get(code, 0.0)
                        if ml_p == 0.0:
                            for prefix in ['sh.', 'sz.', 'bj.']:
                                ml_p = ml_probs.get(prefix + code, 0.0)
                                if ml_p > 0:
                                    break
                        signals = []
                        # ML概率偏低警告
                        if ml_p < 0.3 and ml_p > 0:
                            signals.append('ML看弱(概率{:.0%})'.format(ml_p))
                        # 浮盈触发止盈
                        if pct > 20:
                            signals.append('累计涨幅{:.1f}%>20%，建议减仓1/3'.format(pct))
                        elif pct > 15:
                            signals.append('浮盈{:.1f}%，动态止损已上移至{:.2f}'.format(pct, h.get('dynamic_stop', 0)))
                        # 浮亏触发止损
                        if pct < -5:
                            signals.append('已跌破5%止损线({:.2f})'.format(h.get('stop_loss_5', 0)))
                        elif pct < -15:
                            signals.append('已跌破15%硬止损({:.2f})，必须清仓'.format(h.get('stop_loss_15', 0)))
                        # 单日涨幅>7%止盈
                        pct_chg = None
                        for _, r in df.iterrows():
                            if r.get('code') in code or code in r.get('code', ''):
                                pct_chg = r.get('chg_pct')
                                break
                        if pct_chg and pct_chg > 7:
                            signals.append('单日涨幅{:.1f}%>7%，建议减仓1/3'.format(pct_chg))
                        
                        if signals:
                            print()
                            print(f'[持仓] ⚠️ {name}({code}) ML:{ml_p:.2%} 浮盈:{pct:+.1f}%')
                            for s in signals:
                                print(f'       → {s}')
                        else:
                            print(f'[持仓] ✅ {name}({code}) ML:{ml_p:.2%} 浮盈:{pct:+.1f}% 正常')
            except Exception as e:
                print(f'[持仓] 检查失败: {e}')

            print("=" * 70)
            return df
    
    if not use_mx or not mx_enabled():
        # ===== DB通道模式（原有逻辑）=====
        print("\n[Step 1] 量化筛选候选股（DB通道）...")
        candidates = scan_stocks_quantitative(date)
        print(f"   量化筛选结果：{len(candidates)} 只候选")
        if len(candidates) == 0:
            print("\n今日无符合条件股票")
            return candidates
        
        # Step 2: 供应链卡点验证
        print("\n[Step 2] 供应链卡点验证...")
        verified = verify_candidates_with_supply_chain(candidates, tier_map)
        
        if len(verified) > 0:
            verified = verified.sort_values('supply_chain_score', ascending=False)
            print(f"   卡点匹配：{len(verified)} 只")
            with_tier = verified[verified['supply_tier'].isin(['S', 'A', 'B'])]
            without_tier = verified[~verified['supply_tier'].isin(['S', 'A', 'B'])]
            
            print(f"\n{'='*70}")
            print(f"[S/A级卡点优先] ({len(with_tier[with_tier['supply_tier'].isin(['S','A'])]) if len(with_tier) > 0 else 0} 只)")
            print(f"{'='*70}")
            s_a_stocks = with_tier[with_tier['supply_tier'].isin(['S', 'A'])]
            for i, (_, row) in enumerate(s_a_stocks.head(5).iterrows(), 1):
                tier_icon = "[S]" if row['supply_tier'] == 'S' else "[A]"
                t = f"{row['turnover']:.1f}%" if pd.notna(row.get('turnover')) else "N/A"
                print(f"  {tier_icon} {row['code']} | {row['industry']} | {row['bottleneck']}")
                print(f"      今日:{row['chg_pct']:+.2f}% | 量比:{row['vol_ratio']:.2f} | 近3日:{row['chg_3d']:+.2f}% | 换手:{t}")
            
            print(f"\n{'='*70}")
            print(f"[B级卡点] ({len(with_tier[with_tier['supply_tier'] == 'B'])} 只)")
            print(f"{'='*70}")
            b_stocks = with_tier[with_tier['supply_tier'] == 'B']
            for i, (_, row) in enumerate(b_stocks.head(5).iterrows(), 1):
                t = f"{row['turnover']:.1f}%" if pd.notna(row.get('turnover')) else "N/A"
                print(f"  [B] {row['code']} | {row['industry']} | {row['bottleneck']}")
                print(f"      今日:{row['chg_pct']:+.2f}% | 量比:{row['vol_ratio']:.2f} | 近3日:{row['chg_3d']:+.2f}%")
            
            if len(without_tier) > 0:
                print(f"\n{'='*70}")
                print(f"[量化候选无卡点] ({len(without_tier)} 只)")
                print(f"{'='*70}")
                for i, (_, row) in enumerate(without_tier.head(3).iterrows(), 1):
                    t = f"{row['turnover']:.1f}%" if pd.notna(row.get('turnover')) else "N/A"
                    print(f"  {i}. {row['code']} | 今日:{row['chg_pct']:+.2f}% | 量比:{row['vol_ratio']:.2f} | 换手:{t}")
        else:
            print("   无卡点匹配，仅输出量化候选")
            for i, (_, row) in enumerate(candidates.head(5).iterrows(), 1):
                t = f"{row['turnover']:.1f}%" if pd.notna(row.get('turnover')) else "N/A"
                print(f"  {i:2d}. {row['code']} | 今日:{row['chg_pct']:+.2f}% | 量比:{row['vol_ratio']:.2f} | 近3日:{row['chg_3d']:+.2f}% | 换手:{t}")
        return verified if len(verified) > 0 else candidates
    
    print()
    print("=" * 70)

    # 记录Top候选到推荐追踪系统
    try:
        from scripts.recommendation_tracker import record_recommendation
        top_candidates = candidates.head(5) if isinstance(candidates, pd.DataFrame) else []
        for _, row in top_candidates.iterrows():
            code = row.get('code', '')
            name = row.get('name', code)
            price = row.get('close', row.get('price', None))
            score = row.get('score', 0)
            if code and score > 0:
                record_recommendation(
                    source='strategy_scan',
                    code=code,
                    name=str(name),
                    price=float(price) if price else None,
                    reason=f"策略扫描 评分{score:.1f}"
                )
        print(f"[追踪] Top5候选已记录到推荐追踪系统")
    except Exception as e:
        print(f"[追踪] 记录失败: {e}")

    # 写入Supermemory
    _save_to_memory(date, candidates, version)


def _save_to_memory(date, candidates, version):
    """将策略扫描结果写入Supermemory投资库"""
    try:
        import sys as _sys
        _sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'memory'))
        from memory_tools import MemoryTools
        mt = MemoryTools()
        
        top_n = 10
        summary_lines = []
        summary_lines.append(f"尾盘策略扫描 {version} {date}")
        summary_lines.append(f"")
        
        if isinstance(candidates, pd.DataFrame) and not candidates.empty:
            top = candidates.head(top_n)
            for _, row in top.iterrows():
                code = row.get('code', '')
                name = row.get('name', code)
                score = row.get('score', 0)
                summary_lines.append(f"  {name}({code}): 评分{score:.1f}")
        
        mt.save_memory(
            '\n'.join(summary_lines),
            category='strategy',
            domain='investment'
        )
        print(f"[memory] 策略结果已写入Supermemory")
    except ImportError:
        print(f"[memory] 跳过（memory_tools不可用）")
    except Exception as e:
        print(f"[memory] 写入失败: {e}")


if __name__ == '__main__':
    import sys
    use_mx = '--mx' in sys.argv
    date = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != '--mx' else datetime.now().strftime('%Y-%m-%d')
    run_scan(date, use_mx=use_mx)