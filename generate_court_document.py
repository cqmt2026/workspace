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
add_para(doc, '庭审质证意见稿', bold=True, size=18, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)

# 案件信息
add_para(doc, '案号：（2026）渝0157民初82907号', bold=True, size=12, space_after=6)
add_para(doc, '被告：唐斐男', bold=True, size=12, space_after=6)
add_para(doc, '原告：成都万科物业服务有限公司', bold=True, size=12, space_after=12)

# 开场陈述
add_para(doc, '一、开场陈述', bold=True, size=14, space_before=16)

opening = '''尊敬的审判员：

我是被告唐斐男。本案的核心争议是：物业服务质量是否达标，被告是否应当减免物业费。

我的答辩请求是：
1. 确认被告在2019年5月至2022年2月期间已按时缴纳物业费；
2. 减免2022年2月至2026年6月期间物业费30%；
3. 免除全部违约金；
4. 本案诉讼费用由原告承担。

我的证据将证明：漏水问题自2019年交房时即存在，物业未尽协助、配合、监督义务，服务质量不达标。'''

add_para(doc, opening, indent=0.74)

doc.add_paragraph()

# 质证意见
add_para(doc, '二、对原告证据的质证意见', bold=True, size=14, space_before=16)

cross_examination = '''原告提交了以下证据：
1. 前期物业服务合同（27页）
2. 催缴记录（微信截图）
3. 通话记录截图

对上述证据的质证意见如下：

证据1（前期物业服务合同）：
- 对真实性无异议；
- 对证明目的有异议。合同仅证明双方存在物业服务关系，不能证明原告已按约提供服务。

证据2（催缴记录）：
- 对真实性无异议；
- 对证明目的有异议。催缴记录只能证明原告进行了催收，不能证明原告已按约提供服务。

证据3（通话记录）：
- 对真实性无异议；
- 对证明目的有异议。通话记录只能证明双方有过沟通，不能证明原告已按约提供服务。

重点：原告未提供任何证明其已按约提供服务的证据，包括但不限于维修记录、投诉处理记录、巡查记录、满意度测评记录等。

根据《民法典》第九百四十四条，物业服务人已经按照约定提供服务的，业主才应当支付物业费。原告未能举证证明已按约提供服务，应承担举证不能的不利后果。'''

add_para(doc, cross_examination, indent=0.74)

doc.add_paragraph()

# 被告举证
add_para(doc, '三、被告举证陈述', bold=True, size=14, space_before=16)

defendant_evidence = '''审判员，我现在举证。

第一组证据：漏水事实证据
证据A-1至A-5，证明漏水问题自2019年交房时即存在，且持续时间长、问题严重。

第二组证据：沟通记录证据
证据A-6至A-10，证明业主积极投诉，物业不作为；漏水问题具有普遍性。

第三组证据：缴费记录证据
证据A-11，证明被告历史缴费记录良好，前29个月按时缴费，不存在恶意欠费故意。

第四组证据：辅助证据
证据A-12至A-13，证明被告身份及房屋质保期限。

以上证据，请审判员审阅。'''

add_para(doc, defendant_evidence, indent=0.74)

doc.add_paragraph()

# 法庭提问应对
add_para(doc, '四、法庭提问应对要点', bold=True, size=14, space_before=16)

# 创建问答表格
qa_data = [
    ['提问', '回答要点'],
    ['漏水是什么时候开始的？', '2019年5月2日收房时即发现。这是首次发现漏水的照片（展示证据A-1），拍摄时间是2019年5月2日。'],
    ['漏水有多严重？', '非常严重。天花板、墙面大量漏水，家具、地板受损。这是受损物品的照片（展示证据A-5），这是漏水过程的视频（展示证据A-5）。'],
    ['你向物业报修过吗？', '报过，而且报修了很多次。这是首次报修的记录（展示证据A-1），这是微信报修的聊天记录（展示证据A-2），共多次记录。'],
    ['物业整改了吗？', '物业承诺整改，但整改不力。这是物业的整改承诺记录（展示证据A-2），但整改后仍然漏水（展示证据A-4）。整改历时16个月以上，物业多次敷衍塞责。'],
    ['漏水问题解决了吗？', '基本解决，但期间我无法正常居住。这是问题解决后的照片（展示证据A-4），但之前的损失已经造成。'],
    ['你有证据证明漏水吗？', '有，这是我的证据清单（展示证据目录）。第一组是漏水事实证据，第二组是报修记录证据，第三组是整改过程证据……'],
    ['你认为物业服务哪里不达标？', '主要体现在三个方面：1.漏水问题长期未解决（历时2年以上）；2.物业未尽保修协助义务；3.物业未尽承接查验协议配合监督义务。'],
    ['你有证据证明服务质量不达标吗？', '有，这是整改记录照片（展示证据A-2至A-4），这是业主投诉记录（展示证据A-6至A-9）。'],
    ['你为什么不在漏水期间交费？', '我不是不交费，而是希望漏水问题解决后再交费。这是我的抗辩权，不是恶意欠费。漏水问题解决后，我一直在积极与物业沟通缴费事宜。'],
    ['你为什么不同意支付违约金？', '主要有两个理由：1.我不是恶意欠费，是因为物业服务质量不达标，我正当行使抗辩权；2.违约金过高，按LPR的2倍计算远超物业公司的实际损失。'],
    ['你认为违约金应该多少？', '我主张免除全部违约金。因为：1.我不是恶意欠费；2.物业公司的实际损失主要是资金占用利息，按LPR的1倍已足以弥补；3.合同约定每日万分之五，年化18.25%，明显过高。'],
    ['你为什么对小额诉讼程序提出异议？', '因为本案涉及漏水原因鉴定、整改责任主体认定等复杂事实，不适合小额诉讼的快速程序。'],
]

