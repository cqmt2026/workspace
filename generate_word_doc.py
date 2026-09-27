# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

def add_run_with_format(run, text, bold=False, size=12, font_name='SimSun'):
    """添加格式化文本"""
    run.text = text
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)

def add_paragraph_with_format(doc, text, bold=False, size=12, alignment=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=6, first_line_indent=None):
    """添加格式化段落"""
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

# 创建文档
doc = Document()

# 设置页面边距
sections = doc.sections
for section in sections:
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)

# 标题
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_run_with_format(title.runs[0] if title.runs else title.add_run(), '民事答辩状', bold=True, size=18)
title.paragraph_format.space_after = Pt(12)

# 案号
add_paragraph_with_format(doc, '案号：（2026）渝0157民初82907号', bold=True, size=12, space_after=12)

# 答辩人信息
add_paragraph_with_format(doc, '答辩人（被告）信息', bold=True, size=12, space_before=12)

defining_cells = [
    ('姓名', '唐斐男'),
    ('性别', '男'),
    ('出生日期', '1982年6月5日'),
    ('民族', '汉族'),
    ('身份证号', '51020219820605622X'),
    ('联系电话', '15025355361'),
    ('住址', '重庆市九龙坡区经纬大道1399号隆鑫花漾四季2幢4-6')
]
table = doc.add_table(rows=len(defining_cells), cols=2)
table.style = 'Table Grid'
for i, (label, value) in enumerate(defining_cells):
    table.rows[i].cells[0].text = label
    table.rows[i].cells[1].text = value
    for cell in table.rows[i].cells:
        for para in cell.paragraphs:
            if para.runs:
                para.runs[0].font.size = Pt(11)
                para.runs[0].font.name = 'SimSun'
                para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

doc.add_paragraph()

# 原告信息
add_paragraph_with_format(doc, '被答辩人（原告）信息', bold=True, size=12, space_before=12)

plaintiff_info = [
    ('名称', '成都万科物业服务有限公司'),
    ('住所地', '四川省成都市锦江区静安路1号3栋附36号'),
    ('法定代表人', '赵振东'),
    ('联系电话', '88910555'),
    ('统一社会信用代码', '91510104723445820B')
]
table2 = doc.add_table(rows=len(plaintiff_info), cols=2)
table2.style = 'Table Grid'
for i, (label, value) in enumerate(plaintiff_info):
    table2.rows[i].cells[0].text = label
    table2.rows[i].cells[1].text = value
    for cell in table2.rows[i].cells:
        for para in cell.paragraphs:
            if para.runs:
                para.runs[0].font.size = Pt(11)
                para.runs[0].font.name = 'SimSun'
                para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

doc.add_paragraph()

# 答辩请求
add_paragraph_with_format(doc, '答辩请求', bold=True, size=14, space_before=16)

requests = [
    '1. 确认被告在2019年5月至2022年2月期间已按时缴纳物业费，原告主张的53个月欠费期间与事实不符，实际欠费期间为2022年2月至2026年6月，共34个月；',
    '2. 减免2022年2月至2026年6月期间物业费30%（即减免6,442.49元，实际支付15,032.47元）；',
    '3. 免除全部违约金；',
    '4. 本案诉讼费用由原告承担。'
]
for req in requests:
    add_paragraph_with_format(doc, req, size=12, first_line_indent=0.74)

doc.add_paragraph()

# 事实与理由
add_paragraph_with_format(doc, '事实与理由', bold=True, size=14, space_before=16)

intro = '本案争议焦点在于：被告未缴纳物业费是否有正当理由。被告认为，未缴纳物业费并非恶意拖欠，而是基于以下两大正当理由：'
add_paragraph_with_format(doc, intro, size=12, first_line_indent=0.74)

reasons = [
    '第一，原告在房屋质量漏水整改过程中未尽到相关义务；',
    '第二，原告提供的物业服务未达到合同约定的服务标准。'
]
for reason in reasons:
    add_paragraph_with_format(doc, reason, size=12, first_line_indent=0.74)

doc.add_paragraph()

# 第一部分
add_paragraph_with_format(doc, '第一部分：原告在漏水整改过程中未尽相关义务', bold=True, size=13, space_before=12)

