"""
从经信委原始Excel读取真实企业名称，补充到CRM，然后高德POI补电话
"""
import openpyxl, sqlite3, urllib.parse, urllib.request, json, os, time, re, random, sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'
XLSX_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source\jingxinwei'
LEDGER_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\multi_channel_ledger.json'

# 区县 -> adcode
COUNTY_MAP = {
    '万州区': '500101', '涪陵区': '500102', '渝中区': '500103', '大渡口区': '500104',
    '江北区': '500105', '沙坪坝区': '500106', '九龙坡区': '500107', '南岸区': '500108',
    '北碚区': '500109', '渝北区': '500110', '巴南区': '500111', '长寿区': '500112',
    '江津区': '500116', '合川区': '500117', '永川区': '500118', '璧山区': '500120',
    '綦江区': '500110', '大足区': '500111', '荣昌区': '500111', '铜梁区': '500110',
    '潼南区': '500106', '高新区': '500301', '两江新区': '500105',
}

def get_key():
    key = os.environ.get('GD_MAP_KEY', '')
    if not key:
        try:
            with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            key = data.get('channels', {}).get('高德POI', {}).get('key_source', '').replace('完整32位Key: ', '')
        except: pass
    return key

def search(kw, city='500000'):
    key = get_key()
    url = f"https://restapi.amap.com/v3/place/text?key={key}&keywords={urllib.parse.quote(kw)}&city={city}&offset=1&pageSize=10&output=json"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode('utf-8'))
        if data.get('status') == '1':
            return data.get('pois', []), data.get('info', '')
        return [], data.get('info', 'ERR')
    except Exception as e:
        return [], str(e)

# Step 1: 读取Excel
print("=== Step 1: 读取经信委Excel ===", flush=True)

companies = []
for xlsx_file in ['2025_创新型_申报通过.xlsx', '2025_创新型_复核通过.xlsx']:
    path = os.path.join(XLSX_PATH, xlsx_file)
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i < 2:  # 跳过标题行
            continue
        seq, name, county = row[0], row[1], row[2]
        if name and str(name).strip():
            companies.append({
                'name': str(name).strip(),
                'county': str(county).strip() if county else '',
                'source': xlsx_file
            })
    wb.close()

print(f"  从Excel读取 {len(companies)} 家企业", flush=True)

# Step 2: 更新CRM中序号行的name和county
print("\n=== Step 2: 更新CRM名称和区县 ===", flush=True)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

updated = 0
# 按seq排序匹配
companies_sorted = sorted(companies, key=lambda x: (x['county'] or '', x['name']))

# 找到经信委来源且name是序号的行
c.execute("""SELECT id, name FROM customers
    WHERE industry='创新型中小企业' AND source LIKE '%经信委%'
    AND (name GLOB '[0-9]*' OR name = '序号')
    ORDER BY id""")
old_rows = c.fetchall()
print(f"  需更新的序号行: {len(old_rows)}家", flush=True)

# 映射：按顺序匹配（经信委名单已按区县+序号排列）
for idx, (old_id, old_name) in enumerate(old_rows):
    if idx >= len(companies_sorted):
        break
    new_name = companies_sorted[idx]['name']
    new_county = companies_sorted[idx]['county']
    c.execute("UPDATE customers SET name=?, district=? WHERE id=?", (new_name, new_county, old_id))
    updated += 1

conn.commit()
print(f"  更新了 {updated} 条名称和区县", flush=True)

# Step 3: 高德POI补电话
print(f"\n=== Step 3: 高德POI补电话 ===", flush=True)
c.execute("""SELECT id, name, district FROM customers
    WHERE industry='创新型中小企业'
    AND (phone IS NULL OR phone='')
    ORDER BY id""")
no_phone = c.fetchall()
print(f"  无电话: {len(no_phone)}家", flush=True)

found = processed = quota_hits = consec_errs = 0

for sid, sname, scounty in no_phone:
    processed += 1
    
    # 确定city code
    city = '500000'
    if scounty:
        for kw, code in COUNTY_MAP.items():
            if kw in scounty:
                city = code
                break
    
    kw_str = f"{sname} 重庆"
    pois, info = search(kw_str, city)
    
    if info == 'QUOTA_EXCEEDED':
        quota_hits += 1
        print(f"  [!] 配额超限, 等待30秒...", flush=True)
        time.sleep(30)
        pois, info = search(kw_str, city)
        if info == 'QUOTA_EXCEEDED':
            print(f"  持续超限, 停止", flush=True)
            break
        continue
    
    if info != 'OK':
        consec_errs += 1
        if consec_errs > 5:
            print(f"  连续错误{consec_errs}次, 停止", flush=True)
            break
        time.sleep(2)
        continue
    
    consec_errs = 0
    
    if pois:
        for poi in pois:
            pn = poi.get('name', '')
            pp = poi.get('tel', '')
            if pp and (sname[:4] in pn or pn[:4] in sname):
                c.execute("UPDATE customers SET phone=? WHERE id=?", (pp, sid))
                found += 1
                print(f"  [{processed}] FOUND [{scounty}]: {sname[:20]}... -> {pp}", flush=True)
                time.sleep(0.3)
                break
    
    if processed % 15 == 0:
        print(f"  Progress: {processed}, found:{found}, quota:{quota_hits}", flush=True)
    
    time.sleep(random.uniform(0.5, 1.0))

conn.commit()

c.execute("SELECT COUNT(*) FROM customers WHERE industry='创新型中小企业' AND phone IS NOT NULL AND phone!=''")
total = c.fetchone()[0]

print(f"\n{'='*50}", flush=True)
print(f"完成! 处理:{processed} 新增:{found} 配额超限:{quota_hits}", flush=True)
print(f"创新型中小企业电话: {total}/1793 ({total/1793*100:.1f}%)", flush=True)
conn.close()
