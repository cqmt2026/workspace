# -*- coding: utf-8 -*-
"""
Province Map Drawer - 省级地图绘制模块
职责:绘制省级行政区划地图,支持数据驱动配色、排名图、高亮指定省份
"""
import os
import json
import logging
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.cm as cm
import matplotlib.font_manager as fm

# 设置中文字体
_CN_FONT_CANDIDATES = ['SimHei', 'Microsoft YaHei', 'Noto Sans SC']
_CN_FONT = None
for fname in _CN_FONT_CANDIDATES:
    try:
        _CN_FONT = fm.FontProperties(family=fname)
        plt.rcParams['font.sans-serif'] = [fname]
        plt.rcParams['axes.unicode_minus'] = False
        _CN_FONT = fname
        break
    except:
        continue

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ProvinceMapDrawer:
    """省级地图绘制器"""

    def __init__(self, style="default"):
        """
        Args:
            style: 风格名称,从 style_config 加载,或 'direct' 使用直接参数
        """
        self.style_name = style

        if style == "direct":
            # 直接参数模式(兼容旧代码)
            self.bg_color = "#0D0D17"
            self.text_color = "#FFFFFF"
            self.accent_color = "#FF4500"
            self.sub_color = "#FFA07A"
            self.province_base = "#2B1A10"
            self.province_edge = "#8B4513"
            self.highlight_fill = "#FF4500"
            self.highlight_edge = "#FFA500"
            self.data_color = "#FFD700"
            self.rank_color = "#FF6347"
            self.highlight_colors = ["#FF4500", "#FF6347", "#FF8C00", "#FFA500", "#FFD700"]
            self.heatmap_cmap = LinearSegmentedColormap.from_list(
                'aging', ['#0D0D17', '#2B1A10', '#FF4500', '#FF8C00', '#FFD700']
            )
        else:
            # 从风格配置加载
            self._load_from_style_config(style)

    def _load_from_style_config(self, style_name: str):
        """从 style_config 加载配色"""
        from style_config import get_style_config
        cfg = get_style_config(style_name)

        self.bg_color = cfg.get('bg_color', "#0D0D17")
        self.text_color = cfg.get('text_color', "#FFFFFF")
        self.accent_color = cfg.get('accent_color', "#FF4500")
        self.sub_color = cfg.get('sub_color', "#FFA07A")
        self.province_base = cfg.get('province_base', "#2B1A10")
        self.province_edge = cfg.get('province_edge', "#8B4513")
        self.highlight_fill = cfg.get('highlight_fill', "#FF4500")
        self.highlight_edge = cfg.get('highlight_edge', "#FFA500")
        self.data_color = cfg.get('data_color', "#FFD700")
        self.rank_color = cfg.get('rank_color', "#FF6347")
        self.highlight_colors = cfg.get('highlight_colors', ["#FF4500", "#FF6347", "#FF8C00", "#FFA500", "#FFD700"])

        # 热力图配色
        cmap_name = cfg.get('heatmap_cmap', 'hot')
        try:
            self.heatmap_cmap = cm.get_cmap(cmap_name)
        except:
            self.heatmap_cmap = LinearSegmentedColormap.from_list(
                'custom', [self.bg_color, self.province_base, self.highlight_fill, self.data_color]
            )

    def _load_geojson(self):
        """加载全国GeoJSON"""
        path = os.path.join(BASE_DIR, 'data', 'cache', 'geojson', '中国.geojson')
        if not os.path.exists(path):
            path = os.path.join(BASE_DIR, 'data', 'cache', 'geojson', 'china.geojson')
        if not os.path.exists(path):
            logger.warning("Province GeoJSON not found")
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error("加载GeoJSON失败: {}".format(e))
            return None

    def _name_mapping(self):
        return {
            '北京市': '北京', '天津市': '天津', '上海市': '上海', '重庆市': '重庆',
            '河北省': '河北', '山西省': '山西', '辽宁省': '辽宁', '吉林省': '吉林',
            '黑龙江省': '黑龙江', '江苏省': '江苏', '浙江省': '浙江', '安徽省': '安徽',
            '福建省': '福建', '江西省': '江西', '山东省': '山东', '河南省': '河南',
            '湖北省': '湖北', '湖南省': '湖南', '广东省': '广东', '海南省': '海南',
            '四川省': '四川', '贵州省': '贵州', '云南省': '云南', '陕西省': '陕西',
            '甘肃省': '甘肃', '青海省': '青海', '台湾省': '台湾',
            '内蒙古自治区': '内蒙古', '广西壮族自治区': '广西',
            '西藏自治区': '西藏', '宁夏回族自治区': '宁夏', '新疆维吾尔自治区': '新疆',
            '香港特别行政区': '香港', '澳门特别行政区': '澳门',
        }

    def _reverse_mapping(self):
        return {v: k for k, v in self._name_mapping().items()}

    def _get_province_center(self, geojson, geo_name):
        for feat in geojson.get('features', []):
            if feat.get('properties', {}).get('name', '') == geo_name:
                geom = feat['geometry']
                coords = geom['coordinates']
                geom_type = geom['type']
                all_pts = []
                if geom_type == 'Polygon':
                    for ring in coords:
                        all_pts.extend(ring)
                elif geom_type == 'MultiPolygon':
                    for poly in coords:
                        for ring in poly:
                            all_pts.extend(ring)
                if all_pts:
                    pts = np.array(all_pts)
                    return pts.mean(axis=0)
        return None

    def _load_terrain_shading(self, ax, extent):
        """叠加地形阴影底图,提升信息密度
        优先使用真实SRTM DEM数据,没有则使用模拟数据
        """
        try:
            dem_path = os.path.join(BASE_DIR, 'data', 'cache', 'dem', 'china_shaded_relief.npy')

            if os.path.exists(dem_path):
                # 使用真实SRTM DEM数据
                shaded = np.load(dem_path)
                # 真实数据需要resize到地图范围
                from scipy.ndimage import zoom
                ny, nx = 300, int(300 * (extent[1] - extent[0]) / (extent[3] - extent[2]))
                nx = max(200, min(500, nx))
                factor_y = ny / shaded.shape[0]
                factor_x = nx / shaded.shape[1]
                shaded_resized = zoom(shaded, (factor_y, factor_x), order=1)
                ax.imshow(shaded_resized, extent=extent, cmap='gray',
                         alpha=0.15, zorder=0, aspect='auto')
                logger.info(f"真实SRTM地形阴影已叠加 (来源: AWS Open Data Terrarium z=10)")
                return True
            else:
                # 生成简易地形阴影(模拟数据)
                x = np.linspace(extent[0], extent[1], 200)
                y = np.linspace(extent[2], extent[3], 300)
                X, Y = np.meshgrid(x, y)

                Z = np.zeros_like(X)
                Z += 4000 * np.exp(-((X - 85)**2 / 200 + (Y - 32)**2 / 150))
                Z += 1500 * np.exp(-((X - 114)**2 / 10 + (Y - 38)**2 / 20))
                Z += 2000 * np.exp(-((X - 108)**2 / 30 + (Y - 34)**2 / 5))
                Z += 1000 * np.exp(-((X - 100)**2 / 20 + (Y - 25)**2 / 15))
                Z += np.random.randn(*Z.shape) * 50
                Z = np.clip(Z, 0, 8000)

                dx, dy = np.gradient(Z)
                shaded = np.sin(np.arctan(np.sqrt(dx*dx + dy*dy))) * 0.5 + 0.3
                shaded = np.clip(shaded, 0, 1)

                ax.imshow(shaded, extent=extent, cmap='gray',
                         alpha=0.12, zorder=0, aspect='auto')
                logger.info("模拟地形阴影已叠加(无真实DEM数据)")

                os.makedirs(os.path.dirname(dem_path), exist_ok=True)
                np.save(dem_path, shaded)
                return True
        except Exception as e:
            logger.warning(f"地形阴影叠加失败(跳过): {e}")
            return False

    def _auto_zoom(self, ax, features):
        """自动缩放,让地图填满1080x1920竖屏

        策略:用set_aspect('equal')保持地图比例正确,
        然后调整ax.set_position让地图在竖屏中居中且填满宽度。
        """
        all_x, all_y = [], []
        for feat in features:
            geom = feat['geometry']
            coords = geom['coordinates']
            geom_type = geom['type']
            if geom_type == 'Polygon':
                for ring in coords:
                    for pt in ring:
                        all_x.append(pt[0])
                        all_y.append(pt[1])
            elif geom_type == 'MultiPolygon':
                for poly in coords:
                    for ring in poly:
                        for pt in ring:
                            all_x.append(pt[0])
                            all_y.append(pt[1])

        if all_x:
            margin = 0.02
            x_min, x_max = min(all_x), max(all_x)
            y_min, y_max = min(all_y), max(all_y)
            x_range = x_max - x_min
            y_range = y_max - y_min

            x_min -= x_range * margin
            x_max += x_range * margin
            y_min -= y_range * margin
            y_max += y_range * margin

            # 计算地图数据宽高比
            map_aspect = (x_max - x_min) / (y_max - y_min)
            target_aspect = 1080 / 1920

            if map_aspect > target_aspect:
                # 地图太宽:扩展y范围
                new_y_range = (x_max - x_min) / target_aspect
                y_center = (y_min + y_max) / 2
                y_min = y_center - new_y_range / 2
                y_max = y_center + new_y_range / 2

            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)
            ax.set_aspect('equal')
            # 全屏铺满
            ax.set_position([0, 0, 1, 1])

    def draw_rank_map(self, provinces_data, output_path=None, title=None):
        """绘制全国省份排名热力图(全屏布局,比例对齐1080x1920)"""
        geojson = self._load_geojson()
        if not geojson:
            logger.error("无法加载GeoJSON")
            return None

        fig = plt.figure(figsize=(1080/100, 1920/100), dpi=100, facecolor=self.bg_color)
        ax = fig.add_axes([0, 0, 1.0, 1.0])
        ax.set_facecolor(self.bg_color)
        ax.axis('off')

        data_map = {}
        for p in provinces_data:
            data_map[p['name']] = p

        values = []
        for p in provinces_data:
            v = p.get('data1', '0%')
            try:
                values.append(float(v.replace('%', '')))
            except:
                values.append(0)
        v_min, v_max = min(values), max(values) if values else (0, 1)
        v_range = v_max - v_min if v_max != v_min else 1

        rev_map = self._reverse_mapping()

        for feat in geojson.get('features', []):
            geo_name = feat.get('properties', {}).get('name', '')
            data_name = self._name_mapping().get(geo_name, geo_name)
            geom = feat['geometry']
            coords = geom['coordinates']
            geom_type = geom['type']

            if data_name in data_map:
                p = data_map[data_name]
                v = float(p['data1'].replace('%', ''))
                norm = (v - v_min) / v_range if v_range > 0 else 0.5
                color = self.heatmap_cmap(norm)
                edge = 'white'
                lw = 0.8
            else:
                color = self.province_base
                edge = self.province_edge
                lw = 0.3

            if geom_type == 'Polygon':
                for ring in coords:
                    pts = np.array(ring)
                    ax.fill(pts[:, 0], pts[:, 1], facecolor=color,
                            edgecolor=edge, linewidth=lw, alpha=0.95)
            elif geom_type == 'MultiPolygon':
                for poly in coords:
                    for ring in poly:
                        pts = np.array(ring)
                        ax.fill(pts[:, 0], pts[:, 1], facecolor=color,
                                edgecolor=edge, linewidth=lw, alpha=0.95)

        # 自动缩放,让地图填满竖屏
        self._auto_zoom(ax, geojson.get('features', []))

        for p in provinces_data:
            name = p['name']
            geo_name = rev_map.get(name, name)
            center = self._get_province_center(geojson, geo_name)
            if center is not None:
                if transparent_bg:
                    ax.text(center[0], center[1] + 0.8, name,
                            fontsize=28, ha='center', va='bottom',
                            color='white', fontweight='bold',
                            bbox=dict(boxstyle='round,pad=0.4', facecolor='#00000077',
                                      edgecolor='none'))
                    ax.text(center[0], center[1] - 0.8, p['data1'],
                            fontsize=30, ha='center', va='top',
                            color='#FF6B6B', fontweight='bold',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='#00000066',
                                      edgecolor='none'))
                else:
                    ax.text(center[0], center[1] + 0.8, name,
                            fontsize=20, ha='center', va='bottom',
                            color=self.text_color, fontweight='bold',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='#0F1923CC',
                                      edgecolor='none', alpha=0.8))
                    ax.text(center[0], center[1] - 0.8, p['data1'],
                            fontsize=22, ha='center', va='top',
                        color='#F0883E', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='#0F1923AA',
                                  edgecolor='none', alpha=0.7))

        # 标题 overlay(直接用ax.text,放在地图轴内)
        if title:
            ax.text(0.5, 0.95, title, fontsize=28, fontweight='bold',
                    color=self.text_color, ha='center', va='center',
                    transform=ax.transAxes, zorder=100)

        # 色标 overlay
        legend_ax = fig.add_axes([0.15, 0.01, 0.70, 0.02])
        legend_ax.axis('off')
        gradient = np.linspace(0, 1, 256).reshape(1, -1)
        legend_ax.imshow(gradient, aspect='auto', cmap=self.heatmap_cmap,
                         extent=[v_min, v_max, 0, 1])
        legend_ax.set_xlim(v_min, v_max)
        legend_ax.tick_params(colors=self.text_color, labelsize=8)
        legend_ax.set_xlabel('老龄化率(%)', color=self.sub_color, fontsize=9)

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            fig.savefig(output_path, dpi=100, facecolor=self.bg_color,
                       pad_inches=0.1)
            plt.close(fig)
            logger.info("排名地图已保存: {}".format(output_path))
            return output_path

        plt.close(fig)
        return None

    def draw_province_map(self, provinces_data, highlight_name=None, output_path=None, data_label=None, transparent_bg=False, map_title=None, map_subtitle=None):
        """
        绘制中国省份地图 - 全屏布局,标题和底部数据卡用overlay叠加
        地图区域比例对齐1080x1920,zoompan时不会被裁剪

        Args:
            transparent_bg: True=透明背景(只保留省份轮廓和高亮),False=深色背景
            map_title: 主标题(动态传入,覆盖硬编码)
            map_subtitle: 副标题(动态传入,覆盖硬编码)
        """
        geojson = self._load_geojson()
        if not geojson:
            return None

        bg = None if transparent_bg else self.bg_color
        fig_bg = '#FFFFFF' if transparent_bg else self.bg_color
        fig = plt.figure(figsize=(1080/100, 1920/100), dpi=100, facecolor=fig_bg)

        # ============ 全屏地图区(标题/卡片用overlay) ============
        ax = fig.add_axes([0, 0, 1.0, 1.0])
        if transparent_bg:
            ax.set_facecolor('none')
        else:
            ax.set_facecolor(self.bg_color)
        ax.axis('off')

        rev_map = self._reverse_mapping()

        highlight_center = None
        if highlight_name:
            highlight_center = self._get_province_center(geojson, highlight_name)

        # 光晕
        if highlight_center is not None:
            for radius, alpha in [(5.0, 0.20), (3.5, 0.30), (2.0, 0.40)]:
                circle = plt.Circle(highlight_center, radius,
                                    color='#FF4500', alpha=alpha,
                                    transform=ax.transData, zorder=1)
                ax.add_patch(circle)

        # 绘制省份
        for feat in geojson.get('features', []):
            name = feat.get('properties', {}).get('name', '')
            geom = feat['geometry']
            coords = geom['coordinates']
            geom_type = geom['type']

            # 用name_mapping转换GeoJSON全称以匹配highlight_name简称
            name_map = self._name_mapping()
            short_name = name_map.get(name, name)
            if short_name == highlight_name:
                color = self.highlight_fill
                edge = self.highlight_edge
                lw = 3.0
            else:
                if transparent_bg:
                    # 透明模式:非高亮省份只显示浅灰色轮廓
                    color = '#FFFFFF00'  # 完全透明
                    edge = '#CCCCCC'  # 浅灰色边框
                    lw = 0.5
                else:
                    color = self.province_base
                    edge = self.province_edge
                    lw = 0.8

            if geom_type == 'Polygon':
                for ring in coords:
                    pts = np.array(ring)
                    ax.fill(pts[:, 0], pts[:, 1], facecolor=color,
                            edgecolor=edge, linewidth=lw, alpha=0.95)
            elif geom_type == 'MultiPolygon':
                for poly in coords:
                    for ring in poly:
                        pts = np.array(ring)
                        ax.fill(pts[:, 0], pts[:, 1], facecolor=color,
                                edgecolor=edge, linewidth=lw, alpha=0.95)

        # 自动缩放,让地图填满竖屏
        self._auto_zoom(ax, geojson.get('features', []))

        # 叠加地形阴影底图(提升信息密度)
        extent = (ax.get_xlim()[0], ax.get_xlim()[1], ax.get_ylim()[0], ax.get_ylim()[1])
        self._load_terrain_shading(ax, extent)

        # ============ 标题 overlay(动态传入,不再硬编码)============
        main_title = map_title or '中国省份TOP10'
        sub_title = map_subtitle or '数据排名'
        if transparent_bg:
            ax.text(0.5, 0.78, main_title,
                    fontsize=32, fontweight='bold',
                    color='white', ha='center', va='center',
                    transform=ax.transAxes, zorder=100,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#00000077',
                              edgecolor='none'))
            ax.text(0.5, 0.74, sub_title,
                    fontsize=14, ha='center', va='center',
                    color='white',
                    transform=ax.transAxes, zorder=100,
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='#00000066',
                              edgecolor='none'))
        else:
            ax.text(0.5, 0.78, main_title,
                    fontsize=26, fontweight='bold',
                    color='white', ha='center', va='center',
                    transform=ax.transAxes, zorder=100)
            ax.text(0.5, 0.74, sub_title,
                    fontsize=13, ha='center', va='center',
                    color=self.sub_color,
                    transform=ax.transAxes, zorder=100)

        # ============ 底部柱状图排行面板(所有省份) ============
        if highlight_name:
            short_name = highlight_name
            for suffix in ['省', '市', '自治区', '壮族', '回族', '维吾尔']:
                short_name = short_name.replace(suffix, '')

            rank_str = ''
            data_value = ''
            gdp_raw = 0
            max_gdp = 1

            # 计算所有数据值用于柱状图比例
            gdp_values = [p.get('gdp_raw', 0) or p.get('rank', 0) for p in provinces_data]
            max_gdp = max(gdp_values) if gdp_values else 1

            for prov in provinces_data:
                short = prov.get('name', '')
                geo_name = rev_map.get(short, short)
                if geo_name == highlight_name:
                    rank_str = '#{}'.format(prov.get('rank', ''))
                    data_value = prov.get('value', data_label or '')
                    gdp_raw = prov.get('gdp_raw', 0) or prov.get('rank', 0)
                    break

            # ============ 底部柱状图面板（用 fig.transFigure 绘制，不受 axes 影响） ============
            if not transparent_bg:
                # 面板背景
                fig.add_artist(mpatches.Rectangle(
                    (0.02, 0.01), 0.96, 0.20,
                    facecolor='#0D0D17', edgecolor='#30363D', linewidth=1,
                    transform=fig.transFigure
                ))
                
                # 标题
                fig.text(0.5, 0.19, map_title or '省份TOP10', fontsize=13,
                         fontweight='bold', ha='center', va='center', color='white',
                         transform=fig.transFigure)
                
                # 竖条形图：逐一显示，当前高亮第N名时只显示前N根柱条
                max_val = max_gdp if max_gdp > 0 else 1
                total_bars = min(len(provinces_data), 10)
                
                # 当前高亮到第几名
                current_rank = 0
                if highlight_name:
                    for p in provinces_data:
                        pname = p.get('name', '')
                        geo_name = rev_map.get(pname, pname)
                        if geo_name == highlight_name or pname == highlight_name:
                            current_rank = p.get('rank', 0)
                            break
                
                bar_area_x = 0.04
                bar_area_w = 0.92
                bar_unit = bar_area_w / total_bars
                bar_w = bar_unit * 0.6
                bar_max_h = 0.12
                bar_bottom = 0.03
                
                for idx, prov in enumerate(provinces_data):
                    if idx >= 10:
                        break
                    name = prov.get('name', '')
                    short = name
                    for suffix in ['省', '市', '自治区', '壮族', '回族', '维吾尔']:
                        short = short.replace(suffix, '')
                    val = prov.get('gdp_raw', 0) or prov.get('rank', 0)
                    rank = prov.get('rank', idx + 1)
                    is_highlight = (name == highlight_name or rev_map.get(name, name) == highlight_name)
                    is_revealed = (rank <= current_rank) if current_rank > 0 else False
                    
                    ratio = val / max_val if max_val > 0 else 0
                    bh = bar_max_h * ratio
                    bx = bar_area_x + idx * bar_unit + (bar_unit - bar_w) / 2
                    
                    # 背景槽
                    slot_alpha = 0.06 if is_revealed else 0.03
                    fig.add_artist(mpatches.Rectangle(
                        (bx, bar_bottom), bar_w, bar_max_h,
                        facecolor=(1, 1, 1, slot_alpha), edgecolor='none',
                        transform=fig.transFigure
                    ))
                    
                    if is_revealed:
                        # 实际柱条
                        bar_color = '#FF4500' if is_highlight else '#FFA500'
                        fig.add_artist(mpatches.Rectangle(
                            (bx, bar_bottom + bar_max_h - bh), bar_w, bh,
                            facecolor=bar_color, edgecolor='none',
                            transform=fig.transFigure
                        ))
                        
                        # 数值（柱条上方）
                        data_text = prov.get('value', '')
                        display_val = data_text if data_text else str(val)
                        fig.text(bx + bar_w/2, bar_bottom + bar_max_h + 0.005, display_val,
                                 fontsize=8, ha='center', va='bottom',
                                 color='#FFD740' if is_highlight else '#8B949E',
                                 transform=fig.transFigure)
                        
                        # 排名+省份名
                        label_color = '#FF4500' if is_highlight else 'white'
                        fig.text(bx + bar_w/2, bar_bottom - 0.005, f'#{rank} {short}',
                                 fontsize=9, ha='center', va='top',
                                 color=label_color,
                                 fontweight='bold' if is_highlight else 'normal',
                                 transform=fig.transFigure)
                        
                        # 信息维度：area + tag（在面板底部）
                        info_parts = []
                        p_area = prov.get('area', '')
                        p_tag = prov.get('tag', '')
                        if p_area:
                            info_parts.append(p_area)
                        if p_tag:
                            info_parts.append(p_tag[:8] + '..' if len(p_tag) > 8 else p_tag)
                        if info_parts:
                            info_text = ' | '.join(info_parts)
                            fig.text(bx + bar_w/2, 0.008, info_text,
                                     fontsize=5, ha='center', va='bottom',
                                     color='#8B949E' if not is_highlight else '#FFD740',
                                     transform=fig.transFigure)
                    else:
                        # 未揭示：只显示暗淡的排名号
                        fig.text(bx + bar_w/2, bar_bottom - 0.005, f'#{rank}',
                                 fontsize=8, ha='center', va='top',
                                 color='#333333',
                                 transform=fig.transFigure)
            else:
                # 透明背景：简单文字
                info_line = ''
                if rank_str:
                    info_line += rank_str + '  '
                info_line += short_name + '  '
                if data_value:
                    info_line += data_value
                ax.text(0.5, 0.04, info_line,
                        fontsize=28, ha='center', va='center',
                        color='white', fontweight='bold',
                        transform=ax.transAxes, zorder=100,
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='#00000077',
                                  edgecolor='none'))
        else:
            if transparent_bg:
                ax.text(0.5, 0.04, '全国视角',
                        fontsize=18, ha='center', va='center',
                        color='white',
                        transform=ax.transAxes, zorder=100,
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='#00000055',
                                  edgecolor='none'))
            else:
                ax.text(0.5, 0.04, '全国视角',
                        fontsize=18, ha='center', va='center',
                        color=self.sub_color,
                        transform=ax.transAxes, zorder=100,
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='#161B22',
                                  edgecolor='#30363D', linewidth=1))

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            if transparent_bg:
                fig.savefig(output_path, dpi=100, facecolor='none',
                           pad_inches=0.1, transparent=True)
            else:
                fig.savefig(output_path, dpi=100, facecolor=self.bg_color,
                           pad_inches=0.1)
            plt.close(fig)
            return output_path

        plt.close(fig)
        return None

    def _load_province_geojson(self, province_name):
        """加载单个省份的GeoJSON（从 china_full.geojson 中提取）
        
        Args:
            province_name: 省份全称，如 "湖北省", "湖南省"
            
        Returns:
            dict: GeoJSON FeatureCollection 或 None
        """
        # 尝试直接加载省份文件
        path = os.path.join(BASE_DIR, 'data', 'cache', 'geojson', f"{province_name}.geojson")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载{province_name}.geojson失败: {e}")
        
        # 从全国GeoJSON提取
        china_path = os.path.join(BASE_DIR, 'data', 'cache', 'geojson', '中国.geojson')
        if not os.path.exists(china_path):
            china_path = os.path.join(BASE_DIR, 'data', 'cache', 'geojson', 'china_full.geojson')
        if not os.path.exists(china_path):
            china_path = os.path.join(BASE_DIR, 'data', 'cache', 'geojson', 'china.geojson')
        
        if not os.path.exists(china_path):
            logger.warning("全国GeoJSON也不存在")
            return None
        
        try:
            with open(china_path, 'r', encoding='utf-8') as f:
                china = json.load(f)
            
            matched = None
            for feat in china.get('features', []):
                if feat.get('properties', {}).get('name', '') == province_name:
                    matched = feat
                    break
            
            if matched:
                prov_geojson = {
                    'type': 'FeatureCollection',
                    'features': [matched]
                }
                # 保存到缓存
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(prov_geojson, f, ensure_ascii=False)
                return prov_geojson
            else:
                logger.warning(f"在全国GeoJSON中未找到 {province_name}")
                return None
        except Exception as e:
            logger.error(f"从全国GeoJSON提取{province_name}失败: {e}")
            return None

    def _load_multi_province_geojson(self, province_names):
        """加载多个省份的GeoJSON并合并
        
        Args:
            province_names: 省份全称列表，如 ["湖北省", "湖南省", "江西省"]
            
        Returns:
            dict: 合并后的 GeoJSON FeatureCollection
        """
        all_features = []
        for name in province_names:
            prov = self._load_province_geojson(name)
            if prov and prov.get('features'):
                all_features.extend(prov['features'])
        
        if all_features:
            return {
                'type': 'FeatureCollection',
                'features': all_features
            }
        return None

    def _calc_multi_center(self, features):
        """计算多个特征的中心点（用于多省份地图的居中）"""
        all_x, all_y = [], []
        for feat in features:
            geom = feat['geometry']
            coords = geom['coordinates']
            geom_type = geom['type']
            if geom_type == 'Polygon':
                for ring in coords:
                    for pt in ring:
                        all_x.append(pt[0])
                        all_y.append(pt[1])
            elif geom_type == 'MultiPolygon':
                for poly in coords:
                    for ring in poly:
                        for pt in ring:
                            all_x.append(pt[0])
                            all_y.append(pt[1])
        if all_x:
            return (min(all_x) + max(all_x)) / 2, (min(all_y) + max(all_y)) / 2
        return None

    def draw_basin_map(self, provinces, highlight_names=None, river_points=None,
                       lake_points=None, geo_labels=None, output_path=None,
                       map_title=None, map_subtitle=None):
        """绘制流域/区域地图，支持多省份高亮 + 地理要素标注
        
        Args:
            provinces: 省份数据列表，每项含 name, data 等
            highlight_names: 高亮省份名称列表
            river_points: 河流标注点列表，每项 {lat, lon, label, color}
            lake_points: 湖泊标注点列表，每项 {lat, lon, label, area}
            geo_labels: 地理标签列表，每项 {lat, lon, text, fontsize}
            output_path: 输出PNG路径
            map_title: 主标题
            map_subtitle: 副标题
            
        Returns:
            str: 输出文件路径，或 None
        """
        # 获取省份名（全称）
        province_names = [p.get('name', '') for p in provinces]
        
        # 加载合并的GeoJSON
        geojson = self._load_multi_province_geojson(province_names)
        if not geojson or not geojson.get('features'):
            logger.error(f"无法加载省份GeoJSON: {province_names}")
            return None
        
        # 创建图形
        fig = plt.figure(figsize=(1080/100, 1920/100), dpi=100, facecolor=self.bg_color)
        ax = fig.add_axes([0, 0, 1.0, 1.0])
        ax.set_facecolor(self.bg_color)
        ax.axis('off')
        
        # 构建高亮名称集合
        if highlight_names is None:
            highlight_names = province_names
        
        # 名称映射（全称 -> 简称）
        name_map = self._name_mapping()
        rev_map = self._reverse_mapping()
        full_highlight = set()
        for h in highlight_names:
            # 尝试匹配全称
            matched = False
            for full_name, short_name in name_map.items():
                if h == short_name or h == full_name:
                    full_highlight.add(full_name)
                    matched = True
                    break
            if not matched:
                # 尝试直接作为全称
                full_highlight.add(h)
        
        # 颜色映射
        color_map = {}
        for i, name in enumerate(province_names):
            color = self.highlight_colors[i % len(self.highlight_colors)]
            color_map[name] = color
        
        # 绘制省份
        features = geojson.get('features', [])
        for feat in features:
            feat_name = feat.get('properties', {}).get('name', '')
            geom = feat['geometry']
            coords = geom['coordinates']
            geom_type = geom['type']
            
            if feat_name in full_highlight:
                color = color_map.get(feat_name, self.highlight_fill)
                edge = '#FFFFFF'
                lw = 2.0
            else:
                color = self.province_base
                edge = self.province_edge
                lw = 0.5
            
            if geom_type == 'Polygon':
                for ring in coords:
                    pts = np.array(ring)
                    ax.fill(pts[:, 0], pts[:, 1], facecolor=color,
                            edgecolor=edge, linewidth=lw, alpha=0.9)
            elif geom_type == 'MultiPolygon':
                for poly in coords:
                    for ring in poly:
                        pts = np.array(ring)
                        ax.fill(pts[:, 0], pts[:, 1], facecolor=color,
                                edgecolor=edge, linewidth=lw, alpha=0.9)
        
        # 自动缩放
        self._auto_zoom(ax, features)
        ax.set_aspect('equal')
        ax.set_position([0, 0, 1, 1])  # 全屏铺满
        
        # 叠加地形阴影
        extent = (ax.get_xlim()[0], ax.get_xlim()[1], ax.get_ylim()[0], ax.get_ylim()[1])
        self._load_terrain_shading(ax, extent)
        
        # ============ 标注省份名 ============
        for feat in features:
            feat_name = feat.get('properties', {}).get('name', '')
            if feat_name in full_highlight:
                # 计算省份中心
                center = self._get_province_center(geojson, feat_name)
                if center is not None:
                    short_name = name_map.get(feat_name, feat_name)
                    ax.text(center[0], center[1], short_name, fontsize=20,
                            fontweight='bold', ha='center', va='center',
                            color='#FFFFFF', alpha=0.9)
        
        # ============ 标注河流（蓝色线条 + 标签） ============
        if river_points:
            for rp in river_points:
                lon = rp.get('lon', 0)
                lat = rp.get('lat', 0)
                label = rp.get('label', '')
                color = rp.get('color', '#3B82F6')
                # 画河流标签
                ax.text(lon, lat, label, fontsize=14,
                        fontweight='bold', ha='center', va='center',
                        color=color, alpha=0.8,
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='#00000088',
                                  edgecolor=color, linewidth=1))
        
        # ============ 标注湖泊（蓝色区域 + 面积标签） ============
        if lake_points:
            for lp in lake_points:
                lon = lp.get('lon', 0)
                lat = lp.get('lat', 0)
                label = lp.get('label', '')
                area = lp.get('area', '')
                # 画湖泊标记（蓝色半透明圆）
                circle = plt.Circle((lon, lat), 0.8, color='#3B82F6',
                                    alpha=0.3, transform=ax.transData, zorder=5)
                ax.add_patch(circle)
                # 湖泊名
                ax.text(lon, lat, label, fontsize=16,
                        fontweight='bold', ha='center', va='bottom',
                        color='#60A5FA')
                if area:
                    ax.text(lon, lat, f'({area})', fontsize=11,
                            ha='center', va='top',
                            color='#93C5FD')
        
        # ============ 自定义地理标签 ============
        if geo_labels:
            for gl in geo_labels:
                lon = gl.get('lon', 0)
                lat = gl.get('lat', 0)
                text = gl.get('text', '')
                fontsize = gl.get('fontsize', 12)
                ax.text(lon, lat, text, fontsize=fontsize,
                        ha='center', va='center',
                        color='#FFFFFF', alpha=0.7,
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='#00000077',
                                  edgecolor='none'))
        
        # ============ 标题 ============
        main_title = map_title or '区域地图'
        sub_title = map_subtitle or ''
        ax.text(0.5, 0.93, main_title, fontsize=28, fontweight='bold',
                color='white', ha='center', va='center',
                transform=ax.transAxes, zorder=100)
        if sub_title:
            ax.text(0.5, 0.88, sub_title, fontsize=16,
                    color=self.sub_color, ha='center', va='center',
                    transform=ax.transAxes, zorder=100)
        
        # ============ 底部数据面板 ============
        if provinces:
            panel_y = 0.02
            panel_height = 0.15
            fig.add_artist(mpatches.Rectangle(
                (0.02, panel_y), 0.96, panel_height,
                facecolor='#0D0D17', edgecolor='#30363D', linewidth=1,
                transform=fig.transFigure
            ))
            
            # 数据条目
            for i, p in enumerate(provinces):
                if i >= 5:
                    break
                name = p.get('name', '')
                short = name_map.get(name, name)
                for suffix in ['省', '市', '自治区', '壮族', '回族', '维吾尔']:
                    short = short.replace(suffix, '')
                data_val = p.get('value', '')
                data_label = p.get('data_label', '')
                
                x_pos = 0.04 + i * 0.19
                
                # 颜色标记
                is_hl = (name in full_highlight or name_map.get(name, '') in full_highlight)
                color = color_map.get(name, self.highlight_fill) if is_hl else '#555555'
                
                # 小圆点
                fig.add_artist(mpatches.Circle(
                    (x_pos, panel_y + panel_height - 0.025), 0.008,
                    facecolor=color, edgecolor='white', linewidth=0.5,
                    transform=fig.transFigure
                ))
                
                # 省份名
                fig.text(x_pos, panel_y + panel_height - 0.05, short,
                         fontsize=12, fontweight='bold',
                         ha='left', va='center', color='white',
                         transform=fig.transFigure)
                
                # 数据值
                if data_val:
                    fig.text(x_pos, panel_y + panel_height - 0.08, data_val,
                             fontsize=14, fontweight='bold',
                             ha='left', va='center', color='#FFD740',
                             transform=fig.transFigure)
                
                # 数据标签
                if data_label:
                    fig.text(x_pos, panel_y + panel_height - 0.11, data_label,
                             fontsize=9, ha='left', va='center',
                             color=self.sub_color,
                             transform=fig.transFigure)
        
        # 保存
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            fig.savefig(output_path, dpi=100, facecolor=self.bg_color,
                       pad_inches=0.1)
            plt.close(fig)
            logger.info(f"流域地图已保存: {output_path}")
            return output_path
        
        plt.close(fig)
        return None



if __name__ == '__main__':
    drawer = ProvinceMapDrawer()
    path = drawer.draw_province_map([{'name': '广东省'}], highlight_name='广东省')
    print("Generated: {}".format(path))