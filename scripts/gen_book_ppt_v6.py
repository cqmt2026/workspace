#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成《路上有惊慌》好书推荐PPT - 专业设计版v6"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import numpy as np

OUTPUT_DIR = r"C:\Users\Administrator\.openclaw\workspace\output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "路上有惊慌_好书推荐_v6.pptx")

# 创建演示文稿
prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)

# 高级配色 - 学术文艺风
C = {
    'bg': RGBColor(250, 248, 245),      # 暖白
    'primary': RGBColor(120, 110, 100),  # 深棕灰
    'secondary': RGBColor(160, 145, 130), # 中棕
    'accent': RGBColor(200, 120, 80),    # 陶土红
    'highlight': RGBColor(220, 180, 100), # 金色
    'text': RGBColor(70, 65, 60),        # 深灰文字
    'white': RGBColor(255, 255, 255),
    'light': RGBColor(245, 242, 238),
}

def set_font(run, size=18, bold=False, color=None):
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    run.font.name = 'Microsoft YaHei'
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.insert(0, ea)
    ea.set(qn('a:typeface'), 'Microsoft YaHei')

def add_slide_bg(slide, color=C['bg']):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()

def add_top_bar(slide, color=C['primary'], height=Inches(0.08)):
    """顶部装饰线"""
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, height)
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.line.fill.background()

def add_left_line(slide, y_start=Inches(1.5), height=Inches(5)):
    """左侧装饰线"""
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.3), y_start, Inches(0.04), height)
    line.fill.solid()
    line.fill.fore_color.rgb = C['accent']
    line.line.fill.background()

# ===== 第1页：封面 =====
s1 = prs.slides.add_slide(prs.slide_layouts[6])
add_slide_bg(s1)
add_top_bar(s1, C['primary'])
add_left_line(s1)

# 右侧装饰块
deco1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(9), Inches(1), Inches(4), Inches(0.15))
deco1.fill.solid()
deco1.fill.fore_color.rgb = C['accent']
deco1.line.fill.background()

deco2 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(9.5), Inches(1.2), Inches(3.5), Inches(0.1))
deco2.fill.solid()
deco2.fill.fore_color.rgb = C['highlight']
deco2.line.fill.background()

# 书名
t = s1.shapes.add_textbox(Inches(1), Inches(2.5), Inches(10), Inches(1.5))
tf = t.text_frame
p = tf.paragraphs[0]
p.text = "《路上有惊慌》"
p.font.size = Pt(72)
p.font.bold = True
p.font.color.rgb = C['primary']
set_font(p.runs[0] if p.runs else p.add_run(), 72, True, C['primary'])

# 作者
a = s1.shapes.add_textbox(Inches(1), Inches(4.2), Inches(10), Inches(0.6))
tf = a.text_frame
p = tf.paragraphs[0]
p.text = "饭饭 著"
p.font.size = Pt(32)
p.font.color.rgb = C['text']
set_font(p.runs[0] if p.runs else p.add_run(), 32, False, C['text'])

# 分隔线
line = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(5.0), Inches(4), Inches(0.04))
line.fill.solid()
line.fill.fore_color.rgb = C['accent']
line.line.fill.background()

# 信息
info = s1.shapes.add_textbox(Inches(1), Inches(5.2), Inches(10), Inches(0.5))
tf = info.text_frame
p = tf.paragraphs[0]
p.text = "上海三联书店  |  豆瓣 8.0分"
p.font.size = Pt(16)
p.font.color.rgb = C['secondary']
set_font(p.runs[0] if p.runs else p.add_run(), 16, False, C['secondary'])

# 推荐人
rec = s1.shapes.add_textbox(Inches(1), Inches(6.5), Inches(10), Inches(0.5))
tf = rec.text_frame
p = tf.paragraphs[0]
p.text = "四年级X班 XXX 推荐"
p.font.size = Pt(18)
p.font.color.rgb = C['text']
set_font(p.runs[0] if p.runs else p.add_run(), 18, False, C['text'])

# ===== 第2页：书籍简介 =====
s2 = prs.slides.add_slide(prs.slide_layouts[6])
add_slide_bg(s2)
add_top_bar(s2, C['accent'])

