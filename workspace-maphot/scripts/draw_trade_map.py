# -*- coding: utf-8 -*-
"""
绘制中国贸易朋友圈全球分布图
输出: 1080x1920 竖屏 PNG
"""
import os, sys, json
import math
import numpy as np
from io import BytesIO

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, FancyBboxPatch
import matplotlib.patheffects as pe

# 配置中文字体
font_path = 'C:/Windows/Fonts/simhei.ttf'
if os.path.exists(font_path):
    font_manager.fontManager.addfont(font_path)
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, 'scripts', 'modules'))

# 加载贸易伙伴数据
with open(os.path.join(BASE_DIR, 'data', 'materials', 'trade_partners.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

partners = data['partners']
china_center = data['china_center']

# 创建画布 1080x1920
fig = plt.figure(figsize=(10.8, 19.2), dpi=100)
fig.patch.set_facecolor('#0a0e27')  # 深空蓝背景
ax = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor('#0a0e27')

# 移除坐标轴
ax.set_xlim(-180, 180)
ax.set_ylim(-60, 80)
ax.set_aspect('auto')
ax.axis('off')

# 颜色映射
GROUP_COLORS = {
    'RCEP': '#FF6B6B',      # 珊瑚红 - 核心
    '自贸协定': '#4ECDC4',   # 青绿
    '重要伙伴': '#FFE66D',   # 金黄
    '欧盟': '#A8E6CF',       # 薄荷绿
    '金砖国家': '#DDA0DD',   # 梅红
    '东盟对话伙伴': '#87CEEB', # 天蓝
    '上合组织': '#98D8C8',   # 青灰
}

# 绘制世界地图轮廓（简化版 - 用网格点表示大陆）
def draw_simplified_continents(ax):
    """绘制简化大陆轮廓"""
    continents = [
        # 北美洲
        [(-130, 50), (-100, 60), (-80, 70), (-60, 50), (-65, 45), (-80, 30), (-100, 20), (-120, 30), (-130, 50)],
        # 南美洲
        [(-80, 10), (-60, 10), (-40, -5), (-35, -20), (-40, -35), (-55, -55), (-70, -55), (-75, -40), (-70, -20), (-80, 0), (-80, 10)],
        # 欧洲
        [(-10, 60), (10, 70), (30, 70), (40, 65), (40, 55), (30, 45), (10, 35), (-10, 35), (-10, 60)],
        # 非洲
        [(-20, 35), (10, 35), (40, 30), (50, 10), (45, -5), (35, -35), (20, -35), (10, -20), (-10, -5), (-20, 10), (-20, 35)],
        # 亚洲
        [(40, 70), (80, 70), (120, 70), (140, 60), (140, 45), (130, 35), (100, 30), (80, 25), (60, 25), (40, 30), (40, 70)],
        # 澳大利亚
        [(115, -15), (150, -15), (155, -25), (150, -35), (130, -38), (115, -30), [115, -15]],
    ]
    
    for cont in continents:
        lons = [p[0] for p in cont]
        lats = [p[1] for p in cont]
        ax.fill(lons, lats, color='#1a1f3a', alpha=0.8, edgecolor='#2a3050', linewidth=0.5)

draw_simplified_continents(ax)

# 绘制中国（突出显示）
china_lon = [73, 135, 135, 73, 73]
china_lat = [18, 18, 54, 54, 18]
ax.fill(china_lon, china_lat, color='#e74c3c', alpha=0.6, edgecolor='#ff6b6b', linewidth=2)

# 绘制贸易伙伴点
for p in partners:
    lon, lat = p['lon'], p['lat']
    color = GROUP_COLORS.get(p['group'], '#ffffff')
    size = 30 + math.sqrt(p['trade_billion']) * 2
    
    circle = Circle((lon, lat), size, facecolor=color, alpha=0.8, edgecolor='white', linewidth=0.5)
    ax.add_patch(circle)
    
    # 标签（仅对大贸易额国家）
    if p['trade_billion'] > 500:
        ax.text(lon, lat + 3, p['name'], fontsize=7, color='white', 
                ha='center', va='bottom', alpha=0.9)

# 绘制从中国出发的飞线（到关键伙伴）
key_partners = [p for p in partners if p['trade_billion'] > 1000]
for p in key_partners:
    # 使用二次贝塞尔曲线
    clon, clat = china_center['lon'], china_center['lat']
    lon, lat = p['lon'], p['lat']
    
    # 控制点（拱起效果）
    ctrl_lon = (clon + lon) / 2
    ctrl_lat = max(clat, lat) + 15
    
    t = np.linspace(0, 1, 50)
    bezier_x = (1-t)**2 * clon + 2*(1-t)*t * ctrl_lon + t**2 * lon
    bezier_y = (1-t)**2 * clat + 2*(1-t)*t * ctrl_lat + t**2 * lat
    
    color = GROUP_COLORS.get(p['group'], '#ffffff')
    ax.plot(bezier_x, bezier_y, color=color, alpha=0.4, linewidth=1)

# 添加标题区域
ax.text(0, 85, '中国贸易朋友圈', fontsize=28, color='white', 
        ha='center', va='center', fontweight='bold')
ax.text(0, 78, '加速扩容至160+个国家和地区', fontsize=14, color='#FFE66D', 
        ha='center', va='center')

# 添加统计信息
stats_text = f"贸易伙伴: {data['total_partners']}个 | RCEP: {data['rcep_count']}国 | 自贸协定: {data['fta_count']}国"
ax.text(0, 73, stats_text, fontsize=10, color='white', 
        ha='center', va='center', alpha=0.8)

# 添加图例
legend_y = -55
legend_items = [
    ('RCEP成员国', '#FF6B6B'),
    ('自贸协定伙伴', '#4ECDC4'),
    ('重要贸易伙伴', '#FFE66D'),
    ('欧盟', '#A8E6CF'),
    ('金砖国家', '#DDA0DD'),
]
for i, (label, color) in enumerate(legend_items):
    x = -50 + i * 22
    ax.plot(x, legend_y, 'o', color=color, markersize=10)
    ax.text(x, legend_y - 4, label, fontsize=7, color='white', 
            ha='center', va='top', alpha=0.8)

# 数据来源
ax.text(0, -58, '数据来源: 商务部、海关总署、IMF', fontsize=7, color='#888888', 
        ha='center', va='top', alpha=0.6)

# 保存图片
output_path = os.path.join(BASE_DIR, 'data', 'maps', 'trade_circle_map.png')
os.makedirs(os.path.dirname(output_path), exist_ok=True)
fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#0a0e27')
plt.close(fig)

print(f"地图已保存: {output_path}")
print(f"文件大小: {os.path.getsize(output_path) / 1024:.1f} KB")
