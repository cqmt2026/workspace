# -*- coding: utf-8 -*-
import re, olefile
from collections import Counter

ole = olefile.OleFileIO(r'C:\Users\Administrator\.openclaw\workspace\百都科技面试资料\重庆专精特新2025名单.doc')
data = ole.openstream('WordDocument').read()
text = data.decode('utf-16-le', errors='ignore')
companies = re.findall(r'[\u4e00-\u9fffA-Za-z（）()、\-·]+?(?:股份有限公司|有限责任公司|有限公司|股份公司|工厂|研究所|公司)', text)
seen = []
for c in companies:
    c = c.strip()
    if c and c not in seen and not any(k in c for k in ['序号','区县','企业名称','名单','公示']):
        seen.append(c)

sectors = [
    ('医疗', re.compile(r'(医疗|医院|生物|医药|制药|器械|诊断|IVD|骨科|口腔|牙科|植入|医用|康复|体检|血液透析|内窥镜|超声|医学检验|体外诊断|卫生材料|消毒产品|药用材料)')),
    ('新材料', re.compile(r'(新材料|化工|涂料|塑胶|橡胶|塑料|纤维|玻璃|陶瓷|碳材料|硅材料|合金|金属制品|粉体|纳米|复合材料|密封|保温|防水卷材|防腐|胶粘剂|颜料|染料|锂电池材料|新能源材料|特种气体|电子化学品|阻燃剂|抗菌材料)')),
    ('软件IT', re.compile(r'(软件|信息|大数据|云计算|物联网|AI|人工智能|智慧城市|数字孪生|工业互联网|SaaS|ERP|MES|CRM|EDA|IC设计|芯片|半导体|嵌入式|信息安全|网络安全|区块链|元宇宙)')),
    ('新能源', re.compile(r'(新能源|充电|电动车|电动汽车|充电站|换电站|储能|光伏|风电|氢能|电池|电气|电力设备|配电|变压器|智能电网|节能设备|碳资产)')),
    ('机械汽配', re.compile(r'(机械|装备|汽车|摩托|零部件|配件|铸造|模具|齿轮|电机|轴承|液压|锻造|五金|刀具|机床|数控|机器人|自动化|仪器仪表|泵阀|压缩机|起重|纺织机械|矿山机械|工程机械|专用设备)')),
    ('建筑建材', re.compile(r'(建筑|建设|建材|混凝土|装饰|装修|钢结构|门窗|防水|保温|瓷砖|卫浴|地板|家具|幕墙|照明|灯具|电线电缆|管道|阀门|石材|家居)')),
    ('食品农业', re.compile(r'(食品|农产品|粮油|乳品|肉制品|饮料|酒类|调味品|榨菜|茶叶|果蔬|水产|畜牧|养殖|种植|农业|饲料|兽药|农资|烘焙|休闲食品|方便食品)')),
    ('包装印刷', re.compile(r'(包装|印刷|标签|喷码|纸制品|塑料制品|复合膜|袋|容器|箱|盒|礼盒|说明书|彩印|凹印|柔印|防伪标签)')),
    ('环保检测', re.compile(r'(环保|环境|检测|监测|净化|水处理|废气|固废|危废|噪声|土壤|空气检测|认证|测试|检验|计量|校准|环评|生态修复|节能减排)')),
]

def classify(name):
    for sec, pattern in sectors:
        if pattern.search(name):
            return sec
    return '其他'

uncategorized = []
classified = Counter()
for c in seen:
    sec = classify(c)
    if sec == '其他':
        uncategorized.append(c)
    else:
        classified[sec] += 1

print('已分类统计:', dict(classified))
print(f'未分类: {len(uncategorized)}家')
print('\n未分类前50条:')
for i, c in enumerate(uncategorized[:50]):
    print(f'  {i+1}. {c}')

# 后缀词分布
suffixes = Counter()
for c in uncategorized:
    if '科技' in c: suffixes['科技'] += 1
    if '智能' in c: suffixes['智能'] += 1
    if '信息' in c: suffixes['信息'] += 1
    if '数字' in c: suffixes['数字'] += 1
    if '网络' in c: suffixes['网络'] += 1
    if '电子商务' in c: suffixes['电商'] += 1
    if '咨询' in c: suffixes['咨询'] += 1
    if '贸易' in c: suffixes['贸易'] += 1
    if '实业' in c: suffixes['实业'] += 1
    if '集团' in c: suffixes['集团'] += 1
    if '管理' in c: suffixes['管理'] += 1
    if '服务' in c: suffixes['服务'] += 1
for k, v in sorted(suffixes.items(), key=lambda x: -x[1]):
    print(f'  后缀"{ k}": {v}家')