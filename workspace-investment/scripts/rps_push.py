# -*- coding: utf-8 -*-

"""

RPS每日推送 v1.1

================

计算5日/20日RPS，精选Top10强势股，推送微信



数据来源: F:/market_data.db (daily_k表)

执行时间: 每天10:30（前一日收盘数据）

推送: Server酱



更新 v1.1: 修复交易日历获取逻辑（使用DISTINCT date而非指数代码）

"""

import io
import sqlite3, os, sys, requests, json

from datetime import datetime, date, timedelta

from typing import List, Dict



# ========== 配置 ==========

WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'

DB = r'F:/market_data.db'

OUT_DIR = os.path.join(WORK_DIR, 'out_data')

os.makedirs(OUT_DIR, exist_ok=True)



# 推送由Cron WeChat delivery处理（已禁用方糖）



# RPS参数

MIN_PRICE = 3.0      # 最低股价（过滤幽灵股）

MAX_PRICE = 300.0    # 最高股价

MIN_TURNOVER = 1000  # 最低成交额（万元），约1000万





# ========== 核心函数 ==========

def get_trading_dates(ref_date: str = None, n: int = 25) -> List[str]:

    """获取ref_date之前N个交易日列表（按日期降序）"""

    conn = sqlite3.connect(DB)

    cur = conn.cursor()

    

    if ref_date:

        cur.execute("""

            SELECT DISTINCT date FROM daily_k 

            WHERE date <= ?

            ORDER BY date DESC 

            LIMIT ?

        """, (ref_date, n))

    else:

        cur.execute("""

            SELECT DISTINCT date FROM daily_k 

            ORDER BY date DESC 

            LIMIT ?

        """, (n,))

    

    dates = [r[0] for r in cur.fetchall()]

    conn.close()

    return dates





