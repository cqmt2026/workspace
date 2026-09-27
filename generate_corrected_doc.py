# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
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

# 生成修正后的异议申请书
doc = Document()
sections = doc.sections
for s in sections:
    s.top_margin = Cm(2.54)
    s.bottom_margin = Cm(2.54)
    s.left_margin = Cm(3.17)
    s.right_margin = Cm(3.17)

add_para(doc, '对小额诉讼程序异议申请书', bold=True, size=18, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)
add_para(doc, '申请人（被告）：唐斐男', bold=True, size=12)
add_para(doc, '案号：（2026）渝0157民初82907号', bold=True, size=12, space_after=12)

add_para(doc, '异议事项', bold=True, size=14, space_before=12)
add_para(doc, '请求贵院裁定本案不适用小额诉讼程序，转为普通程序审理。', indent=0.74)

add_para(doc, '事实和理由', bold=True, size=14, space_before=12)
add_para(doc, '申请人与被申请人物业服务合同纠纷一案，贵院已立案受理，案号为（2026）渝0157民初82907号。贵院向申请人送达了《适用小额诉讼案件通知书》，申请人对此提出异议，理由如下：', indent=0.74)

add_para(doc, '一、本案存在重大事实争议，不属于"事实清楚、争议不大"的案件', bold=True, size=12, space_before=8)

add_para(doc, '1. 漏水问题涉及多方责任认定，需经实体审理查明', bold=True, size=11, space_before=6)
add_para(doc, '申请人收房后即发现房屋存在严重漏水问题，该问题涉及：', indent=0.74)
add_para(doc, '- 开发商责任认定：需查明漏水是否系工程质量问题所致，开发商是否履行保修义务', indent=0.74)
add_para(doc, '- 物业协助义务认定：需查明物业是否尽到接收报修、转达开发商、跟进进度、反馈结果的协助义务', indent=0.74)
add_para(doc, '- 物业配合监督义务认定：需查明物业是否尽到配合整改、监督进度、复验结果的义务', indent=0.74)
add_para(doc, '- 责任比例划分：需查明开发商、物业各自应承担的责任比例', indent=0.74)
add_para(doc, '上述事实需经法庭调查、举证质证，可能还需要司法鉴定才能查明，不属于"事实清楚"的简单案件。', indent=0.74)

add_para(doc, '2. 物业服务质量争议需实体审理', bold=True, size=11, space_before=6)
add_para(doc, '申请人对物业服务质量存在重大异议，包括但不限于：', indent=0.74)
add_para(doc, '- 漏水问题长期未解决（历时2年以上），物业未尽协助、配合、监督义务', indent=0.74)
add_para(doc, '- 物业未尽质量保证书委托义务', indent=0.74)
add_para(doc, '- 物业未尽承接查验协议配合监督义务', indent=0.74)
add_para(doc, '- 物业服务质量不达标，原告未提供任何服务质量达标证据', indent=0.74)
add_para(doc, '上述争议需经完整庭审程序才能查明，不适合小额诉讼的快速程序。', indent=0.74)

add_para(doc, '二、本案涉及违约金调整，需实体审理', bold=True, size=12, space_before=8)
add_para(doc, '被申请人主张的违约金计算方式存在争议：', indent=0.74)
add_para(doc, '1. 申请人并非恶意拖欠，而是因物业未履行协助、配合、监督义务导致的合理抗辩', indent=0.74)
add_para(doc, '2. 违约金标准可能过高，需法院酌情调整', indent=0.74)
add_para(doc, '3. 该争议需实体审理，不适合小额诉讼', indent=0.74)

add_para(doc, '三、本案符合转为普通程序的情形', bold=True, size=12, space_before=8)
add_para(doc, '根据《最高人民法院关于审理民事案件适用小额诉讼程序若干问题的规定》第六条，下列案件，不适用小额诉讼程序：', indent=0.74)
add_para(doc, '- 人身关系、财产确权纠纷', indent=0.74)
add_para(doc, '- 涉外民事纠纷', indent=0.74)
add_para(doc, '- 知识产权纠纷', indent=0.74)
add_para(doc, '- 评估、鉴定或者对诉前评估、鉴定结果有异议的纠纷', indent=0.74)
add_para(doc, '- 其他不宜适用一审终审的纠纷', indent=0.74)
add_para(doc, '本案虽不属于上述明确列举情形，但存在重大事实争议，需通过完整庭审程序查明事实，符合"其他不宜适用一审终审的纠纷"之情形。', indent=0.74)

add_para(doc, '四、程序保障需要', bold=True, size=12, space_before=8)
add_para(doc, '申请人作为自然人，缺乏法律专业知识，小额诉讼程序简化的庭审流程可能影响申请人充分行使诉讼权利。转为普通程序可保障申请人的：', indent=0.74)
add_para(doc, '- 充分的举证质证权利', indent=0.74)
add_para(doc, '- 完整的法庭辩论权利', indent=0.74)
add_para(doc, '- 如判决不利，可依法上诉的权利', indent=0.74)

add_para(doc, '补充说明', bold=True, size=12, space_before=8)
add_para(doc, '申请人深知《适用小额诉讼案件通知书》规定的异议期为5日，本申请已逾期提交。但申请人并非故意延误，而是因对法律程序理解不足所致。考虑到本案确实存在上述复杂情形，恳请贵院综合考虑，裁定本案转为普通程序审理。', indent=0.74)

add_para(doc, '法律依据', bold=True, size=14, space_before=12)
add_para(doc, '1. 《中华人民共和国民事诉讼法》第一百六十五条', indent=0.74)
add_para(doc, '2. 《最高人民法院关于适用〈中华人民共和国民事诉讼法〉的解释》第二百七十八条', indent=0.74)
add_para(doc, '3. 《最高人民法院关于审理民事案件适用小额诉讼程序若干问题的规定》第六条', indent=0.74)

add_para(doc, '此致', space_before=24)
add_para(doc, '重庆市两江新区人民法院', indent=0.74)
add_para(doc, '')
add_para(doc, '申请人：唐斐男（签字）', bold=True, space_before=24)
add_para(doc, '日期：2026年9月13日', bold=True)
add_para(doc, '')
add_para(doc, '附：提交说明', bold=True, space_before=12)
add_para(doc, '提交材料：', indent=0.74)
add_para(doc, '1. 本申请书原件1份', indent=0.74)
add_para(doc, '2. 申请人身份证复印件1份', indent=0.74)
add_para(doc, '3. 《适用小额诉讼案件通知书》复印件1份', indent=0.74)
add_para(doc, '提交方式：', indent=0.74)
add_para(doc, '- 现场提交：重庆市两江新区人民法院空港审判区调解室（一）【空港大道418号】', indent=0.74)
add_para(doc, '- 邮寄提交：寄至上述地址，使用EMS或挂号信，保留邮寄凭证', indent=0.74)
add_para(doc, '联系人：审判员曹阳 联系电话：023-67820501', indent=0.74)

output_path = r'C:\Users\Administrator\.openclaw\workspace\memory\案件分析\异议申请书_唐斐男_修正版_20260913.docx'
doc.save(output_path)
print(f'✅ 已生成：{output_path}')