add_paragraph_with_format(doc, '一、漏水问题的基本情况', bold=True, size=12, space_before=10)

add_paragraph_with_format(doc, '（一）漏水问题自交房时即存在', bold=True, size=11, space_before=8)

text1 = '''被告于2019年5月2日收房，同日将房屋钥匙委托物业代管，委托原因明确注明为"整改"，并有书面凭证为证（证据A-1）。

该事实表明：
1. 漏水问题在交房时即已存在；
2. 被告已履行报修义务；
3. 原告作为开发商委托的保修服务履行主体，明知房屋存在质量问题。'''

add_paragraph_with_format(doc, text1, size=12, first_line_indent=0.74)

add_paragraph_with_format(doc, '（二）漏水问题的具体内容', bold=True, size=11, space_before=8)

text2 = '2019年6月22日，被告通过微信向物业反馈具体问题，并发送了现场照片（证据A-2）。反馈的具体问题包括：'
add_paragraph_with_format(doc, text2, size=12, first_line_indent=0.74)

# 问题表格
problems = [
    ['序号', '问题描述', '问题性质'],
    ['1', '二楼阳台有积水潭', '防水问题'],
    ['2', '三楼楼梯口墙角处渗水、墙体地面潮湿', '防水/结构问题'],
    ['3', '二楼儿童房门口顶部渗水', '防水问题'],
    ['4', '窗户油漆脱落', '质量问题'],
    ['5', '二楼主卧滑门处顶部渗水', '防水问题'],
    ['6', '其他问题', '-']
]
table3 = doc.add_table(rows=len(problems), cols=3)
table3.style = 'Table Grid'
for i, row_data in enumerate(problems):
    for j, cell_text in enumerate(row_data):
        table3.rows[i].cells[j].text = cell_text
        for para in table3.rows[i].cells[j].paragraphs:
            if para.runs:
                para.runs[0].font.size = Pt(10)
                para.runs[0].font.name = 'SimSun'
                para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

text3 = '上述问题均属于屋面防水、外墙防渗漏范畴。根据《建设工程质量管理条例》第四十条，质保期为5年，至2024年5月2日届满。'
add_paragraph_with_format(doc, text3, size=12, first_line_indent=0.74)

# 时间线表格
add_paragraph_with_format(doc, '（三）漏水问题持续时间长', bold=True, size=11, space_before=8)

timeline = [
    ['时间节点', '事项', '证据'],
    ['2019年5月2日', '首次报修（钥匙委托）', '证据A-1'],
    ['2019年6月22日', '详细反馈6项问题', '证据A-2'],
    ['2019年7月27日', '邻居反映"整改无下文"', '证据A-9'],
    ['2020年9月', '发现"大面积返工"', '证据A-4'],
    ['2021年3月5日', '录音投诉', '证据A-6'],
    ['2022年2月', '停止缴费（因问题未解决）', '-']
]
table4 = doc.add_table(rows=len(timeline), cols=3)
table4.style = 'Table Grid'
for i, row_data in enumerate(timeline):
    for j, cell_text in enumerate(row_data):
        table4.rows[i].cells[j].text = cell_text
        for para in table4.rows[i].cells[j].paragraphs:
            if para.runs:
                para.runs[0].font.size = Pt(10)
                para.runs[0].font.name = 'SimSun'
                para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

text4 = '关键结论：从2019年5月至2020年9月，长达16个月，漏水问题未得到有效解决。'
add_paragraph_with_format(doc, text4, size=12, first_line_indent=0.74)

# 二、原告未尽质量保证书委托义务
add_paragraph_with_format(doc, '二、原告未尽质量保证书委托义务', bold=True, size=12, space_before=10)

text5 = '根据《重庆市新建商品房质量保证书》明确约定：'
add_paragraph_with_format(doc, text5, size=12, first_line_indent=0.74)

quotes = [
    '"业主使用后，有关房屋质量的来信来访、投诉，本公司将直接或委托物业管理公司及时给予书面答复和妥善处理。"',
    '"用户发现质量问题时向本公司或委托的物业管理公司进行报修。"',
    '"在接到用户《重庆市新建商品房屋质量保修联系单》后，由本公司或委托的物业管理公司...完成保修工作。"'
]
for quote in quotes:
    p = doc.add_paragraph(quote)
    p.paragraph_format.left_indent = Cm(1.0)
    for run in p.runs:
        run.font.size = Pt(11)
        run.font.name = 'SimSun'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