# 标题
t2 = s2.shapes.add_textbox(Inches(0.8), Inches(0.3), Inches(12), Inches(0.8))
tf = t2.text_frame
p = tf.paragraphs[0]
p.text = "📚 这本书讲了什么？"
p.font.size = Pt(36)
p.font.bold = True
p.font.color.rgb = C['primary']
set_font(p.runs[0] if p.runs else p.add_run(), 36, True, C['primary'])

# 左侧内容卡片
card1 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
    Inches(0.6), Inches(1.3), Inches(6.5), Inches(5.7))
card1.fill.solid()
card1.fill.fore_color.rgb = C['white']
card1.line.color.rgb = C['secondary']
card1.line.width = Pt(1)

# 卡片标题
ct1 = s2.shapes.add_textbox(Inches(0.9), Inches(1.5), Inches(6), Inches(0.6))
tf = ct1.text_frame
p = tf.paragraphs[0]
p.text = "📖 内容简介"
p.font.size = Pt(22)
p.font.bold = True
p.font.color.rgb = C['accent']
set_font(p.runs[0] if p.runs else p.add_run(), 22, True, C['accent'])

# 卡片内容
cc1 = s2.shapes.add_textbox(Inches(0.9), Inches(2.2), Inches(6), Inches(4.5))
tf = cc1.text_frame
tf.word_wrap = True
lines = [
    "《路上有惊慌》是作家饭饭的随笔集，",
    "记录生活中的大小事。",
    "",
    "有家庭的温馨，有社会的观察，",
    "还有有趣的思考。",
    "",
    "书名意思是：人生路上总会遇到",
    "意想不到的事情，",
    "作者教会我们勇敢面对。",
    "",
    "文字幽默风趣，读起来轻松愉快，",
    "适合全家人一起阅读。"
]
for i, line in enumerate(lines):
    if i == 0:
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
    p.text = line
    p.font.size = Pt(15)
    p.font.color.rgb = C['text']
    set_font(p.runs[0] if p.runs else p.add_run(), 15, False, C['text'])
    p.space_before = Pt(4)
    p.line_spacing = 1.5

# 右侧卡片组
card2 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
    Inches(7.5), Inches(1.3), Inches(5.3), Inches(2.6))
card2.fill.solid()
card2.fill.fore_color.rgb = C['light']
card2.line.color.rgb = C['accent']
card2.line.width = Pt(1)

ct2 = s2.shapes.add_textbox(Inches(7.8), Inches(1.5), Inches(4.8), Inches(0.5))
tf = ct2.text_frame
p = tf.paragraphs[0]
p.text = "⭐ 书籍亮点"
p.font.size = Pt(20)
p.font.bold = True
p.font.color.rgb = C['accent']
set_font(p.runs[0] if p.runs else p.add_run(), 20, True, C['accent'])

cc2 = s2.shapes.add_textbox(Inches(7.8), Inches(2.1), Inches(4.8), Inches(1.6))
tf = cc2.text_frame
tf.word_wrap = True
for i, item in enumerate(["语言幽默风趣，读起来轻松愉快", "故事贴近生活，学会观察身边事物", "篇幅短小精悍，适合碎片时间阅读"]):
    if i == 0:
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
    p.text = f"✓ {item}"
    p.font.size = Pt(13)
    p.font.color.rgb = C['text']
    set_font(p.runs[0] if p.runs else p.add_run(), 13, False, C['text'])
    p.space_before = Pt(10)

# 右下角卡片
card3 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
    Inches(7.5), Inches(4.1), Inches(5.3), Inches(2.9))
card3.fill.solid()
card3.fill.fore_color.rgb = C['white']
card3.line.color.rgb = C['secondary']
card3.line.width = Pt(1)

ct3 = s2.shapes.add_textbox(Inches(7.8), Inches(4.3), Inches(4.8), Inches(0.5))
tf = ct3.text_frame
p = tf.paragraphs[0]
p.text = "👥 适合谁读？"
p.font.size = Pt(20)
p.font.bold = True
p.font.color.rgb = C['primary']
set_font(p.runs[0] if p.runs else p.add_run(), 20, True, C['primary'])

