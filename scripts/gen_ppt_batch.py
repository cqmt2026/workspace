# -*- coding: utf-8 -*-
"""
V3.1 批量PPT模板生成器 - 配置驱动
基于Mck-ppt-design-skill设计系统，JSON配置切换主题
"""
import sys, os, io, json, zipfile
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi']
plt.rcParams['axes.unicode_minus'] = False

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

output_dir = os.path.join(os.path.dirname(__file__), 'output', 'ppt_templates_v3')
os.makedirs(output_dir, exist_ok=True)

# ===== 常量 =====
SW = Inches(13.333)
SH = Inches(7.5)
LM = Inches(0.8)
CONTENT_W = SW - LM - LM
BL = 6

# ===== 辅助函数 =====
# 全局字体变量，由generate_template在运行时设置
_HEADING_FONT = 'Georgia'
_BODY_FONT = 'Arial'
_EA_FONT = 'KaiTi'

def _clean_shape(shape):
    sp = shape._element
    style = sp.find(qn('p:style'))
    if style is not None: sp.remove(style)

def set_ea_font(run, typeface='KaiTi', fallback='SimSun'):
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.append(ea)
    ea.set('typeface', typeface)
    sym = rPr.find(qn('a:sym'))
    if sym is None:
        sym = rPr.makeelement(qn('a:sym'), {})
        rPr.append(sym)
    sym.set('typeface', fallback)
    sym.set('pitchFamily', '2')

def C(rgb_list):
    return RGBColor(*rgb_list)

def add_rect(slide, l, t, w, h, color):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = color; s.line.fill.background()
    _clean_shape(s); return s

def add_hline(slide, x, y, length, color=C([0,0,0]), thickness=Pt(0.5)):
    h = max(int(thickness), Emu(6350))
    return add_rect(slide, x, y, length, h, color)

def _apply_font_to_paragraph(p, font_size, font_color, bold, font_name, ea_font):
    """将字体设置传播到段落和所有run上，确保PowerPoint能识别"""
    p.font.size = font_size
    p.font.color.rgb = font_color
    p.font.bold = bold
    p.font.name = font_name
    # 传播到每个run（PowerPoint优先读取run属性）
    for r in p.runs:
        r.font.size = font_size
        r.font.color.rgb = font_color
        r.font.bold = bold
        r.font.name = font_name
        set_ea_font(r, ea_font)

def add_text(slide, l, t, w, h, text, font_size=Pt(14), font_color=C([51,51,51]),
             bold=False, font_name=None, ea_font=None,
             alignment=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=None):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame; tf.word_wrap = True
    bodyPr = tf._txBody.find(qn('a:bodyPr'))
    for attr in ['lIns','tIns','rIns','bIns']: bodyPr.set(attr, '45720')
    anchor_map = {MSO_ANCHOR.MIDDLE: 'ctr', MSO_ANCHOR.BOTTOM: 'b', MSO_ANCHOR.TOP: 't'}
    bodyPr.set('anchor', anchor_map.get(anchor, 't'))
    # 使用模板字体配置（如果调用方没传则用默认）
    fn = font_name if font_name is not None else _BODY_FONT
    ef = ea_font if ea_font is not None else _EA_FONT
    lines = text if isinstance(text, list) else [text]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.alignment = alignment
        _apply_font_to_paragraph(p, font_size, font_color, bold, fn, ef)
        if line_spacing:
            pPr = p._p.get_or_add_pPr()
            lnSpc = pPr.makeelement(qn('a:lnSpc'), {})
            lnSpc.append(lnSpc.makeelement(qn('a:spcPct'), {'val': str(int(line_spacing))}))
            pPr.append(lnSpc)
    return tb

def add_oval(slide, l, t, text='', size=Inches(0.45), bg=C([5,28,44]), fg=C([255,255,255])):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, l, t, size, size)
    s.fill.solid(); s.fill.fore_color.rgb = bg; s.line.fill.background()
    _clean_shape(s)
    tf = s.text_frame; tf.word_wrap = False
    bodyPr = tf._txBody.find(qn('a:bodyPr')); bodyPr.set('anchor', 'ctr')
    p = tf.paragraphs[0]; p.text = str(text)
    p.font.size = Pt(int(size / Inches(1) * 14))
    p.font.color.rgb = fg; p.font.bold = True; p.font.name = 'Arial'; p.alignment = PP_ALIGN.CENTER
    if text and p.runs: set_ea_font(p.runs[0])
    return s

def add_action_title(slide, title_text, NAVY):
    add_rect(slide, 0, 0, SW, Inches(0.05), NAVY)
    add_text(slide, LM, Inches(0.2), CONTENT_W, Inches(0.7), title_text,
             font_size=Pt(22), font_color=C([0,0,0]), bold=True, font_name=_HEADING_FONT, anchor=MSO_ANCHOR.MIDDLE)
    add_hline(slide, LM, Inches(1.05), CONTENT_W, C([0,0,0]), Pt(0.5))

def add_source(slide, text='来源：公司数据'):
    add_text(slide, LM, Inches(7.05), CONTENT_W, Inches(0.3), text, font_size=Pt(9), font_color=C([102,102,102]))

def add_page_number(slide, num, total):
    # 封面封底不显示页码（由调用方控制）
    add_text(slide, Inches(12.2), Inches(7.1), Inches(1), Inches(0.3),
             f"{num}/{total}", font_size=Pt(9), font_color=C([102,102,102]), alignment=PP_ALIGN.RIGHT)

def add_bg(slide, color):
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = color

def generate_bar_chart(title, labels, values, color_hex='#006BA6'):
    fig, ax = plt.subplots(figsize=(7, 3.5), dpi=150)
    fig.patch.set_facecolor('white'); ax.set_facecolor('white')
    bars = ax.bar(labels, values, color=color_hex, width=0.55, edgecolor='white', linewidth=1.5)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CCCCCC'); ax.spines['bottom'].set_color('#CCCCCC')
    ax.tick_params(colors='#333333', labelsize=9)
    ax.set_title(title, fontsize=12, fontweight='bold', color='#333333', pad=10)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                f'{val}', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#333333')
    plt.tight_layout()
    buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', transparent=False)
    plt.close(); buf.seek(0); return buf

def generate_pie_chart(labels, values, colors_list):
    fig, ax = plt.subplots(figsize=(5.5, 3.5), dpi=150)
    fig.patch.set_facecolor('white')
    wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.0f%%',
        colors=colors_list, startangle=90, textprops={'fontsize': 10, 'color': '#333333'})
    for at in autotexts: at.set_fontweight('bold')
    plt.tight_layout()
    buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', transparent=False)
    plt.close(); buf.seek(0); return buf

def generate_placeholder_image(text='产品示意图', size=(800, 450)):
    fig, ax = plt.subplots(figsize=(size[0]/100, size[1]/100), dpi=100)
    # 渐变风格背景
    fig.patch.set_facecolor('#F8F9FA'); ax.set_facecolor('#E8F0FE')
    # 装饰性边框
    from matplotlib.patches import FancyBboxPatch
    rect = FancyBboxPatch((0.05, 0.05), 0.9, 0.9, boxstyle='round,pad=0.08',
                           facecolor='#E8F0FE', edgecolor='#006BA6', linewidth=2, linestyle='--')
    ax.add_patch(rect)
    # 主图标
    ax.text(0.5, 0.65, '\u2728', fontsize=28, ha='center', va='center', transform=ax.transAxes)
    ax.text(0.5, 0.5, text, fontsize=14, ha='center', va='center',
            color='#006BA6', fontweight='bold', transform=ax.transAxes)
    ax.text(0.5, 0.32, '\u00a9 可悦PPT', fontsize=9, ha='center', va='center',
            color='#999999', transform=ax.transAxes)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    plt.tight_layout(pad=0)
    buf = io.BytesIO(); plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', transparent=False)
    plt.close(); buf.seek(0); return buf

