# -*- coding: utf-8 -*-
"""用python-pptx生成专业PPT模板 - 互联网创业BP方向"""
import sys, os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import io

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

output_dir = os.path.join(os.path.dirname(__file__), 'output', 'ppt_templates_v2')
os.makedirs(output_dir, exist_ok=True)

# ===== 配色方案 =====
COLORS = {
    'primary': RGBColor(0x1A, 0x23, 0x3D),      # 深蓝
    'accent': RGBColor(0x00, 0x96, 0xD6),        # 亮蓝
    'accent2': RGBColor(0x00, 0xCD, 0xAC),       # 青绿
    'dark': RGBColor(0x1A, 0x1A, 0x2E),          # 深紫
    'white': RGBColor(0xFF, 0xFF, 0xFF),
    'light_gray': RGBColor(0xE0, 0xE0, 0xE0),
    'gray': RGBColor(0x88, 0x88, 0x88),
    'dark_text': RGBColor(0x33, 0x33, 0x33),
    'orange': RGBColor(0xFF, 0x6B, 0x35),
}

TEMPLATE_NAME = "互联网创业商业计划书"
PAGE_COUNT = 18

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

def add_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_rect(slide, left, top, width, height, color, alpha=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    if alpha is not None:
        # python-pptx doesn't directly support alpha, skip
        pass
    return shape

def add_text_box(slide, left, top, width, height, text, font_size=18, color=COLORS['white'], bold=False, align=PP_ALIGN.LEFT, font_name='微软雅黑'):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = align
    return txBox

def add_multi_text(slide, left, top, width, height, items, font_size=14, color=COLORS['white'], line_spacing=1.5):
    """多行文本"""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = item
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.name = '微软雅黑'
        p.space_after = Pt(font_size * 0.5)
    return txBox

# ===== 第1页：封面 =====
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
add_bg(slide, COLORS['primary'])

# 主标题区域
add_rect(slide, Inches(0), Inches(0), Inches(13.333), Inches(1.5), COLORS['accent'])
add_rect(slide, Inches(0), Inches(1.5), Inches(13.333), Inches(0.08), COLORS['accent2'])

add_text_box(slide, Inches(1), Inches(0.3), Inches(11), Inches(1), 
             TEMPLATE_NAME, font_size=40, color=COLORS['white'], bold=True)

# 副标题
add_text_box(slide, Inches(1), Inches(2.2), Inches(11), Inches(1),
             "投资人必看的商业计划书模板", font_size=24, color=COLORS['accent'])

# 装饰线
add_rect(slide, Inches(1), Inches(3.3), Inches(3), Inches(0.04), COLORS['accent2'])

# 关键信息
add_multi_text(slide, Inches(1), Inches(3.8), Inches(11), Inches(2.5), [
    "📊 18页完整商业计划书架构",
    "📈 包含市场分析、财务预测、竞争分析",
    "🎯 适合天使轮/A轮融资路演",
    "🚀 图文并茂，数据可视化",
], font_size=16, color=COLORS['light_gray'])

# 底部信息
add_rect(slide, Inches(0), Inches(6.8), Inches(13.333), Inches(0.7), COLORS['dark'])
add_text_box(slide, Inches(1), Inches(6.85), Inches(5), Inches(0.5),
             "模板版本 1.0 | 适用于创业路演", font_size=12, color=COLORS['gray'])

print(f"  ✅ 封面")

# ===== 第2页：目录 =====
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, COLORS['white'])

add_rect(slide, Inches(0), Inches(0), Inches(0.15), Inches(7.5), COLORS['accent'])
add_text_box(slide, Inches(1), Inches(0.3), Inches(5), Inches(0.8),
             "目录 CONTENTS", font_size=32, color=COLORS['primary'], bold=True)
add_rect(slide, Inches(1), Inches(1.1), Inches(2), Inches(0.04), COLORS['accent'])

