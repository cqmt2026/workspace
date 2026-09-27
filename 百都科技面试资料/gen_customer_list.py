# -*- coding: utf-8 -*-
"""重庆百度推广目标客户名单生成器"""
import olefile, re, json, xlrd, os

WORKDIR = r"C:\Users\Administrator\.openclaw\workspace\百都科技面试资料"
os.chdir(WORKDIR)

# ---------- 1. 解析专精特新doc ----------
def parse_doc(filename):
    ole = olefile.OleFileIO(filename)
    data = ole.openstream('WordDocument').read()
    text = data.decode('utf-16-le', errors='ignore')
    companies = re.findall(r'[\u4e00-\u9fffA-Za-z（）()、\-·]+?(?:股份有限公司|有限责任公司|有限公司|股份公司|工厂|研究所|公司)', text)
    seen = []
    for c in companies:
        c = c.strip()
        if c and c not in seen and not any(k in c for k in ['序号','区县','企业名称','名单','公示']):
            seen.append(c)
    return seen

zjtx = parse_doc('重庆专精特新2025名单.doc')
print(f'专精特新企业总数: {len(zjtx)}')

# ---------- 2. 解析医疗器械xls ----------
wb = xlrd.open_workbook('重庆医疗器械生产许可2025.xls')
sh = wb.sheet_by_index(0)
ylqx = []
for r in range(2, sh.nrows):
    v = str(sh.cell_value(r,1)).strip()
    if v and '企业名称' not in v and v not in ylqx:
        ylqx.append(v)

# ---------- 3. 按百度推广价值行业分类 ----------
# 定义高价值行业关键词（中小企业密集+百度推广空白）
sectors = {
    '医疗器械/生物医药': ['医疗','生物','医疗','医药','药','器械','诊断','IVD','血液','口腔','牙','制药','健康','养生','康复'],
    '新材料/化工': ['材料','化工','塑料','橡胶','纤维','玻璃','铝','镁','钛','金属','合金','涂料','胶','膜','碳','硅'],
    '软件/IT/人工智能': ['软件','科技','信息','数据','智能','AI','人工智能','互联网','网络','数字','云','机器人','物联网','电子','芯片','半导体'],
    '新能源/充电/电力': ['新能源','充电','电力','电气','电池','储能','光伏','风电','能源','电'],
    '机械/装备/汽配': ['机械','装备','汽车','摩托','摩托','零部件','配件','铸造','模具','齿轮','电机','轴承','液压','锻造','五金','刀具'],
    '食品/农业': ['食品','农','养殖','肉','粮油','乳','茶','酒','饮料','调味','榨菜','豆腐','种植','畜牧'],
    '建筑/建材/装修': ['建筑','建设','建材','混凝土','装饰','装修','钢结构','门窗','防水','保温','涂料家装','瓷砖','卫浴'],
    '包装/印刷': ['包装','印刷','塑料制品','纸','喷码','标签','容器'],
    '环保/检测': ['环保','环境','检测','监测','净化','水处理','废气','固废','认证','测试','检验'],
    '其他制造': ['制造','生产','加工','实业','科技','工贸','商贸','贸易'],
}

def classify(name):
    for sector, kws in sectors.items():
        for kw in kws:
            if kw in name:
                return sector
    return '其他/综合'

# 分类统计
from collections import defaultdict
sector_map = defaultdict(list)
for c in zjtx:
    sec = classify(c)
    sector_map[sec].append(c)

print('\n===== 行业分类统计 =====')
for sec, lst in sorted(sector_map.items(), key=lambda x: -len(x[1])):
    print(f'{sec}: {len(lst)}家')

# ---------- 4. 生成输出文件 ----------
def write_file(fname, content):
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'已写入: {fname} ({os.path.getsize(fname)}字节)')

# 完整名单
write_file('重庆专精特新企业全名单_2275家.md',
    '# 2025年重庆市专精特新中小企业完整名单（2275家）\n'
    '> 来源：重庆市经济信息委2025年公示（申报1087家+复核1190家）\n> 整理时间：2026-08-21\n\n'
    + '\n'.join(f'{i+1}. {c}' for i, c in enumerate(zjtx)))

# 分行业名单
for sec, lst in sector_map.items():
    write_file(f'行业_{sec}.md',
        f'# {sec} 企业名单（{len(lst)}家，百度推广高价值）\n\n'
        + '\n'.join(f'{i+1}. {c}' for i, c in enumerate(lst)))

print('\n===== 完成 ====')
print(f'总企业数: {len(zjtx)}，医疗器械生产许可补充: {len(ylqx)}家')