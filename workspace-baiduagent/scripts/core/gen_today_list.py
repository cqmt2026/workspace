import sqlite3, json

conn = sqlite3.connect(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db')
cur = conn.cursor()

priority_map = {
    '医疗器械': 1, '医疗健康': 1, '医疗卫生': 1, '医美机构': 1,
    '新材料化工': 2,
    '机械装备汽配': 3, '工程机械': 3, '数控机床': 3, '模具': 3, '精密机械': 3,
    '传动设备': 3, '轴承': 3, '液压设备': 3, '自动化设备': 3, '焊接设备': 3,
    '切割设备': 3, '注塑机械': 3, '齿轮': 3, '铸造': 3, '锻造': 3, '风机': 3,
    '金属加工': 3, '润滑油': 3, '电机电气': 3,
    '环保检测': 4, '检验检测': 4,
    '新能源充电电力': 5,
    '建筑建材': 6, '装修装饰': 6,
    '电子科技': 7, '软件信息': 7, '商贸批发': 7, '广告传媒': 7, '文化传媒': 7,
    '人力资源': 8, '物流货运': 8, '健身瑜伽': 8, '宠物医院': 8,
    '母婴亲子': 8, '酒店餐饮': 8, '房产中介': 8, '教培机构': 8,
    '食品加工': 9, '家具家居': 9, '法律服务': 9, '汽摩配件': 9,
}

cur.execute('''
    SELECT c.id, c.name, c.industry, c.phone, c.status 
    FROM customers c 
    WHERE c.tier='A' AND (c.status IS NULL OR c.status='待联系')
    ORDER BY c.id ASC
''')
rows = cur.fetchall()

sorted_rows = sorted(rows, key=lambda r: priority_map.get(r[2], 99))
top10 = sorted_rows[:10]

result = []
for r in top10:
    result.append({
        'id': r[0],
        'name': r[1],
        'industry': r[2],
        'phone': r[3],
        'status': r[4]
    })

print(json.dumps(result, ensure_ascii=False, indent=2))
conn.close()
