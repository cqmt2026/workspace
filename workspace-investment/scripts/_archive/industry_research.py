"""
行业研究报告生成器 v2.1（投资建议增强版）
在v2.0基础上新增：

  ⑤投资建议：
    - 综合评级（强烈推荐/关注/中性/回避）
    - 核心逻辑（资金+基本面+研报三维度）
    - 估值判断（当前PE vs 历史中枢）
    - 风险点
    - 操作建议（买入/持有/观望）

数据来源整合：
  - 板块RPS → 资金态度
  - 成分股平均RPS → 强势程度
  - 研报评级分布 → 机构共识
  - 财务（毛利率/ROE） → 基本面健康度
  - PE预测 → 估值定位

评级算法：
  score = RPS得分×0.3 + 基本面得分×0.3 + 研报得分×0.2 + 资金得分×0.2
  - 80+ → 强烈推荐⭐
  - 65-79 → 关注✅
  - 50-64 → 中性⚠️
  - <50 → 回避❌
"""
import akshare as ak
import json
import warnings
import os
import time
import re
from datetime import datetime, timedelta
from technical_target import technical_target

warnings.filterwarnings('ignore')

WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
OUT_DIR = WORK_DIR + r'\out_data'
CACHE_DIR = WORK_DIR + r'\data\cache'
OBSIDIAN_DIR = r'C:\Users\Administrator\Obsidian\Jarvis\03-知识\投资行业研究'

# =====================
# L0: 工具函数
# =====================
def retry_apicall(fn, *args, max_retries=3, delay=2, **kwargs):
    last_error = None
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_error = str(e)[:80]
            if attempt < max_retries - 1:
                time.sleep(delay)
    return None

def find_board_code(concept_name):
    cache_file = CACHE_DIR + r'\concept_boards_list.json'
    boards = None

    # Load from cache if exists
    if os.path.exists(cache_file):
        try:
            cache = json.load(open(cache_file, encoding='utf-8'))
            boards = cache.get('boards', [])
        except:
            boards = None

    # Refresh cache if missing or empty
    if not boards:
        print('  [自动刷新板块列表缓存...]')
        try:
            import akshare as ak
            df = ak.stock_board_concept_name_em()
            boards = [{'name': str(r['板块名称']), 'code': str(r['板块代码'])} for _, r in df.iterrows()]
            json.dump({'boards': boards}, open(cache_file, 'w', encoding='utf-8'), ensure_ascii=False)
            print('  缓存已保存: ' + str(len(boards)) + ' 个板块')
        except Exception as e:
            print('  刷新失败: ' + str(e)[:60])
            return concept_name, None

    # Exact match first
    for b in boards:
        if b['name'] == concept_name:
            return b['name'], b['code']
    # Fuzzy match
    for b in boards:
        if concept_name in b['name'] or b['name'] in concept_name:
            return b['name'], b['code']
    return concept_name, None

# =====================
# L1: 成分股
# =====================
def get_concept_stocks(concept_name):
    board_name, board_code = find_board_code(concept_name)
    if not board_code:
        return [], concept_name
    df = retry_apicall(ak.stock_board_concept_cons_em, symbol=board_code, max_retries=5, delay=3)
    if df is None or len(df) == 0:
        # Fallback: use THS industry spot
        try:
            ind_df = ak.stock_board_industry_spot_ths(symbol=board_code)
            if ind_df is not None and len(ind_df) > 0:
                df = ind_df
        except:
            pass
    if df is None or len(df) == 0:
        return [], board_name
    stocks = []
    for _, r in df.iterrows():
        # Handle both EM and THS column naming
        code = str(r.get('代码') or r.get('code') or r.get('股票代码') or '')
        name = str(r.get('名称') or r.get('name') or r.get('股票名称') or r.get('名称') or '')
        price = float(r.get('最新价') or r.get('price') or r.get('现价') or 0)
        chg = float(r.get('涨跌幅') or r.get('chg') or r.get('涨跌幅(%)') or 0)
        pe = None
        for col in ['市盈率-动态', 'pe', 'PE', '市盈率']:
            v = r.get(col)
            if v and v not in ['-', '', None]:
                try:
                    pe = float(v)
                    break
                except:
                    pass
        pb = None
        for col in ['市净率', 'pb', 'PB', '市净率']:
            v = r.get(col)
            if v and v not in ['-', '', None]:
                try:
                    pb = float(v)
                    break
                except:
                    pass
        vol = float(r.get('成交额') or r.get('volume') or r.get('成交额(万元)') or 0)
        stocks.append({
            'code': code,
            'name': name,
            'price': price,
            'chg_pct': float(r.get('涨跌幅') or r.get('涨跌幅(%)') or 0),
            'pe': pe,
            'pb': pb,
            'volume': float(r.get('成交额') or r.get('volume') or r.get('成交额(万元)') or 0),
            })
    return stocks, board_name

