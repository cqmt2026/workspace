# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

def add_formatted_paragraph(doc, text, bold=False, size=12, alignment=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=6, first_line_indent=None):
    para = doc.add_paragraph()
    para.alignment = alignment
    para.paragraph_format.space_before = Pt(space_before)
    para.paragraph_format.space_after = Pt(space_after)
    if first_line_indent:
        para.paragraph_format.first_line_indent = Cm(first_line_indent)
    run = para.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = 'SimSun'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
    return para

def create_doc(title, content_sections):
    doc = Document()
    
    # 设置页面边距
    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(3.17)
        section.right_margin = Cm(3.17)
    
    # 标题
    add_formatted_paragraph(doc, title, bold=True, size=18, alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)
    
    # 内容
    for section in content_sections:
        if isinstance(section, tuple):
            text, *opts = section
            add_formatted_paragraph(doc, text, **{k: v for k, v in opts.items() if k in ['bold', 'size', 'alignment', 'space_before', 'space_after', 'first_line_indent']})
        else:
            add_formatted_paragraph(doc, section)
    
    return doc

# 1. 延期举证申请书
doc1 = create_doc('延期举证申请书', [
    ('申请人（被告）：唐斐男', {'bold': True, 'size': 12}),
    ('案号：（2026）渝0157民初82907号', {'bold': True, 'size': 12, 'space_after': 12}),
    ('申请事项', {'bold': True, 'size': 14, 'space_before': 12}),
    ('请求延长举证期限至2026年9月21日。', {'first_line_indent': 0.74}),
    ('事实与理由', {'bold': True, 'size': 14, 'space_before': 12}),
    ('申请人因以下原因，无法在现有举证期限内完成举证：', {'first_line_indent': 0.74}),
    ('一、需要整理现有证据', {'bold': True, 'size': 12, 'space_before': 8}),
    ('申请人需要时间整理漏水时间线、制作证据目录、装订证据材料。', {'first_line_indent': 0.74}),
    ('二、需要申请法院调取证据', {'bold': True, 'size': 12, 'space_before': 8}),
    ('申请人已准备《调查取证申请书》，需要时间提交并等待法院裁定。', {'first_line_indent': 0.74}),
    ('三、需要联系证人获取证言', {'bold': True, 'size': 12, 'space_before': 8}),
    ('申请人需要联系邻居、其他业主获取证言，证明漏水问题及物业服务质量问题。', {'first_line_indent': 0.74}),
    ('法律依据', {'bold': True, 'size': 14, 'space_before': 12}),
    ('根据《最高人民法院关于民事诉讼证据的若干规定》第三十六条：', {'first_line_indent': 0.74}),
    ('"当事人在举证期限内提交证据材料确有困难的，应当在举证期限内向人民法院申请延期举证，经人民法院准许，可以适当延长举证期限。"', {'first_line_indent': 0.74}),
    ('此致', {'space_before': 24}),
    ('重庆市两江新区人民法院', {'first_line_indent': 0.74}),
    ('', {}),
    ('申请人：唐斐男（签字）', {'bold': True, 'space_before': 24}),
    ('日期：2026年9月14日', {'bold': True}),
    ('', {}),
    ('附：联系方式', {'bold': True, 'space_before': 12}),
    ('- 地址：重庆市九龙坡区经纬大道1399号隆鑫花漾四季2幢4-6', {}),
    ('- 电话：15025355361', {})
])
doc1.save(r'C:\Users\Administrator\.openclaw\workspace\memory\案件分析\延期举证申请书_唐斐男_20260914.docx')
print('✅ 已生成：延期举证申请书.docx')