text6 = '法律解读：开发商明确将保修服务委托给物业；物业成为保修服务的实际履行主体；业主向物业报修=向开发商报修；物业有义务接收报修、转达开发商、跟进处理、反馈结果。'
add_paragraph_with_format(doc, text6, size=12, first_line_indent=0.74)

# 违约事实表格
breach = [
    ['违约行为', '具体表现', '证据'],
    ['未有效转达报修', '2019年5月2日报修，至7月27日仍"无下文"', '证据A-9（邻居聊天记录）'],
    ['未跟进整改进度', '2019年6月22日详细反馈，至2020年9月仍未解决', '证据A-2、A-4'],
    ['未反馈处理结果', '业主多次询问，物业未给予明确答复', '证据A-6、A-7、A-8'],
    ['未监督整改效果', '2020年9月发现"大面积返工"，整改无效', '证据A-4']
]
table5 = doc.add_table(rows=len(breach), cols=3)
table5.style = 'Table Grid'
for i, row_data in enumerate(breach):
    for j, cell_text in enumerate(row_data):
        table5.rows[i].cells[j].text = cell_text
        for para in table5.rows[i].cells[j].paragraphs:
            if para.runs:
                para.runs[0].font.size = Pt(10)
                para.runs[0].font.name = 'SimSun'
                para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

text7 = '法律后果：物业未尽委托义务，构成违约，应减免物业费。'
add_paragraph_with_format(doc, text7, size=12, first_line_indent=0.74)

# 三、原告未尽承接查验协议配合监督义务
add_paragraph_with_format(doc, '三、原告未尽承接查验协议配合监督义务', bold=True, size=12, space_before=10)

text8 = '根据《前期物业服务合同》附件七《物业承接查验协议》约定：'
add_paragraph_with_format(doc, text8, size=12, first_line_indent=0.74)

agreement_quotes = [
    '"甲方有权要求乙方配合工程遗留问题的整改工作，为整改工作提供水、电、现场秩序等方面的便利。"',
    '"乙方有权监督甲方对工程遗留问题的整改进度，并依据国家强制性规范、标准和商品房买卖合同对整改结果进行复验。"'
]
for quote in agreement_quotes:
    p = doc.add_paragraph(quote)
    p.paragraph_format.left_indent = Cm(1.0)
    for run in p.runs:
        run.font.size = Pt(11)
        run.font.name = 'SimSun'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

breach_table = [
    ['合同义务', '实际情况', '违约程度'],
    ['配合整改工作', '未有效配合开发商整改', '❌ 违约'],
    ['监督整改进度', '16个月无实质进展，物业未有效监督', '❌ 严重违约'],
    ['复验整改结果', '2020年9月发现"大面积返工"，复验流于形式', '❌ 违约']
]
table6 = doc.add_table(rows=len(breach_table), cols=3)
table6.style = 'Table Grid'
for i, row_data in enumerate(breach_table):
    for j, cell_text in enumerate(row_data):
        table6.rows[i].cells[j].text = cell_text
        for para in table6.rows[i].cells[j].paragraphs:
            if para.runs:
                para.runs[0].font.size = Pt(10)
                para.runs[0].font.name = 'SimSun'
                para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

# 四、原告未尽维修养护义务
add_paragraph_with_format(doc, '四、原告未尽维修养护义务', bold=True, size=12, space_before=10)

text9 = '根据《前期物业服务合同》第二条及附件四第7条约定，物业有维修养护义务，应实行24小时报修值班制度，急修20分钟内到场。'
add_paragraph_with_format(doc, text9, size=12, first_line_indent=0.74)