# =====================
# L2: 个股RPS
# =====================
def get_stock_rps(code, today):
    f = OUT_DIR + '\\RPS_stock_' + today + '.json'
    if os.path.exists(f):
        try:
            d = json.load(open(f, encoding='utf-8'))
            for s in d.get('stocks_rps', []):
                if s.get('code') == code:
                    return s.get('rps'), s.get('rank')
        except:
            pass
    return None, None

# =====================
# L3: A. 公司主营业务
# =====================
def get_company_profile(code):
    df = retry_apicall(ak.stock_profile_cninfo, symbol=code, max_retries=3, delay=3)
    if df is None or len(df) == 0:
        return {}
    row = df.iloc[0]
    return {
        'main_business': str(row.get('主营业务', ''))[:500],
        'business_scope': str(row.get('经营范围', ''))[:500],
        'company_intro': str(row.get('机构简介', ''))[:600],
        'industry_cninfo': str(row.get('所属行业', '')),
        'reg_address': str(row.get('注册地址', ''))[:100],
        'website': str(row.get('官方网站', '')),
        'legal_rep': str(row.get('法人代表', '')),
        'reg_capital': str(row.get('注册资金', '')),
        'established': str(row.get('成立日期', '')),
        'listed_date': str(row.get('上市日期', '')),
    }

# =====================
# L4: B. 行业研报
# =====================
def get_research_reports(code, top_n=5):
    df = retry_apicall(ak.stock_research_report_em, symbol=code, max_retries=3, delay=3)
    if df is None or len(df) == 0:
        return []
    reports = []
    for _, r in df.head(top_n).iterrows():
        try:
            reports.append({
                'title': str(r.get('报告名称', '')),
                'rating': str(r.get('东财评级', '')),
                'institution': str(r.get('机构', '')),
                'date': str(r.get('日期', '')),
                'pe_2026': str(r.get('2026-盈利预测-市盈率', '')),
                'pe_2027': str(r.get('2027-盈利预测-市盈率', '')),
                'eps_2026': str(r.get('2026-盈利预测-收益', '')),
                'eps_2027': str(r.get('2027-盈利预测-收益', '')),
                'pdf_url': str(r.get('报告PDF链接', ''))[:100],
            })
        except:
            pass
    return reports

# =====================
# L5: C. 个股公告（批量）
# =====================
def get_stock_notices_batch(stocks, top_n_each=3):
    notices_map = {s['code']: [] for s in stocks}
    today = datetime.now()
    for days_ago in range(0, 3):
        date = (today - timedelta(days=days_ago)).strftime('%Y%m%d')
        try:
            df = retry_apicall(ak.stock_notice_report, date=date, max_retries=2, delay=1)
            if df is None or len(df) == 0:
                continue
            for s in stocks:
                code, name = s['code'], s['name']
                filtered = df[(df['名称'] == name) | (df['代码'] == code)]
                for _, r in filtered.head(top_n_each).iterrows():
                    notices_map[code].append({
                        'title': str(r.get('公告标题', '')),
                        'type': str(r.get('公告类型', '')),
                        'date': str(r.get('公告日期', '')),
                        'code': code,
                        'url': str(r.get('网址', ''))[:100],
                    })
        except:
            pass
    all_notices = []
    for code, notices in notices_map.items():
        all_notices.extend(notices)
    all_notices.sort(key=lambda x: x['date'], reverse=True)
    return all_notices[:top_n_each * len(stocks)]

# =====================
# L6: D. 公司基本信息
# =====================
def get_company_basic_info(code):
    df = retry_apicall(ak.stock_individual_info_em, symbol=code, max_retries=5, delay=3)
    if df is None:
        return {}
    info = {}
    for _, row in df.iterrows():
        item = str(row.get('item', ''))
        val = str(row.get('value', ''))
        info[item] = val
    return info

