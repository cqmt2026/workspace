import openpyxl, sys
sys.stdout.reconfigure(encoding='utf-8')

wb = openpyxl.load_workbook(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source\jingxinwei\2025_创新型_申报通过.xlsx', read_only=True)
ws = wb.active
print(f"Sheet: {ws.title}")

# 读取前20行
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i < 25:
        print(f"Row {i}: {row}")
    if i >= 50:
        break

wb.close()