maintenance_breach = [
    ['合同要求', '实际情况', '违约程度'],
    ['24小时报修值班', '漏水问题多年未解决', '❌ 违约'],
    ['急修20分钟内到场', '漏水问题历时多年未解决', '❌ 严重违约'],
    ['回访率100%', '无回访记录', '❌ 违约'],
    ['建立维修档案', '无法提供维修记录', '❌ 违约']
]
table7 = doc.add_table(rows=len(maintenance_breach), cols=3)
table7.style = 'Table Grid'
for i, row_data in enumerate(maintenance_breach):
    for j, cell_text in enumerate(row_data):
        table7.rows[i].cells[j].text = cell_text
        for para in table7.rows[i].cells[j].paragraphs:
            if para.runs:
                para.runs[0].font.size = Pt(10)
                para.runs[0].font.name = 'SimSun'
                para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

doc.add_paragraph()

# 第二部分
add_paragraph_with_format(doc, '第二部分：原告提供的物业服务未达到合同约定的服务标准', bold=True, size=13, space_before=12)

add_paragraph_with_format(doc, '一、原告未提供任何服务质量达标证据', bold=True, size=12, space_before=10)

text10 = '原告仅提交了以下证据：'
add_paragraph_with_format(doc, text10, size=12, first_line_indent=0.74)

evidence_list = ['前期物业服务合同（27页）', '催缴记录（微信截图）', '通话记录截图']
for item in evidence_list:
    p = doc.add_paragraph(f'- {item}')
    p.paragraph_format.left_indent = Cm(1.0)
    for run in p.runs:
        run.font.size = Pt(12)
        run.font.name = 'SimSun'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

text11 = '原告缺失的证据：'
add_paragraph_with_format(doc, text11, size=12, first_line_indent=0.74)

missing_list = [
    '维修记录档案（⭐⭐⭐⭐⭐）',
    '投诉处理记录（⭐⭐⭐⭐⭐）',
    '报修值班记录（⭐⭐⭐⭐）',
    '巡查记录（⭐⭐⭐）',
    '满意度测评记录（⭐⭐⭐）',
    '公示记录（⭐⭐⭐）'
]
for item in missing_list:
    p = doc.add_paragraph(f'- {item}')
    p.paragraph_format.left_indent = Cm(1.0)
    for run in p.runs:
        run.font.size = Pt(12)
        run.font.name = 'SimSun'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

text12 = '法律后果：根据《最高人民法院关于民事诉讼证据的若干规定》第九十五条，原告作为物业服务人，掌握服务质量的全部证据。如原告无法提供上述证据，应承担举证不能的不利后果，法院应推定原告服务不达标。'
add_paragraph_with_format(doc, text12, size=12, first_line_indent=0.74)

doc.add_paragraph()

# 第三部分
add_paragraph_with_format(doc, '第三部分：被告历史缴费记录良好，不存在恶意欠费', bold=True, size=13, space_before=12)

payment_history = '''一、缴费时间线

| 期间 | 缴费状态 | 说明 |
|------|----------|------|
| 2019年5月-2022年2月 | ✅ 已按时缴纳（29个月） | 证明无恶意欠费故意 |
| 2022年2月-2026年6月 | ❌ 未缴纳（34个月） | 因漏水问题持续未解决 |

二、法律意义

1. 证明被告信用良好，前29个月按时缴费，从未拖欠；
2. 证明非恶意欠费：暂停缴费是因为物业服务质量问题，而非恶意逃避；
3. 强化违约金抗辩：被告历史表现良好，违约金应予以免除。'''

add_paragraph_with_format(doc, payment_history, size=12, first_line_indent=0.74)

doc.add_paragraph()

# 第四部分
add_paragraph_with_format(doc, '第四部分：违约金过高，应予以免除', bold=True, size=13, space_before=12)

penalty_basis = '''一、法律依据

根据《民法典》第五百八十五条：约定的违约金过分高于造成的损失的，人民法院可以根据当事人的请求予以适当减少。

二、本案适用

1. 被告非恶意欠费：历史缴费记录良好，暂停缴费是正当行使抗辩权；
2. 原告损失有限：物业公司的主要损失是资金占用利息，按LPR的1倍已足以弥补；
3. 违约金明显过高：原告主张的违约金占物业费总额的8.8%，明显过高。

三、结论

违约金应予以免除。'''

add_paragraph_with_format(doc, penalty_basis, size=12, first_line_indent=0.74)

doc.add_paragraph()

