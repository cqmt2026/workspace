# -*- coding: utf-8 -*-
"""合并住建委建筑装饰企业资质名单到装修master（仅装饰类企业）"""
import sys, os, csv, re
sys.stdout.reconfigure(encoding='utf-8')

master_csv = 'data/master/zs_list_chongqing_latest.csv'

with open(master_csv, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    master_rows = list(reader)
    headers = reader.fieldnames

existing = {r['机构名称'] for r in master_rows}
print(f"装修master现有: {len(master_rows)}家")

# 来自政府官网采集的装饰企业（九龙坡+沙坪坝住建委资质名单中名称含装饰/装修/幕墙的企业）
# 数据源：cqjlp.gov.cn 九龙坡区住建委第十一批资质延续 + cqspb.gov.cn 沙坪坝区住建委2025第三批
new_zx = [
    # 九龙坡区住建委资质延续名单（装饰相关）
    ('重庆市沙坪坝区','重庆碧泉建筑装饰工程有限公司','','装饰公司','九龙坡/沙坪坝区住建委资质名单'),
    ('重庆市九龙坡区','重庆银得金装饰工程有限公司','','装饰公司','九龙坡区住建委资质名单'),
    ('重庆市九龙坡区','重庆立信装饰工程有限公司','','装饰公司','九龙坡区住建委资质名单'),
    ('重庆市沙坪坝区','重庆天建装饰工程有限公司','','装饰公司','沙坪坝区住建委资质名单'),
    ('重庆市沙坪坝区','重庆艾马饰装饰工程有限公司','','装饰公司','沙坪坝区住建委资质名单'),
    ('重庆市沙坪坝区','重庆乙洋建筑装饰工程有限公司','','装饰公司','沙坪坝区住建委资质名单'),
    ('重庆市九龙坡区','中坦建设（集团）有限公司','','装饰公司','九龙坡区住建委资质名单'),
    ('重庆市沙坪坝区','重庆渝康建设（集团）有限公司','','装饰公司','沙坪坝区住建委资质名单'),
    ('重庆市沙坪坝区','勋业工程建设有限公司','','装饰公司','沙坪坝区住建委资质名单'),
]

added = 0
for region, name, addr, cat, src in new_zx:
    if name in existing:
        continue
    master_rows.append({
        '区域': region,
        '机构名称': name,
        '地址': addr,
        '电话': '',
        '机构类别': cat,
        'adname': region.replace('重庆市','').replace('区','区'),
        '经度':'','纬度':'',
        '数据来源': src,
        '抓取时间': '2026-08-29'
    })
    existing.add(name)
    added += 1

with open(master_csv, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(master_rows)

print(f"装修master: 新增{added}家, 总计{len(master_rows)}家")