def get_stock_name_simple(code: str) -> str:

    """股票名称（静态映射表，约500只常用股）"""

    NAME_MAP = {

        # 上证主板 600xxx

        'sh.600519': '贵州茅台', 'sh.601318': '中国平安', 'sh.600036': '招商银行',

        'sh.600000': '浦发银行', 'sh.601166': '兴业银行', 'sh.601398': '工商银行',

        'sh.600016': '民生银行', 'sh.601288': '农业银行', 'sh.601988': '中国银行',

        'sh.601088': '中国神华', 'sh.601857': '中国石油', 'sh.600028': '中国石化',

        'sh.600030': '中信证券', 'sh.601211': '国泰君安', 'sh.600837': '海通证券',

        'sh.600900': '长江电力', 'sh.601225': '陕西煤业', 'sh.601898': '中煤能源',

        'sh.601668': '中国建筑', 'sh.601800': '中国交建', 'sh.600048': '保利发展',

        'sh.600104': '上汽集团', 'sh.600050': '中国联通', 'sh.601728': '中国电信',

        'sh.600276': '恒瑞医药', 'sh.601012': '隆基绿能', 'sh.600585': '海螺水泥',

        'sh.601319': '中国人保', 'sh.600309': '万华化学', 'sh.600887': '伊利股份',

        'sh.603259': '药明康德', 'sh.600436': '片仔癀', 'sh.600887': '伊利股份',

        'sh.600132': '重庆啤酒', 'sh.600115': '东方航空', 'sh.600009': '上海机场',

        'sh.600031': '三一重工', 'sh.600690': '海尔智家', 'sh.600760': '中航沈飞',

        'sh.600882': '妙可蓝多', 'sh.600438': '通威股份', 'sh.600703': '三安光电',

        'sh.600690': '海尔智家', 'sh.600089': '特变电工', 'sh.600585': '海螺水泥',

        'sh.600150': '中国船舶', 'sh.600018': '上港集团', 'sh.600309': '万华化学',

        'sh.601012': '隆基绿能', 'sh.603288': '海天味业', 'sh.603501': '韦尔股份',

        'sh.600745': '闻泰科技', 'sh.601166': '兴业银行', 'sh.600176': '中国巨石',

        'sh.600487': '亨通光电', 'sh.600588': '用友网络', 'sh.600570': '恒生电子',

        'sh.601012': '隆基绿能', 'sh.600406': '国电南瑞', 'sh.600900': '长江电力',

        'sh.601186': '中国铁建', 'sh.601390': '中国中铁', 'sh.601766': '中国中车',

        'sh.601668': '中国建筑', 'sh.601857': '中国石油', 'sh.600028': '中国石化',

        'sh.600050': '中国联通', 'sh.601728': '中国电信', 'sh.600050': '中国联通',

        'sh.601688': '华泰证券', 'sh.601336': '新华保险', 'sh.601601': '中国太保',

        'sh.601628': '中国人寿', 'sh.601628': '中国人寿', 'sh.600036': '招商银行',

        'sh.601398': '工商银行', 'sh.601939': '建设银行', 'sh.601288': '农业银行',

        'sh.600016': '民生银行', 'sh.600000': '浦发银行', 'sh.601818': '光大银行',

        'sh.601825': '沪农商行', 'sh.600926': '杭州银行', 'sh.600919': '江苏银行',

        'sh.600835': '上海机电', 'sh.600004': '白云机场', 'sh.601111': '中国国航',

        'sh.600029': '南方航空', 'sh.601021': '春秋航空', 'sh.601877': '正泰电器',

        'sh.600398': '海澜之家', 'sh.600606': '绿地控股', 'sh.600823': '世茂股份',

        'sh.601155': '新城控股', 'sh.600048': '保利发展', 'sh.600383': '金地集团',

        'sh.600208': '新湖中宝', 'sh.600657': '信达地产', 'sh.600648': '外高桥',

        'sh.600639': '浦东金桥', 'sh.600735': '新华锦', 'sh.600007': '中国国贸',

        'sh.600663': '陆家嘴', 'sh.600846': '同济科技', 'sh.600850': '电科数字',

        'sh.600718': '东软集团', 'sh.600406': '国电南瑞', 'sh.600089': '特变电工',

        'sh.601727': '上海电气', 'sh.601727': '上海电气', 'sh.601727': '上海电气',

        'sh.601727': '上海电气', 'sh.601390': '中国中铁', 'sh.601390': '中国中铁',

        'sh.600320': '振华重工', 'sh.601390': '中国中铁', 'sh.600170': '上海建工',

        'sh.601186': '中国铁建', 'sh.600502': '安徽建工', 'sh.600284': '浦东建设',

        'sh.600284': '浦东建设', 'sh.601668': '中国建筑', 'sh.600210': '紫江企业',

        'sh.601669': '中国电建', 'sh.601618': '中国中冶', 'sh.601263': '陕西煤业',

        'sh.601666': '平煤股份', 'sh.601001': '晋控煤业', 'sh.600971': '恒源煤电',

        'sh.600508': '上海能源', 'sh.600188': '兖矿能源', 'sh.600508': '上海能源',

        'sh.601088': '中国神华', 'sh.600256': '广汇能源', 'sh.600348': '华阳股份',

        'sh.600123': '兰花科创', 'sh.601666': '平煤股份', 'sh.601001': '晋控煤业',

        'sh.600971': '恒源煤电', 'sh.601015': '陕西黑猫', 'sh.600792': '云煤能源',

        'sh.600395': '盘江股份', 'sh.600971': '恒源煤电', 'sh.600997': '开滦股份',

        'sh.601666': '平煤股份', 'sh.600348': '华阳股份', 'sh.601225': '陕西煤业',

        'sh.601225': '陕西煤业', 'sh.600256': '广汇能源', 'sh.601666': '平煤股份',

        'sh.600188': '兖矿能源', 'sh.600971': '恒源煤电', 'sh.601001': '晋控煤业',

        'sh.600997': '开滦股份', 'sh.601088': '中国神华', 'sh.601225': '陕西煤业',

        'sh.601898': '中煤能源', 'sh.600256': '广汇能源', 'sh.601139': '深圳燃气',

        'sh.601666': '平煤股份', 'sh.600926': '杭州银行', 'sh.601128': '常熟银行',

        'sh.601577': '长沙银行', 'sh.601658': '邮储银行', 'sh.601077': '渝农商行',

        'sh.600365': 'ST通葡', 'sh.600959': '江苏有线', 'sh.600650': '锦江在线',

        'sh.600832': '东方明珠', 'sh.601021': '春秋航空', 'sh.601111': '中国国航',

        'sh.600029': '南方航空', 'sh.601719': '中航高科', 'sh.600760': '中航沈飞',

        'sh.600685': '中船防务', 'sh.600150': '中国船舶', 'sh.601989': '中国重工',

        'sh.600038': '中直股份', 'sh.600316': '洪都航空', 'sh.600391': '航发科技',

        'sh.600775': '南京熊猫', 'sh.600970': '中材国际', 'sh.601106': '中国一重',

        'sh.601106': '中国一重', 'sh.600169': '太原重工', 'sh.600243': '青海华鼎',

        'sh.601012': '隆基绿能', 'sh.600406': '国电南瑞', 'sh.601615': '明阳智能',

        'sh.601615': '明阳智能', 'sh.603806': '福斯特', 'sh.601012': '隆基绿能',

        'sh.600438': '通威股份', 'sh.601012': '隆基绿能', 'sh.601865': '福莱特',

        'sh.603806': '福斯特', 'sh.601615': '明阳智能', 'sh.601619': '嘉泽新能',

        'sh.603185': '弘元绿能', 'sh.600900': '长江电力', 'sh.600674': '川投能源',

        'sh.600886': '国投电力', 'sh.601016': '节能风电', 'sh.600795': '国电电力',

        'sh.600011': '华能国际', 'sh.601088': '中国神华', 'sh.600025': '华能水电',

        'sh.600023': '浙能电力', 'sh.600795': '国电电力', 'sh.600900': '长江电力',

        'sh.600236': '桂冠电力', 'sh.600310': '桂东电力', 'sh.600726': '华电能源',

        'sh.600726': '华电能源', 'sh.600795': '国电电力', 'sh.601619': '嘉泽新能',

        'sh.601985': '中国核电', 'sh.601611': '中国核建', 'sh.600027': '华电国际',

        'sh.600027': '华电国际', 'sh.600011': '华能国际', 'sh.601225': '陕西煤业',

        'sh.600188': '兖矿能源', 'sh.601088': '中国神华', 'sh.601139': '深圳燃气',

        'sh.600917': '重庆燃气', 'sh.603393': '新天然气', 'sh.601225': '陕西煤业',

        'sh.600926': '杭州银行', 'sh.601128': '常熟银行', 'sh.601838': '成都银行',

        'sh.601577': '长沙银行', 'sh.601187': '厦门银行', 'sh.601658': '邮储银行',

        'sh.601077': '渝农商行', 'sh.600919': '江苏银行', 'sh.600928': '紫金银行',

        'sh.601166': '兴业银行', 'sh.601398': '工商银行', 'sh.601939': '建设银行',

        'sh.600016': '民生银行', 'sh.600000': '浦发银行', 'sh.601818': '光大银行',

        'sh.601328': '交通银行', 'sh.601288': '农业银行', 'sh.601988': '中国银行',

        'sh.601818': '光大银行', 'sh.600036': '招商银行', 'sh.601166': '兴业银行',

        'sh.601398': '工商银行', 'sh.601818': '光大银行', 'sh.601169': '北京银行',

        'sh.600015': '华夏银行', 'sh.601229': '上海银行', 'sh.600926': '杭州银行',

        'sh.600036': '招商银行', 'sh.601818': '光大银行', 'sh.601398': '工商银行',

        'sh.601939': '建设银行', 'sh.601398': '工商银行', 'sh.601818': '光大银行',

        # 科创板 688xxx

        'sh.688041': '寒武纪', 'sh.688111': '金山办公', 'sh.688036': '传音控股',

        'sh.688012': '中微公司', 'sh.688981': '中芯国际', 'sh.688008': '澜起科技',

        'sh.688072': '拓荆科技', 'sh.688256': '寒武纪', 'sh.688396': '华润微',

        'sh.688099': '晶晨股份', 'sh.688126': '沪硅产业', 'sh.688008': '澜起科技',

        'sh.688187': '时代电气', 'sh.688223': '晶科能源', 'sh.688385': '复旦微电',

        'sh.688116': '天奈科技', 'sh.688185': '康希通信', 'sh.688388': '禾迈股份',

        'sh.688170': '华大九天', 'sh.688256': '寒武纪', 'sh.688125': '安集科技',

        'sh.688123': '聚辰股份', 'sh.688036': '传音控股', 'sh.688111': '金山办公',

        'sh.688981': '中芯国际', 'sh.688012': '中微公司', 'sh.688072': '拓荆科技',

        'sh.688561': '奇安信', 'sh.688169': '石头科技', 'sh.688050': '爱博医疗',

        'sh.688198': '百济神州', 'sh.688185': '康希通信', 'sh.688521': '芯原股份',

        'sh.688499': '利元亨', 'sh.688022': '瀚川智能', 'sh.688116': '天奈科技',

        'sh.688200': '华峰测控', 'sh.688036': '传音控股', 'sh.688256': '寒武纪',

        # 深证主板 000xxx

        'sz.000651': '格力电器', 'sz.000333': '美的集团', 'sz.000001': '平安银行',

        'sz.000002': '万科A', 'sz.000063': '中兴通讯', 'sz.000338': '潍柴动力',

        'sz.000568': '泸州老窖', 'sz.000596': '古井贡酒', 'sz.000661': '长春高新',

        'sz.000876': '新希望', 'sz.000895': '双汇发展', 'sz.000938': '紫光股份',

        'sz.001979': '招商蛇口', 'sz.000002': '万科A', 'sz.000063': '中兴通讯',

        'sz.000100': 'TCL科技', 'sz.000157': '中联重科', 'sz.000166': '申万宏源',

        'sz.000333': '美的集团', 'sz.000338': '潍柴动力', 'sz.000423': '东阿阿胶',

        'sz.000425': '徐工机械', 'sz.000438': '动力新科', 'sz.000488': '晨鸣纸业',

        'sz.000501': '鄂武商A', 'sz.000513': '丽珠集团', 'sz.000518': '四环生物',

        'sz.000519': '中兵红箭', 'sz.000538': '云南白药', 'sz.000596': '古井贡酒',

        'sz.000651': '格力电器', 'sz.000661': '长春高新', 'sz.000568': '泸州老窖',

        'sz.000858': '五粮液', 'sz.000876': '新希望', 'sz.000895': '双汇发展',

        'sz.000938': '紫光股份', 'sz.000983': '山西焦煤', 'sz.000001': '平安银行',

        'sz.000002': '万科A', 'sz.000063': '中兴通讯', 'sz.000100': 'TCL科技',

        'sz.000157': '中联重科', 'sz.000338': '潍柴动力', 'sz.000423': '东阿阿胶',

        'sz.000488': '晨鸣纸业', 'sz.000501': '鄂武商A', 'sz.000513': '丽珠集团',

        'sz.000538': '云南白药', 'sz.000568': '泸州老窖', 'sz.000596': '古井贡酒',

        'sz.000651': '格力电器', 'sz.000661': '长春高新', 'sz.000708': '中信特钢',

        'sz.000729': '燕京啤酒', 'sz.000738': '航发控制', 'sz.000758': '中色股份',

        'sz.000768': '中航西飞', 'sz.000786': '北新建材', 'sz.000793': '华闻集团',

        'sz.000858': '五粮液', 'sz.000876': '新希望', 'sz.000895': '双汇发展',

        'sz.000938': '紫光股份', 'sz.000983': '山西焦煤', 'sz.000001': '平安银行',

        'sz.000002': '万科A', 'sz.000063': '中兴通讯', 'sz.000100': 'TCL科技',

        # 创业板 300xxx

        'sz.300015': '爱尔眼科', 'sz.300059': '东方财富', 'sz.300122': '智飞生物',

        'sz.300274': '阳光电源', 'sz.300498': '温氏股份', 'sz.300750': '宁德时代',

        'sz.300760': '迈瑞医疗', 'sz.300122': '智飞生物', 'sz.300015': '爱尔眼科',

        'sz.300059': '东方财富', 'sz.300142': '沃森生物', 'sz.300122': '智飞生物',

        'sz.300347': '泰格医药', 'sz.300363': '博腾股份', 'sz.300122': '智飞生物',

        'sz.300601': '康泰生物', 'sz.300529': '健帆生物', 'sz.300015': '爱尔眼科',

        'sz.300760': '迈瑞医疗', 'sz.300750': '宁德时代', 'sz.300274': '阳光电源',

        'sz.300014': '亿纬锂能', 'sz.300274': '阳光电源', 'sz.300450': '先导智能',

        'sz.300274': '阳光电源', 'sz.300014': '亿纬锂能', 'sz.300750': '宁德时代',

        'sz.300014': '亿纬锂能', 'sz.300059': '东方财富', 'sz.300124': '汇川技术',

        'sz.300124': '汇川技术', 'sz.300015': '爱尔眼科', 'sz.300142': '沃森生物',

        'sz.300003': '乐普医疗', 'sz.300122': '智飞生物', 'sz.300760': '迈瑞医疗',

        'sz.300059': '东方财富', 'sz.300347': '泰格医药', 'sz.300529': '健帆生物',

        'sz.300363': '博腾股份', 'sz.300601': '康泰生物', 'sz.300529': '健帆生物',

        'sz.300015': '爱尔眼科', 'sz.300760': '迈瑞医疗', 'sz.300750': '宁德时代',

        'sz.300014': '亿纬锂能', 'sz.300274': '阳光电源', 'sz.300124': '汇川技术',

        'sz.300450': '先导智能', 'sz.300274': '阳光电源', 'sz.300014': '亿纬锂能',

        # 中小板 002xxx

        'sz.002594': '比亚迪', 'sz.002415': '海康威视', 'sz.002475': '立讯精密',

        'sz.002714': '牧原股份', 'sz.002352': '顺丰控股', 'sz.002460': '赣锋锂业',

        'sz.002466': '天齐锂业', 'sz.002493': '荣盛石化', 'sz.002594': '比亚迪',

        'sz.002415': '海康威视', 'sz.002475': '立讯精密', 'sz.002714': '牧原股份',

        'sz.002352': '顺丰控股', 'sz.002460': '赣锋锂业', 'sz.002466': '天齐锂业',

        'sz.002493': '荣盛石化', 'sz.002594': '比亚迪', 'sz.002415': '海康威视',

        'sz.002475': '立讯精密', 'sz.002714': '牧原股份', 'sz.002352': '顺丰控股',

        'sz.002460': '赣锋锂业', 'sz.002466': '天齐锂业', 'sz.002493': '荣盛石化',

        'sz.002001': '新和成', 'sz.002007': '华兰生物', 'sz.002008': '大族激光',

        'sz.002013': '中航机电', 'sz.002024': '苏宁易购', 'sz.002027': '分众传媒',

        'sz.002028': '思源电气', 'sz.002032': '苏泊尔', 'sz.002044': '美年健康',

        'sz.002050': '三花智控', 'sz.002069': '獐子岛', 'sz.002081': '金螳螂',

        'sz.002092': '中泰化学', 'sz.002104': '恒宝股份', 'sz.002120': '韵达股份',

        'sz.002230': '科大讯飞', 'sz.002236': '大华股份', 'sz.002252': '上海莱士',

        'sz.002304': '洋河股份', 'sz.002311': '海大集团', 'sz.002352': '顺丰控股',

        'sz.002371': '北方华创', 'sz.002384': '东山精密', 'sz.002415': '海康威视',

        'sz.002428': '云南锗业', 'sz.002460': '赣锋锂业', 'sz.002466': '天齐锂业',

        'sz.002493': '荣盛石化', 'sz.002594': '比亚迪', 'sz.002601': '龙佰集团',

        'sz.002602': '世纪华通', 'sz.002607': '亚玛顿', 'sz.002624': '完美世界',

        'sz.002653': '海思科', 'sz.002714': '牧原股份', 'sz.002773': '康弘药业',

        'sz.002812': '恩捷股份', 'sz.002841': '视源股份', 'sz.002916': '华虹半导体',

        'sz.002925': '垒知集团', 'sz.002958': '青农商行', 'sz.002966': '苏州银行',

    }

    

    return NAME_MAP.get(code, code)