table = doc.add_table(rows=len(qa_data), cols=2)
table.style = 'Table Grid'
table.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, row_data in enumerate(qa_data):
    for j, cell_text in enumerate(row_data):
        table.rows[i].cells[j].text = cell_text
        for para in table.rows[i].cells[j].paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if para.runs:
                para.runs[0].font.size = Pt(10)
                para.runs[0].font.name = 'SimSun'
                para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
                if i == 0:
                    para.runs[0].bold = True

doc.add_paragraph()

# 辩论意见
add_para(doc, '五、辩论意见', bold=True, size=14, space_before=16)

debate = '''审判员，我现在发表辩论意见。

第一，物业未履行协助义务，构成违约。
根据《重庆市新建商品房质量保证书》约定，开发商将保修服务委托给物业。物业成为保修服务的实际履行主体，负有接收报修、转达开发商、跟进处理、反馈结果的四重义务。但本案中，物业未在合理期限内促成整改，导致漏水问题历时16个月未解决。

第二，物业未履行配合监督义务，构成违约。
根据《前期物业服务合同》附件七《物业承接查验协议》约定，物业有配合整改、监督进度、复验结果的义务。但本案中，物业未有效配合开发商整改，未有效监督整改进度，未有效复验整改结果。

第三，物业未履行维修养护义务，构成违约。
根据《前期物业服务合同》第二条及附件四第7条约定，物业有维修养护义务，应实行24小时报修值班制度，急修20分钟内到场。但本案中，漏水问题历时多年未解决，物业无法提供维修记录。

第四，原告未举证证明其已按约提供服务。
根据《民法典》第九百四十四条，物业服务人已经按照约定提供服务的，业主才应当支付物业费。原告仅提交了合同文本和催缴记录，未提供任何服务达标的证据。根据《证据规定》第九十五条，原告应承担举证不能的不利后果。

第五，被告非恶意欠费，违约金应予以免除。
被告在2019年5月至2022年2月期间（共29个月）已按时缴纳物业费，从未拖欠。2022年2月后暂停缴费，是因为漏水问题长期未解决，被告正当行使抗辩权。根据《民法典》第五百八十五条，违约金应予以免除。

综上，请求法院支持被告的全部答辩请求。'''

add_para(doc, debate, indent=0.74)

doc.add_paragraph()

# 最后陈述
add_para(doc, '六、最后陈述', bold=True, size=14, space_before=16)

closing = '''尊敬的审判员，

我承认欠费事实，但欠费原因是物业服务质量不达标。我并非恶意欠费，而是正当行使抗辩权。

我请求法院公平裁判，减免整改期间的物业费，免除违约金。

如果法庭同意调解，我愿意在公平合理的基础上达成调解。

谢谢。'''

add_para(doc, closing, indent=0.74)

doc.add_paragraph()

# 调解方案
add_para(doc, '七、调解方案', bold=True, size=14, space_before=16)

mediation = '''最佳方案：减免30%物业费+免除违约金（约15,032元）
底线方案：减免20%物业费+免除违约金（约17,180元）
让步方案：减免15%物业费+违约金降至LPR的1倍（约18,254元）'''

add_para(doc, mediation, indent=0.74)

doc.add_paragraph()

# 注意事项
add_para(doc, '八、庭审注意事项', bold=True, size=14, space_before=16)

notes = '''1. 着装整洁、正式；
2. 称呼"审判员"、"法庭"；
3. 态度恭敬、诚恳；
4. 发言经许可后发言；
5. 认真记录法庭讲话；
6. 保持冷静，不激动；
7. 回答前停顿2-3秒，思考后再回答；
8. 回答要完整：结论+理由+证据；
9. 不懂就问，坦诚说明；
10. 不要争吵，保持尊重。'''

add_para(doc, notes, indent=0.74)

# 保存
output_path = r'C:\Users\Administrator\.openclaw\workspace\memory\案件分析\庭审质证意见稿_唐斐男_20260914.docx'
doc.save(output_path)
print(f'✅ 已生成：{output_path}')
