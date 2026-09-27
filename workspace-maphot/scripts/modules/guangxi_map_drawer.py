# -*- coding: utf-8 -*-
"""
GuangxiMapDrawer - 广西专属地图绘制器
专注平陆运河等广西区域题材，展示真实地理信息
"""
import os
import json
import logging
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置中文字体
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
_fonts = ['SimHei', 'Microsoft YaHei', 'Noto Sans SC', 'Arial Unicode MS']
for _f in _fonts:
    try:
        plt.rcParams['font.sans-serif'] = [_f]
        plt.rcParams['axes.unicode_minus'] = False
        break
    except Exception:
        pass


class GuangxiMapDrawer:
    """广西专属地图绘制器"""

    def __init__(self, style="direct"):
        self.style_name = style
        if style == "direct":
            self.bg_color = "#0A0F1A"
            self.text_color = "#FFFFFF"
            self.accent_color = "#00D4FF"
            self.sub_color = "#FFD740"
            self.province_base = "#1A2744"
            self.province_edge = "#2E4A7A"
            self.highlight_fill = "#00D4FF"
            self.highlight_edge = "#FFFFFF"
        else:
            self.bg_color = "#0A0F1A"
            self.text_color = "#FFFFFF"
            self.accent_color = "#00D4FF"
            self.sub_color = "#FFD740"
            self.province_base = "#1A2744"
            self.province_edge = "#2E4A7A"
            self.highlight_fill = "#00D4FF"
            self.highlight_edge = "#FFFFFF"

    def _load_guangxi_geojson(self):
        """从全国GeoJSON中提取广西"""
        paths = [
            os.path.join(BASE_DIR, 'data', 'cache', 'geojson', 'china.geojson'),
            os.path.join(BASE_DIR, 'data', 'cache', 'geojson', '中国.geojson'),
            os.path.join(BASE_DIR, 'data', 'cache', 'geojson', 'china_full.geojson'),
        ]
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    for feat in data.get('features', []):
                        name = feat.get('properties', {}).get('name', '')
                        if '广西' in name or name == '广西壮族自治区':
                            return {'type': 'FeatureCollection', 'features': [feat]}
                except Exception as e:
                    logger.warning(f"加载GeoJSON失败: {e}")
        return None

    def draw(self, output_path=None, title=None, subtitle=None, 
             canal_points=None, city_points=None, labels=None):
        """
        绘制广西地图 + 平陆运河路线
        
        Args:
            canal_points: 运河关键节点 [(lon, lat, label), ...]
            city_points: 城市点位 [(lon, lat, name, type), ...]
            labels: 额外标注 [(lon, lat, text, color, fontsize), ...]
        """
        geojson = self._load_guangxi_geojson()
        if not geojson:
            logger.error("无法加载广西GeoJSON")
            return None

        fig = plt.figure(figsize=(1080/100, 1920/100), dpi=100, facecolor=self.bg_color)
        ax = fig.add_axes([0, 0, 1.0, 1.0])
        ax.set_facecolor(self.bg_color)
        ax.axis('off')

        # 提取广西边界坐标
        features = geojson.get('features', [])
        all_lons, all_lats = [], []
        for feat in features:
            geom = feat['geometry']
            coords = geom['coordinates']
            for poly in coords:
                for ring in poly:
                    for pt in ring:
                        all_lons.append(pt[0])
                        all_lats.append(pt[1])

        # 计算广西中心区域（裁剪掉南海诸岛）
        lons_main = [l for l in all_lons if l < 115]  # 排除南海
        lats_main = [la for la in all_lats if la > 20]  # 排除南海
        if lons_main and lats_main:
            lon_min, lon_max = min(lons_main), max(lons_main)
            lat_min, lat_max = min(lats_main), max(lats_main)
            margin_lon = (lon_max - lon_min) * 0.15
            margin_lat = (lat_max - lat_min) * 0.15
            ax.set_xlim(lon_min - margin_lon, lon_max + margin_lon)
            ax.set_ylim(lat_min - margin_lat, lat_max + margin_lat)
        else:
            ax.set_xlim(105, 112)
            ax.set_ylim(20.5, 26.5)

        ax.set_aspect('equal')

        # 绘制广西边界
        for feat in features:
            geom = feat['geometry']
            coords = geom['coordinates']
            for poly in coords:
                for ring in poly:
                    pts = np.array(ring)
                    # 只绘制 mainland 部分（排除南海小岛屿）
                    if hasattr(pts, '__len__') and len(pts) > 0:
                        if all(float(x) < 115 for x in pts[:, 0]) and all(float(y) > 20 for y in pts[:, 1]):
                            ax.fill(pts[:, 0], pts[:, 1], 
                                   facecolor=self.province_base,
                                   edgecolor=self.province_edge,
                                   linewidth=1.5, alpha=0.9)

        # 绘制运河路线（蓝色虚线）
        if canal_points:
            canal_lons = [p[0] for p in canal_points]
            canal_lats = [p[1] for p in canal_points]
            # 平滑曲线
            from scipy.interpolate import make_interp_spline
            try:
                x_smooth = np.linspace(min(canal_lons), max(canal_lons), 200)
                y_smooth = make_interp_spline(canal_lons, canal_lats, k=3)(x_smooth)
                ax.plot(x_smooth, y_smooth, color=self.accent_color, 
                       linewidth=3, alpha=0.9, linestyle='-', zorder=10)
                # 发光效果
                ax.plot(x_smooth, y_smooth, color='#00D4FF', 
                       linewidth=8, alpha=0.15, zorder=9)
            except Exception:
                ax.plot(canal_lons, canal_lats, color=self.accent_color,
                       linewidth=3, alpha=0.9, zorder=10)

        # 标注城市
        if city_points:
            for lon, lat, name, ptype in city_points:
                if ptype == '起点':
                    color = '#00D4FF'
                    size = 12
                elif ptype == '终点':
                    color = '#FFD740'
                    size = 12
                else:
                    color = '#FFFFFF'
                    size = 9
                ax.scatter(lon, lat, s=100, color=color, alpha=0.8, zorder=11)
                ax.text(lon, lat + 0.15, name, fontsize=size, 
                       color='white', ha='center', va='bottom',
                       fontweight='bold', zorder=12,
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='#0A0F1Acc', 
                                edgecolor=color, linewidth=0.5))

        # 标注运河节点
        if canal_points:
            for i, (lon, lat, label) in enumerate(canal_points):
                if i == 0:
                    marker = '▶'
                elif i == len(canal_points) - 1:
                    marker = '■'
                else:
                    marker = '●'
                ax.text(lon, lat, marker, fontsize=14, color=self.accent_color,
                       ha='center', va='center', zorder=13)
                ax.text(lon, lat - 0.25, label, fontsize=9, color=self.sub_color,
                       ha='center', va='top', zorder=13)

        # 额外标注
        if labels:
            for lon, lat, text, color, fontsize in labels:
                ax.text(lon, lat, text, fontsize=fontsize, color=color,
                       ha='center', va='center', zorder=12,
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='#0A0F1Acc'))

        # 标题
        if title:
            ax.text(0.5, 0.97, title, fontsize=26, fontweight='bold',
                   color='white', ha='center', va='top',
                   transform=ax.transAxes, zorder=100)
        if subtitle:
            ax.text(0.5, 0.93, subtitle, fontsize=13,
                   color=self.sub_color, ha='center', va='top',
                   transform=ax.transAxes, zorder=100)

        # 底部信息栏
        fig.add_artist(mpatches.Rectangle(
            (0.02, 0.01), 0.96, 0.12,
            facecolor='#0D1525', edgecolor='#1E3A5F', linewidth=1,
            transform=fig.transFigure
        ))
        fig.text(0.5, 0.08, '平陆运河 · 南宁横州 → 钦州茅尾海', fontsize=11,
                color='#8899AA', ha='center', va='center',
                transform=fig.transFigure)
        fig.text(0.5, 0.04, '全长134.2公里 | 19座梯级船闸 | 总投资507亿元', fontsize=10,
                color=self.accent_color, ha='center', va='center',
                transform=fig.transFigure)

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            fig.savefig(output_path, dpi=100, facecolor=self.bg_color, pad_inches=0)
            plt.close(fig)
            logger.info(f"广西地图已保存: {output_path}")
            return output_path

        plt.close(fig)
        return None


