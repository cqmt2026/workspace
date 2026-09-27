# -*- coding: utf-8 -*-
"""优化行业分类：缩小科技类范围，更精准"""
import re, os
from collections import defaultdict

WORKDIR = r"C:\Users\Administrator\.openclaw\workspace\百都科技面试资料"
os.chdir(WORKDIR)

# 读全名单
lines = open('重庆主城区创新型中小企业_全名单.md', encoding='utf-8').read()
# 提取所有企业名称+区县+批次
companies = []
current_district = None
current_source = None
for line in lines.split('\n'):
    m = re.match(r'### (.+?)（\d+家）', line)
    if m:
        current_district = m.group(1)
    m2 = re.match(r'\d+\.\s+\((.+?)\)\s+(.+)', line)
    if m2 and current_district:
        src, name = m2.group(1), m2.group(2)
        companies.append((src, current_district, name))

print(f'读取到企业: {len(companies)}')

# 优化行业分类（缩小IT类范围）
SECTORS = [
    ('医疗器械生物医药', ['医疗','医院','生物','医药','制药','器械','IVD','骨科','口腔','牙科','植入','医用','康复','体检','血液透析','内窥镜','超声','医学检验','体外诊断','卫生材料','消毒产品','药用材料','再生医学','医疗科技','医疗装备','康复医学','病理','检验','临床','生物医药','医药连锁','药业','莱福医疗','益宁医疗','智迈医疗','莱马科技']),
    ('新材料化工', ['新材料','化工','涂料','塑胶','橡胶','塑料','纤维','玻璃','陶瓷','碳材料','硅材料','合金','金属制品','粉体','纳米','复合材料','密封','保温','防水卷材','防腐','胶粘剂','颜料','染料','锂电池材料','新能源材料','特种气体','电子化学品','阻燃剂','抗菌材料','锰业','稀土','石墨','碳纤维','硅胶','树脂','胶黏剂','铝','压铸','铸造','化工','新材料']),
    ('软件IT人工智能', ['软件','大数据','云计算','物联网','智慧城市','数字孪生','工业互联网','SaaS','ERP','MES','CRM','EDA','IC设计','芯片','半导体','嵌入式','信息安全','网络安全','区块链','元宇宙','数字科技','数字技术','人工智能','智能科技','数智科技','信息技术','网络科技','网络科技','智能科技','数据科技','数智']),
    ('新能源充电电力', ['新能源','充电','电动车','电动汽车','充电站','换电站','储能','光伏','风电','氢能','电池','电气','电力设备','配电','变压器','智能电网','节能设备','通汇能源','石油','燃气','电力','电气']),
    ('机械装备汽配', ['机械','装备','汽车','摩托','零部件','配件','铸造','模具','齿轮','电机','轴承','液压','锻造','五金','刀具','机床','数控','机器人','自动化','仪器仪表','泵阀','压缩机','起重','矿山机械','工程机械','专用设备','机电设备','机械制造','机械加工','机车','传动','螺杆','精密','设备','重工','车辆','机车工业','压铸']),
    ('建筑建材装修', ['建筑','建设','建材','混凝土','装饰','装修','钢结构','门窗','防水','保温','瓷砖','卫浴','地板','家具','幕墙','照明','灯具','电线电缆','管道','阀门','石材','家居','建筑工程','建筑装饰','幕墙']),
    ('食品农业', ['食品','农产品','粮油','乳品','肉制品','饮料','酒类','调味品','榨菜','茶叶','果蔬','水产','畜牧','养殖','种植','农业','饲料','兽药','农资','烘焙','休闲食品','方便食品','油脂','屠宰','面业','畜禽','畜牧业','动物药业']),
    ('包装印刷', ['包装','印刷','标签','喷码','纸制品','复合膜','彩印','凹印','柔印','防伪标签','印务']),
    ('环保检测', ['环保','环境','检测','监测','净化','水处理','废气','固废','危废','噪声','土壤','空气检测','认证','测试','检验','计量','校准','环评','生态修复','节能减排','清洁用品','环境卫生','再生资源','固废处理','水处理']),
]

