# -*- coding: utf-8 -*-
"""重庆专精特新2275家企业精准分类生成器"""
import re, olefile, os
from collections import defaultdict

WORKDIR = r"C:\Users\Administrator\.openclaw\workspace\百都科技面试资料"
os.chdir(WORKDIR)

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
print(f'总数: {len(zjtx)}')

# 多关键词规则：优先匹配更具体的行业词，再匹配泛词
# 注意：每个规则的关键词要精确，避免"科技"误判
sectors = [
    ('医疗器械生物医药', [
        '医疗','医院','生物','医药','制药','器械','诊断','IVD','骨科','口腔','牙科',
        '植入','医用','康复','体检','血液透析','内窥镜','超声','医学检验','体外诊断',
        '卫生材料','消毒产品','药用材料','再生医学','健康服务','医疗器械','医疗科技'
    ]),
    ('新材料化工', [
        '新材料','化工','涂料','塑胶','橡胶','塑料','纤维','玻璃','陶瓷','碳材料','硅材料',
        '合金','金属制品','粉体','纳米','复合材料','密封','保温','防水卷材','防腐',
        '胶粘剂','颜料','染料','锂电池材料','新能源材料','特种气体','电子化学品',
        '阻燃剂','抗菌材料','锰业','稀土','石墨','碳纤维','硅胶','树脂','胶黏剂'
    ]),
    ('软件IT人工智能', [
        '软件','信息','大数据','云计算','物联网','智慧城市','数字孪生','工业互联网',
        'SaaS','ERP','MES','CRM','EDA','IC设计','芯片','半导体','嵌入式','信息安全',
        '网络安全','区块链','元宇宙','数字科技','信息系统','软件服务','信息技术'
    ]),
    ('新能源充电电力', [
        '新能源','充电','电动车','电动汽车','充电站','换电站','储能','光伏','风电','氢能',
        '电池','电气','电力设备','配电','变压器','智能电网','节能设备','碳资产',
        '通汇能源','中石化','石油','燃气'
    ]),
    ('机械装备汽配', [
        '机械','装备','汽车','摩托','零部件','配件','铸造','模具','齿轮','电机','轴承',
        '液压','锻造','五金','刀具','机床','数控','机器人','自动化','仪器仪表',
        '泵阀','压缩机','起重','纺织机械','矿山机械','工程机械','专用设备','不锈钢',
        '机电设备','机械制造','机械加工'
    ]),
    ('建筑建材装修', [
        '建筑','建设','建材','混凝土','装饰','装修','钢结构','门窗','防水','保温',
        '瓷砖','卫浴','地板','家具','幕墙','照明','灯具','电线电缆','管道','阀门',
        '石材','家居','建筑科技','建筑工程','建筑装饰'
    ]),
    ('食品农业', [
        '食品','农产品','粮油','乳品','肉制品','饮料','酒类','调味品','榨菜','茶叶',
        '果蔬','水产','畜牧','养殖','种植','农业','饲料','兽药','农资','烘焙',
        '休闲食品','方便食品','油脂','屠宰','面业','畜禽','畜牧业','动物药业'
    ]),
    ('包装印刷', [
        '包装','印刷','标签','喷码','纸制品','塑料制品','复合膜','袋','容器','箱','盒',
        '礼盒','说明书','彩印','凹印','柔印','防伪标签','印务'
    ]),
    ('环保检测', [
        '环保','环境','检测','监测','净化','水处理','废气','固废','危废','噪声',
        '土壤','空气检测','认证','测试','检验','计量','校准','环评','生态修复',
        '节能减排','清洁用品','环境卫生'
    ]),
]

def classify(name):
    # 先匹配具体业务词，再匹配泛词
    name_lower = name.lower()
    for sec, kws in sectors:
        for kw in kws:
            if kw in name_lower:
                return sec
    return '其他综合'

sector_map = defaultdict(list)
uncategorized = []
for c in zjtx:
    sec = classify(c)
    if sec == '其他综合':
        uncategorized.append(c)
    else:
        sector_map[sec].append(c)

print('\n===== 精准分类统计 =====')
total_categorized = 0
for sec, lst in sorted(sector_map.items(), key=lambda x: -len(x[1])):
    print(f'{sec}: {len(lst)}家')
    total_categorized += len(lst)
print(f'已分类: {total_categorized}家，未分类: {len(uncategorized)}家')

# 看未分类里有什么特征
suffixes = defaultdict(int)
for c in uncategorized:
    if '科技' in c: suffixes['科技'] += 1
    if '智能' in c: suffixes['智能'] += 1
    if '实业' in c: suffixes['实业'] += 1
    if '集团' in c: suffixes['集团'] += 1
    if '网络' in c: suffixes['网络'] += 1
    if '数字' in c: suffixes['数字'] += 1
    if '文化' in c: suffixes['文化'] += 1
    if '传媒' in c: suffixes['传媒'] += 1
    if '广告' in c: suffixes['广告'] += 1
    if '咨询' in c: suffixes['咨询'] += 1
    if '服务' in c: suffixes['服务'] += 1
print('\n未分类关键词分布:', dict(suffixes))
print('\n未分类前20条:')
for i, c in enumerate(uncategorized[:20]):
    print(f'  {i+1}. {c}')

# 写入主文件
lines = ['# 重庆专精特新企业全名单（2275家）— 精准行业分类版\n\n']
lines.append('> 来源：重庆市经济信息委2025年专精特新公示（申报1087家+复核1190家）\n')
lines.append('> 整理时间：2026-08-21\n')
lines.append('> 百度推广价值排序：医疗器械>新材料>软件IT>新能源>机械>食品>建材>包装>环保\n\n')

for sec, lst in sorted(sector_map.items(), key=lambda x: -len(x[1])):
    lines.append(f'## 【{sec}】{len(lst)}家\n')
    for i, c in enumerate(lst):
        lines.append(f'{i+1}. {c}\n')
    lines.append('\n')

if uncategorized:
    lines.append(f'## 【其他综合】{len(uncategorized)}家\n')
    for i, c in enumerate(uncategorized):
        lines.append(f'{i+1}. {c}\n')

fname = '重庆企业全名单_精准分类版.md'
with open(fname, 'w', encoding='utf-8') as f:
    f.write(''.join(lines))
size = os.path.getsize(fname)
print(f'\n主文件: {fname} ({size//1024}KB)')

for sec, lst in sector_map.items():
    safe_sec = sec.replace('/', '_').replace(' ', '_')
    fname2 = f'行业_{safe_sec}.txt'
    with open(fname2, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lst))
    print(f'{fname2}: {len(lst)}家')

print('\n===== 完成 ====')