# 目录项 - 两列
sections = [
    ("01", "项目概述", "公司愿景、使命与核心价值"),
    ("02", "市场分析", "行业规模、趋势与痛点"),
    ("03", "产品方案", "核心功能与技术创新"),
    ("04", "商业模式", "盈利路径与收入结构"),
    ("05", "竞争分析", "竞品对比与护城河"),
    ("06", "运营数据", "核心指标与增长曲线"),
    ("07", "团队介绍", "核心团队与顾问"),
    ("08", "财务预测", "收入、成本、利润模型"),
    ("09", "融资计划", "融资需求与资金用途"),
]

for i, (num, title, desc) in enumerate(sections):
    col = i % 2
    row = i // 2
    x = Inches(1) + col * Inches(6)
    y = Inches(1.8) + row * Inches(1.3)
    
    # 编号
    add_text_box(slide, x, y, Inches(0.6), Inches(0.5),
                 num, font_size=24, color=COLORS['accent'], bold=True)
    # 标题
    add_text_box(slide, x + Inches(0.6), y, Inches(4.5), Inches(0.4),
                 title, font_size=18, color=COLORS['dark_text'], bold=True)
    # 描述
    add_text_box(slide, x + Inches(0.6), y + Inches(0.4), Inches(4.5), Inches(0.4),
                 desc, font_size=12, color=COLORS['gray'])

print(f"  ✅ 目录")

# ===== 第3-17页：内容页（多种版式） =====

# 版式1：标题+正文（3-4页）
content_slides = [
    ("项目概述", [
        "公司成立于202X年，专注于[领域]的科技创新",
        "愿景：成为[行业]领域的领军企业",
        "使命：用[技术]解决[痛点]，为用户创造价值",
        "核心价值观：创新、务实、共赢、卓越",
    ]),
    ("市场分析", [
        "行业规模：202X年全球市场规模达[X]亿元，年增长率[X]%",
        "目标用户：[X]类核心用户群体，需求痛点明确",
        "市场趋势：数字化转型、消费升级、政策利好",
        "切入机会：现有解决方案存在[X]大核心痛点",
    ]),
    ("商业模式", [
        "收入来源一：[产品/服务] 占比[X]%",
        "收入来源二：[增值服务] 占比[X]%",
        "成本结构：研发[X]% 运营[X]% 营销[X]%",
        "盈利模型：单用户经济模型LTV/CAC = [X]",
    ]),
]

for title, items in content_slides:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, COLORS['white'])
    
    # 左侧色块
    add_rect(slide, Inches(0), Inches(0), Inches(0.15), Inches(7.5), COLORS['accent'])
    
    # 标题
    add_text_box(slide, Inches(1), Inches(0.5), Inches(10), Inches(0.7),
                 title, font_size=28, color=COLORS['primary'], bold=True)
    add_rect(slide, Inches(1), Inches(1.2), Inches(1.5), Inches(0.04), COLORS['accent'])
    
    # 内容 - 带序号
    for i, item in enumerate(items):
        y = Inches(1.8) + i * Inches(1.2)
        # 序号圆点
        shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(1.2), y + Inches(0.05), Inches(0.25), Inches(0.25))
        shape.fill.solid()
        shape.fill.fore_color.rgb = COLORS['accent']
        shape.line.fill.background()
        # 文本
        add_text_box(slide, Inches(1.7), y, Inches(9), Inches(0.5),
                     item, font_size=16, color=COLORS['dark_text'])
    
    # 底部装饰
    add_rect(slide, Inches(0), Inches(7.1), Inches(13.333), Inches(0.4), COLORS['primary'])
    add_text_box(slide, Inches(1), Inches(7.1), Inches(5), Inches(0.4),
                 TEMPLATE_NAME, font_size=10, color=COLORS['gray'])
    
    print(f"  ✅ {title}")

# 版式2：图表页 - 用matplotlib生成图表插入
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

chart_pages = [
    ("财务预测", "未来三年收入增长预测（单位：万元）"),
    ("用户增长", "月活跃用户增长趋势"),
]

