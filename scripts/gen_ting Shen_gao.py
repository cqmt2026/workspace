# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

doc = Document()

for section in doc.sections:
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2.5)

style = doc.styles['Normal']
style.font.name = '宋体'
style.font.size = Pt(12)
style._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
style.paragraph_format.line_spacing = 1.5
style.paragraph_format.first_line_indent = Pt(24)

content = [
    ('title', '唐斐男诉成都万科物业案 — 庭审陈述稿'),
    ('info', '案号：（2026）渝0157民初82907号'),
    ('info', '被告：唐斐男'),
    ('info', '开庭时间：2026年10月22日 09:35'),
    ('info', '审判员：曹阳'),
    ('info', '管辖法院：重庆市两江新区人民法院空港审判区调解室（一）'),
    ('h1', '开场陈述（1分钟）'),
    ('para', '尊敬的审判员：'),
    ('para', '我是本案被告唐斐男。对于原告主张的物业费本金，我对计算方式和金额没有异议。但我方认为，减免30%物业费并免除全部违约金具有充分的事实和法律依据，理由如下：'),
    ('para', '第一，原告在房屋质量漏水整改过程中未尽到协助义务；'),
    ('para', '第二，原告提供的物业服务未达到合同约定的服务标准；'),
    ('para', '第三，我方历史缴费记录良好，前29个月按时缴费，不存在恶意欠费故意。'),
    ('para', '下面我逐一说明。'),
    ('h1', '第一部分：漏水事实与物业未尽协助义务（4分钟）'),
    ('h2', '一、漏水问题自交房时即存在'),
    ('para', '2019年5月2日，我收房当天，发现房屋存在多处漏水问题，当即向物业提交《钥匙委托凭证》，明确注明委托原因为"整改"（见证据A-1）。'),
    ('para', '这证明：'),
    ('para', '1. 漏水问题在交房时即已存在；'),
    ('para', '2. 我已履行报修义务；'),
    ('para', '3. 原告作为开发商委托的保修服务履行主体，明知房屋存在质量问题。'),
    ('h2', '二、漏水问题的具体内容'),
    ('para', '2019年6月22日，我通过微信向物业反馈具体问题，并发送了现场照片（证据A-2）。反馈的具体问题包括：'),
    ('table', ['序号', '问题描述', '问题性质']),
    ('row', ['1', '二楼阳台有积水潭', '防水问题']),
    ('row', ['2', '三楼楼梯口墙角处渗水、墙体地面潮湿', '防水/结构问题']),
    ('row', ['3', '二楼儿童房门口顶部渗水', '防水问题']),
    ('row', ['4', '窗户油漆脱落', '质量问题']),
    ('row', ['5', '二楼主卧滑门处顶部渗水', '防水问题']),
    ('para', '上述问题均属于屋面防水、外墙防渗漏范畴，根据《建设工程质量管理条例》第四十条，质保期为5年，至2024年5月2日届满。'),
    ('h2', '三、漏水问题持续时间长'),
    ('table', ['时间节点', '事项', '证据']),
    ('row', ['2019年5月2日', '首次报修（钥匙委托）', '证据A-1']),
    ('row', ['2019年6月22日', '详细反馈6项问题', '证据A-2']),
    ('row', ['2019年7月27日', '邻居反映"整改无下文"', '证据A-8']),
    ('row', ['2020年9月', '发现"大面积返工"', '证据A-4']),
    ('row', ['2021年3月5日', '录音投诉', '证据A-5']),
    ('row', ['2022年2月', '停止缴费（因问题未解决）', '-']),
    ('para', '从2019年5月至2020年9月，长达16个月，漏水问题未得到有效解决。'),
    ('h2', '四、原告未尽协助义务的四种表现'),
    ('para', '根据《重庆市新建商品房质量保证书》约定：'),
    ('quote', '"业主使用后，有关房屋质量的来信来访、投诉，本公司将直接或委托物业管理公司及时给予书面答复和妥善处理。"'),
    ('para', '物业的协助义务包括：'),
    ('para', '1. 接收报修：业主向物业报修 = 向开发商报修'),
    ('para', '2. 转达开发商：及时将报修信息转达开发商'),
    ('para', '3. 跟进处理进度：监督开发商整改进度'),
    ('para', '4. 反馈处理结果：向业主反馈维修结果'),
    ('para', '但原告存在以下违约行为：'),
    ('table', ['违约行为', '具体表现', '证据']),
    ('row', ['1. 未有效转达报修', '2019年5月2日报修，至7月27日仍"无下文"', '证据A-8']),
    ('row', ['2. 未跟进整改进度', '2019年6月22日详细反馈，至2020年9月仍未解决', '证据A-2、A-4']),
    ('row', ['3. 未反馈处理结果', '业主多次询问，物业未给予明确答复', '证据A-5、A-6、A-7']),
    ('row', ['4. 未监督整改效果', '2020年9月发现"大面积返工"，整改无效', '证据A-4']),
    ('para', '原告未尽协助义务，构成违约，应减免物业费。'),
    ('h1', '第二部分：原告未尽承接查验协议配合监督义务（2分钟）'),
    ('h2', '一、法律依据'),
    ('para', '根据《前期物业服务合同》附件七《物业承接查验协议》约定：'),
    ('quote', '"甲方有权要求乙方配合工程遗留问题的整改工作，为整改工作提供水、电、现场秩序等方面的便利。"'),
    ('quote', '"乙方有权监督甲方对工程遗留问题的整改进度，并依据国家强制性规范、标准和商品房买卖合同对整改结果进行复验。"'),
    ('h2', '二、原告违约事实'),
    ('table', ['合同义务', '实际情况', '违约程度']),
    ('row', ['配合整改工作', '未有效配合开发商整改', '❌ 违约']),
    ('row', ['监督整改进度', '16个月无实质进展，物业未有效监督', '❌ 严重违约']),
    ('row', ['复验整改结果', '2020年9月发现"大面积返工"，复验流于形式', '❌ 违约']),
    ('para', '原告未尽配合监督义务，导致漏水问题长期未解决，应承担相应违约责任。'),
    ('h1', '第三部分：原告未举证服务达标（2分钟）'),
    ('h2', '一、原告提交的证据'),
    ('para', '原告仅提交了以下证据：'),
    ('para', '- 前期物业服务合同（27页）'),
    ('para', '- 催缴记录（微信截图）'),
    ('para', '- 通话记录截图'),
    ('h2', '二、原告缺失的证据'),
    ('table', ['缺失证据', '重要性']),
    ('row', ['维修记录档案', '⭐⭐⭐⭐⭐']),
    ('row', ['投诉处理记录', '⭐⭐⭐⭐⭐']),
    ('row', ['报修值班记录', '⭐⭐⭐⭐']),
    ('row', ['巡查记录', '⭐⭐⭐']),
    ('row', ['满意度测评记录', '⭐⭐⭐']),
    ('h2', '三、法律后果'),
    ('para', '根据《最高人民法院关于民事诉讼证据的若干规定》第九十五条：'),
    ('quote', '"一方当事人控制证据无正当理由拒不提交，对待证事实负有举证责任的当事人主张该证据的内容不利于控制人的，人民法院可以认定该主张成立。"'),
    ('para', '原告作为物业服务人，掌握服务质量的全部证据。如原告无法提供上述证据，应承担举证不能的不利后果，法院应推定原告服务不达标。'),
    ('h1', '第四部分：被告非恶意欠费（1分钟）'),
    ('h2', '一、缴费时间线'),
    ('table', ['期间', '缴费状态']),
    ('row', ['2019年5月-2022年2月', '✅ 已按时缴纳（29个月）']),
    ('row', ['2022年2月-2026年6月', '❌ 未缴纳（34个月）']),
    ('h2', '二、法律意义'),
    ('para', '1. 证明被告信用良好：前29个月按时缴费，从未拖欠；'),
    ('para', '2. 证明非恶意欠费：暂停缴费是因为物业服务质量问题，而非恶意逃避；'),
    ('para', '3. 强化违约金抗辩：被告历史表现良好，违约金应予以免除。'),
    ('h1', '第五部分：违约金过高，应予以免除（1分钟）'),
    ('h2', '一、法律依据'),
    ('para', '根据《民法典》第五百八十五条：'),
    ('quote', '"约定的违约金过分高于造成的损失的，人民法院可以根据当事人的请求予以适当减少。"'),
    ('h2', '二、本案适用'),
    ('para', '1. 被告非恶意欠费：历史缴费记录良好，暂停缴费是正当行使抗辩权；'),
    ('para', '2. 原告损失有限：物业公司的主要损失是资金占用利息，按LPR的1倍已足以弥补；'),
    ('para', '3. 违约金明显过高：原告主张的违约金占物业费总额的8.8%，明显过高。'),
    ('para', '结论：违约金应予以免除。'),
    ('h1', '总结陈词（30秒）'),
    ('para', '尊敬的审判员，综上所述：'),
    ('para', '1. 原告未尽漏水整改协助义务，构成违约；'),
    ('para', '2. 原告未尽承接查验协议配合监督义务，构成违约；'),
    ('para', '3. 原告未提供任何服务质量达标证据，应承担举证不能的不利后果；'),
    ('para', '4. 被告历史缴费记录良好，不存在恶意欠费故意；'),
    ('para', '5. 违约金明显过高，应予以免除。'),
    ('para', '我方请求：'),
    ('para', '- 减免30%物业费（即减免6,442.49元，实际支付15,032.47元）；'),
    ('para', '- 免除全部违约金；'),
    ('para', '- 本案诉讼费用由原告承担。'),
    ('para', '以上陈述，请审判员采纳。'),
]