cc3 = s2.shapes.add_textbox(Inches(7.8), Inches(4.9), Inches(4.8), Inches(1.8))
tf = cc3.text_frame
tf.word_wrap = True
for i, item in enumerate(["小学高年级学生 ✓", "初中生及家长 ✓", "喜欢散文的读者 ✓", "想缓解压力的人 ✓"]):
    if i == 0:
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
    p.text = item
    p.font.size = Pt(14)
    p.font.color.rgb = C['text']
    set_font(p.runs[0] if p.runs else p.add_run(), 14, False, C['text'])
    p.space_before = Pt(12)

# ===== 第3页：精彩片段 =====
s3 = prs.slides.add_slide(prs.slide_layouts[6])
add_slide_bg(s3)
add_top_bar(s3, C['secondary'])

t3 = s3.shapes.add_textbox(Inches(0.8), Inches(0.3), Inches(12), Inches(0.8))
tf = t3.text_frame
p = tf.paragraphs[0]
p.text = "💬 书中金句"
p.font.size = Pt(36)
p.font.bold = True
p.font.color.rgb = C['primary']
set_font(p.runs[0] if p.runs else p.add_run(), 36, True, C['primary'])

# 引用框 - 左侧装饰条
quote_frame = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
    Inches(1.2), Inches(1.5), Inches(10.93), Inches(4))
quote_frame.fill.solid()
quote_frame.fill.fore_color.rgb = C['light']
quote_frame.line.color.rgb = C['secondary']
quote_frame.line.width = Pt(1)

# 左侧色条
quote_bar = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE,
    Inches(1.2), Inches(1.5), Inches(0.12), Inches(4))
quote_bar.fill.solid()
quote_bar.fill.fore_color.rgb = C['accent']
quote_bar.line.fill.background()

# 引用文字
qt = s3.shapes.add_textbox(Inches(1.6), Inches(2.0), Inches(10), Inches(2.5))
tf = qt.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "人生就像走路，不可能一直平坦，也会有坑坑洼洼。但正是这些不平，让旅程变得有趣。"
p.font.size = Pt(28)
p.font.italic = True
p.font.color.rgb = C['primary']
p.font.name = 'KaiTi'
p.alignment = PP_ALIGN.CENTER
p.space_after = Pt(30)

# 来源
qs = s3.shapes.add_textbox(Inches(1.6), Inches(4.3), Inches(10), Inches(0.5))
tf = qs.text_frame
p = tf.paragraphs[0]
p.text = "—— 饭饭《路上有惊慌》"
p.font.size = Pt(16)
p.font.color.rgb = C['secondary']
set_font(p.runs[0] if p.runs else p.add_run(), 16, False, C['secondary'])
p.alignment = PP_ALIGN.RIGHT

# 底部感悟
ref_box = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
    Inches(1.2), Inches(5.8), Inches(10.93), Inches(1.3))
ref_box.fill.solid()
ref_box.fill.fore_color.rgb = C['accent']
ref_box.line.fill.background()

ref_t = s3.shapes.add_textbox(Inches(1.5), Inches(5.9), Inches(10.43), Inches(0.4))
tf = ref_t.text_frame
p = tf.paragraphs[0]
p.text = "💭 我的感悟"
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = C['white']
set_font(p.runs[0] if p.runs else p.add_run(), 18, True, C['white'])

ref_c = s3.shapes.add_textbox(Inches(1.5), Inches(6.35), Inches(10.43), Inches(0.6))
tf = ref_c.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "这句话让我明白：遇到困难不要怕，这就是成长的机会！"
p.font.size = Pt(14)
p.font.color.rgb = C['white']
set_font(p.runs[0] if p.runs else p.add_run(), 14, False, C['white'])
p.alignment = PP_ALIGN.CENTER

# ===== 第4页：推荐理由 =====
s4 = prs.slides.add_slide(prs.slide_layouts[6])
add_slide_bg(s4)
add_top_bar(s4, C['primary'])

t4 = s4.shapes.add_textbox(Inches(0.8), Inches(0.3), Inches(12), Inches(0.8))
tf = t4.text_frame
p = tf.paragraphs[0]
p.text = "⭐ 为什么推荐这本书？"
p.font.size = Pt(36)
p.font.bold = True
p.font.color.rgb = C['primary']
set_font(p.runs[0] if p.runs else p.add_run(), 36, True, C['primary'])