# =====================
# L7: 行业趋势
# =====================
def analyze_trend(stocks, today):
    if not stocks:
        return {}
    up = len([s for s in stocks if s['chg_pct'] > 0])
    dn = len([s for s in stocks if s['chg_pct'] < 0])
    avg_chg = sum(s['chg_pct'] for s in stocks) / len(stocks)
    rps_vals = []
    for s in stocks[:15]:
        r = get_stock_rps(s['code'], today)[0]
        if r:
            rps_vals.append(r)
    avg_rps = sum(rps_vals) / len(rps_vals) if rps_vals else 50
    strength = '强势' if avg_rps >= 70 else ('中性' if avg_rps >= 50 else '弱势')
    return {
        'total': len(stocks), 'up': up, 'down': dn,
        'avg_chg': round(avg_chg, 2),
        'avg_rps': round(avg_rps, 2),
        'strength': strength,
    }

# =====================
# L8: 核心公司财务
# =====================
def get_financials(codes):
    results = []
    for code in codes[:6]:
        df = retry_apicall(
            ak.stock_financial_analysis_indicator,
            symbol=code, start_year=str(datetime.now().year - 3),
            max_retries=2, delay=1
        )
        if df is not None and len(df) > 0:
            latest = df.iloc[0]
            results.append({
                'code': code,
                'revenue_yoy': round(float(latest.get('营业收入增长率(%)', 0) or 0), 1),
                'gross_margin': round(float(latest.get('主营业务利润率(%)', 0) or 0), 1),
                'roe': round(float(latest.get('总资产利润率(%)', 0) or 0), 1),
            })
    return results

