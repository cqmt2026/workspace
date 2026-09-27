import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = openpyxl.Workbook()
ws = wb.active
ws.title = '光伏组件品牌总表'

# Styles
header_font = Font(bold=True, size=11, color='FFFFFF')
header_fill = PatternFill(start_color='2F5496', end_color='2F5496', fill_type='solid')
sub_fill = PatternFill(start_color='D6E4F0', end_color='D6E4F0', fill_type='solid')
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)
center = Alignment(horizontal='center', vertical='center', wrap_text=True)
left = Alignment(horizontal='left', vertical='center', wrap_text=True)

# Headers
headers = ['排名', '品牌', '公司', '上市代码', '2025出货量(GW)', '技术路线', '主要产品系列', '量产效率', '最高功率(W)', '备注']
for i, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=i, value=h)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = center
    cell.border = thin_border

# Data
data = [
    [1, '晶科能源', '晶科能源股份有限公司', '688223.SH', 86.81, 'TOPCon', 'Tiger Neo飞虎3系列', '24.8%', 670, '七度全球出货冠军，2026年目标75-85GW'],
    [2, '隆基绿能', '隆基绿能科技股份有限公司', '601012.SH', 86.58, 'BC', 'Hi-MO 9系列', '24.8%', 670, 'BC组件出货22.87GW，占比26.4%'],
    [3, '晶澳科技', '晶澳太阳能科技股份有限公司', '002459.SZ', 69.56, 'TOPCon', 'DeepBlue 4.0 Pro / 5.0', '24.8%', 670, 'DeepBlue 5.0量产下线'],
    [4, '天合光能', '天合光能股份有限公司', '688599.SH', 67.00, 'TOPCon/210', 'Vertex系列', '~24.5%', 670, '210组件累计出货超236GW'],
    [5, '通威股份', '通威股份有限公司', '600438.SH', 43.25, 'TOPCon', 'TNC系列', '24.58%', 763, '全球最大电池片+组件制造商'],
    [6, '正泰新能', '正泰新能科技有限公司', '601877.SH', 36.50, 'TOPCon', 'ASTRO系列', '~24.0%', 660, '预估数据，户用分布式强势'],
    [7, '协鑫集成', '协鑫集成科技股份有限公司', '002506.SZ', 25.28, 'TOPCon', 'GCL系列', '23.2%', 670, '含电池销售，GPC电池效率突破27.5%'],
    [8, '横店东磁', '横店集团东磁股份有限公司', '002056.SZ', 24.90, 'TOPCon', 'DM系列', '~24.0%', 650, '2025年唯一盈利的组件企业之一'],
    [9, '阿特斯', '阿特斯阳光电力集团', '688472.SH', 24.30, 'TOPCon', 'CS系列', '~24.0%', 660, '战略重心转向储能，美国出货8.1GW'],
    [10, '英利能源', '英利能源发展有限公司', '国资', 25.00, 'TOPCon', '熊猫系列', '~23.5%', 650, '唯一国企，高原/沙戈荒/防尘组件'],
    [11, '一道新能', '一道新能源科技股份有限公司', '被TCL中环控股', 25.00, 'TOPCon', 'DAON系列', '~24.0%', 660, 'TOPCon黑马，已被TCL中环收购'],
    [12, 'TCL中环', 'TCL中环新能源科技股份有限公司', '002129.SZ', 15.10, 'TOPCon', 'G12系列', '~23.5%', 650, '收购一道新能后出货量将大幅提升'],
    [13, '爱旭股份', '上海爱旭新能源股份有限公司', '600732.SH', 14.71, 'ABC', '恒星/彗星/黑洞系列', '25.2%', 680, '量产效率全球第一，ABC组件'],
    [14, '东方日升', '东方日升新能源股份有限公司', '300118.SZ', '~12.0', 'HJT', 'RSM系列', '~24.0%', 660, 'HJT异质结技术路线'],
]

for r_idx, row in enumerate(data, 2):
    for c_idx, val in enumerate(row, 1):
        cell = ws.cell(row=r_idx, column=c_idx, value=val)
        cell.alignment = center if c_idx <= 2 else left
        cell.border = thin_border
        if r_idx % 2 == 0:
            cell.fill = PatternFill(start_color='F2F7FB', end_color='F2F7FB', fill_type='solid')