# 2. 调查取证申请书
doc2 = create_doc('调查取证申请书', [
    ('申请人（被告）：唐斐男', {'bold': True, 'size': 12}),
    ('案号：（2026）渝0157民初82907号', {'bold': True, 'size': 12, 'space_after': 12}),
    ('申请事项', {'bold': True, 'size': 14, 'space_before': 12}),
    ('请求法院向以下单位调取证据：', {'first_line_indent': 0.74}),
    ('一、向成都万科物业服务有限公司调取', {'bold': True, 'size': 12, 'space_before': 8}),
    ('1. 申请人房屋（重庆万科观承一期别墅9幢114）的报修记录', {'first_line_indent': 0.74}),
    ('2. 物业维修人员上门维修的记录', {'first_line_indent': 0.74}),
    ('3. 对申请人投诉的处理记录', {'first_line_indent': 0.74}),
    ('4. 物业服务质量检查记录', {'first_line_indent': 0.74}),
    ('5. 小区公共区域巡查记录', {'first_line_indent': 0.74}),
    ('6. 业主满意度测评记录', {'first_line_indent': 0.74}),
    ('7. 物业管理档案（含共用部位、共用设施设备档案）', {'first_line_indent': 0.74}),
    ('二、向重庆星畔置业有限公司调取', {'bold': True, 'size': 12, 'space_before': 8}),
    ('1. 申请人房屋的工程验收记录', {'first_line_indent': 0.74}),
    ('2. 申请人房屋的保修记录', {'first_line_indent': 0.74}),
    ('3. 防水工程的质保记录', {'first_line_indent': 0.74}),
    ('事实与理由', {'bold': True, 'size': 14, 'space_before': 12}),
    ('一、申请调取证据的必要性', {'bold': True, 'size': 12, 'space_before': 8}),
    ('本案中，漏水问题的维修记录、投诉处理记录等均由物业公司掌握，工程验收记录、保修记录等由开发商掌握。申请人作为自然人，无法自行收集上述证据。', {'first_line_indent': 0.74}),
    ('二、申请调取证据与案件事实的关系', {'bold': True, 'size': 12, 'space_before': 8}),
    ('上述证据对查明案件事实至关重要，具体证明目的如下：', {'first_line_indent': 0.74}),
    ('- 维修记录：证明物业是否履行维修义务', {'first_line_indent': 0.74}),
    ('- 投诉处理记录：证明物业是否及时处理投诉', {'first_line_indent': 0.74}),
    ('- 服务质量检查记录：证明物业服务质量是否达标', {'first_line_indent': 0.74}),
    ('- 工程验收记录：证明房屋质量是否符合标准', {'first_line_indent': 0.74}),
    ('- 保修记录：证明开发商是否履行保修义务', {'first_line_indent': 0.74}),
    ('三、申请人无法自行收集的原因', {'bold': True, 'size': 12, 'space_before': 8}),
    ('1. 申请人与物业公司不存在隶属关系，无法强制要求物业公司提供档案资料；', {'first_line_indent': 0.74}),
    ('2. 申请人与开发商不存在隶属关系，无法强制要求开发商提供工程记录；', {'first_line_indent': 0.74}),
    ('3. 上述证据属于物业公司、开发商的内部管理资料，申请人无法通过公开渠道获取。', {'first_line_indent': 0.74}),
    ('法律依据', {'bold': True, 'size': 14, 'space_before': 12}),
    ('1. 《中华人民共和国民事诉讼法》第六十七条：人民法院有权向有关单位调查取证。有关单位不得拒绝。', {'first_line_indent': 0.74}),
    ('2. 《最高人民法院关于民事诉讼证据的若干规定》第四十七条：确因客观原因不能自行收集的其他材料，可以申请人民法院调查收集。', {'first_line_indent': 0.74}),
    ('此致', {'space_before': 24}),
    ('重庆市两江新区人民法院', {'first_line_indent': 0.74}),
    ('', {}),
    ('申请人：唐斐男（签字）', {'bold': True, 'space_before': 24}),
    ('日期：2026年9月14日', {'bold': True}),
    ('', {}),
    ('附：联系方式', {'bold': True, 'space_before': 12}),
    ('- 地址：重庆市九龙坡区经纬大道1399号隆鑫花漾四季2幢4-6', {}),
    ('- 电话：15025355361')
])
doc2.save(r'C:\Users\Administrator\.openclaw\workspace\memory\案件分析\调查取证申请书_唐斐男_20260914.docx')
print('✅ 已生成：调查取证申请书.docx')