def full_cleanup(outpath):
    tmppath = outpath + '.tmp'
    with zipfile.ZipFile(outpath, 'r') as zin:
        with zipfile.ZipFile(tmppath, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename.endswith('.xml'):
                    root = etree.fromstring(data)
                    ns_p = 'http://schemas.openxmlformats.org/presentationml/2006/main'
                    ns_a = 'http://schemas.openxmlformats.org/drawingml/2006/main'
                    for style in root.findall(f'.//{{{ns_p}}}style'):
                        style.getparent().remove(style)
                    if 'theme' in item.filename.lower():
                        for tag in ['outerShdw', 'innerShdw', 'scene3d', 'sp3d']:
                            for el in root.findall(f'.//{{{ns_a}}}{tag}'):
                                el.getparent().remove(el)
                    data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
                zout.writestr(item, data)
    os.replace(tmppath, outpath)

# ===== 生成单套模板 =====
def generate_template(cfg):
    NAVY = C(cfg['colors']['primary'])
    ACCENT_BLUE = C(cfg['colors']['accent_blue'])
    ACCENT_GREEN = C(cfg['colors']['accent_green'])
    ACCENT_ORANGE = C(cfg['colors']['accent_orange'])
    ACCENT_RED = C(cfg['colors']['accent_red'])
    LIGHT_BLUE = C([0xE3, 0xF2, 0xFD]); LIGHT_GREEN = C([0xE8, 0xF5, 0xE9])
    LIGHT_ORANGE = C([0xFF, 0xF3, 0xE0]); LIGHT_RED = C([0xFF, 0xEB, 0xEE])
    BG_GRAY = C([0xF2, 0xF2, 0xF2]); LINE_GRAY = C([0xCC, 0xCC, 0xCC])
    DARK_GRAY = C([0x33, 0x33, 0x33]); MED_GRAY = C([0x66, 0x66, 0x66])
    WHITE = C([0xFF, 0xFF, 0xFF])
    BLACK = C([0, 0, 0])
    # 字体配置：从config读取，允许模板覆盖
    # 使用全局变量以便add_text等函数可以访问
    global _HEADING_FONT, _BODY_FONT, _EA_FONT
    cfg_fonts = cfg.get('fonts', {'heading': 'Georgia', 'body': 'Arial', 'ea': 'KaiTi'})
    _HEADING_FONT = cfg_fonts.get('heading', 'Georgia')
    _BODY_FONT = cfg_fonts.get('body', 'Arial')
    _EA_FONT = cfg_fonts.get('ea', 'KaiTi')
    HEADER_SIZE = Pt(28); SUB_HEADER_SIZE = Pt(18); BODY_SIZE = Pt(14); FOOTNOTE_SIZE = Pt(9)

    name = cfg['name']; sections = cfg['sections']; d = cfg['data']
    total_slides = 22; page = 0; section_idx = 0
    section_cn = ['一','二','三','四','五','六','七','八','九']

    prs = Presentation()
    prs.slide_width = SW; prs.slide_height = SH

    def add_page():
        nonlocal page; page += 1
        return prs.slides.add_slide(prs.slide_layouts[BL])

    # ===== 背景装饰系统 =====
    def deco_corner_bl(slide, color, w=Inches(2.5), h=Inches(3.0)):
        """左下角色块装饰"""
        add_rect(slide, Inches(-0.5), SH - h - Inches(0.5), w, h, color)

    def deco_corner_tr(slide, color, w=Inches(3.0), h=Inches(2.0)):
        """右上角色块装饰"""
        add_rect(slide, SW - w + Inches(0.5), Inches(-0.5), w, h, color)

    def deco_circle(slide, cx, cy, r, color):
        """圆形装饰"""
        s = slide.shapes.add_shape(MSO_SHAPE.OVAL, cx - r/2, cy - r/2, r, r)
        s.fill.solid(); s.fill.fore_color.rgb = color; s.line.fill.background()
        _clean_shape(s)

    def deco_lines(slide, color=LINE_GRAY, count=3, spacing=Inches(0.8)):
        """右侧竖线装饰"""
        for i in range(count):
            y = Inches(1.5) + i * spacing
            add_hline(slide, Inches(12.5), y, Inches(0.5), color, Pt(1.0))

    def deco_dots(slide, color=MED_GRAY, cols=4, rows=3, start_x=Inches(11.5), start_y=Inches(5.5), spacing=Inches(0.3)):
        """点阵装饰"""
        for r in range(rows):
            for c in range(cols):
                x = start_x + c * spacing; y = start_y + r * spacing
                dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, Inches(0.06), Inches(0.06))
                dot.fill.solid(); dot.fill.fore_color.rgb = color; dot.line.fill.background()
                _clean_shape(dot)

    def deco_diag_line(slide, color=NAVY):
        """对角线装饰"""
        # 用细矩形模拟对角线
        dx = Inches(0.1); dy = Inches(0.01)
        add_rect(slide, Inches(0.5), Inches(1.0), Inches(12.5), dy, color)

    def deco_bottom_bar(slide, color=NAVY):
        """底部品牌栏"""
        add_rect(slide, 0, Inches(7.0), SW, Inches(0.5), color)

    def deco_top_accent(slide, color=NAVY):
        """顶部装饰条"""
        add_rect(slide, 0, 0, SW, Inches(0.08), color)

    # ===== 版式渲染函数 =====
    def render_cover():
        s = add_page()
        # 左侧2/3深色 + 右侧1/3白色 — 既有高级感又不全黑
        add_bg(s, WHITE)
        add_rect(s, 0, 0, Inches(9.0), SH, NAVY)  # 左侧深色区域
        add_rect(s, 0, 0, SW, Inches(0.06), ACCENT_BLUE)  # 顶部细条
        # 深色区几何装饰
        deco_circle(s, Inches(8.0), Inches(6.0), Inches(3.5), C([26,35,61]))
        deco_circle(s, Inches(5.0), Inches(1.5), Inches(2.0), C([26,35,61]))
        deco_dots(s, color=C([0,150,214]), cols=3, rows=3, start_x=Inches(6.5), start_y=Inches(1.0), spacing=Inches(0.25))
        # 左侧文字
        add_text(s, Inches(1.2), Inches(2.2), Inches(7.0), Inches(1.2), cfg['cover']['title'],
                 font_size=Pt(44), font_color=WHITE, bold=True, font_name=_HEADING_FONT)
        add_text(s, Inches(1.2), Inches(3.6), Inches(7.0), Inches(0.5), cfg['cover']['subtitle'],
                 font_size=Pt(18), font_color=ACCENT_BLUE)
        add_hline(s, Inches(1.2), Inches(4.3), Inches(3.0), C([0,150,214]), Pt(1.5))
        add_text(s, Inches(1.2), Inches(4.6), Inches(7.0), Inches(0.5), cfg['cover']['tagline'],
                 font_size=BODY_SIZE, font_color=C([148,163,184]))
        # 右侧白色区域的品牌信息
        add_text(s, Inches(9.5), Inches(3.0), Inches(3.5), Inches(1.0), 'PPT\nTEMPLATE',
                 font_size=Pt(32), font_color=NAVY, bold=True, font_name=_HEADING_FONT)
        add_hline(s, Inches(9.5), Inches(4.2), Inches(2.0), ACCENT_BLUE, Pt(2))

    def render_toc():
        s = add_page()
        # 左侧装饰条
        add_rect(s, 0, 0, Inches(0.1), SH, NAVY)
        deco_corner_tr(s, NAVY, Inches(2.0), Inches(1.5))
        deco_dots(s, color=NAVY, cols=6, rows=4, start_x=Inches(10.5), start_y=Inches(5.0), spacing=Inches(0.15))
        add_action_title(s, '目录', NAVY)
        iy = Inches(1.6)
        for i, sec in enumerate(sections):
            add_oval(s, LM, iy, str(i+1), bg=NAVY if i%2==0 else ACCENT_BLUE, fg=WHITE)
            add_text(s, LM + Inches(0.7), iy, Inches(4.0), Inches(0.4), sec,
                     font_size=SUB_HEADER_SIZE, font_color=NAVY, bold=True)
            add_text(s, Inches(5.5), iy + Inches(0.05), Inches(6.5), Inches(0.4),
                     f'第{section_cn[i]}部分', font_size=BODY_SIZE, font_color=MED_GRAY)
            iy += Inches(0.65); add_hline(s, LM, iy, CONTENT_W, LINE_GRAY); iy += Inches(0.25)
        add_source(s, '目录结构'); add_page_number(s, page, total_slides)

    def render_section():
        nonlocal section_idx
        s = add_page()
        title = sections[section_idx] if section_idx < len(sections) else '章节'
        sec_idx = min(section_idx, len(section_cn)-1)
        # 白底 + 左侧深色装饰条 — 透气感，不费墨
        add_bg(s, WHITE)
        # 左侧宽装饰条
        add_rect(s, 0, 0, Inches(0.12), SH, NAVY)
        # 底部装饰条
        add_rect(s, 0, SH - Inches(0.08), SW, Inches(0.08), ACCENT_BLUE)
        # 章节号大圆
        add_oval(s, LM, Inches(1.8), str(sec_idx+1), size=Inches(1.5), bg=NAVY, fg=WHITE)
        add_text(s, Inches(3.5), Inches(2.0), Inches(8), Inches(0.6),
                 f'第{section_cn[sec_idx]}部分', font_size=SUB_HEADER_SIZE, font_color=ACCENT_BLUE, font_name=_HEADING_FONT)
        add_text(s, Inches(3.5), Inches(2.8), Inches(8), Inches(1.0),
                 title, font_size=Pt(36), font_color=NAVY, bold=True, font_name=_HEADING_FONT)
        add_hline(s, Inches(3.5), Inches(4.0), Inches(5), LINE_GRAY)
        add_text(s, Inches(3.5), Inches(4.3), Inches(8), Inches(0.5),
                 f'SECTION {section_idx+1}  |  {sections[sec_idx]}', font_size=BODY_SIZE, font_color=MED_GRAY)
        add_page_number(s, page, total_slides)
        section_idx += 1

    def render_big_number():
        s = add_page()
        idx = min(section_idx-1, len(sections)-1) if section_idx > 0 else 0
        add_bg(s, WHITE)
        deco_top_accent(s, NAVY)
        deco_corner_tr(s, C([226,232,240]), Inches(2.5), Inches(2.0))
        deco_dots(s, color=C([148,163,184]), cols=6, rows=5, start_x=Inches(10.5), start_y=Inches(4.5), spacing=Inches(0.15))
        add_action_title(s, f'{sections[idx]}——核心数据说明', NAVY)
        add_rect(s, LM, Inches(1.4), Inches(3.5), Inches(1.8), NAVY)
        big = d['users'] if d['users'] != '—' else d['market_size']
        add_text(s, LM + Inches(0.2), Inches(1.5), Inches(3.1), Inches(0.8),
                 big, font_size=Pt(36), font_color=WHITE, bold=True, font_name=_HEADING_FONT, alignment=PP_ALIGN.CENTER)
        add_text(s, LM + Inches(0.2), Inches(2.3), Inches(3.1), Inches(0.7),
                 '核心指标', font_size=Pt(12), font_color=WHITE, alignment=PP_ALIGN.CENTER)
        big_desc = cfg.get('content', {}).get('big_number_desc', '')
        add_text(s, Inches(5.0), Inches(1.5), Inches(7.5), Inches(2.0),
                 [f'  {d["company_desc"]}', big_desc[:40] if big_desc else f'  {d["vision"]}', f'  {d["tech_advantage"][:35]}'] if big_desc else [f'  {d["company_desc"]}', f'  {d["vision"]}', f'  {d["tech_advantage"][:35]}'],
                 font_size=BODY_SIZE)
        add_rect(s, LM, Inches(4.5), CONTENT_W, Inches(2.2), BG_GRAY)
        add_text(s, LM + Inches(0.3), Inches(4.6), Inches(1.5), Inches(0.4),
                 '核心洞见', font_size=BODY_SIZE, font_color=NAVY, bold=True)
        add_text(s, LM + Inches(0.3), Inches(5.1), CONTENT_W - Inches(0.6), Inches(1.4),
                 [big_desc] if big_desc else [f'{d["tech_advantage"]}', f'团队经验：{d["team_exp"]}', f'增长率：{d["growth_rate"]}'],
                 line_spacing=Pt(800), font_size=BODY_SIZE)
        add_source(s, '来源：公司数据'); add_page_number(s, page, total_slides)

    def render_two_stat():
        s = add_page()
        idx = min(section_idx-1, len(sections)-1) if section_idx > 0 else 0
        add_action_title(s, f'{sections[idx]}——核心对比', NAVY)
        two_desc = cfg.get('content', {}).get('two_stat_desc', [])
        s1_label = two_desc[0].split('，')[0][:8] if len(two_desc) > 0 else '指标一'
        s2_label = two_desc[1].split('，')[0][:8] if len(two_desc) > 1 else '指标二'
        s1 = (d['avg_order'] if d['avg_order'] != '—' else '—', s1_label, True)
        s2 = (d['cac'] if d['cac'] != '—' else '—', s2_label, False)
        sw = Inches(5.5); sg = Inches(0.733)
        for i, (big, small, is_navy) in enumerate([s1, s2]):
            sx = LM + (sw + sg) * i; fill = NAVY if is_navy else BG_GRAY
            bc = WHITE if is_navy else NAVY; sc = WHITE if is_navy else DARK_GRAY
            add_rect(s, sx, Inches(1.8), sw, Inches(2.5), fill)
            add_text(s, sx + Inches(0.3), Inches(2.0), sw - Inches(0.6), Inches(1.0),
                     big, font_size=Pt(36), font_color=bc, bold=True, font_name=_HEADING_FONT, alignment=PP_ALIGN.CENTER)
            add_text(s, sx + Inches(0.3), Inches(3.2), sw - Inches(0.6), Inches(0.5),
                     small, font_size=BODY_SIZE, font_color=sc, alignment=PP_ALIGN.CENTER)
        desc_lines = [d[:50] for d in two_desc] if two_desc else ['收入结构多元化，抗风险能力强', 'LTV/CAC 持续优化，单位经济模型健康']
        add_text(s, LM, Inches(5.0), CONTENT_W, Inches(1.5),
                 desc_lines, font_size=BODY_SIZE, line_spacing=Pt(800))
        add_source(s, '来源：运营数据'); add_page_number(s, page, total_slides)

    def render_three_stat():
        s = add_page()
        idx = min(section_idx-1, len(sections)-1) if section_idx > 0 else 0
        add_action_title(s, f'{sections[idx]}——多维度数据验证增长', NAVY)
        items = [(d['users'], '月活用户', True), (d['gmv'], '季度GMV', False), (d['conversion'], '转化率', False)]
        sw = Inches(3.5); sg = (CONTENT_W - sw * 3) / 2
        for i, (big, small, is_navy) in enumerate(items):
            sx = LM + (sw + sg) * i; fill = NAVY if is_navy else BG_GRAY
            bc = WHITE if is_navy else NAVY; sc = WHITE if is_navy else DARK_GRAY
            add_rect(s, sx, Inches(1.4), sw, Inches(1.8), fill)
            add_text(s, sx + Inches(0.2), Inches(1.5), sw - Inches(0.4), Inches(0.7),
                     big, font_size=HEADER_SIZE, font_color=bc, bold=True, font_name=_HEADING_FONT, alignment=PP_ALIGN.CENTER)
            add_text(s, sx + Inches(0.2), Inches(2.25), sw - Inches(0.4), Inches(0.6),
                     small, font_size=Pt(12), font_color=sc, alignment=PP_ALIGN.CENTER)
        # 根据模板名称生成不同图表数据
        name = cfg['name']
        if '学术' in name or '研究' in name:
            bar_data = [15, 30, 55, 78, 96]
            pie_labels = ['论文', '专利', '数据集', '其他']
            pie_vals = [40, 30, 20, 10]
        elif '文化' in name or '宣导' in name:
            bar_data = [60, 72, 80, 88, 92]
            pie_labels = ['培训', '福利', '活动', '其他']
            pie_vals = [35, 30, 25, 10]
        elif '运营' in name or '报告' in name:
            bar_data = [30, 80, 150, 220, 300]
            pie_labels = ['SaaS', '增值', '广告', '其他']
            pie_vals = [50, 30, 15, 5]
        elif '立项' in name:
            bar_data = [10, 30, 60, 100, 150]
            pie_labels = ['研发', '人力', '设备', '其他']
            pie_vals = [45, 25, 20, 10]
        elif '营销' in name:
            bar_data = [40, 100, 180, 260, 350]
            pie_labels = ['搜索', '信息流', '社交', '其他']
            pie_vals = [35, 30, 25, 10]
        elif '路演' in name or '融资' in name:
            bar_data = [50, 120, 200, 280, 350]
            pie_labels = ['SaaS', '增值', '广告', '其他']
            pie_vals = [55, 25, 15, 5]
        else:
            bar_data = [50, 120, 200, 280, 350]
            pie_labels = ['SaaS', '增值', '广告', '其他']
            pie_vals = [55, 25, 15, 5]
        buf = generate_bar_chart('增长趋势', ['Q1','Q2','Q3','Q4','次年Q1'], bar_data)
        s.shapes.add_picture(buf, LM, Inches(3.8), Inches(6), Inches(3.0))
        buf2 = generate_pie_chart(pie_labels, pie_vals,
                                  ['#006BA6','#007A53','#D46A00','#CCCCCC'])
        s.shapes.add_picture(buf2, Inches(7.5), Inches(3.8), Inches(5), Inches(3.0))
        add_source(s, '来源：后台数据'); add_page_number(s, page, total_slides)

    def render_pillar():
        s = add_page()
        idx = min(section_idx-1, len(sections)-1) if section_idx > 0 else 0
        content_data = cfg.get('content', {})
        p_titles = content_data.get('pillar_titles', ['技术', '产品', '商业'])
        p_tech = content_data.get('pillar_points_tech', [f'{d["patents"]}', '自研AI算法', '数据积累'])
        p_product = content_data.get('pillar_points_product', [f'月活{d["users"]}', f'留存{d["retention"]}', f'NPS {d["nps"]}'])
        p_biz = content_data.get('pillar_points_biz', [f'毛利率{d["gross_margin"]}', f'LTV {d["avg_order"]}', f'回报{d["roi"]}'])
        add_action_title(s, f'{sections[idx]}——{p_titles[0]}构建核心能力' if idx < len(sections) else '核心能力', NAVY)
        pillars = [(p_titles[0], p_tech), (p_titles[1], p_product), (p_titles[2], p_biz)]
        pw = Inches(3.5); pg = (CONTENT_W - pw * 3) / 2
        for i, (title, points) in enumerate(pillars):
            px = LM + (pw + pg) * i
            add_rect(s, px, Inches(1.5), pw, Inches(0.6), NAVY)
            add_text(s, px + Inches(0.15), Inches(1.5), pw - Inches(0.3), Inches(0.6),
                     title, font_size=SUB_HEADER_SIZE, font_color=WHITE, bold=True,
                     anchor=MSO_ANCHOR.MIDDLE, alignment=PP_ALIGN.CENTER)
            add_rect(s, px, Inches(2.1), pw, Inches(4.0), BG_GRAY)
            add_text(s, px + Inches(0.2), Inches(2.3), pw - Inches(0.4), Inches(3.5),
                     [f'  {p}' for p in points], font_size=BODY_SIZE, line_spacing=Pt(1000))
        add_source(s, '来源：公司数据'); add_page_number(s, page, total_slides)

    def render_data_table():
        s = add_page()
        idx = min(section_idx-1, len(sections)-1) if section_idx > 0 else 0
        add_action_title(s, f'{sections[idx]}——多维度对比', NAVY)
        tbl_data = [['维度', '我们', '竞品A', '竞品B', '竞品C'],
                    ['定位', d['company_desc'][:15], '传统方案', '相似方案', '低端方案'],
                    ['技术', f'{d["patents"]}+自研', '人工为主', '半自动化', '无'],
                    ['用户', d['users'], '80万', '50万', '200万'],
                    ['壁垒', f'{d["patents"]}+数据', '品牌', '渠道', '价格']]
        rows, cols = len(tbl_data), len(tbl_data[0])
        tbl = s.shapes.add_table(rows, cols, LM, Inches(1.5), CONTENT_W, Inches(4.5)).table
        for r in range(rows):
            for c in range(cols):
                cell = tbl.cell(r, c); cell.text = tbl_data[r][c]
                for p in cell.text_frame.paragraphs:
                    p.font.size = Pt(11); p.font.name = 'Arial'; p.alignment = PP_ALIGN.CENTER
                    if r == 0: p.font.bold = True; p.font.color.rgb = WHITE
                    else: p.font.color.rgb = DARK_GRAY
                if r == 0: cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
                elif c == 0: cell.fill.solid(); cell.fill.fore_color.rgb = BG_GRAY
                elif c == 1: cell.fill.solid(); cell.fill.fore_color.rgb = LIGHT_BLUE
        add_source(s, '来源：公开信息'); add_page_number(s, page, total_slides)

    def render_timeline():
        s = add_page()
        idx = min(section_idx-1, len(sections)-1) if section_idx > 0 else 0
        add_action_title(s, f'{sections[idx]}——关键里程碑回顾', NAVY)
        add_hline(s, LM + Inches(0.5), Inches(3.0), Inches(10.7), LINE_GRAY, Pt(2))
        ms = [('2023', '启动'), ('2024', '上线'), ('2025', '增长'), ('2026', '盈利'), ('2027', '扩张')]
        spacing = Inches(10.7) / (len(ms) - 1)
        for i, (label, desc) in enumerate(ms):
            mx = LM + Inches(0.5) + spacing * i
            add_oval(s, mx - Inches(0.225), Inches(2.775), str(i+1), bg=NAVY, fg=WHITE)
            add_text(s, mx - Inches(1.0), Inches(2.0), Inches(2.0), Inches(0.5),
                     label, font_size=SUB_HEADER_SIZE, font_color=NAVY, bold=True, alignment=PP_ALIGN.CENTER)
            add_text(s, mx - Inches(1.0), Inches(3.5), Inches(2.0), Inches(1.5),
                     desc, font_size=BODY_SIZE, alignment=PP_ALIGN.CENTER)
        add_source(s, '来源：发展记录'); add_page_number(s, page, total_slides)

    def render_team():
        s = add_page()
        idx = min(section_idx-1, len(sections)-1) if section_idx > 0 else 0
        team_tagline = cfg.get('content', {}).get('team_tagline', f'{d["team_exp"]}行业经验')
        add_action_title(s, f'{sections[idx]}——{team_tagline}', NAVY)
        team = [('CEO', '张明远', '连续创业者', '前阿里高管'),
                ('CTO', '李思远', '技术大牛', '前腾讯总监'),
                ('CMO', '王雨晴', '营销专家', '前字节总监'),
                ('顾问', '陈建国', '行业领袖', '20年经验')]
        cw = Inches(2.7); cg = (CONTENT_W - cw * 4) / 3
        for i, (role, mn, tag, exp) in enumerate(team):
            cx = LM + (cw + cg) * i
            add_rect(s, cx, Inches(1.5), cw, Inches(5.0), BG_GRAY)
            add_oval(s, cx + Inches(0.8), Inches(1.7), '', size=Inches(1.1), bg=NAVY, fg=WHITE)
            add_text(s, cx + Inches(0.15), Inches(3.0), cw - Inches(0.3), Inches(0.4),
                     mn, font_size=SUB_HEADER_SIZE, font_color=NAVY, bold=True, alignment=PP_ALIGN.CENTER)
            add_text(s, cx + Inches(0.15), Inches(3.5), cw - Inches(0.3), Inches(0.3),
                     role, font_size=BODY_SIZE, font_color=MED_GRAY, alignment=PP_ALIGN.CENTER)
            add_hline(s, cx + Inches(0.3), Inches(3.9), cw - Inches(0.6), LINE_GRAY)
            add_text(s, cx + Inches(0.15), Inches(4.1), cw - Inches(0.3), Inches(2.0),
                     [tag, '', exp], font_size=BODY_SIZE, alignment=PP_ALIGN.CENTER)
        add_source(s, '来源：团队简介'); add_page_number(s, page, total_slides)

    def render_finance():
        s = add_page()
        idx = min(section_idx-1, len(sections)-1) if section_idx > 0 else 0
        finance_note = cfg.get('content', {}).get('finance_note', f'{d["breakeven"]}盈亏平衡')
        add_action_title(s, f'{sections[idx]}——{finance_note[:20]}', NAVY)
        f1 = (d['revenue_2026'] if d['revenue_2026'] != '—' else '—', '营收', True)
        f2 = (d['gross_margin'] if d['gross_margin'] != '—' else '—', '毛利率', False)
        for i, (big, small, is_navy) in enumerate([f1, f2]):
            sx = LM + (Inches(5.5) + Inches(0.733)) * i; fill = NAVY if is_navy else BG_GRAY
            bc = WHITE if is_navy else NAVY; sc = WHITE if is_navy else DARK_GRAY
            add_rect(s, sx, Inches(1.4), Inches(5.5), Inches(2.0), fill)
            add_text(s, sx + Inches(0.3), Inches(1.5), Inches(4.9), Inches(0.8),
                     big, font_size=Pt(36), font_color=bc, bold=True, font_name=_HEADING_FONT, alignment=PP_ALIGN.CENTER)
            add_text(s, sx + Inches(0.3), Inches(2.4), Inches(4.9), Inches(0.5),
                     small, font_size=BODY_SIZE, font_color=sc, alignment=PP_ALIGN.CENTER)
        name = cfg['name']
        if '学术' in name:
            fbar_labels = ['2024','2025','2026','2027','2028']
            fbar_vals = [30, 80, 150, 300, 500]
            fpie_labels = ['科研经费','设备','人力','运营','其他']
            fpie_vals = [40, 25, 20, 10, 5]
        elif '文化' in name:
            fbar_labels = ['2024','2025','2026','2027','2028']
            fbar_vals = [200, 350, 500, 650, 800]
            fpie_labels = ['培训','福利','活动','薪酬','其他']
            fpie_vals = [30, 25, 20, 15, 10]
        elif '运营' in name:
            fbar_labels = ['2024','2025','2026','2027','2028']
            fbar_vals = [3000, 4500, 6800, 9000, 12000]
            fpie_labels = ['SaaS','增值','广告','运营','其他']
            fpie_vals = [45, 20, 15, 12, 8]
        elif '立项' in name:
            fbar_labels = ['投入','1年后','2年后','3年后','5年后']
            fbar_vals = [-800, 200, 800, 2000, 5000]
            fpie_labels = ['研发','人力','设备','运营','其他']
            fpie_vals = [40, 25, 15, 12, 8]
        elif '营销' in name:
            fbar_labels = ['2024','2025','2026','2027','2028']
            fbar_vals = [5000, 8000, 12000, 18000, 25000]
            fpie_labels = ['搜索','信息流','社交','内容','其他']
            fpie_vals = [30, 25, 20, 15, 10]
        else:
            fbar_labels = ['2024','2025','2026','2027','2028']
            fbar_vals = [500, 1500, 4500, 12000, 30000]
            fpie_labels = ['研发','市场','人力','运营','其他']
            fpie_vals = [35, 25, 20, 12, 8]
        buf = generate_bar_chart('收入预测', fbar_labels, fbar_vals, '#006BA6')
        s.shapes.add_picture(buf, LM, Inches(3.8), Inches(6), Inches(3.0))
        buf2 = generate_pie_chart(fpie_labels, fpie_vals,
                                  ['#006BA6','#007A53','#D46A00','#C62828','#CCCCCC'])
        s.shapes.add_picture(buf2, Inches(7.5), Inches(3.8), Inches(5), Inches(3.0))
        add_source(s, '来源：财务模型'); add_page_number(s, page, total_slides)

    def render_product_showcase():
        s = add_page()
        idx = min(section_idx-1, len(sections)-1) if section_idx > 0 else 0
        add_action_title(s, f'{sections[idx]}——核心产品解决方案', NAVY)
        img_buf = generate_placeholder_image(f'{name} - 产品架构')
        s.shapes.add_picture(img_buf, LM, Inches(1.4), Inches(5.5), Inches(3.0))
        add_text(s, Inches(7.0), Inches(1.5), Inches(5.5), Inches(0.4),
                 '⚙️ 核心功能', font_size=SUB_HEADER_SIZE, font_color=NAVY, bold=True)
        add_text(s, Inches(7.0), Inches(2.2), Inches(5.5), Inches(2.0),
                 ['  AI智能推荐：转化率提升35%', '  实时协作：效率提升50%', '  数据分析：决策效率60%'],
                 font_size=BODY_SIZE, line_spacing=Pt(800))
        cards = [('A', '精度', f'{d["conversion"]}', True), ('B', '速度', '< 50ms', False), ('C', '覆盖', '95%', False)]
        cw = Inches(3.5); cg = (CONTENT_W - cw * 3) / 2
        for i, (letter, title, desc, is_navy) in enumerate(cards):
            cx = LM + (cw + cg) * i; fill = NAVY if is_navy else BG_GRAY
            tc = WHITE if is_navy else NAVY; dc = WHITE if is_navy else DARK_GRAY
            add_rect(s, cx, Inches(4.8), cw, Inches(1.8), fill)
            add_text(s, cx + Inches(0.2), Inches(4.9), cw - Inches(0.4), Inches(0.4),
                     title, font_size=SUB_HEADER_SIZE, font_color=tc, bold=True, alignment=PP_ALIGN.CENTER)
            add_text(s, cx + Inches(0.2), Inches(5.4), cw - Inches(0.4), Inches(0.5),
                     desc, font_size=BODY_SIZE, font_color=dc, alignment=PP_ALIGN.CENTER)
        add_source(s, '来源：产品文档'); add_page_number(s, page, total_slides)

    def render_comparison():
        s = add_page()
        add_action_title(s, '方案对比分析——两种路径的优劣权衡', NAVY)
        cw = Inches(5.5); cg = Inches(0.733)
        opts = [('方案A：自建', ['投入可控', '周期较长', '成本可控']),
                ('方案B：合作', ['快速启动', '依赖供应商', '成本较低'])]
        for i, (title, points) in enumerate(opts):
            cx = LM + (cw + cg) * i
            add_rect(s, cx, Inches(1.5), cw, Inches(0.6), NAVY)
            add_text(s, cx + Inches(0.15), Inches(1.5), cw - Inches(0.3), Inches(0.6),
                     title, font_size=SUB_HEADER_SIZE, font_color=WHITE, bold=True,
                     anchor=MSO_ANCHOR.MIDDLE, alignment=PP_ALIGN.CENTER)
            add_rect(s, cx, Inches(2.1), cw, Inches(4.0), BG_GRAY)
            add_text(s, cx + Inches(0.3), Inches(2.3), cw - Inches(0.6), Inches(3.5),
                     [f'  {p}' for p in points], font_size=BODY_SIZE, line_spacing=Pt(1000))
        add_source(s, '来源：内部评估'); add_page_number(s, page, total_slides)

    def render_before_after():
        s = add_page()
        add_action_title(s, '从现状到目标——变革路径清晰可见', NAVY)
        hw = Inches(5.0)
        add_rect(s, LM, Inches(1.5), hw, Inches(4.5), BG_GRAY)
        add_text(s, LM + Inches(0.3), Inches(1.6), hw - Inches(0.6), Inches(0.5),
                 '❌ 现状（Before）', font_size=SUB_HEADER_SIZE, font_color=DARK_GRAY, bold=True)
        add_hline(s, LM + Inches(0.3), Inches(2.2), hw - Inches(0.6), LINE_GRAY)
        add_text(s, LM + Inches(0.3), Inches(2.4), hw - Inches(0.6), Inches(3.0),
                 ['效率低下', '成本高昂', '体验差'], font_size=BODY_SIZE, line_spacing=Pt(1000))
        add_text(s, LM + hw + Inches(0.1), Inches(3.2), Inches(1.5), Inches(0.5),
                 '→', font_size=Pt(36), font_color=NAVY, bold=True, alignment=PP_ALIGN.CENTER)
        ax = LM + hw + Inches(1.733)
        add_rect(s, ax, Inches(1.5), hw, Inches(4.5), NAVY)
        add_text(s, ax + Inches(0.3), Inches(1.6), hw - Inches(0.6), Inches(0.5),
                 '✅ 目标（After）', font_size=SUB_HEADER_SIZE, font_color=WHITE, bold=True)
        add_hline(s, ax + Inches(0.3), Inches(2.2), hw - Inches(0.6), WHITE)
        add_text(s, ax + Inches(0.3), Inches(2.4), hw - Inches(0.6), Inches(3.0),
                 ['效率提升50%', '成本降低30%', '体验评分90+'], font_color=WHITE, font_size=BODY_SIZE, line_spacing=Pt(1000))
        add_source(s, '来源：项目规划'); add_page_number(s, page, total_slides)

    def render_scorecard():
        s = add_page()
        add_action_title(s, '综合评估计分——各维度量化评分', NAVY)
        items = [('客户满意度', '92', 0.92), ('产品质量', '85', 0.85),
                 ('交付速度', '78', 0.78), ('创新能力', '65', 0.65)]
        add_text(s, LM, Inches(1.5), Inches(4.0), Inches(0.4), '评估维度',
                 font_size=BODY_SIZE, font_color=MED_GRAY, bold=True)
        add_text(s, Inches(5.0), Inches(1.5), Inches(1.5), Inches(0.4), '得分',
                 font_size=BODY_SIZE, font_color=MED_GRAY, bold=True)
        add_hline(s, LM, Inches(2.0), CONTENT_W, BLACK, Pt(1.0))
        ry = Inches(2.2); bar_max = Inches(5.0)
        for name, score, pct in items:
            add_text(s, LM, ry, Inches(4.0), Inches(0.5), name, font_size=BODY_SIZE)
            add_text(s, Inches(5.0), ry, Inches(1.5), Inches(0.5), score,
                     font_size=BODY_SIZE, font_color=NAVY, bold=True)
            add_rect(s, Inches(7.0), ry + Inches(0.1), bar_max, Inches(0.3), BG_GRAY)
            add_rect(s, Inches(7.0), ry + Inches(0.1), Inches(5.0 * pct), Inches(0.3), NAVY)
            ry += Inches(0.85); add_hline(s, LM, ry, CONTENT_W, LINE_GRAY)
        add_source(s, '来源：综合评估'); add_page_number(s, page, total_slides)

    def render_pyramid():
        s = add_page()
        add_action_title(s, '层级架构——从愿景到执行', NAVY)
        levels = [('愿景', d['vision'], Inches(3.5)), ('战略', d['mission'], Inches(5.0)), ('执行', d['company_desc'], Inches(6.5))]
        for i, (label, desc, w) in enumerate(levels):
            lx = Inches(6.666) - w / 2; ly = Inches(1.8) + Inches(1.5) * i; h = Inches(1.2)
            fill = NAVY if i == 0 else BG_GRAY; tc = WHITE if i == 0 else NAVY
            add_rect(s, lx, ly, w, h, fill)
            add_text(s, lx + Inches(0.2), ly + Inches(0.1), w - Inches(0.4), Inches(0.4),
                     label, font_size=SUB_HEADER_SIZE, font_color=tc, bold=True, alignment=PP_ALIGN.CENTER)
            add_text(s, lx + Inches(0.2), ly + Inches(0.55), w - Inches(0.4), Inches(0.5),
                     desc, font_size=BODY_SIZE, font_color=tc if i == 0 else DARK_GRAY, alignment=PP_ALIGN.CENTER)
        add_source(s, '来源：战略规划'); add_page_number(s, page, total_slides)

    def render_chevron():
        s = add_page()
        content_data = cfg.get('content', {})
        chevron_steps = content_data.get('chevron_steps', [('诊断', '现状评估\n痛点识别'), ('设计', '方案制定\n资源规划'),
                 ('实施', '分阶段落地\n快速迭代'), ('优化', '效果追踪\n持续改进')])
        add_action_title(s, '实施路径——四步走策略', NAVY)
        steps = chevron_steps
        sw = Inches(2.5); sg = (CONTENT_W - sw * len(steps)) / (len(steps) - 1)
        for i, (title, desc) in enumerate(steps):
            sx = LM + (sw + sg) * i; fill = NAVY if i == 0 else BG_GRAY; tc = WHITE if i == 0 else NAVY
            add_rect(s, sx, Inches(2.0), sw, Inches(1.2), fill)
            add_oval(s, sx + Inches(0.1), Inches(2.1), str(i+1),
                     bg=WHITE if i == 0 else NAVY, fg=NAVY if i == 0 else WHITE)
            add_text(s, sx + Inches(0.6), Inches(2.1), sw - Inches(0.8), Inches(1.0),
                     title, font_size=SUB_HEADER_SIZE, font_color=tc, bold=True, anchor=MSO_ANCHOR.MIDDLE)
            add_text(s, sx + Inches(0.1), Inches(3.4), sw - Inches(0.2), Inches(1.5),
                     desc, font_size=BODY_SIZE, alignment=PP_ALIGN.CENTER)
            if i < len(steps) - 1:
                add_text(s, sx + sw + Inches(0.05), Inches(2.3), Inches(0.4), Inches(0.5),
                         '→', font_size=SUB_HEADER_SIZE, font_color=NAVY, bold=True)
        add_source(s, '来源：实施计划'); add_page_number(s, page, total_slides)

    def render_matrix():
        s = add_page()
        add_action_title(s, '四象限分析——战略优先级排序', NAVY)
        mx = LM + Inches(1.5); my = Inches(1.8); cw = Inches(4.5); ch = Inches(2.5)
        add_text(s, mx - Inches(1.3), my + Inches(0.8), Inches(1.1), Inches(0.4),
                 '高影响', font_size=BODY_SIZE, font_color=NAVY, bold=True, alignment=PP_ALIGN.CENTER)
        add_rect(s, mx, my, cw, ch, NAVY)
        add_rect(s, mx + cw + Inches(0.15), my, cw, ch, BG_GRAY)
        add_rect(s, mx, my + ch + Inches(0.15), cw, ch, BG_GRAY)
        add_rect(s, mx + cw + Inches(0.15), my + ch + Inches(0.15), cw, ch, BG_GRAY)
        quads = [('立即执行', WHITE), ('规划推进', DARK_GRAY), ('持续观察', DARK_GRAY), ('低优先级', DARK_GRAY)]
        for qi, (qt, qc) in enumerate(quads):
            qx = mx + (cw + Inches(0.15)) * (qi % 2); qy = my + (ch + Inches(0.15)) * (qi // 2)
            add_text(s, qx + Inches(0.3), qy + Inches(0.3), cw - Inches(0.6), Inches(0.5),
                     qt, font_size=SUB_HEADER_SIZE, font_color=qc, bold=True)
        add_source(s, '来源：战略分析'); add_page_number(s, page, total_slides)

    def render_funnel():
        s = add_page()
        add_action_title(s, '转化漏斗——从曝光到成交', NAVY)
        stages = [('曝光', '100%', Inches(9.5)), ('点击', '15%', Inches(7.5)),
                  ('注册', '8%', Inches(5.5)), ('付费', '3.5%', Inches(3.5))]
        iy = Inches(1.6)
        for label, pct, w in stages:
            add_rect(s, Inches(6.666) - w/2, iy, w, Inches(1.2), NAVY)
            add_text(s, Inches(6.666) - w/2, iy + Inches(0.15), w, Inches(0.4),
                     label, font_size=SUB_HEADER_SIZE, font_color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
            add_text(s, Inches(6.666) - w/2, iy + Inches(0.6), w, Inches(0.4),
                     pct, font_size=BODY_SIZE, font_color=WHITE, alignment=PP_ALIGN.CENTER)
            iy += Inches(1.4)
        add_source(s, '来源：转化数据'); add_page_number(s, page, total_slides)

    def render_quote():
        s = add_page()
        add_rect(s, 0, 0, SW, Inches(0.05), NAVY)
        add_text(s, LM, Inches(2.5), CONTENT_W, Inches(2.5),
                 f'"{d["vision"]}"', font_size=Pt(24), font_color=DARK_GRAY, alignment=PP_ALIGN.CENTER)
        add_hline(s, Inches(5.5), Inches(5.3), Inches(2.3), NAVY, Pt(1.5))
        add_text(s, LM, Inches(5.6), CONTENT_W, Inches(0.5),
                 f'—— {d["company_desc"]}', font_size=BODY_SIZE, font_color=MED_GRAY, alignment=PP_ALIGN.CENTER)
        add_page_number(s, page, total_slides)

    def render_rag():
        s = add_page()
        add_action_title(s, '项目状态总览——红绿灯预警机制', NAVY)
        headers = ['项目', '状态', '进度', '备注']
        widths = [Inches(3.0), Inches(1.5), Inches(2.0), Inches(5.233)]
        hx = LM
        for hdr, w in zip(headers, widths):
            add_text(s, hx, Inches(1.5), w, Inches(0.4), hdr,
                     font_size=BODY_SIZE, font_color=MED_GRAY, bold=True); hx += w
        add_hline(s, LM, Inches(2.0), CONTENT_W, BLACK, Pt(1.0))
        rows = [('产品研发', NAVY, '85%', '按计划'), ('市场推广', MED_GRAY, '60%', '需关注'), ('团队扩招', DARK_GRAY, '30%', '阻塞')]
        ry = Inches(2.2)
        for name, status_color, pct, note in rows:
            add_text(s, LM, ry, Inches(3.0), Inches(0.6), name, font_size=BODY_SIZE)
            add_oval(s, LM + Inches(3.3), ry + Inches(0.05), '', size=Inches(0.35), bg=status_color)
            add_text(s, LM + Inches(4.5), ry, Inches(2.0), Inches(0.6), pct, font_size=BODY_SIZE)
            add_text(s, LM + Inches(6.5), ry, Inches(5.233), Inches(0.6), note, font_size=BODY_SIZE)
            ry += Inches(0.85); add_hline(s, LM, ry, CONTENT_W, LINE_GRAY)
        add_source(s, '来源：项目管理系统'); add_page_number(s, page, total_slides)

    def render_exec_summary():
        s = add_page()
        content_data = cfg.get('content', {})
        es_points = content_data.get('exec_summary_points', [('市场机会', f'市场规模{d["market_size"]}，增长{d["growth_rate"]}'),
                  ('核心优势', d['tech_advantage'][:25]),
                  ('财务展望', f'{d["revenue_2026"]}营收，{d["breakeven"]}盈亏平衡')])
        add_action_title(s, '执行摘要——核心结论汇总', NAVY)
        add_rect(s, LM, Inches(1.4), CONTENT_W, Inches(1.0), NAVY)
        add_text(s, LM + Inches(0.3), Inches(1.4), CONTENT_W - Inches(0.6), Inches(1.0),
                 f'核心结论：{d["company_desc"]}，{d["users"]}用户验证',
                 font_size=SUB_HEADER_SIZE, font_color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        points = [('1', es_points[0][0], es_points[0][1]),
                  ('2', es_points[1][0], es_points[1][1]),
                  ('3', es_points[2][0], es_points[2][1])]
        iy = Inches(2.8)
        for num, title, desc in points:
            add_oval(s, LM, iy, num, bg=NAVY, fg=WHITE)
            add_text(s, LM + Inches(0.6), iy, Inches(3.5), Inches(0.4),
                     title, font_size=BODY_SIZE, font_color=NAVY, bold=True)
            add_text(s, Inches(5.0), iy, Inches(7.5), Inches(0.4),
                     desc, font_size=BODY_SIZE)
            iy += Inches(0.6); add_hline(s, LM, iy, CONTENT_W, LINE_GRAY); iy += Inches(0.3)
        add_source(s, '来源：综合评估'); add_page_number(s, page, total_slides)

    def render_takeaway():
        s = add_page()
        add_action_title(s, '核心发现——数据背后的洞察', NAVY)
        add_text(s, LM, Inches(1.5), Inches(7.5), Inches(0.4),
                 '分析论述', font_size=SUB_HEADER_SIZE, font_color=NAVY, bold=True)
        add_hline(s, LM, Inches(2.0), Inches(7.5), LINE_GRAY)
        add_text(s, LM, Inches(2.2), Inches(7.5), Inches(4.0),
                 [f'{d["company_desc"]}正在快速成长', '', f'核心数据验证了市场需求'], font_size=BODY_SIZE, line_spacing=Pt(800))
        tk_x = Inches(9.0); tk_w = Inches(3.5)
        add_rect(s, tk_x, Inches(1.5), tk_w, Inches(5.0), BG_GRAY)
        add_text(s, tk_x + Inches(0.2), Inches(1.7), tk_w - Inches(0.4), Inches(0.4),
                 '💡 Key Takeaways', font_size=BODY_SIZE, font_color=NAVY, bold=True)
        add_hline(s, tk_x + Inches(0.2), Inches(2.2), tk_w - Inches(0.4), LINE_GRAY)
        add_text(s, tk_x + Inches(0.2), Inches(2.4), tk_w - Inches(0.4), Inches(3.8),
                 ['1. 市场空间广阔', '2. 技术壁垒坚实', '3. 商业模式验证'], font_size=BODY_SIZE, line_spacing=Pt(1000))
        add_source(s, '来源：分析报告'); add_page_number(s, page, total_slides)

    def render_closing():
        s = add_page()
        add_rect(s, 0, 0, SW, Inches(0.05), NAVY)
        add_text(s, LM, Inches(2.0), CONTENT_W, Inches(1.0), 'THANK YOU',
                 font_size=Pt(44), font_color=NAVY, bold=True, font_name=_HEADING_FONT, alignment=PP_ALIGN.CENTER)
        add_hline(s, Inches(5.5), Inches(3.3), Inches(2.3), NAVY, Pt(1.5))
        add_text(s, LM, Inches(3.8), CONTENT_W, Inches(0.6), '期待与您携手共创未来',
                 font_size=Pt(24), font_color=DARK_GRAY, alignment=PP_ALIGN.CENTER)
        add_text(s, LM, Inches(5.0), CONTENT_W, Inches(1.0),
                 '联系方式：[邮箱] | [电话] | [公司地址]', font_size=BODY_SIZE, font_color=MED_GRAY, alignment=PP_ALIGN.CENTER)
        add_hline(s, LM, Inches(6.8), Inches(3), NAVY, Pt(2))

    # ===== Q&A问答页 =====
    def render_qa():
        s = add_page()
        add_bg(s, WHITE)
        deco_top_accent(s, NAVY)
        add_rect(s, 0, 0, Inches(0.08), SH, NAVY)
        add_text(s, LM, Inches(0.3), CONTENT_W, Inches(0.8), 'Q & A',
                 font_size=Pt(36), font_color=NAVY, bold=True, font_name=_HEADING_FONT)
        add_hline(s, LM, Inches(1.2), Inches(3.0), NAVY, Pt(1.5))
        # 左侧常见问题
        qa_left = [('Q1', '项目核心优势是什么？', 'A：技术壁垒+数据积累+团队经验'),
                   ('Q2', '目标市场规模多大？', f'A：市场规模{d["market_size"]}，年增长{d["growth_rate"]}'),
                   ('Q3', '盈利模式是什么？', f'A：{d["company_desc"]}，{d["gross_margin"]}毛利率')]
        qy = Inches(1.8)
        for q_label, question, answer in qa_left:
            add_oval(s, LM, qy, q_label, size=Inches(0.5), bg=NAVY, fg=WHITE)
            add_text(s, LM + Inches(0.7), qy, Inches(5.5), Inches(0.4),
                     question, font_size=Pt(16), font_color=NAVY, bold=True)
            add_text(s, LM + Inches(0.7), qy + Inches(0.45), Inches(5.5), Inches(0.6),
                     answer, font_size=BODY_SIZE, font_color=DARK_GRAY)
            qy += Inches(1.2)
        # 右侧联系信息
        rx = Inches(8.0)
        add_rect(s, rx, Inches(1.8), Inches(4.5), Inches(4.5), BG_GRAY)
        add_text(s, rx + Inches(0.3), Inches(2.0), Inches(3.9), Inches(0.5),
                 '联系我们', font_size=Pt(18), font_color=NAVY, bold=True, alignment=PP_ALIGN.CENTER)
        add_hline(s, rx + Inches(0.5), Inches(2.6), Inches(3.5), LINE_GRAY)
        contact_items = ['邮箱：contact@company.com', '电话：400-888-0000', '地址：北京市海淀区', '官网：www.company.com']
        add_text(s, rx + Inches(0.3), Inches(2.9), Inches(3.9), Inches(2.5),
                 contact_items, font_size=BODY_SIZE, line_spacing=Pt(900))
        add_page_number(s, page, total_slides)

    # ===== 多栏文字页（1/2/3栏可切换） =====
    def render_text_columns():
        s = add_page()
        idx = min(section_idx-1, len(sections)-1) if section_idx > 0 else 0
        add_action_title(s, f'{sections[idx]}——核心要点', NAVY)
        # 3栏内容
        col_data = [
            {'title': '战略方向', 'items': [f'聚焦{d["company_desc"][:20]}', '持续技术创新投入', f'目标{d["market_size"]}市场']},
            {'title': '执行路径', 'items': ['分阶段规模化落地', '数据驱动决策体系', '敏捷迭代快速验证']},
            {'title': '成果预期', 'items': [f'{d["revenue_2026"]}营收目标', f'用户{d["users"]}突破', f'ROI {d["roi"]}回报']},
        ]
        cw = Inches(3.8); cg = (CONTENT_W - cw * 3) / 2
        for i, col in enumerate(col_data):
            cx = LM + (cw + cg) * i
            add_rect(s, cx, Inches(1.5), cw, Inches(0.55), NAVY)
            add_text(s, cx + Inches(0.15), Inches(1.5), cw - Inches(0.3), Inches(0.55),
                     col['title'], font_size=Pt(16), font_color=WHITE, bold=True,
                     anchor=MSO_ANCHOR.MIDDLE, alignment=PP_ALIGN.CENTER)
            add_rect(s, cx, Inches(2.05), cw, Inches(4.5), BG_GRAY)
            add_text(s, cx + Inches(0.2), Inches(2.2), cw - Inches(0.4), Inches(4.0),
                     ['  ' + p for p in col['items']], font_size=BODY_SIZE, line_spacing=Pt(900))
        add_source(s, '来源：内部资料'); add_page_number(s, page, total_slides)

    # ===== 新版式1: 全屏大数字 =====
    def render_mega_number():
        s = add_page()
        idx = min(section_idx-1, len(sections)-1) if section_idx > 0 else 0
        add_rect(s, 0, 0, SW, Inches(0.05), NAVY)
        big = d['users'] if d['users'] != '—' else d['market_size']
        add_text(s, LM, Inches(1.8), CONTENT_W, Inches(2.0),
                 big, font_size=Pt(72), font_color=NAVY, bold=True, font_name=_HEADING_FONT, alignment=PP_ALIGN.CENTER)
        add_hline(s, Inches(5.5), Inches(4.0), Inches(2.3), NAVY, Pt(2))
        big_desc = cfg.get('content', {}).get('big_number_desc', f'累计服务{d["users"]}，年增长{d["growth_rate"]}')
        add_text(s, LM, Inches(4.3), CONTENT_W, Inches(0.8),
                 big_desc, font_size=Pt(20), font_color=DARK_GRAY, alignment=PP_ALIGN.CENTER)
        add_text(s, LM, Inches(5.3), CONTENT_W, Inches(0.6),
                 f'{sections[idx]}',
                 font_size=BODY_SIZE, font_color=MED_GRAY, alignment=PP_ALIGN.CENTER)
        add_page_number(s, page, total_slides)

    # ===== 新版式2: 左右图文 =====
    def render_side_image():
        s = add_page()
        idx = min(section_idx-1, len(sections)-1) if section_idx > 0 else 0
        add_action_title(s, f'{sections[idx]}——核心内容', NAVY)
        # 左侧配图
        img_buf = generate_placeholder_image(f'{name} - 示意图')
        s.shapes.add_picture(img_buf, LM, Inches(1.5), Inches(5.5), Inches(5.0))
        # 右侧文字
        rx = Inches(7.0)
        add_text(s, rx, Inches(1.8), Inches(5.5), Inches(0.5),
                 '要点概述', font_size=SUB_HEADER_SIZE, font_color=NAVY, bold=True)
        add_hline(s, rx, Inches(2.4), Inches(5.0), LINE_GRAY)
        points = [f'  🎯 {d["company_desc"]}', f'  👁️ {d["vision"]}',
                  f'  🏆 {d["tech_advantage"][:25]}', f'  📈 增长{d["growth_rate"]}']
        add_text(s, rx, Inches(2.7), Inches(5.5), Inches(3.5),
                 points, font_size=BODY_SIZE, line_spacing=Pt(900))
        add_source(s, '来源：公司数据')
        add_page_number(s, page, total_slides)

    # ===== 新版式3: 数据墙九宫格 =====
    def render_data_wall():
        s = add_page()
        idx = min(section_idx-1, len(sections)-1) if section_idx > 0 else 0
        add_bg(s, WHITE)
        deco_top_accent(s, NAVY)
        deco_corner_bl(s, C([226,232,240]), Inches(2.0), Inches(2.5))
        deco_lines(s, count=5, spacing=Inches(0.5))
        add_action_title(s, f'{sections[idx]}——核心数据一览', NAVY)
        data_items = [
            (d['users'] if d['users'] != '—' else '—', '用户数'),
            (d['gmv'] if d['gmv'] != '—' else '—', 'GMV'),
            (d['conversion'] if d['conversion'] != '—' else '—', '转化率'),
            (d['revenue_2026'] if d['revenue_2026'] != '—' else '—', '营收'),
            (d['gross_margin'] if d['gross_margin'] != '—' else '—', '毛利率'),
            (d['retention'] if d['retention'] != '—' else '—', '留存率'),
            (d['avg_order'] if d['avg_order'] != '—' else '—', '客单价'),
            (d['growth_rate'] if d['growth_rate'] != '—' else '—', '增长率'),
            (d['nps'] if d['nps'] != '—' else '—', 'NPS'),
        ]
        cw = Inches(3.7); ch = Inches(1.7)
        cg_x = (CONTENT_W - cw * 3) / 2; cg_y = Inches(0.25)
        for i, (val, label) in enumerate(data_items):
            col = i % 3; row = i // 3
            cx = LM + (cw + cg_x) * col
            cy = Inches(1.5) + (ch + cg_y) * row
            fill = NAVY if i % 3 == 0 else BG_GRAY
            bc = WHITE if i % 3 == 0 else NAVY
            sc = WHITE if i % 3 == 0 else DARK_GRAY
            add_rect(s, cx, cy, cw, ch, fill)
            add_text(s, cx + Inches(0.15), cy + Inches(0.2), cw - Inches(0.3), Inches(0.7),
                     val, font_size=Pt(22), font_color=bc, bold=True, font_name=_HEADING_FONT, alignment=PP_ALIGN.CENTER)
            add_text(s, cx + Inches(0.15), cy + Inches(1.0), cw - Inches(0.3), Inches(0.4),
                     label, font_size=Pt(11), font_color=sc, alignment=PP_ALIGN.CENTER)
        add_source(s, '来源：运营数据')
        add_page_number(s, page, total_slides)

    # ===== 版式映射表 =====
    layout_handlers = {
        'cover': render_cover, 'toc': render_toc, 'section': render_section,
        'big_number': render_big_number, 'two_stat': render_two_stat, 'three_stat': render_three_stat,
        'pillar': render_pillar, 'data_table': render_data_table, 'timeline': render_timeline,
        'team': render_team, 'finance': render_finance, 'product_showcase': render_product_showcase,
        'comparison': render_comparison, 'before_after': render_before_after, 'scorecard': render_scorecard,
        'pyramid': render_pyramid, 'chevron': render_chevron, 'matrix': render_matrix,
        'funnel': render_funnel, 'quote': render_quote, 'rag': render_rag,
        'exec_summary': render_exec_summary, 'takeaway': render_takeaway, 'closing': render_closing,
        'mega_number': render_mega_number, 'side_image': render_side_image, 'data_wall': render_data_wall,
        'qa': render_qa, 'text_columns': render_text_columns,
    }

    # ===== 按版式序列生成 =====
    slide_specs = cfg.get('slides', [])
    for spec in slide_specs:
        handler = layout_handlers.get(spec)
        if handler: handler()
        else: print(f'  ⚠️ 未知版式: {spec}')

    # 回退：如果没定义slides
    if not slide_specs:
        render_cover(); render_toc()
        for _ in range(min(len(sections), 9)): render_section()
        render_big_number(); render_two_stat(); render_three_stat()
        render_data_table(); render_timeline(); render_pillar()
        render_team(); render_finance(); render_closing()

    # 统一添加页脚装饰条（母版效果）
    for i, slide in enumerate(prs.slides):
        # 判断是否为封面或封底（第1页和最后1页）
        is_cover = (i == 0)
        is_closing = (i == len(prs.slides) - 1)
        # 底部装饰细条，封面封底保留
        add_rect(slide, 0, Inches(7.35), SW, Inches(0.04), ACCENT_BLUE)

    # 保存 + 清理
    safe_name = name.replace('/', '_').replace('\\', '_').replace(':', '_')
    output_path = os.path.join(output_dir, f'{safe_name}.pptx')
    prs.save(output_path)
    full_cleanup(output_path)
    sz = os.path.getsize(output_path)
    return output_path, sz, len(prs.slides)

# ===== 主流程：批量生成 =====
if __name__ == '__main__':
    config_path = os.path.join(os.path.dirname(__file__), 'ppt_templates_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(f"📦 共 {len(config['templates'])} 套模板配置，开始批量生成...\n")
    for i, cfg in enumerate(config['templates']):
        print(f"{'='*50}")
        print(f"📄 模板 {i+1}/{len(config['templates'])}: {cfg['name']}")
        print(f"{'='*50}")
        output_path, sz, total = generate_template(cfg)
        print(f"\n✅ 生成完成！")
        print(f"📁 {output_path}")
        print(f"📊 {total}页 | {sz/1024:.0f}KB")
        print()
    print(f"{'='*50}")
    print(f"🎉 批量生成全部完成！")
    print(f"📁 输出目录: {output_dir}")
    print(f"📦 共 {len(config['templates'])} 套模板")
    print(f"{'='*50}")