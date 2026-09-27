# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

def add_para(doc, text, bold=False, size=12, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=6, indent=None):
    para = doc.add_paragraph()
    para.alignment = align
    para.paragraph_format.space_before = Pt(space_before)
    para.paragraph_format.space_after = Pt(space_after)
    if indent:
        para.paragraph_format.first_line_indent = Cm(indent)
    run = para.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = 'SimSun'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
    return para

# 创建文档
doc = Document()
sections = doc.sections
for s in sections:
    s.top_margin = Cm(2.54)
    s.bottom_margin = Cm(2.54)
    s.left_margin = Cm(3.17)
    s.right_margin = Cm(3.17)

# 标题
add_para(doc, '证据目录', bold=True, size=18, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)

# 案件信息
add_para(doc, '案号：（2026）渝0157民初82907号', bold=True, size=12, space_after=6)
add_para(doc, '答辩人（被告）：唐斐男', bold=True, size=12, space_after=6)
add_para(doc, '被答辩人（原告）：成都万科物业服务有限公司', bold=True, size=12, space_after=12)

# 说明
add_para(doc, '本证据目录共计13项证据，分四组提交。所有证据均准备一式三份（法院一份、原告一份、被告留存一份）。', indent=0.74, space_before=12, space_after=12)

# 第一组
add_para(doc, '第一组：漏水事实证据', bold=True, size=14, space_before=16)

group1 = [
    ['编号', '证据名称', '证据来源', '证明目的', '页码', '形式'],
    ['A-1', '钥匙委托凭证（2019年5月2日）', '被告提供', '证明漏水问题在交房时即存在，被告已履行报修义务，原告明知房屋存在质量问题', '1', '书证'],
    ['A-2', '微信反馈截图及照片（2019年6月22日）', '被告提供', '证明漏水具体问题和被告积极报修，反馈内容包括二楼阳台积水、三楼楼梯口渗水、儿童房渗水、窗户油漆脱落、主卧滑门渗水共6项问题', '2-10', '电子数据+书证'],
    ['A-3', '整改记录照片（2019年8月）', '被告提供', '证明漏水问题持续存在，物业多次维修未果', '11-12', '书证'],
    ['A-4', '整改记录照片（2020年9月）', '被告提供', '证明整改无效，问题反复，发现房屋内堆放建材，两个露台大面积返工', '13-19', '书证'],
    ['A-5', '漏水视频（2022年5月9日）', '被告提供', '证明漏水严重程度，影响正常居住', '20-23', '视听资料']
]

table1 = doc.add_table(rows=len(group1), cols=6)
table1.style = 'Table Grid'
table1.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, row_data in enumerate(group1):
    for j, cell_text in enumerate(row_data):
        table1.rows[i].cells[j].text = cell_text
        for para in table1.rows[i].cells[j].paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if para.runs:
                para.runs[0].font.size = Pt(9)
                para.runs[0].font.name = 'SimSun'
                para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
                if i == 0:
                    para.runs[0].bold = True

doc.add_paragraph()

# 第二组
add_para(doc, '第二组：沟通记录证据', bold=True, size=14, space_before=16)

group2 = [
    ['编号', '证据名称', '证据来源', '证明目的', '页码', '形式'],
    ['A-6', '录音（2021年3月5日）', '被告提供', '证明业主持续投诉，物业不作为', '24-25', '视听资料'],
    ['A-7', '李霖聊天记录（17张）', '被告提供', '证明业主积极沟通，物业敷衍塞责', '26-42', '电子数据'],
    ['A-8', '观承售后聊天记录（16张）', '被告提供', '证明业主持续投诉，物业未有效处理', '43-58', '电子数据'],
    ['A-9', '其他业主漏水问题聊天记录（40张）', '被告提供', '证明漏水问题具有普遍性，物业不作为；特别是2019年7月27日邻居反映"5月接房承诺的整改一直没有下文"', '59-98', '电子数据'],
    ['A-10', '通话记录截图', '被告提供', '证明业主主动沟通，物业催缴', '99-101', '书证']
]

