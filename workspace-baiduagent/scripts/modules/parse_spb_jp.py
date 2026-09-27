# -*- coding: utf-8 -*-
"""从沙坪坝PDF提取干净机构名列表（基于全文本）"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
import pdfplumber

pdf_path = 'data/source/weijkw/jp_list_chongqing_weijkw_20260829_shapingba.pdf'

with pdfplumber.open(pdf_path) as pdf:
    full = ''
    for page in pdf.pages:
        full += (page.extract_text() or '') + '\n'

# 清洗：去掉换行（PDF行内截断），再按序号分段
# 先把所有换行去掉（地址内也有换行，但机构名和地址会粘连）——改用：按"数字+机构名"开头行识别
lines = [l.strip() for l in full.split('\n') if l.strip()]

# 机构名特征：以重庆/重庆市开头，包含 培训/学校/中心/有限公司
# 遍历行，找出真正以序号开头且含机构名特征的行
org_names = []
for line in lines:
    m = re.match(r'^(\d{1,3})\s+(.+)$', line)
    if m:
        rest = m.group(2)
        # 机构名：从开头到第一个 地址特征（沙坪坝/重庆市沙坪坝地址等）
        # 机构名通常以 重庆 开头
        # 取"重庆...有限公司/学校/中心" 作为机构名
        m2 = re.match(r'^(.{0,60}?(?:有限公司|有限责任公司|培训学校|学校|培训中心|艺术培训中心|教育培训中心|中心))\s*(.*)$', rest)
        if m2:
            name = m2.group(1)
            org_names.append(name)

# 统计
print(f"提取到 {len(org_names)} 家机构名")
for n in org_names:
    print(' ', n)

# 保存纯名称列表
out = 'data/source/weijkw/jp_chongqing_shapingba_names.txt'
with open(out, 'w', encoding='utf-8') as f:
    for n in org_names:
        f.write(n + '\n')
print(f"\n已保存: {out}")