# 3. 司法鉴定申请书
doc3 = create_doc('司法鉴定申请书', [
    ('申请人（被告）：唐斐男', {'bold': True, 'size': 12}),
    ('案号：（2026）渝0157民初82907号', {'bold': True, 'size': 12, 'space_after': 12}),
    ('申请事项', {'bold': True, 'size': 14, 'space_before': 12}),
    ('请求法院委托具有资质的鉴定机构对以下事项进行鉴定：', {'first_line_indent': 0.74}),
    ('一、漏水原因鉴定', {'bold': True, 'size': 12, 'space_before': 8}),
    ('鉴定申请人房屋（重庆万科观承一期别墅9幢114）漏水原因，明确以下问题：', {'first_line_indent': 0.74}),
    ('1. 漏水系工程质量问题还是物业维修不当所致', {'first_line_indent': 0.74}),
    ('2. 漏水部位属于专有部分还是共用部位', {'first_line_indent': 0.74}),
    ('3. 漏水原因与开发商、物业、申请人之间的关系', {'first_line_indent': 0.74}),
    ('二、损失评估鉴定（如需要）', {'bold': True, 'size': 12, 'space_before': 8}),
    ('鉴定漏水造成的损失金额，包括：', {'first_line_indent': 0.74}),
    ('1. 房屋受损价值', {'first_line_indent': 0.74}),
    ('2. 物品损坏价值', {'first_line_indent': 0.74}),
    ('3. 租房费用损失（如有）', {'first_line_indent': 0.74}),
    ('4. 其他经济损失', {'first_line_indent': 0.74}),
    ('事实与理由', {'bold': True, 'size': 14, 'space_before': 12}),
    ('一、申请鉴定的必要性', {'bold': True, 'size': 12, 'space_before': 8}),
    ('本案中，漏水原因是核心争议焦点。漏水可能由以下原因导致：', {'first_line_indent': 0.74}),
    ('1. 开发商工程质量问题（如防水层施工不当）', {'first_line_indent': 0.74}),
    ('2. 物业维修不当（如维修技术不当）', {'first_line_indent': 0.74}),
    ('3. 申请人使用不当（如装修破坏防水层）', {'first_line_indent': 0.74}),
    ('4. 混合原因（多方共同导致）', {'first_line_indent': 0.74}),
    ('上述原因需要通过专业鉴定才能查明。如无法查明漏水原因，将根据举证责任分配原则，由主张减免的一方承担不利后果。', {'first_line_indent': 0.74}),
    ('二、申请鉴定的法律依据', {'bold': True, 'size': 12, 'space_before': 8}),
    ('根据《中华人民共和国民事诉讼法》第七十六条：当事人可以就查明事实的专门性问题向人民法院申请鉴定。当事人申请鉴定的，由双方当事人协商确定具备资格的鉴定人；协商不成的，由人民法院指定。', {'first_line_indent': 0.74}),
    ('根据《最高人民法院关于民事诉讼证据的若干规定》第三十一条：当事人申请鉴定，应当在人民法院指定期间内提出，并填交鉴定申请书。', {'first_line_indent': 0.74}),
    ('三、鉴定机构的选择', {'bold': True, 'size': 12, 'space_before': 8}),
    ('申请人请求法院委托具有资质的建筑工程质量鉴定机构进行鉴定。', {'first_line_indent': 0.74}),
    ('此致', {'space_before': 24}),
    ('重庆市两江新区人民法院', {'first_line_indent': 0.74}),
    ('', {}),
    ('申请人：唐斐男（签字）', {'bold': True, 'space_before': 24}),
    ('日期：2026年9月14日', {'bold': True}),
    ('', {}),
    ('附：联系方式', {'bold': True, 'space_before': 12}),
    ('- 地址：重庆市九龙坡区经纬大道1399号隆鑫花漾四季2幢4-6', {}),
    ('- 电话：15025355361')
])
doc3.save(r'C:\Users\Administrator\.openclaw\workspace\memory\案件分析\司法鉴定申请书_唐斐男_20260914.docx')
print('✅ 已生成：司法鉴定申请书.docx')

