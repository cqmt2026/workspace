#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出Excel格式拨打清单"""
import sqlite3
import random
import os

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
except ImportError:
    print('请安装openpyxl: pip install openpyxl')
    exit(1)

DB = 'data/baidu_crm.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

# 获取所有有电话的企业，排除宠物医院
c.execute('''SELECT id, name, industry, phone, district 
             FROM customers 
             WHERE phone IS NOT NULL 
             AND phone != ""
             AND industry != "宠物医院"
             ORDER BY id''')
all_customers = c.fetchall()

random.seed(20260927)
random.shuffle(all_customers)

day1 = all_customers[:200]
day2 = all_customers[200:400]
day3 = all_customers[400:600]

# 创建Excel
wb = openpyxl.Workbook()

# 样式
header_font = Font(bold=True, size=11)
header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
header_font_white = Font(bold=True, size=11, color="FFFFFF")
thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

def create_sheet(ws, title, data):
    ws.title = title
    ws.append([title])
    ws.append([])
    ws.append(['序号', '企业名称', '行业', '电话', '区域', '拨打状态', '意向等级', '备注'])
    
    for i, cust in enumerate(data, 1):
        idx, name, industry, phone, district = cust
        ws.append([i, name, industry, phone, district, '', '', ''])
    
    # 设置表头样式
    for cell in ws[3]:
        cell.font = header_font_white
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # 调整列宽
    ws.column_dimensions['A'].width = 6
    ws.column_dimensions['B'].width = 35
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 18
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 12
    ws.column_dimensions['H'].width = 20

ws1 = wb.create_sheet()
ws2 = wb.create_sheet()
ws3 = wb.create_sheet()

create_sheet(ws1, '周一 09-29', day1)
create_sheet(ws2, '周二 09-30', day2)
create_sheet(ws3, '周三 10-01', day3)

# 添加汇总页
ws_summary = wb.create_sheet('汇总', 0)
ws_summary.append(['下周三天拨打清单汇总'])
ws_summary.append([])
ws_summary.append(['日期', '行业分布TOP5', '目标数量', '实际拨打', '意向数', '转化率'])
ws_summary.append(['周一 09-29', '', '200', '', '', ''])
ws_summary.append(['周二 09-30', '', '200', '', '', ''])
ws_summary.append(['周三 10-01', '', '200', '', '', ''])
ws_summary.append(['总计', '', '600', '', '', ''])

output_path = 'assets/下周三天拨打清单_20260929-09-30.xlsx'
wb.save(output_path)
conn.close()

print(f'已导出：{output_path}')
print(f'包含3个工作表：周一/周二/周三')
print(f'每个工作表200行，含拨打状态/意向等级/备注列')