# =====================
# L9: 投资建议分析
# =====================
def analyze_investment_advice(board_name, stocks, trend, financials, reports, tech_targets, today):
    """综合评分 + 投资建议"""
    # === 1. 板块RPS得分（资金态度，30%）===
    board_rps_file = OUT_DIR + '\\RPS_concept_' + today + '.json'
    board_rps = 50
    if os.path.exists(board_rps_file):
        try:
            d = json.load(open(board_rps_file, encoding='utf-8'))
            for r in d.get('rps_data', []):
                if r['board_name'] == board_name:
                    board_rps = r.get('rps', 50)
                    break
        except:
            pass

    rps_score = min(board_rps, 100)  # 板块RPS直接当分数

    # === 2. 基本面得分（30%）===
    if financials:
        avg_margin = sum(f['gross_margin'] for f in financials) / len(financials)
        avg_roe = sum(f['roe'] for f in financials) / len(financials)
        # 毛利率>30% = 好，>20% = 中，<20% = 差
        if avg_margin >= 30:
            margin_score = 100
        elif avg_margin >= 20:
            margin_score = 70
        else:
            margin_score = 40
        # ROE>10% = 好，>5% = 中，<5% = 差
        if avg_roe >= 10:
            roe_score = 100
        elif avg_roe >= 5:
            roe_score = 70
        else:
            roe_score = 40
        basic_score = (margin_score * 0.6 + roe_score * 0.4)
    else:
        avg_margin, avg_roe = 0, 0
        basic_score = 50

    # === 3. 研报得分（20%）===
    if reports:
        # 统计评级分布
        rating_map = {'强烈推荐': 100, '买入': 80, '增持': 60, '中性': 40, '回避': 20}
        scores = []
        for r in reports:
            rating = r.get('rating', '中性')
            # 模糊匹配
            score = 50
            for k, v in rating_map.items():
                if k in rating:
                    score = v
                    break
            # 尝试从标题判断
            if '首次覆盖' in rating or '深度' in rating:
                score = max(score, 85)
            elif '下调' in r.get('title', '') or '风险' in r.get('title', ''):
                score = min(score, 40)
            scores.append(score)
        report_score = sum(scores) / len(scores)
        report_count = len(reports)
        report_top_rating = max(scores) if scores else 50
    else:
        report_score = 50
        report_count = 0
        report_top_rating = 50

    # === 4. 资金得分（20%）===
    if trend:
        # 上涨家数占比
        up_ratio = trend.get('up', 0) / max(trend.get('total', 1), 1)
        avg_chg = trend.get('avg_chg', 0)
        # 上涨家数多 + 平均涨幅正 = 强
        if up_ratio >= 0.7 and avg_chg > 1:
            money_score = 90
        elif up_ratio >= 0.5 and avg_chg > 0:
            money_score = 70
        elif up_ratio >= 0.4:
            money_score = 55
        else:
            money_score = 40
    else:
        money_score = 50

    # === 综合评分 ===
    total_score = round(
        rps_score * 0.3 +
        basic_score * 0.3 +
        report_score * 0.2 +
        money_score * 0.2
    )

    # === 评级 ===
    if total_score >= 80:
        rating = '[推荐]强烈推荐'
        rating_en = 'STRONG BUY'
        color = '[GREEN]'
    elif total_score >= 65:
        rating = '[关注]'
        rating_en = 'BUY'
        color = '[YELLOW]'
    elif total_score >= 50:
        rating = '[中性]'
        rating_en = 'NEUTRAL'
        color = '[ORANGE]'
    else:
        rating = '[回避]'
        rating_en = 'AVOID'
        color = '[RED]'

    # === 技术面估值分析（从技术指标计算）===
    # tech_targets: {code: {target, stop, upside_pct, risk_pct, trend, strategy, cur_price, ...}}
    tech_valid = [v for v in (tech_targets or {}).values() if v]
    if tech_valid:
        # 板块整体技术面判断
        up_trends = sum(1 for v in tech_valid if v.get('trend') == '上升趋势')
        dn_trends = sum(1 for v in tech_valid if v.get('trend') == '下降趋势')
        avg_upside = round(sum(v.get('upside_pct', 0) for v in tech_valid) / len(tech_valid), 1)
        avg_stop = round(sum(v.get('risk_pct', 0) for v in tech_valid) / len(tech_valid), 1)
        # 板块整体技术评级
        if up_trends >= len(tech_valid) * 0.6:
            tech_comment = '技术面良好（' + str(up_trends) + '/' + str(len(tech_valid)) + '只上升趋势）'
        elif dn_trends >= len(tech_valid) * 0.6:
            tech_comment = '技术面偏弱（' + str(dn_trends) + '/' + str(len(tech_valid)) + '只下降趋势）'
        else:
            tech_comment = '技术面分化（上升' + str(up_trends) + '只/下降' + str(dn_trends) + '只）'
        # 用技术面修正操作建议
        if tech_comment.startswith('技术面良好'):
            tech_action_suffix = '技术面强势，顺势关注。'
        elif tech_comment.startswith('技术面分化'):
            tech_action_suffix = '注意内部分化，精选个股。'
        else:
            tech_action_suffix = '技术面偏弱，谨慎。'
        tech_analysis = {
            'stocks_analysed': len(tech_valid),
            'up_trends': up_trends,
            'dn_trends': dn_trends,
            'avg_upside': avg_upside,
            'avg_stop': avg_stop,
            'comment': tech_comment,
            'action_suffix': tech_action_suffix,
        }
    else:
        tech_analysis = None

    # === 核心逻辑 ===
    logic = []
    if rps_score >= 70:
        logic.append('资金强势：板块RPS ' + str(round(rps_score)) + '，资金持续流入')
    if basic_score >= 70:
        logic.append('基本面健康：平均毛利率 ' + str(round(avg_margin, 1)) + '%，ROE ' + str(round(avg_roe, 1)) + '%')
    elif basic_score >= 50:
        logic.append('基本面一般：平均毛利率 ' + str(round(avg_margin, 1)) + '%')
    if report_score >= 70:
        logic.append('机构看多：' + str(report_count) + '篇研报，最高评级' + str(report_top_rating) + '分')
    if money_score >= 70:
        logic.append('市场情绪好：上涨家数占比 ' + str(round(up_ratio * 100)) + '%')

    # === 风险点 ===
    risks = []
    if tech_analysis and tech_analysis.get('avg_upside', 0) < 5:
        risks.append('技术面提示：平均上涨空间不足5%，性价比一般')
    if tech_analysis and tech_analysis.get('comment', '').startswith('技术面偏弱'):
        risks.append('技术面偏弱，注意止损')
    if basic_score < 50:
        risks.append('基本面偏弱：毛利率/ROE低于行业平均')
    if rps_score < 50:
        risks.append('资金偏弱：RPS低于50，关注趋势是否持续')
    if trend and trend.get('up', 0) < trend.get('down', 0):
        risks.append('下跌家数多于上涨，板块内部分化')
    if not reports:
        risks.append('暂无机构研报覆盖，缺乏专业背书')
    if not risks:
        risks.append('未发现明显风险点')

    # === 操作建议 ===
    tech_suffix = (tech_analysis or {}).get('action_suffix', '')
    if total_score >= 80:
        action = '建议重点关注，择机布局。' + tech_suffix
    elif total_score >= 65:
        action = '可以关注，等待更好的入场时机。' + tech_suffix
    elif total_score >= 50:
        action = '保持观察，不盲目追入。' + tech_suffix
    else:
        action = '建议回避，等基本面改善。' + tech_suffix

    return {
        'total_score': total_score,
        'rating': rating,
        'rating_en': rating_en,
        'color': color,
        'rps_score': round(rps_score, 1),
        'basic_score': round(basic_score, 1),
        'report_score': round(report_score, 1),
        'money_score': round(money_score, 1),
        'avg_margin': round(avg_margin, 1) if financials else 0,
        'avg_roe': round(avg_roe, 1) if financials else 0,
        'report_count': report_count,
        'report_top_rating': round(report_top_rating, 1),
        'tech_analysis': tech_analysis,
        'logic': logic,
        'risks': risks,
        'action': action,
    }