# 4. 异议申请书
doc4 = create_doc('对小额诉讼程序异议申请书', [
    ('申请人（被告）：唐斐男', {'bold': True, 'size': 12}),
    ('案号：（2026）渝0157民初82907号', {'bold': True, 'size': 12, 'space_after': 12}),
    ('异议事项', {'bold': True, 'size': 14, 'space_before': 12}),
    ('请求贵院裁定本案不适用小额诉讼程序，转为普通程序审理。', {'first_line_indent': 0.74}),
    ('事实和理由', {'bold': True, 'size': 14, 'space_before': 12}),
    ('申请人与被申请人物业服务合同纠纷一案，贵院已立案受理，案号为（2026）渝0157民初82907号。贵院向申请人送达了《适用小额诉讼案件通知书》，申请人对此提出异议，理由如下：', {'first_line_indent': 0.74}),
    ('一、本案存在重大事实争议，不属于"事实清楚、争议不大"的案件', {'bold': True, 'size': 12, 'space_before': 8}),
    ('1. 漏水问题需经实体审理查明', {'first_line_indent': 0.74}),
    ('申请人收房后即发现房屋存在严重漏水问题，该问题涉及：', {'first_line_indent': 0.74}),
    ('- 漏水原因鉴定：需确定是开发商工程质量问题还是物业维修不当所致', {'first_line_indent': 0.74}),
    ('- 整改责任主体认定：需查明整改责任应由开发商、物业还是双方共同承担', {'first_line_indent': 0.74}),
    ('- 整改期间认定：需查明漏水持续时间和整改历时', {'first_line_indent': 0.74}),
    ('- 物业是否尽到维修义务：需审查物业是否及时响应、有效维修', {'first_line_indent': 0.74}),
    ('上述事实需经法庭调查、举证质证，可能还需要司法鉴定才能查明，不属于"事实清楚"的简单案件。', {'first_line_indent': 0.74}),
    ('2. 服务质量争议需实体审理', {'first_line_indent': 0.74}),
    ('申请人对物业服务质量存在重大异议，包括但不限于：', {'first_line_indent': 0.74}),
    ('- 漏水问题长期未解决（历时2年以上）', {'first_line_indent': 0.74}),
    ('- 物业未尽保修协助义务', {'first_line_indent': 0.74}),
    ('- 物业未尽承接查验协议配合监督义务', {'first_line_indent': 0.74}),
    ('- 物业服务质量不达标', {'first_line_indent': 0.74}),
    ('上述争议需经完整庭审程序才能查明，不适合小额诉讼的快速程序。', {'first_line_indent': 0.74}),
    ('二、本案涉及违约金调整，需实体审理', {'bold': True, 'size': 12, 'space_before': 8}),
    ('被申请人主张的违约金计算方式存在争议：', {'first_line_indent': 0.74}),
    ('1. 申请人并非恶意拖欠，而是因物业未履行维修义务导致的合理抗辩', {'first_line_indent': 0.74}),
    ('2. 违约金标准可能过高，需法院酌情调整', {'first_line_indent': 0.74}),
    ('3. 该争议需实体审理，不适合小额诉讼', {'first_line_indent': 0.74}),
    ('三、本案符合转为普通程序的情形', {'bold': True, 'size': 12, 'space_before': 8}),
    ('根据《最高人民法院关于审理民事案件适用小额诉讼程序若干问题的规定》第六条，下列案件，不适用小额诉讼程序：', {'first_line_indent': 0.74}),
    ('- 人身关系、财产确权纠纷', {'first_line_indent': 0.74}),
    ('- 涉外民事纠纷', {'first_line_indent': 0.74}),
    ('- 知识产权纠纷', {'first_line_indent': 0.74}),
    ('- 评估、鉴定或者对诉前评估、鉴定结果有异议的纠纷', {'first_line_indent': 0.74}),
    ('- 其他不宜适用一审终审的纠纷', {'first_line_indent': 0.74}),
    ('本案虽不属于上述明确列举情形，但存在重大事实争议，需通过完整庭审程序查明事实，符合"其他不宜适用一审终审的纠纷"之情形。', {'first_line_indent': 0.74}),
    ('四、程序保障需要', {'bold': True, 'size': 12, 'space_before': 8}),
    ('申请人作为自然人，缺乏法律专业知识，小额诉讼程序简化的庭审流程可能影响申请人充分行使诉讼权利。转为普通程序可保障申请人的：', {'first_line_indent': 0.74}),
    ('- 充分的举证质证权利', {'first_line_indent': 0.74}),
    ('- 完整的法庭辩论权利', {'first_line_indent': 0.74}),
    ('- 如判决不利，可依法上诉的权利', {'first_line_indent': 0.74}),
    ('补充说明', {'bold': True, 'size': 12, 'space_before': 8}),
    ('申请人深知《适用小额诉讼案件通知书》规定的异议期为5日，本申请已逾期提交。但申请人并非故意延误，而是因对法律程序理解不足所致。考虑到本案确实存在上述复杂情形，恳请贵院综合考虑，裁定本案转为普通程序审理。', {'first_line_indent': 0.74}),
    ('法律依据', {'bold': True, 'size': 14, 'space_before': 12}),
    ('1. 《中华人民共和国民事诉讼法》第一百六十五条', {'first_line_indent': 0.74}),
    ('2. 《最高人民法院关于适用〈中华人民共和国民事诉讼法〉的解释》第二百七十八条', {'first_line_indent': 0.74}),
    ('3. 《最高人民法院关于审理民事案件适用小额诉讼程序若干问题的规定》第六条', {'first_line_indent': 0.74}),
    ('此致', {'space_before': 24}),
    ('重庆市两江新区人民法院', {'first_line_indent': 0.74}),
    ('', {}),
    ('申请人：唐斐男（签字）', {'bold': True, 'space_before': 24}),
    ('日期：2026年9月13日', {'bold': True}),
    ('', {}),
    ('附：提交说明', {'bold': True, 'space_before': 12}),
    ('提交材料：', {'first_line_indent': 0.74}),
    ('1. 本申请书原件1份', {'first_line_indent': 0.74}),
    ('2. 申请人身份证复印件1份', {'first_line_indent': 0.74}),
    ('3. 《适用小额诉讼案件通知书》复印件1份', {'first_line_indent': 0.74}),
    ('提交方式：', {'first_line_indent': 0.74}),
    ('- 现场提交：重庆市两江新区人民法院空港审判区调解室（一）【空港大道418号】', {'first_line_indent': 0.74}),
    ('- 邮寄提交：寄至上述地址，使用EMS或挂号信，保留邮寄凭证', {'first_line_indent': 0.74}),
    ('联系人：审判员曹阳 联系电话：023-67820501', {'first_line_indent': 0.74})
])
doc4.save(r'C:\Users\Administrator\.openclaw\workspace\memory\案件分析\异议申请书_唐斐男_20260913.docx')
print('✅ 已生成：异议申请书.docx')

print('\n✅ 所有Word文档已生成完毕！')