# 第五部分
add_paragraph_with_format(doc, '第五部分：程序性问题', bold=True, size=13, space_before=12)

procedure_text = '''一、申请转普通程序

本案存在以下复杂情形，不适合小额诉讼的一审终审程序：

1. 漏水原因需司法鉴定：涉及开发商工程质量问题与物业维修不当的区分；
2. 整改责任主体待认定：涉及开发商、物业、业主三方责任；
3. 服务质量争议需实体审理：需通过完整庭审程序查明事实。

根据《最高人民法院关于审理民事案件适用小额诉讼程序若干问题的规定》第六条第（五）项，本案属于"其他不宜适用一审终审的纠纷"。

请求：将本案转为普通程序审理。

二、申请延期举证

被告需要时间：
1. 整理现有证据；
2. 申请法院调取证据；
3. 准备司法鉴定申请。

请求：延长举证期限至2026年9月21日。'''

add_paragraph_with_format(doc, procedure_text, size=12, first_line_indent=0.74)

doc.add_paragraph()

# 证据清单
add_paragraph_with_format(doc, '证据清单', bold=True, size=14, space_before=16)

evidence_table = [
    ['编号', '证据名称', '证据来源', '证明目的', '页码'],
    ['A-1', '钥匙委托凭证（2019年5月2日）', '被告提供', '证明漏水问题在交房时即存在，被告已履行报修义务', '1'],
    ['A-2', '微信反馈截图及照片（2019年6月22日）', '被告提供', '证明漏水具体问题和被告积极报修', '2-10'],
    ['A-3', '整改记录照片（2019年8月）', '被告提供', '证明漏水问题持续', '11-12'],
    ['A-4', '整改记录照片（2020年9月）', '被告提供', '证明整改无效，问题反复', '13-19'],
    ['A-5', '漏水视频（2022年5月）', '被告提供', '证明漏水严重程度', '20-23'],
    ['A-6', '录音（2021年3月5日）', '被告提供', '证明业主持续投诉，物业不作为', '24-25'],
    ['A-7', '李霖聊天记录（17张）', '被告提供', '证明业主积极沟通，物业敷衍', '26-42'],
    ['A-8', '观承售后聊天记录（16张）', '被告提供', '证明业主持续投诉', '43-58'],
    ['A-9', '其他业主漏水问题聊天记录（40张）', '被告提供', '证明漏水问题普遍性，物业不作为', '59-98'],
    ['A-10', '通话记录截图', '被告提供', '证明业主主动沟通，物业催缴', '99-101'],
    ['A-11', '2019年5月至2022年2月缴费凭证', '被告提供', '证明被告历史缴费记录良好', '102-130'],
    ['A-12', '身份证复印件', '被告提供', '证明身份信息', '131'],
    ['A-13', '房产证/购房合同', '被告提供', '证明业主身份及质保期限', '132-135']
]

table8 = doc.add_table(rows=len(evidence_table), cols=5)
table8.style = 'Table Grid'
for i, row_data in enumerate(evidence_table):
    for j, cell_text in enumerate(row_data):
        table8.rows[i].cells[j].text = cell_text
        for para in table8.rows[i].cells[j].paragraphs:
            if para.runs:
                para.runs[0].font.size = Pt(9)
                para.runs[0].font.name = 'SimSun'
                para.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

# 结尾
doc.add_paragraph()
doc.add_paragraph()

end_text = '''此致

重庆市两江新区人民法院



答辩人：唐斐男（签字）

日期：2026年9月14日

---

附：联系方式
- 地址：重庆市九龙坡区经纬大道1399号隆鑫花漾四季2幢4-6
- 电话：15025355361
- 审判人员：曹阳 审判员
- 联系电话：023-67820501
- 开庭时间：2026年10月22日 09:35
- 开庭地点：空港审判区调解室（一）【空港大道418号】'''

p = doc.add_paragraph(end_text)
for run in p.runs:
    run.font.size = Pt(12)
    run.font.name = 'SimSun'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')

# 保存
output_path = r'C:\Users\Administrator\.openclaw\workspace\memory\案件分析\答辩状_唐斐男_最终版_20260914.docx'
doc.save(output_path)
print(f'✅ 已生成：{output_path}')