# =====================
# L10: 生成报告
# =====================
def generate_report(concept_name, board_name, stocks, trend, financials,
                   profiles, reports, notices, advice,
                   trigger_type, today):
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    safe = concept_name.replace('/', '_').replace('\\', '_')
    name_map = {s['code']: s['name'] for s in stocks}

    lines = []
    lines.append('# ' + board_name + ' 行业研究')
    lines.append('')
    lines.append('> **生成时间**: ' + now_str + '  |  **触发**: ' + trigger_type + '  |  **数据日期**: ' + today)
    lines.append('> **框架**: ①趋势 -> ②产业链 -> ③核心段 -> ④核心公司 -> ⑤投资建议')
    lines.append('')
    lines.append('---')
    lines.append('')

    # === ①行业趋势 ===
    lines.append('## ① 行业趋势')
    lines.append('')
    if trend:
        lines.append('| 指标 | 数值 |')
        lines.append('|------|------|')
        lines.append('| 成分股数量 | ' + str(trend.get('total', len(stocks))) + ' |')
        lines.append('| 上涨家数 | ' + str(trend.get('up', 0)) + ' |')
        lines.append('| 下跌家数 | ' + str(trend.get('down', 0)) + ' |')
        lines.append('| 平均涨跌幅 | ' + str(trend.get('avg_chg', 0)) + '% |')
        lines.append('| 成分股均RPS | ' + str(trend.get('avg_rps', 'N/A')) + ' |')
        lines.append('| 资金态度 | ' + trend.get('strength', '未知') + ' |')
    lines.append('')
    lines.append('> [待填写] 行业所处周期：导入期 / 成长期 / 成熟期 / 衰退期？')
    lines.append('> [待填写] 近1年市场规模增速？核心驱动因素？')
    lines.append('')
    lines.append('---')
    lines.append('')

    # === ②产业链 ===
    lines.append('## ② 产业链结构')
    lines.append('')
    lines.append('> [待填写] 按以下格式填写：')
    lines.append('> - **上游**：原材料/元器件')
    lines.append('> - **中游**：制造/加工')
    lines.append('> - **下游**：终端应用/品牌')
    lines.append('> - **关键节点**：哪个环节最卡脖子？谁有定价权？')
    lines.append('')
    if stocks:
        core = sorted(stocks, key=lambda x: x.get('volume', 0), reverse=True)[:10]
        lines.append('### 资金关注核心标的（今日成交额TOP10）')
        lines.append('')
        lines.append('| 排名 | 代码 | 名称 | 最新价 | 涨跌幅 | PE | PB |')
        lines.append('|------|------|------|--------|--------|---|---|--|')
        for i, s in enumerate(core, 1):
            pe = str(round(s['pe'], 1)) if s.get('pe') else '-'
            pb = str(round(s['pb'], 1)) if s.get('pb') else '-'
            chg = '{:+.2f}'.format(s['chg_pct']) if s.get('chg_pct') else '-'
            lines.append('| ' + str(i) + ' | ' + s['code'] + ' | ' + s['name'] +
                        ' | ' + str(s.get('price', '-')) + ' | ' + chg + ' | ' + pe + ' | ' + pb + ' |')
        lines.append('')
    lines.append('---')
    lines.append('')

    # === ③核心段 ===
    lines.append('## ③ 核心段分析（成本结构）')
    lines.append('')
    lines.append('> [待填写] 成本占比最高的环节是哪个？为什么能拿走最多利润？（技术壁垒/资质壁垒/规模效应）')
    lines.append('> [待填写] 谁被卡脖子？谁有定价权？')
    lines.append('')
    if financials:
        lines.append('### 核心公司财务摘要')
        lines.append('')
        lines.append('| 代码 | 名称 | 营收增长(%) | 毛利率(%) | ROE(%) |')
        lines.append('|------|------|-----------|---------|-------|')
        for b in financials:
            name = name_map.get(b['code'], b['code'])
            lines.append('| ' + b['code'] + ' | ' + name +
                        ' | ' + str(b['revenue_yoy']) + ' | ' + str(b['gross_margin']) +
                        ' | ' + str(b['roe']) + ' |')
        lines.append('')
    lines.append('---')
    lines.append('')

    # === ④核心公司 & 跟踪 ===
    lines.append('## ④ 核心公司 & 持续跟踪')
    lines.append('')
    if stocks:
        sorted_s = sorted(stocks, key=lambda x: x.get('chg_pct', 0), reverse=True)
        lines.append('### 成分股涨跌幅排名')
        lines.append('')
        lines.append('| 排名 | 代码 | 名称 | 最新价 | 涨跌幅(%) | PE | PB |')
        lines.append('|------|------|------|--------|-----------|---|--|')
        for i, s in enumerate(sorted_s[:20], 1):
            pe = str(round(s['pe'], 1)) if s.get('pe') else '-'
            pb = str(round(s['pb'], 1)) if s.get('pb') else '-'
            chg = '{:+.2f}'.format(s['chg_pct']) if s.get('chg_pct') else '-'
            lines.append('| ' + str(i) + ' | ' + s['code'] + ' | ' + s['name'] +
                        ' | ' + str(s.get('price', '-')) + ' | ' + chg + ' | ' + pe + ' | ' + pb + ' |')
        lines.append('')
    lines.append('### 持续跟踪标的')
    lines.append('')
    lines.append('> [待填写] 以下标的值得长期跟踪：')
    lines.append('> 1. （标的名称/代码 - 跟踪理由）')
    lines.append('> 2. （标的名称/代码 - 跟踪理由）')
    lines.append('> 3. （标的名称/代码 - 跟踪理由）')
    lines.append('')
    lines.append('---')
    lines.append('')

    # === A. 公司主营业务 ===
    if profiles:
        lines.append('## A. 公司主营业务')
        lines.append('')
        lines.append('| 代码 | 名称 | 主营业务摘要 |')
        lines.append('|------|------|---------------|')
        for code, p in profiles.items():
            main = p.get('main_business', '')[:60]
            lines.append('| ' + code + ' | ' + p.get('name', '') + ' | ' + main + ' |')
        lines.append('')
        lines.append('---')
        lines.append('')

    # === B. 行业研报 ===
    if reports:
        lines.append('## B. 行业最新研报')
        lines.append('')
        lines.append('| 日期 | 股票 | 评级 | 机构 | 2026PE | 2027PE | 报告标题 |')
        lines.append('|------|------|------|------|--------|--------|----------|')
        for r in reports:
            lines.append('| ' + r['date'] + ' | ' + r.get('code', '') + ' | ' + r['rating'] +
                        ' | ' + r['institution'] + ' | ' + r['pe_2026'] +
                        ' | ' + r['pe_2027'] + ' | ' + r['title'][:50] + ' |')
        lines.append('')
        lines.append('---')
        lines.append('')

    # === C. 个股公告 ===
    if notices:
        lines.append('## C. 近30日个股公告')
        lines.append('')
        lines.append('| 日期 | 股票 | 公告类型 | 标题 |')
        lines.append('|------|------|----------|------|')
        for n in notices:
            lines.append('| ' + n['date'] + ' | ' + n.get('code', '') + ' | ' + n['type'] +
                        ' | ' + n['title'][:50] + ' |')
        lines.append('')
        lines.append('---')
        lines.append('')

    # === D. 管理层 ===
    if profiles:
        lines.append('## D. 公司管理层基础信息')
        lines.append('')
        for code, p in list(profiles.items())[:3]:
            name = p.get('name', '')
            basic = p.get('basic_info', {})
            if basic:
                lines.append('### ' + name + '（' + code + '）')
                lines.append('')
                lines.append('| 项目 | 信息 |')
                lines.append('|------|------|')
                for k, v in basic.items():
                    if v and v not in ['nan', '']:
                        lines.append('| ' + k + ' | ' + str(v)[:80] + ' |')
                lines.append('')
        lines.append('---')
        lines.append('')

    # === ⑤投资建议（新增）===
    if advice:
        lines.append('## ⑤ 投资建议')
        lines.append('')
        # 综合评级大字
        a = advice
        lines.append('### 综合评级：' + a['color'] + ' ' + a['rating'] + '（' + str(a['total_score']) + '分）')
        lines.append('')
        lines.append('| 评分维度 | 得分 | 权重 | 说明 |')
        lines.append('|------|------|------|------|')
        lines.append('| 资金态度（RPS） | ' + str(a['rps_score']) + ' | 30% | 板块相对强弱 |')
        lines.append('| 基本面（毛利率/ROE） | ' + str(a['basic_score']) + ' | 30% | 盈利质量 |')
        lines.append('| 研报评级 | ' + str(a['report_score']) + ' | 20% | 机构共识 |')
        lines.append('| 市场情绪 | ' + str(a['money_score']) + ' | 20% | 内部一致性 |')
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append('### 估值分析')
        lines.append('')
        if a.get('tech_analysis'):
            lines.append('| 指标 | 数值 | 说明 |')
            lines.append('|------|------|------|')