# Auto width
col_widths = [6, 14, 28, 18, 16, 16, 24, 12, 12, 50]
for i, w in enumerate(col_widths, 1):
    ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

# Freeze header
ws.freeze_panes = 'A2'

# ========== Sheet 2: 详细产品规格 ==========
ws2 = wb.create_sheet('重点品牌产品规格')

headers2 = ['品牌', '产品系列', '版型', '功率范围(W)', '效率', '电池技术', '尺寸(mm)', '重量(kg)', '双面率', '质保']
for i, h in enumerate(headers2, 1):
    cell = ws2.cell(row=1, column=i, value=h)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = center
    cell.border = thin_border

specs = [
    ['晶科能源', 'Tiger Neo飞虎3', '48QL6-DV/DB', '430-480', '24.8%', 'N-TOPCon', '1903x1134x30', 24.5, '85%±5%', '15年'],
    ['晶科能源', 'Tiger Neo飞虎3', '51QL6-BDV', '460-515', '24.8%', 'N-TOPCon', '2028x1134x30', 25.5, '85%±5%', '15年'],
    ['晶科能源', 'Tiger Neo飞虎3', '66QL6-BDV', '615-670', '24.8%', 'N-TOPCon', '2382x1134x30', 32.5, '85%±5%', '15年'],
    ['隆基绿能', 'Hi-MO 9', '72版型', '580-670', '24.8%', 'BC', '2278x1134x30', 31.5, '80%±5%', '15年'],
    ['晶澳科技', 'DeepBlue 5.0', '66版型', '620-670', '24.8%', 'N-TOPCon', '2382x1134x30', 32.0, '85%±5%', '15年'],
    ['天合光能', 'Vertex N', '210R-66', '615-670', '24.5%', 'N-TOPCon', '2382x1134x30', 32.0, '85%±5%', '15年'],
    ['通威股份', 'TNC-GI2', '66版型', '650-763', '24.58%', 'N-TOPCon', '2382x1134x30', 32.5, '85%±5%', '15年'],
    ['爱旭股份', '恒星系列', '66版型', '640-680', '25.2%', 'ABC', '2382x1134x30', 32.0, '90%±5%', '15年'],
]

for r_idx, row in enumerate(specs, 2):
    for c_idx, val in enumerate(row, 1):
        cell = ws2.cell(row=r_idx, column=c_idx, value=val)
        cell.alignment = center
        cell.border = thin_border

col_widths2 = [14, 20, 18, 16, 10, 12, 22, 10, 12, 8]
for i, w in enumerate(col_widths2, 1):
    ws2.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
ws2.freeze_panes = 'A2'

# ========== Sheet 3: 行业概览 ==========
ws3 = wb.create_sheet('行业概览')
ws3.merge_cells('A1:B1')
ws3.cell(row=1, column=1, value='2025年中国光伏组件行业概览').font = Font(bold=True, size=14)

summary = [
    ['全球组件出货总量', '约536GW（TOP12企业合计）'],
    ['中国前四强出货', '307.79GW，占比64.63%'],
    ['全行业亏损', '仅横店东磁和阿特斯盈利，前四强合计亏损249亿元'],
    ['主流技术', 'TOPCon占中国电池产量86.9%，已成绝对主流'],
    ['BC技术', '隆基BC组件出货22.87GW，占比26.4%，增速最快'],
    ['组件价格', '0.7-0.9元/W区间（2025年），行业均价低于成本线'],
    ['产能利用率', '约55-60%，产能过剩1.8倍'],
    ['2026年展望', '全球新增装机预计649GW，中国238-287GW'],
    ['价格说明', '光伏组件价格随硅料价格波动，官网不公开价格，需向经销商询价'],
]

for r_idx, (k, v) in enumerate(summary, 3):
    ws3.cell(row=r_idx, column=1, value=k).font = Font(bold=True)
    ws3.cell(row=r_idx, column=1, value=k).border = thin_border
    ws3.cell(row=r_idx, column=2, value=v).border = thin_border

ws3.column_dimensions['A'].width = 25
ws3.column_dimensions['B'].width = 55

output = r'C:\Users\Administrator\.openclaw\workspace\光伏组件品牌价格表.xlsx'
wb.save(output)
print(f'Done! Saved to {output}')