def calc_rps(ref_date: str, days: int, top_n: int = 10) -> List[Dict]:

    """

    计算N日RPS

    ref_date: 基准日期（最新日期）

    days: N日

    返回: [{code, name, rps, return_pct, close}, ...]

    """

    # 获取交易日列表

    dates = get_trading_dates(ref_date, days + 5)

    if len(dates) < days + 1:

        print(f"[W] 仅{len(dates)}个交易日，不足{days}天")

        return []

    

    end_date = dates[0]

    start_date = dates[days - 1]  # N个交易日之前

    

    conn = sqlite3.connect(DB)

    cur = conn.cursor()

    

    # 期末价格

    cur.execute("""

        SELECT code, close FROM daily_k 

        WHERE date = ? AND close > ?

    """, (end_date, MIN_PRICE))

    end_prices = {r[0]: r[1] for r in cur.fetchall()}

    

    # 期初价格

    cur.execute("""

        SELECT code, close FROM daily_k 

        WHERE date = ?

    """, (start_date,))

    start_prices = {r[0]: r[1] for r in cur.fetchall()}

    

    conn.close()

    

    # 交集 + 价格过滤

    codes = set(end_prices.keys()) & set(start_prices.keys())

    raw = []

    for code in codes:

        ep = end_prices[code]

        sp = start_prices[code]

        if not (MIN_PRICE <= ep <= MAX_PRICE and MIN_PRICE <= sp <= MAX_PRICE):

            continue

        if ep == 0 or sp == 0:

            continue

        ret = (ep - sp) / sp * 100

        raw.append({

            'code': code,

            'close': ep,

            'return_pct': round(ret, 2),

        })

    

    if not raw:

        return []

    

    # 计算RPS（百分位排名）

    returns = sorted([r['return_pct'] for r in raw])

    n = len(returns)

    

    for r in raw:

        idx = returns.index(r['return_pct'])

        r['rps'] = round(idx / (n - 1) * 100, 1) if n > 1 else 0

    

    # 排序：RPS优先，涨幅辅助

    # 只保留正涨幅（RPS高但涨幅负的没意义）

    positive = [r for r in raw if r['return_pct'] > 0]

    negative = [r for r in raw if r['return_pct'] <= 0]

    

    # 如果正涨幅太少，放宽条件

    if len(positive) < 5:

        positive = raw

    

    top = sorted(positive, key=lambda x: (x['rps'], x['return_pct']), reverse=True)[:top_n]

    

    # 补充名称（批量获取避免重复）

    for item in top:

        item['name'] = get_stock_name_simple(item['code'])

    

    return top





