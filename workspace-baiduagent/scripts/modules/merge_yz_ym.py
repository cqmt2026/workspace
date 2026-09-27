# -*- coding: utf-8 -*-
"""合并渝中区卫健委医疗美容诊所公示到医美master"""
import sys, os, csv, re
sys.stdout.reconfigure(encoding='utf-8')

master_csv = 'data/master/ym_list_chongqing_latest.csv'

with open(master_csv, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    master_rows = list(reader)
    headers = reader.fieldnames

existing = {r['机构名称'] for r in master_rows}

# 渝中区卫健委公示的医美诊所（截至2026-06-18）
new_ym = [
    ('重庆市渝中区', '重庆雅斯澜医疗美容诊所', '渝中区解放碑街道民族路188号3层309A号商铺', '医美诊所', '渝中区卫健委医疗机构公示(2026.06)'),
    ('重庆市渝中区', '重庆时代天街颜所医疗美容诊所', '渝中区时代天街1号、2号A馆-L2-37号', '医美诊所', '渝中区卫健委医疗机构公示(2026.06)'),
    ('重庆市渝中区', '臻颜医疗美容诊所', '渝中区瑞天路10号第4层409A、409B', '医美诊所', '渝中区卫健委医疗机构公示(2026.06)'),
]

added = 0
for region, name, addr, cat, src in new_ym:
    if name in existing:
        continue
    master_rows.append({
        '区域': region,
        '机构名称': name,
        '地址': addr,
        '电话': '',
        '机构类别': cat,
        'adname': '渝中区',
        '经度': '',
        '纬度': '',
        '数据来源': src,
        '抓取时间': '2026-08-29'
    })
    existing.add(name)
    added += 1

with open(master_csv, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(master_rows)

print(f"医美master: 新增{added}家, 总计{len(master_rows)}家")