for chart_title, chart_subtitle in chart_pages:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_bg(slide, COLORS['white'])
    
    add_rect(slide, Inches(0), Inches(0), Inches(0.15), Inches(7.5), COLORS['accent2'])
    add_text_box(slide, Inches(1), Inches(0.3), Inches(10), Inches(0.6),
                 chart_title, font_size=28, color=COLORS['primary'], bold=True)
    add_text_box(slide, Inches(1), Inches(0.9), Inches(10), Inches(0.4),
                 chart_subtitle, font_size=14, color=COLORS['gray'])
    add_rect(slide, Inches(1), Inches(1.3), Inches(1.5), Inches(0.04), COLORS['accent2'])
    
    # 生成图表
    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    years = ['2024', '2025', '2026', '2027', '2028']
    if chart_title == "财务预测":
        values = [500, 1500, 4500, 12000, 30000]
        color = '#0096D6'
    else:
        values = [1, 5, 20, 80, 300]
        color = '#00CDAC'
    
    bars = ax.bar(years, values, color=color, width=0.5, edgecolor='white', linewidth=1.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CCCCCC')
    ax.spines['bottom'].set_color('#CCCCCC')
    ax.tick_params(colors='#333333')
    
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                f'{val}', ha='center', va='bottom', fontsize=11, fontweight='bold', color='#333333')
    
    plt.tight_layout()
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=150, bbox_inches='tight', transparent=False)
    plt.close()
    img_buf.seek(0)
    
    slide.shapes.add_picture(img_buf, Inches(1.5), Inches(1.8), Inches(9), Inches(4.5))
    
    # 底部
    add_rect(slide, Inches(0), Inches(7.1), Inches(13.333), Inches(0.4), COLORS['primary'])
    add_text_box(slide, Inches(1), Inches(7.1), Inches(5), Inches(0.4),
                 TEMPLATE_NAME, font_size=10, color=COLORS['gray'])
    
    print(f"  ✅ {chart_title}（含图表）")

# 版式3：竞争分析 - 对比表格
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, COLORS['white'])

add_rect(slide, Inches(0), Inches(0), Inches(0.15), Inches(7.5), COLORS['orange'])
add_text_box(slide, Inches(1), Inches(0.3), Inches(10), Inches(0.6),
             "竞争分析", font_size=28, color=COLORS['primary'], bold=True)
add_rect(slide, Inches(1), Inches(0.9), Inches(1.5), Inches(0.04), COLORS['orange'])

# 表格
from pptx.util import Inches, Pt
table_data = [
    ["维度", "我们", "竞品A", "竞品B"],
    ["产品定位", "[核心定位]", "[传统方案]", "[相似方案]"],
    ["技术优势", "[AI/大数据]", "[人工]", "[半自动化]"],
    ["价格", "[X元/月]", "[X元/月]", "[X元/月]"],
    ["用户数", "[X万]", "[X万]", "[X万]"],
    ["融资阶段", "[天使轮]", "[B轮]", "[A轮]"],
]

rows, cols = len(table_data), len(table_data[0])
table = slide.shapes.add_table(rows, cols, Inches(1), Inches(1.5), Inches(11), Inches(4.5)).table

for r in range(rows):
    for c in range(cols):
        cell = table.cell(r, c)
        cell.text = table_data[r][c]
        for paragraph in cell.text_frame.paragraphs:
            paragraph.font.size = Pt(12)
            paragraph.font.name = '微软雅黑'
            paragraph.alignment = PP_ALIGN.CENTER
            if r == 0:
                paragraph.font.bold = True
                paragraph.font.color.rgb = COLORS['white']
            else:
                paragraph.font.color.rgb = COLORS['dark_text']
        
        if r == 0:
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLORS['primary']
        elif c == 0:
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(0xF0, 0xF5, 0xFA)
        elif c == 1:
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(0xE8, 0xF5, 0xE9)

add_rect(slide, Inches(0), Inches(7.1), Inches(13.333), Inches(0.4), COLORS['primary'])
add_text_box(slide, Inches(1), Inches(7.1), Inches(5), Inches(0.4),
             TEMPLATE_NAME, font_size=10, color=COLORS['gray'])

print(f"  ✅ 竞争分析（含表格）")

# 版式4：团队介绍
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, COLORS['white'])