if __name__ == '__main__':
    drawer = GuangxiMapDrawer(style='direct')
    
    # 平陆运河关键节点坐标（真实地理坐标）
    canal_points = [
        (109.95, 22.85, '西津渡口'),    # 起点：南宁横州西津渡口
        (109.60, 22.50, '平塘江口'),    # 平塘江口枢纽
        (109.20, 22.20, '马道口水闸'),  # 马道口
        (108.90, 21.90, '青年渠首'),    # 青年渠首
        (108.65, 21.70, '竹巴滩'),      # 竹巴滩
        (108.60, 21.85, '茅尾海'),      # 终点：钦州茅尾海
    ]
    
    city_points = [
        (108.35, 22.82, '南宁', '省会'),
        (109.95, 22.85, '横州', '起点'),
        (108.60, 21.85, '钦州', '终点'),
    ]
    
    labels = [
        (107.5, 23.5, '西江航道', '#66BBFF', 10),
        (109.0, 21.5, '钦江入海口', '#66BBFF', 10),
        (108.0, 21.0, '北部湾', '#00D4FF', 12),
    ]
    
    out = os.path.join(BASE_DIR, 'data', 'maps', '20260917', 'pinglu_canal_guangxi.png')
    result = drawer.draw(
        output_path=out,
        title='平陆运河 · 西南出海新通道',
        subtitle='新中国成立以来第一条江海连通超级运河',
        canal_points=canal_points,
        city_points=city_points,
        labels=labels
    )
    print('Result:', result)
    if result:
        print('Size:', os.path.getsize(result), 'bytes')