# removed - PE is now replaced with technical analysis
        else:
            lines.append('*暂无PE预测数据*')
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append('### 核心逻辑（看多理由）')
        lines.append('')
        if a['logic']:
            for l in a['logic']:
                lines.append('- ' + l)
        else:
            lines.append('*数据不足，待补充*')
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append('### 风险点')
        lines.append('')
        if a['risks']:
            for r in a['risks']:
                lines.append('- ' + r)
        else:
            lines.append('*暂无明显风险*')
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append('### 操作建议')
        lines.append('')
        lines.append(a['action'])
        lines.append('')
        if a['report_count'] > 0:
            lines.append('> 机构研报覆盖：' + str(a['report_count']) + '篇，最高评级分：' + str(a['report_top_rating']))
        if a['avg_margin'] > 0:
            lines.append('> 基本面：平均毛利率 ' + str(a['avg_margin']) + '%，ROE ' + str(a['avg_roe']) + '%')
        lines.append('')
        lines.append('---')
        lines.append('')

    # === 研究状态跟踪 ===
    lines.append('## 研究状态跟踪')
    lines.append('')
    status = {
        '①行业趋势': '数据已填充' if trend else '待填写',
        '②产业链': '成分股已列出' if stocks else '待填写',
        '③核心段': '财务已填充' if financials else '待填写',
        '④核心公司': '成分股已列出' if stocks else '待填写',
        'A主营业务': '公司概况已填充' if profiles else '待填写',
        'B行业研报': ('研报' + str(len(reports)) + '条') if reports else '暂无研报',
        'C个股公告': ('公告' + str(len(notices)) + '条') if notices else '暂无公告',
        'D管理层': ('基础信息已填充' if profiles else '待填写'),
        '⑤投资建议': ('综合' + str(advice.get('total_score', '?')) + '分 - ' + advice.get('rating', '')) if advice else '待填写',
    }
    lines.append('| 层次 | 状态 |')
    lines.append('|------|------|')
    for k, v in status.items():
        lines.append('| ' + k + ' | ' + v + ' |')
    lines.append('')
    lines.append('---')
    lines.append('*本报告自动生成初稿，人工补充产业链/核心段/跟踪标的判断*')
    lines.append('*生成时间: ' + now_str + '*')

    return '\n'.join(lines)