# 先按行业词精确匹配，剩下的"XX科技"统一归"其他"
# 但为了避免所有"科技"公司都归IT，我们只在有明确IT关键词时才归IT
IT_EXACT = ['软件','大数据','云计算','物联网','智慧城市','数字孪生','工业互联网','SaaS','ERP','MES','CRM','EDA','IC设计','芯片','半导体','嵌入式','信息安全','网络安全','区块链','元宇宙','人工智能','数智科技','数智','数字科技','数字技术','信息技术','网络科技','数据科技','数据','信息系统']
IT_BROAD = ['科技']  # 只有科技二字，没有更精确IT词的，不归IT

def classify(name):
    # 先按各行业精确匹配
    for sec, kws in SECTORS:
        for kw in kws:
            if kw in name:
                return sec
    # 对于"科技"结尾的企业，只有含IT精确词才归IT
    for kw in IT_EXACT:
        if kw in name:
            return '软件IT人工智能'
    return '其他综合'

sector_map = defaultdict(list)
for source, dist, name in companies:
    sec = classify(name)
    sector_map[sec].append((source, dist, name))

# 统计
print('\n优化后行业分类:')
total = 0
for sec, lst in sorted(sector_map.items(), key=lambda x: -len(x[1])):
    print(f'  {sec}: {len(lst)}家')
    total += len(lst)
print(f'  合计: {total}')

# 写最终版（只保留非其他综合的精确分类 + 其他综合）
lines_out = ['# 重庆市主城区创新型中小企业名单（精准版）\n\n']
lines_out.append('> 来源：重庆市经信委2024年第二批+2025年第二批\n')
lines_out.append('> 范围：主城区9区+两江新区+西部科学城重庆高新区\n')
lines_out.append('> **总计: {}家**\n\n'.format(len(companies)))

lines_out.append('## 各区县分布\n\n| 区县 | 数量 |\n|------|------|\n')
dist_counts = defaultdict(int)
for _, d, _ in companies:
    dist_counts[d] += 1
for d, c in sorted(dist_counts.items(), key=lambda x: -x[1]):
    lines_out.append(f'| {d} | {c} |\n')

lines_out.append('\n## 行业分布\n\n| 行业 | 数量 |\n|------|------|\n')
for sec, lst in sorted(sector_map.items(), key=lambda x: -len(x[1])):
    lines_out.append(f'| {sec} | {len(lst)} |\n')

lines_out.append('\n---\n\n')

for sec, lst in sorted(sector_map.items(), key=lambda x: -len(x[1])):
    lines_out.append(f'## 【{sec}】{len(lst)}家\n\n')
    dist_groups = defaultdict(list)
    for source, dist, name in lst:
        dist_groups[dist].append(f'({source}) {name}')
    for d in sorted(dist_groups.keys()):
        lines_out.append(f'### {d}（{len(dist_groups[d])}家）\n\n')
        for i, entry in enumerate(dist_groups[d]):
            lines_out.append(f'{i+1}. {entry}\n')
        lines_out.append('\n')

fname = '重庆主城区创新型中小企业_精准版.md'
with open(fname, 'w', encoding='utf-8') as f:
    f.write(''.join(lines_out))
print(f'\n已写入: {fname} ({os.path.getsize(fname)}字节)')

# 分行业txt
for sec, lst in sector_map.items():
    names = [n for _, _, n in lst]
    safe_sec = sec.replace('/', '_')
    fname2 = f'创新型_{safe_sec}.txt'
    with open(fname2, 'w', encoding='utf-8') as f:
        f.write('\n'.join(names))
    print(f'{fname2}: {len(names)}家')

print('\n===== 完成 ====')