add_rect(slide, Inches(0), Inches(0), Inches(0.15), Inches(7.5), COLORS['accent2'])
add_text_box(slide, Inches(1), Inches(0.3), Inches(10), Inches(0.6),
             "团队介绍", font_size=28, color=COLORS['primary'], bold=True)
add_rect(slide, Inches(1), Inches(0.9), Inches(1.5), Inches(0.04), COLORS['accent2'])

# 团队卡片
team = [
    ("CEO / 创始人", "[姓名]", "连续创业者，前[公司]高管\n[X]年行业经验"),
    ("CTO", "[姓名]", "前[公司]技术总监\n精通[技术栈]，[X]年研发经验"),
    ("CMO", "[姓名]", "前[公司]市场总监\n主导[X]个千万级项目"),
    ("顾问", "[姓名]", "[领域]专家\n[X]年行业资源与经验"),
]

for i, (role, name, desc) in enumerate(team):
    x = Inches(1) + i * Inches(3)
    y = Inches(1.5)
    
    # 卡片背景
    card = add_rect(slide, x, y, Inches(2.8), Inches(4.5), COLORS['primary'])
    card.shadow.inherit = False
    
    # 头像占位
    avatar = slide.shapes.add_shape(MSO_SHAPE.OVAL, x + Inches(0.8), y + Inches(0.3), Inches(1.2), Inches(1.2))
    avatar.fill.solid()
    avatar.fill.fore_color.rgb = COLORS['accent']
    avatar.line.fill.background()
    
    add_text_box(slide, x + Inches(0.1), y + Inches(1.8), Inches(2.6), Inches(0.4),
                 name, font_size=18, color=COLORS['white'], bold=True, align=PP_ALIGN.CENTER)
    add_text_box(slide, x + Inches(0.1), y + Inches(2.3), Inches(2.6), Inches(0.3),
                 role, font_size=12, color=COLORS['accent2'], align=PP_ALIGN.CENTER)
    add_text_box(slide, x + Inches(0.1), y + Inches(2.8), Inches(2.6), Inches(1.2),
                 desc, font_size=11, color=COLORS['light_gray'], align=PP_ALIGN.CENTER)

add_rect(slide, Inches(0), Inches(7.1), Inches(13.333), Inches(0.4), COLORS['primary'])
add_text_box(slide, Inches(1), Inches(7.1), Inches(5), Inches(0.4),
             TEMPLATE_NAME, font_size=10, color=COLORS['gray'])

print(f"  ✅ 团队介绍")

# ===== 第18页：尾页 =====
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, COLORS['primary'])

add_text_box(slide, Inches(1), Inches(2), Inches(11), Inches(1),
             "THANK YOU", font_size=48, color=COLORS['white'], bold=True, align=PP_ALIGN.CENTER)

add_rect(slide, Inches(5.5), Inches(3.3), Inches(2.333), Inches(0.04), COLORS['accent'])

add_text_box(slide, Inches(1), Inches(3.8), Inches(11), Inches(0.6),
             "期待与您携手共创未来", font_size=20, color=COLORS['accent'], align=PP_ALIGN.CENTER)

add_text_box(slide, Inches(1), Inches(5), Inches(11), Inches(1),
             "联系方式：[邮箱] | [电话] | [公司地址]", font_size=14, color=COLORS['gray'], align=PP_ALIGN.CENTER)

add_rect(slide, Inches(0), Inches(6.8), Inches(13.333), Inches(0.7), COLORS['dark'])
add_text_box(slide, Inches(1), Inches(6.85), Inches(5), Inches(0.5),
             TEMPLATE_NAME, font_size=12, color=COLORS['gray'])

print(f"  ✅ 尾页")

# ===== 保存 =====
output_path = os.path.join(output_dir, f'{TEMPLATE_NAME}.pptx')
prs.save(output_path)
sz = os.path.getsize(output_path)
print(f"\n{'='*50}")
print(f"✅ 模板生成完成！")
print(f"📁 {output_path}")
print(f"📊 {PAGE_COUNT}页 | {sz/1024:.0f}KB")
print(f"{'='*50}")