current_table = None
table_rows = []

for item in content:
    if item[0] == 'title':
        p = doc.add_heading(item[1], level=0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
    elif item[0] == 'info':
        p = doc.add_paragraph(item[1])
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        
    elif item[0] == 'h1':
        # 关闭之前的表格
        if current_table and table_rows:
            doc.add_table(rows=len(table_rows), cols=len(table_rows[0]))
            tbl = doc.tables[-1]
            for i, row_data in enumerate(table_rows):
                for j, cell_text in enumerate(row_data):
                    tbl.rows[i].cells[j].text = cell_text
            table_rows = []
            current_table = None
        p = doc.add_heading(item[1], level=1)
        
    elif item[0] == 'h2':
        if current_table and table_rows:
            doc.add_table(rows=len(table_rows), cols=len(table_rows[0]))
            tbl = doc.tables[-1]
            for i, row_data in enumerate(table_rows):
                for j, cell_text in enumerate(row_data):
                    tbl.rows[i].cells[j].text = cell_text
            table_rows = []
            current_table = None
        p = doc.add_heading(item[1], level=2)
        
    elif item[0] == 'para':
        if current_table and table_rows:
            doc.add_table(rows=len(table_rows), cols=len(table_rows[0]))
            tbl = doc.tables[-1]
            for i, row_data in enumerate(table_rows):
                for j, cell_text in enumerate(row_data):
                    tbl.rows[i].cells[j].text = cell_text
            table_rows = []
            current_table = None
        p = doc.add_paragraph(item[1])
        p.paragraph_format.first_line_indent = Pt(24)
        
    elif item[0] == 'quote':
        if current_table and table_rows:
            doc.add_table(rows=len(table_rows), cols=len(table_rows[0]))
            tbl = doc.tables[-1]
            for i, row_data in enumerate(table_rows):
                for j, cell_text in enumerate(row_data):
                    tbl.rows[i].cells[j].text = cell_text
            table_rows = []
            current_table = None
        p = doc.add_paragraph(item[1])
        p.paragraph_format.left_indent = Cm(1)
        
    elif item[0] == 'table':
        current_table = True
        table_rows = [item[1]]
        
    elif item[0] == 'row':
        table_rows.append(item[1])

# 关闭最后的表格
if current_table and table_rows:
    doc.add_table(rows=len(table_rows), cols=len(table_rows[0]))
    tbl = doc.tables[-1]
    for i, row_data in enumerate(table_rows):
        for j, cell_text in enumerate(row_data):
            tbl.rows[i].cells[j].text = cell_text

output_path = r'C:\Users\Administrator\.openclaw\workspace\memory\案件分析\庭审陈述稿_唐斐男_20261011.docx'
doc.save(output_path)
print(f'[OK] {output_path}')