# ========== 推送 ==========

def send_wx(title: str, content: str) -> bool:

    """微信推送（已禁用，改用Cron WeChat delivery）"""

    # 微信推送改由Cron的delivery机制处理，此处禁用方糖

    print(f"[WeChat] {title} - 推送由Cron WeChat delivery完成")

    return True





# ========== 格式化 ==========

def format_stock_item(item: Dict, rank: int) -> str:

    code = item['code']

    name = item.get('name', '') or code

    rps = item['rps']

    ret = item['return_pct']

    short = code.replace('sh.', '').replace('sz.', '')

    label = f"{name}({short})" if name != code else short

    return f"{rank}. {label} RPS={rps} 涨幅={ret:+.2f}%"





def format_full_report(rps5: List[Dict], rps20: List[Dict], ref_date: str) -> str:

    """完整早盘参考格式"""

    lines = [

        f"【RPS强势股】{ref_date}",

        "=" * 32,

        "",

        "RPS5日 TOP10：",

    ]

    

    if rps5:

        for i, item in enumerate(rps5, 1):

            lines.append(format_stock_item(item, i))

    else:

        lines.append("（数据不足）")

    

    lines.extend(["", "RPS20日 TOP10：", ""])

    

    if rps20:

        for i, item in enumerate(rps20, 1):

            lines.append(format_stock_item(item, i))

    else:

        lines.append("（数据不足）")

    

    lines.extend([

        "",

        "=" * 32,

        "* 仅供参考，不构成投资建议",

        f"* 生成: {datetime.now().strftime('%H:%M:%S')}",

    ])

    

    return "\n".join(lines)





