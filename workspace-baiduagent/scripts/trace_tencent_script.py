# -*- coding: utf-8 -*-
"""精确追踪：腾讯批量抓取脚本的每一步"""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

TX_KEY = '***'
TX_CALLS = 0
TX_SUCCESS = 0
TX_FAILED = 0

print("=" * 60)
print("【精确追踪】模拟批量抓取脚本执行过程")
print("=" * 60)

# 模拟脚本的INDUSTRY_KEYWORDS配置
INDUSTRY_KEYWORDS = {
    '口腔诊所': ['口腔诊所', '牙科医院', '齿科', '口腔医院', '口腔门诊', '牙病防治所'],
    '装修装饰': ['装修公司', '室内装饰', '装修设计', '建筑装饰工程', '家装公司'],
    '教培机构': ['培训机构', '教育学校', '兴趣班', '补习班', '艺术培训', '体育培训', '幼儿园'],
    '宠物医院': ['宠物医院', '宠物诊所', '动物诊疗', '宠物保健'],
    '医美机构': ['医疗美容', '医美', '整形医院', '美容医院', '整形门诊', '皮肤科'],
    '母婴亲子': ['母婴店', '月子中心', '早教中心', '儿童乐园', '孕婴用品'],
    '机械装备汽配': ['机械厂', '机械制造', '汽配', '汽车零部件', '机械设备'],
    '新材料化工': ['新材料', '化工', '化工厂', '涂料', '新材料科技'],
    '医疗器械': ['医疗器械', '医疗设备', '医药器械', '生物科技'],
    '环保检测': ['环保检测', '环境监测', '检测服务', '质检'],
    '建筑建材': ['建筑材料', '建材', '水泥', '钢材', '防水材料'],
    '新能源充电电力': ['充电桩', '新能源', '光伏发电', '电力工程', '变电所'],
    '物流货运': ['物流公司', '货运', '快递', '仓储'],
    '酒店餐饮': ['酒店', '餐饮', '饭店', '餐厅'],
    '汽车服务': ['汽车维修', '4S店', '汽车美容', '二手车'],
}

# 模拟脚本执行
total_keywords = sum(len(kws) for kws in INDUSTRY_KEYWORDS.values())
print(f"总关键词数: {total_keywords}")
print(f"每个关键词最多20页，每页20条 = 最大400条/关键词")
print()

# 测试前几个关键词
test_count = 0
for industry, keywords in INDUSTRY_KEYWORDS.items():
    for kw in keywords:
        test_count += 1
        TX_CALLS += 1
        r = requests.get('https://apis.map.qq.com/ws/place/v1/search',
            params={'key': TX_KEY, 'boundary': 'region(重庆,0)', 'keyword': kw, 'max_per_page': 20, 'page': 1},
            timeout=10)
        d = r.json()
        if d.get('status') == 0:
            TX_SUCCESS += 1
            data_count = len(d.get('data', []))
            print(f"[{test_count}/{total_keywords}] {industry}-{kw}: {data_count}条 (累计调用{TX_CALLS}次, 成功{TX_SUCCESS}次)")
            if data_count > 0:
                print(f"   样例: {d['data'][0].get('title')}, tel={d['data'][0].get('tel')}")
        else:
            TX_FAILED += 1
            print(f"[{test_count}/{total_keywords}] {industry}-{kw}: FAIL {d.get('message')} (累计调用{TX_CALLS}次)")
            # 一旦失败就停止
            break
    if TX_FAILED > 0:
        break

print("\n" + "=" * 60)
print("【追踪结论】")
print("=" * 60)
print(f"总调用次数: {TX_CALLS}")
print(f"成功次数: {TX_SUCCESS}")
print(f"失败次数: {TX_FAILED}")
print(f"成功条数: 约{TX_SUCCESS * 10}条 (估算)")
print()
if TX_SUCCESS == 0:
    print("❌ 问题确认: Key从一开始就失败，不是配额耗尽后失败")
    print("   可能原因:")
    print("   1. Key格式问题（但之前测试成功过）")
    print("   2. 配额从第1次就受限（不可能，刚配置成功）")
    print("   3. 时间窗口问题（17:31配置成功，18:02测试已超限？）")
elif TX_SUCCESS > 0 and TX_FAILED > 0:
    print("✅ 部分成功，说明脚本逻辑有问题（保存失败）")
else:
    print("⚠️ 需要进一步分析")
