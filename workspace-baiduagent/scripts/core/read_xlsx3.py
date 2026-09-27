import openpyxl, sys
sys.stdout.reconfigure(encoding='utf-8')

for fname in ['2025_创新型_申报通过.xlsx', '2025_创新型_复核通过.xlsx']:
    path = rf'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source\jingxinwei\{fname}'
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    print(f"\n=== {fname} ===")
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i < 5:
            print(f"Row {i}: {row}")
        elif i == 5:
            print(f"... (total rows will be counted)")
        if i >= 30:
            break
    wb.close()