# ========== 主流程 ==========

def main():

    print(f"[RPS] Start {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    

    # 确定基准日期（前一个交易日）

    today = date.today()

    trading_dates = get_trading_dates(n=2)

    

    if not trading_dates:

        print("[RPS] ERROR: No trading dates found")

        return

    

    latest_date = trading_dates[0]

    # 如果当天开盘了，用当天；否则用前一交易日

    ref_date = latest_date

    

    print(f"[RPS] ref_date={ref_date}")

    

    # 计算RPS

    print("[RPS] Calculating RPS5...")

    rps5 = calc_rps(ref_date, 5, 10)

    print(f"[RPS] RPS5: {len(rps5)} stocks")

    

    print("[RPS] Calculating RPS20...")

    rps20 = calc_rps(ref_date, 20, 10)

    print(f"[RPS] RPS20: {len(rps20)} stocks")

    

    if not rps5 and not rps20:

        print("[RPS] No data, exit")

        return

    

    # 生成报告

    report = format_full_report(rps5, rps20, ref_date)

    print("\n--- REPORT ---")

    print(report)

    

    # 保存JSON

    date_str = ref_date.replace('-', '')

    json_out = os.path.join(OUT_DIR, f"rps_push_{date_str}.json")

    save_data = {

        'date': ref_date,

        'rps5': rps5,

        'rps20': rps20,

        'generated': datetime.now().isoformat(),

    }

    with open(json_out, 'w', encoding='utf-8') as f:

        json.dump(save_data, f, ensure_ascii=False, indent=2)

    print(f"\n[Save] {json_out}")

    

    # 微信推送
    title = f"[RPS强势股] {ref_date}"
    send_wx(title, report)
    
    # 存入supermemory
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
        from memory_adapter import save_investment_strategy
        top5 = rps5[:5] if rps5 else []
        summary = 'RPS强势股 %s: ' % ref_date
        summary += ', '.join('%s(%s)' % (s.get('code','')[:6], s.get('name','')) for s in top5)
        save_investment_strategy(summary, source='investment-rps')
        print('  [Supermemory] 已保存RPS推送')
    except Exception as e:
        print('  [Supermemory] 写入失败: %s' % e)
    
    # 历史记忆参考
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
        from memory_ref import recall
        r = recall([
            ('强势股', 'RPS 强势'),
            ('策略', '策略 信号'),
        ], top_k=3, max_total=4)
        if r['count'] > 0:
            print()
            print('\U0001f4d6 【历史RPS对比】')
            for m in r['results']:
                print(f"  [{m['_label']}] ({m['score']:.2f}) {m['text'][:80]}")
    except Exception as e:
        print('\U0001f4d6 【历史RPS对比】加载失败: %s' % e)
    
    print("\n[RPS] Done")





if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':

    main()