# 五个理由 - 横向排列
reasons = [
    ("语言幽默", "读起来轻松愉快", C['accent']),
    ("贴近生活", "故事都是身边事", C['secondary']),
    ("勇敢面对", "学会乐观心态", C['accent']),
    ("短小精悍", "几分钟读完一篇", C['secondary']),
    ("全家适合", "大人小孩都能读", C['accent']),
]

x_start = Inches(0.3)
width = Inches(2.45)
gap = Inches(0.12)

for i, (title, desc, color) in enumerate(reasons):
    x = x_start + i * (width + gap)
    
    # 卡片
    card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.3), width, Inches(4.8))
    card.fill.solid()
    card.fill.fore_color.rgb = C['white']
    card.line.color.rgb = color
    card.line.width = Pt(1.5)
    
    # 顶部色条
    top_strip = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE,
        x, Inches(1.3), width, Inches(0.12))
    top_strip.fill.solid()
    top_strip.fill.fore_color.rgb = color
    top_strip.line.fill.background()
    
    # 编号圆圈
    num_circle = s4.shapes.add_shape(MSO_SHAPE.OVAL, 
        x + Inches(0.9), Inches(1.6), Inches(0.6), Inches(0.6))
    num_circle.fill.solid()
    num_circle.fill.fore_color.rgb = color
    num_circle.line.fill.background()
    
    num_t = s4.shapes.add_textbox(x + Inches(0.9), Inches(1.68), Inches(0.6), Inches(0.5))
    tf = num_t.text_frame
    p = tf.paragraphs[0]
    p.text = str(i + 1)
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = C['white']
    p.font.name = 'Arial'
    p.alignment = PP_ALIGN.CENTER
    
    # 标题
    rt = s4.shapes.add_textbox(x + Inches(0.15), Inches(2.4), Inches(2.15), Inches(0.6))
    tf = rt.text_frame
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = color
    set_font(p.runs[0] if p.runs else p.add_run(), 18, True, color)
    p.alignment = PP_ALIGN.CENTER
    
    # 分隔线
    dec_line = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE,
        x + Inches(0.6), Inches(3.0), Inches(1.25), Inches(0.03))
    dec_line.fill.solid()
    dec_line.fill.fore_color.rgb = color
    dec_line.line.fill.background()
    
    # 描述
    rd = s4.shapes.add_textbox(x + Inches(0.2), Inches(3.2), Inches(2.05), Inches(2.5))
    tf = rd.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = desc
    p.font.size = Pt(13)
    p.font.color.rgb = C['text']
    set_font(p.runs[0] if p.runs else p.add_run(), 13, False, C['text'])
    p.alignment = PP_ALIGN.CENTER

# 底部号召
cta = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
    Inches(2), Inches(6.5), Inches(9.33), Inches(0.7))
cta.fill.solid()
cta.fill.fore_color.rgb = C['primary']
cta.line.fill.background()

cta_t = s4.shapes.add_textbox(Inches(2), Inches(6.6), Inches(9.33), Inches(0.5))
tf = cta_t.text_frame
p = tf.paragraphs[0]
p.text = "📚 快来和我一起阅读这本好书吧！"
p.font.size = Pt(20)
p.font.bold = True
p.font.color.rgb = C['white']
set_font(p.runs[0] if p.runs else p.add_run(), 20, True, C['white'])
p.alignment = PP_ALIGN.CENTER

# ===== 第5页：阅读建议 =====
s5 = prs.slides.add_slide(prs.slide_layouts[6])
add_slide_bg(s5)
add_top_bar(s5, C['accent'])

t5 = s5.shapes.add_textbox(Inches(0.8), Inches(0.3), Inches(12), Inches(0.8))
tf = t5.text_frame
p = tf.paragraphs[0]
p.text = "📖 阅读小贴士"
p.font.size = Pt(36)
p.font.bold = True
p.font.color.rgb = C['primary']
set_font(p.runs[0] if p.runs else p.add_run(), 36, True, C['primary'])

# 左侧卡片
meth_card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, 
    Inches(0.5), Inches(1.3), Inches(5.8), Inches(5.7))