# =====================
# 主函数
# =====================
def industry_research(concept_name, trigger_type='手动触发', top_stocks=5):
    today = datetime.now().strftime('%Y-%m-%d')
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

    print('=' * 60)
    print('行业研究 v2.1: ' + concept_name + ' - ' + now_str)
    print('=' * 60)

    # Step 1: 成分股
    print('[1/8] 成分股...')
    stocks, board_name = get_concept_stocks(concept_name)
    print('  ' + str(len(stocks)) + '只')
    core = sorted(stocks, key=lambda x: x.get('volume', 0), reverse=True)[:top_stocks]

    # Step 2: 趋势
    print('[2/8] 趋势分析...')
    trend = analyze_trend(stocks, today)
    print('  强度:', trend.get('strength', 'N/A'), ' 均RPS:', trend.get('avg_rps', 'N/A'))

    # Step 3: 财务
    print('[3/8] 财务数据...')
    top_codes = [s['code'] for s in core]
    financials = get_financials(top_codes)
    print('  成功:', str(len(financials)) + '家')

    # Step 4: A. 公司主营业务
    print('[4/8] A. 公司主营业务...')
    profiles = {}
    for s in core:
        df = retry_apicall(ak.stock_profile_cninfo, symbol=s['code'], max_retries=3, delay=2)
        if df is not None and len(df) > 0:
            row = df.iloc[0]
            basic_info = get_company_basic_info(s['code']) or {}
            profiles[s['code']] = {
                'name': s['name'],
                'main_business': str(row.get('主营业务', ''))[:500],
                'business_scope': str(row.get('经营范围', ''))[:500],
                'company_intro': str(row.get('机构简介', ''))[:600],
                'industry_cninfo': str(row.get('所属行业', '')),
                'reg_address': str(row.get('注册地址', ''))[:100],
                'website': str(row.get('官方网站', '')),
                'legal_rep': str(row.get('法人代表', '')),
                'basic_info': basic_info,
            }
        time.sleep(0.5)
    print('  成功:', str(len(profiles)) + '家')

    # Step 5: B. 行业研报
    print('[5/8] B. 行业研报...')
    all_reports = []
    for s in core:
        reports = get_research_reports(s['code'], top_n=3)
        for r in reports:
            r['code'] = s['code']
            r['name'] = s['name']
        all_reports.extend(reports)
        time.sleep(0.5)
    all_reports.sort(key=lambda x: x['date'], reverse=True)
    print('  研报:', str(len(all_reports)) + '条')

    # Step 6: C. 个股公告
    print('[6/8] C. 个股公告...')
    all_notices = get_stock_notices_batch(core, top_n_each=3)
    print('  公告:', str(len(all_notices)) + '条')

    # Step 7: 计算技术目标价
    print('[7/8] 技术面分析（目标价+止损）...')
    tech_targets = {}
    for s in core:
        if s.get('price'):
            t = technical_target(s['code'], s['price'])
            if t:
                tech_targets[s['code']] = t
    tech_count = sum(1 for v in tech_targets.values() if v)
    print('  技术分析成功:', tech_count, '只')

    # Step 8: ⑤投资建议
    print('[8/8] ⑤ 投资建议分析...')
    advice = analyze_investment_advice(board_name, stocks, trend, financials, all_reports, tech_targets, today)
    tech_an = advice.get('tech_analysis', {})
    tech_str = ((tech_an.get('comment', '') if tech_an else '暂无技术分析') + ' 上涨' + str(tech_an.get('avg_upside', 0)) + '%' + ' 止损' + str(tech_an.get('avg_stop', 0)) + '%') if tech_an else '暂无技术分析'
    print('  综合评分:', advice['total_score'], '分 -', advice['rating'])
    print('  技术面:', tech_str)
    print('  核心逻辑:', ' / '.join(advice['logic'][:2]) if advice['logic'] else '待补充')

    # Step 8: 生成报告
    print('[9/9] 生成报告...')
    report = generate_report(
        concept_name, board_name, stocks, trend, financials,
        profiles, all_reports, all_notices, advice, trigger_type, today
    )

    safe = concept_name.replace('/', '_').replace('\\', '_')
    os.makedirs(OBSIDIAN_DIR, exist_ok=True)
    md_file = OBSIDIAN_DIR + '\\' + today + '_' + safe + '_行业研究.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print('  Obsidian:', md_file)

    out_file = OUT_DIR + '\\industry_' + today + '_' + safe + '.md'
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print('  备份:', out_file)

    print()
    print('--- 摘要 ---')
    print('行业:', board_name)
    print('成分股:', len(stocks), '只')
    print('综合评分:', advice['total_score'], '分 -', advice['rating'])
    tech_an = advice.get('tech_analysis', {})
    tech_str = (tech_an.get('comment', '') + ' 上涨' + str(tech_an.get('avg_upside', 0)) + '% 止损' + str(tech_an.get('avg_stop', 0)) + '%') if tech_an else '暂无技术分析'
    print('技术面:', tech_str)
    print('=' * 60)

    return {'concept': board_name, 'stocks': len(stocks), 'advice': advice, 'tech_targets': tech_targets}

if __name__ == '__main__':
    import sys
    concept = sys.argv[1] if len(sys.argv) > 1 else 'MLOps概念'
    trigger = sys.argv[2] if len(sys.argv) > 2 else '手动触发'
    industry_research(concept, trigger)