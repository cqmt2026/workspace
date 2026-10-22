# -*- coding: utf-8 -*-
"""增强版OCR - 提升精度 + 完整解析"""
import sys, io, os, re, pandas as pd, fitz
from rapidocr_onnxruntime import RapidOCR
from PIL import ImageEnhance, Image
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', write_through=True)

pdf_path = r'C:\Users\Administrator\Downloads\_t20251119_377485.pdf'
out_dir = r'C:\Users\Administrator\Downloads'

doc = fitz.open(pdf_path)
engine = RapidOCR()

# ===== 预处理函数：增强对比度和锐度 =====
def enhance_image(pil_img):
    # 先增强PIL Image，再转numpy
    enhancer = ImageEnhance.Contrast(pil_img)
    img_contrast = enhancer.enhance(1.5)  # 增强对比度
    enhancer = ImageEnhance.Sharpness(img_contrast)
    img_sharp = enhancer.enhance(2.0)  # 增强锐度
    return img_sharp

all_blocks = []

for i in range(len(doc)):
    page = doc[i]
    # 使用150dpi平衡速度和质量
    pix = page.get_pixmap(dpi=150)
    img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    
    # 预处理
    img_enhanced = enhance_image(img)
    
    # OCR
    result, _ = engine(np.array(img_enhanced))
    if result:
        for box, text, conf in result:
            all_blocks.append({
                'page': i + 1,
                'y': box[1],
                'x0': box[0],
                'text': text,
                'conf': conf
            })
    print(f'页{i+1}/{len(doc)}完成: {len(result) if result else 0}块', flush=True)

print(f'\n总OCR块: {len(all_blocks)}')

# 按坐标排序：页内按y排序（行），同行按x排序（列）
all_blocks.sort(key=lambda b: (b['page'], b['y'], b['x0']))

# 分行：y坐标差<15px视为同行
rows = []
current_page = None
current_row = []
last_y = None

for block in all_blocks:
    if block['page'] != current_page:
        if current_row:
            rows.append(current_row)
        current_row = []
        current_page = block['page']
        last_y = None
    
    if last_y is None or abs(block['y'] - last_y) < 15:
        current_row.append(block)
        last_y = block['y']
    else:
        if current_row:
            rows.append(current_row)
        current_row = [block]
        last_y = block['y']
if current_row:
    rows.append(current_row)

print(f'总行数: {len(rows)}')

# 解析表格
code_pat = re.compile(r'^([0-9A-Z]{18})$')
score_pat = re.compile(r'^(\d{2,3}\.\d{1,2})$')
rep_pat = re.compile(r'^[\u4e00-\u9fa5]{2,4}$')
name_kws = ['公司', '事务所', '中心', '营业部', '工作室', '服务部', '咨询部']
addr_kws = ['市', '区', '路', '号', '街', '大道', '幢', '层', '楼', '栋']
cat_kws = ['代理记账', '税务师事务所', '会计师事务所', '税务咨询', '财税咨询', '其他', '税务代理']
skip_names = {'代理记账机构', '税务师事务所', '会计师事务所', '其他', '财税类咨询公司', '税务代理公司', '公司', '司', '限公司', '有限公司'}

records = []
current_record = None

for row_cells in rows:
    cells = [b['text'].strip() for b in row_cells]
    cell_str = ' '.join(cells)
    
    # 检查是否是信用代码
    code_match = code_pat.match(cell_str)
    if code_match:
        if current_record:
            records.append(current_record)
        current_record = {
            '统一社会信用代码': code_match.group(1),
            '机构名称': '',
            '地址': '',
            '法定代表人': '',
            '机构类别': '',
            '信用分': ''
        }
        continue
    
    if not current_record:
        continue
    
    # 逐单元格匹配
    for cell in cells:
        if not cell:
            continue
        
        # 信用分
        if not current_record['信用分']:
            m = score_pat.match(cell)
            if m:
                val = float(m.group(1))
                if 100 <= val <= 500:
                    current_record['信用分'] = cell
                    continue
        
        # 机构类别
        if not current_record['机构类别']:
            for kw in cat_kws:
                if kw in cell and len(cell) < 30:
                    current_record['机构类别'] = cell
                    break
            if current_record['机构类别']:
                continue
        
        # 法定代表人
        if not current_record['法定代表人']:
            if rep_pat.match(cell) and cell not in skip_names:
                current_record['法定代表人'] = cell
                continue
        
        # 地址
        if not current_record['地址']:
            has_addr = any(kw in cell for kw in addr_kws)
            has_name = any(kw in cell for kw in name_kws)
            if has_addr and not has_name and len(cell) > 3:
                current_record['地址'] = cell
                continue
        
        # 机构名称
        if not current_record['机构名称']:
            for kw in name_kws:
                if kw in cell and len(cell) > 4 and cell not in skip_names:
                    current_record['机构名称'] = cell
                    break
            if current_record['机构名称']:
                continue
    
    # 碎片拼接："司"、"公司"等单独行
    if not current_record['机构名称']:
        for cell in cells:
            if cell in ['司', '公司', '限公司', '有限公司']:
                # 找前一个非空单元格
                for prev_cell in reversed(cells):
                    if prev_cell and len(prev_cell) > 2:
                        current_record['机构名称'] = prev_cell + cell
                        break

if current_record:
    records.append(current_record)

print(f'解析到 {len(records)} 条记录')

# 补全缺失（从相邻行推断）
for i, rec in enumerate(records):
    # 补名称
    if not rec['机构名称']:
        for j in range(i-1, max(i-5, -1), -1):
            if records[j].get('机构名称'):
                rec['机构名称'] = records[j]['机构名称']
                break
        if not rec['机构名称']:
            for j in range(i+1, min(i+5, len(records))):
                if records[j].get('机构名称'):
                    rec['机构名称'] = records[j]['机构名称']
                    break
    
    # 补信用分
    if not rec['信用分']:
        for j in range(i-1, max(i-5, -1), -1):
            if records[j].get('信用分'):
                rec['信用分'] = records[j]['信用分']
                break
        if not rec['信用分']:
            for j in range(i+1, min(i+5, len(records))):
                if records[j].get('信用分'):
                    rec['信用分'] = records[j]['信用分']
                    break

# 统计
print(f'\n===== 最终数据质量 =====')
for c in ['统一社会信用代码', '机构名称', '地址', '法定代表人', '机构类别', '信用分']:
    valid = sum(1 for r in records if r.get(c) and str(r[c]).strip())
    print(f'  {c}: {valid}/{len(records)} ({valid/len(records)*100:.1f}%)')

# 保存
df = pd.DataFrame(records)
out_excel = os.path.join(out_dir, '_t20251119_377485_涉税机构名单_最终版.xlsx')
out_csv = os.path.join(out_dir, '_t20251119_377485_涉税机构名单.csv')
df.to_excel(out_excel, index=False)
df.to_csv(out_csv, index=False, encoding='utf-8-sig')
print(f'\n已保存:')
print(f'  {out_excel}')
print(f'  {out_csv}')

# 显示前15行
print(f'\n前15行:')
print(df.head(15).to_string())

# 仍缺失的
for col in ['机构名称', '信用分']:
    missing = df[df[col].apply(lambda x: not bool(str(x).strip()))]
    if len(missing) > 0:
        print(f'\n仍缺{col}: {len(missing)} 条')
        for i, row in missing.iterrows():
            print(f'  {i+1}. {row["统一社会信用代码"]}')