meth_card.fill.solid()
meth_card.fill.fore_color.rgb = C['white']
meth_card.line.color.rgb = C['primary']
meth_card.line.width = Pt(1.5)

# 顶部色条
meth_top = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE,
    Inches(0.5), Inches(1.3), Inches(5.8), Inches(0.12))
meth_top.fill.solid()
meth_top.fill.fore_color.rgb = C['primary']
meth_top.line.fill.background()

meth_t = s5.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(5.2), Inches(0.6))
tf = meth_t.text_frame
p = tf.paragraphs[0]
p.text = "📚 怎么读？"
p.font.size = Pt(22)
p.font.bold = True
p.font.color.rgb = C['primary']
set_font(p.runs[0] if p.runs else p.add_run(), 22, True, C['primary'])

meth_c = s5.shapes.add_textbox(Inches(0.8), Inches(2.3), Inches(5.2), Inches(4.5))
tf = meth_c.text_frame
tf.word_wrap = True
items = [
    "✓ 每天读1-2篇，每篇只需5分钟",
    "",
    "✓ 读到有趣的地方，停顿想一想",
    "",
    "✓ 可以和爸爸妈妈分享你的感受",
    "",
    "✓ 试着模仿作者，记录自己的生活",
    "",
    "✓ 好书值得反复读，每次都有新发现"
]
for i, item in enumerate(items):
    if i == 0:
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
    p.text = item
    p.font.size = Pt(14)
    p.font.color.rgb = C['text']
    set_font(p.runs[0] if p.runs else p.add_run(), 14, False, C['text'])
    p.space_before = Pt(8)

# 右侧上卡片
scene_card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
    Inches(6.6), Inches(1.3), Inches(6.2), Inches(2.5))
scene_card.fill.solid()
scene_card.fill.fore_color.rgb = C['secondary']
scene_card.line.fill.background()

scene_t = s5.shapes.add_textbox(Inches(6.9), Inches(1.5), Inches(5.7), Inches(0.5))
tf = scene_t.text_frame
p = tf.paragraphs[0]
p.text = "🌟 适合什么时候读？"
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = C['white']
set_font(p.runs[0] if p.runs else p.add_run(), 18, True, C['white'])

scene_c = s5.shapes.add_textbox(Inches(6.9), Inches(2.1), Inches(5.7), Inches(1.5))
tf = scene_c.text_frame
tf.word_wrap = True
for i, item in enumerate(["• 课间休息时", "• 睡前15分钟", "• 周末午后", "• 和家人一起"]):
    if i == 0:
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
    p.text = item
    p.font.size = Pt(14)
    p.font.color.rgb = C['white']
    set_font(p.runs[0] if p.runs else p.add_run(), 14, False, C['white'])
    p.space_before = Pt(10)

# 右侧下卡片
action_card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
    Inches(6.6), Inches(4.0), Inches(6.2), Inches(3.0))
action_card.fill.solid()
action_card.fill.fore_color.rgb = C['accent']
action_card.line.fill.background()

action_t = s5.shapes.add_textbox(Inches(6.9), Inches(4.2), Inches(5.7), Inches(0.5))
tf = action_t.text_frame
p = tf.paragraphs[0]
p.text = "🎯 行动起来！"
p.font.size = Pt(18)
p.font.bold = True
p.font.color.rgb = C['white']
set_font(p.runs[0] if p.runs else p.add_run(), 18, True, C['white'])

action_c = s5.shapes.add_textbox(Inches(6.9), Inches(4.8), Inches(5.7), Inches(1.8))
tf = action_c.text_frame
tf.word_wrap = True
for i, item in enumerate(["去图书馆借一本", "或让爸爸妈妈帮你买", "", "让我们一起在路上，", "遇见不一样的风景！"]):
    if i == 0:
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
    p.text = item
    p.font.size = Pt(14)
    p.font.color.rgb = C['white']
    set_font(p.runs[0] if p.runs else p.add_run(), 14, False, C['white'])
    p.space_before = Pt(10)

# 保存
prs.save(OUTPUT_PATH)
print(f"[OK] v6 saved: {OUTPUT_PATH}")
print(f"[Pages] {len(prs.slides)}")
