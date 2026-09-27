# -*- coding: utf-8 -*-
"""重庆企业名单批量生成器"""
import olefile, re, os
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
print(f'专精特新企业总数: {len(zjtx)}')

# 行业分类关键词
sectors = {
    '医疗器械生物医药': ['医疗','生物','医药','药','器械','诊断','IVD','口腔','牙','制药','健康','康复'],
    '新材料化工': ['材料','化工','塑料','橡胶','纤维','玻璃','铝','镁','钛','金属','合金','涂料','胶','膜','碳','硅'],
    '软件IT人工智能': ['软件','科技','信息','数据','智能','互联网','网络','数字','云','机器人','物联网','电子','芯片','半导体'],
    '新能源充电电力': ['新能源','充电','电力','电气','电池','储能','光伏','风电','能源'],
    '机械装备汽配': ['机械','装备','汽车','摩托','零部件','配件','铸造','模具','齿轮','电机','轴承','液压','锻造','五金','刀具'],
    '食品农业': ['食品','农','养殖','肉','粮油','乳','茶','酒','饮料','调味','榨菜','豆腐','种植','畜牧'],
    '建筑建材装修': ['建筑','建设','建材','混凝土','装饰','装修','钢结构','门窗','防水','保温','瓷砖','卫浴'],
    '包装印刷': ['包装','印刷','塑料制品','纸','喷码','标签','容器'],
    '环保检测': ['环保','环境','检测','监测','净化','水处理','废气','固废','认证','测试','检验'],
}

def classify(name):
    for sector, kws in sectors.items():
        for kw in kws:
            if kw in name:
                return sector
    return '其他综合'

sector_map = defaultdict(list)
for c in zjtx:
    sec = classify(c)
    sector_map[sec].append(c)

print('\n===== 行业分类统计 =====')
total = 0
for sec, lst in sorted(sector_map.items(), key=lambda x: -len(x[1])):
    print(f'{sec}: {len(lst)}家')
    total += len(lst)
print(f'分类总计: {total}家')

# 输出主文件（含所有分类）
lines = ['# 重庆专精特新企业全名单（2275家）\n\n']
lines.append('> 来源：重庆市经济信息委2025年公示（申报1087家+复核1190家）\n')
lines.append('> 整理时间：2026-08-21\n\n')
lines.append('> 百度推广价值排序：低空经济>新能源充电>医疗器械>软件IT>新材料>机械装备>建材装修\n\n')

for sec, lst in sorted(sector_map.items(), key=lambda x: -len(x[1])):
    lines.append(f'## 【{sec}】{len(lst)}家\n')
    for i, c in enumerate(lst):
        lines.append(f'{i+1}. {c}\n')
    lines.append('\n')

fname_main = '重庆企业全名单_2275家.md'
with open(fname_main, 'w', encoding='utf-8') as f:
    f.write(''.join(lines))
size = os.path.getsize(fname_main)
print(f'\n主文件: {fname_main} ({size}字节, {size//1024}KB)')

# 单独输出各行业txt（方便复制到企查查导入）
for sec, lst in sector_map.items():
    safe_sec = sec.replace('/', '_').replace(' ', '_')
    fname = f'行业_{safe_sec}.txt'
    with open(fname, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lst))
    print(f'{fname}: {len(lst)}家')

print('\n===== 全部完成 ====')