table2 = doc.add_table(rows=len(group2), cols=6)
table2.style = 'Table Grid'
table2.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, row_data in enumerate(group2):
    for j, cell_text in enumerate(row_data):
        table2.rows[i].cells[j].text = cell_text
        for para in table2.rows[i].cells[j].paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if para.runs:
                para.runs[0].font.size = Pt(9)
                para.runs[0].font.name = 'SimSun'
                para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
                if i == 0:
                    para.runs[0].bold = True

doc.add_paragraph()

# 第三组
add_para(doc, '第三组：缴费记录证据', bold=True, size=14, space_before=16)

group3 = [
    ['编号', '证据名称', '证据来源', '证明目的', '页码', '形式'],
    ['A-11', '2019年5月至2022年2月缴费凭证', '被告提供', '证明被告历史缴费记录良好，前29个月按时缴费，不存在恶意欠费故意', '102-130', '书证']
]

table3 = doc.add_table(rows=len(group3), cols=6)
table3.style = 'Table Grid'
table3.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, row_data in enumerate(group3):
    for j, cell_text in enumerate(row_data):
        table3.rows[i].cells[j].text = cell_text
        for para in table3.rows[i].cells[j].paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if para.runs:
                para.runs[0].font.size = Pt(9)
                para.runs[0].font.name = 'SimSun'
                para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
                if i == 0:
                    para.runs[0].bold = True

doc.add_paragraph()

# 第四组
add_para(doc, '第四组：辅助证据', bold=True, size=14, space_before=16)

group4 = [
    ['编号', '证据名称', '证据来源', '证明目的', '页码', '形式'],
    ['A-12', '身份证复印件', '被告提供', '证明身份信息', '131', '书证'],
    ['A-13', '房产证/购房合同', '被告提供', '证明业主身份及质保期限', '132-135', '书证']
]

table4 = doc.add_table(rows=len(group4), cols=6)
table4.style = 'Table Grid'
table4.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, row_data in enumerate(group4):
    for j, cell_text in enumerate(row_data):
        table4.rows[i].cells[j].text = cell_text
        for para in table4.rows[i].cells[j].paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if para.runs:
                para.runs[0].font.size = Pt(9)
                para.runs[0].font.name = 'SimSun'
                para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
                if i == 0:
                    para.runs[0].bold = True

doc.add_paragraph()

# 证据说明
add_para(doc, '证据说明', bold=True, size=14, space_before=16)

evidence_notes = '''一、证据形式说明

1. 书证：包括钥匙委托凭证、整改记录照片、通话记录截图、缴费凭证、身份证复印件、房产证等纸质材料；
2. 电子数据：包括微信聊天记录截图、录音文字整理稿等；
3. 视听资料：包括漏水视频、录音等。

二、证据原件保管

1. 所有电子数据证据均已保留原始载体（手机），庭审时可供核对；
2. 所有录音证据已刻录光盘，保留原始录音设备；
3. 所有照片证据已打印，保留原始电子文件。

三、证据装订要求

1. 按证据编号顺序排列；
2. 每份证据单独一页（照片可多张一页）；
3. 编写页码；
4. 一式三份（法院一份、原告一份、被告留存一份）。'''

add_para(doc, evidence_notes, indent=0.74, space_before=8)

# 落款
doc.add_paragraph()
doc.add_paragraph()
add_para(doc, '答辩人：唐斐男（签字）', bold=True, space_before=24)
add_para(doc, '日期：2026年9月14日', bold=True)

# 保存
output_path = r'C:\Users\Administrator\.openclaw\workspace\memory\案件分析\证据目录_唐斐男_20260914.docx'
doc.save(output_path)
print(f'✅ 已生成：{output_path}')
