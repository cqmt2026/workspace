# -*- coding: utf-8 -*-
"""
GuangxiMapDrawerV2 - 平陆运河地理故事流多段地图
4个场景：广西全貌 -> 起点横州 -> 穿越丘陵 -> 终点钦州
"""
import os, json, logging, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

for _f in ['SimHei', 'Microsoft YaHei', 'Noto Sans SC']:
    try:
        plt.rcParams['font.sans-serif'] = [_f]
        plt.rcParams['axes.unicode_minus'] = False
        break
    except: pass

class GuangxiMapDrawerV2:
    def __init__(self):
        self.bg = "#0A0F1A"; self.accent = "#00D4FF"
        self.sub = "#FFD740"; self.base = "#1A2744"
        self.edge = "#2E4A7A"; self.hfill = "#00D4FF"; self.hedge = "#FFFFFF"

    def _load_geojson(self):
        for p in [os.path.join(BASE_DIR, 'data', 'cache', 'geojson', f) for f in ['china.geojson', '中国.geojson']]:
            if os.path.exists(p):
                try:
                    with open(p, encoding='utf-8') as f: data = json.load(f)
                    for feat in data.get('features', []):
                        n = feat.get('properties', {}).get('name', '')
                        if '广西' in n: return {'type': 'FeatureCollection', 'features': [feat]}
                except: pass
        return None

    def _draw(self, ax, features, xlim, ylim, title, subtitle, highlights=None, river=None, labels=None):
        ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect('equal')
        ax.set_facecolor(self.bg); ax.axis('off')
        for feat in features:
            for poly in feat['geometry']['coordinates']:
                for ring in poly:
                    pts = np.array(ring)
                    if all(float(x) < 115 and float(y) > 20 for x, y in pts):
                        ax.fill(pts[:, 0], pts[:, 1], facecolor=self.base, edgecolor=self.edge, linewidth=1.5, alpha=0.9)
        if river:
            lons, lats = zip(*river)
            ax.plot(lons, lats, color=self.accent, linewidth=3, alpha=0.9, zorder=9)
            ax.plot(lons, lats, color='#00D4FF', linewidth=8, alpha=0.15, zorder=8)
        if highlights:
            for lon, lat, name, color, size in highlights:
                ax.scatter(lon, lat, s=size, color=color, alpha=0.9, zorder=10)
                ax.text(lon, lat+0.05, name, fontsize=10, color='white', ha='center', va='bottom', fontweight='bold', zorder=11,
                       bbox=dict(boxstyle='round,pad=0.15', facecolor='#0A0F1Acc', edgecolor=color, linewidth=0.5))
        if labels:
            for lon, lat, text, color, fs in labels:
                ax.text(lon, lat, text, fontsize=fs, color=color, ha='center', va='center', fontweight='bold', zorder=12,
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='#0A0F1Acc'))
        ax.text(0.5, 0.97, title, fontsize=24, fontweight='bold', color='white', ha='center', va='top', transform=ax.transAxes, zorder=100)
        if subtitle: ax.text(0.5, 0.92, subtitle, fontsize=12, color=self.sub, ha='center', va='top', transform=ax.transAxes, zorder=100)

    def draw_all(self, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        geojson = self._load_geojson()
        if not geojson: logger.error("无法加载GeoJSON"); return {}

        scenes = {}
        # Scene 1: 广西全貌
        fig = plt.figure(figsize=(10.8, 19.2), dpi=100, facecolor=self.bg)
        ax = fig.add_axes([0, 0, 1, 1])
        self._draw(ax, geojson['features'], (105.5, 112.0), (20.5, 26.5),
                  '平陆运河', '广西 · 新中国成立以来第一条江海连通超级运河',
                  highlights=[(108.35, 22.82, '南宁', '#FFFFFF', 60), (109.95, 22.85, '横州', '#00D4FF', 80), (108.60, 21.85, '钦州', '#FFD740', 80)],
                  labels=[(107.5, 23.5, '西江', '#66BBFF', 10), (108.0, 21.0, '北部湾', '#00D4FF', 11)])
        out = os.path.join(out_dir, 'scene1_full_guangxi.png'); fig.savefig(out, dpi=100, facecolor=self.bg, pad_inches=0); plt.close(fig)
        scenes['scene1'] = out; logger.info(f"Scene1: {out} ({os.path.getsize(out)} bytes)")

        # Scene 2: 起点横州
        canal_start = [(109.95, 22.85), (109.85, 22.75), (109.70, 22.60), (109.60, 22.50)]
        fig = plt.figure(figsize=(10.8, 19.2), dpi=100, facecolor=self.bg)
        ax = fig.add_axes([0, 0, 1, 1])
        self._draw(ax, geojson['features'], (109.0, 110.5), (22.3, 23.2),
                  '起点：西津渡口', '南宁横州市 · 西江支流上的普通渡口',
                  river=canal_start,
                  highlights=[(109.95, 22.85, '西津渡口', '#00D4FF', 100), (109.60, 22.50, '平塘江口', '#FFD740', 80), (108.35, 22.82, '南宁', '#FFFFFF', 60)],
                  labels=[(109.5, 22.95, '西江', '#66BBFF', 10)])
        fig.add_artist(mpatches.Rectangle((0.02, 0.01), 0.96, 0.15, facecolor='#0D1525', edgecolor='#1E3A5F', linewidth=1, transform=fig.transFigure))
        fig.text(0.5, 0.12, '起点海拔：约60米', fontsize=11, color=self.accent, ha='center', va='center', transform=fig.transFigure)
        fig.text(0.5, 0.06, '西江是广西最大的水系，平陆运河从这里开始', fontsize=10, color='#8899AA', ha='center', va='center', transform=fig.transFigure)
        out = os.path.join(out_dir, 'scene2_nanning_start.png'); fig.savefig(out, dpi=100, facecolor=self.bg, pad_inches=0); plt.close(fig)
        scenes['scene2'] = out; logger.info(f"Scene2: {out} ({os.path.getsize(out)} bytes)")

        # Scene 3: 穿越丘陵
        canal_mid = [(109.60, 22.50), (109.40, 22.30), (109.20, 22.10), (109.00, 21.90), (108.80, 21.80), (108.65, 21.70)]
        fig = plt.figure(figsize=(10.8, 19.2), dpi=100, facecolor=self.bg)
        ax = fig.add_axes([0, 0, 1, 1])
        self._draw(ax, geojson['features'], (108.3, 109.8), (21.5, 22.8),
                  '穿越广西丘陵', '19座梯级船闸 · 逐级提水翻山',
                  river=canal_mid,
                  highlights=[(109.40, 22.30, '马道口', '#00D4FF', 70), (109.00, 21.90, '青年渠首', '#00D4FF', 70), (108.65, 21.70, '竹巴滩', '#FFD740', 80)],
                  labels=[(108.8, 22.0, '丘陵地带', '#FF6B6B', 9)])
        fig.add_artist(mpatches.Rectangle((0.02, 0.01), 0.96, 0.15, facecolor='#0D1525', edgecolor='#1E3A5F', linewidth=1, transform=fig.transFigure))
        fig.text(0.5, 0.12, '全程落差19米 | 19座船闸 | 逐级提水', fontsize=11, color=self.accent, ha='center', va='center', transform=fig.transFigure)
        fig.text(0.5, 0.06, '穿越广西最复杂的丘陵地带', fontsize=10, color='#8899AA', ha='center', va='center', transform=fig.transFigure)
        out = os.path.join(out_dir, 'scene3_crossing.png'); fig.savefig(out, dpi=100, facecolor=self.bg, pad_inches=0); plt.close(fig)
        scenes['scene3'] = out; logger.info(f"Scene3: {out} ({os.path.getsize(out)} bytes)")

        # Scene 4: 终点茅尾海
        canal_end = [(108.65, 21.70), (108.62, 21.60), (108.60, 21.50), (108.60, 21.40), (108.60, 21.30), (108.60, 21.85)]
        fig = plt.figure(figsize=(10.8, 19.2), dpi=100, facecolor=self.bg)
        ax = fig.add_axes([0, 0, 1, 1])
        self._draw(ax, geojson['features'], (108.0, 109.0), (21.0, 22.0),
                  '终点：茅尾海', '注入北部湾 · 直通南海',
                  river=canal_end,
                  highlights=[(108.60, 21.85, '茅尾海', '#FFD740', 100), (108.35, 21.82, '钦州', '#FFFFFF', 80)],
                  labels=[(108.4, 21.2, '北部湾', '#00D4FF', 12)])
        fig.add_artist(mpatches.Rectangle((0.02, 0.01), 0.96, 0.15, facecolor='#0D1525', edgecolor='#1E3A5F', linewidth=1, transform=fig.transFigure))
        fig.text(0.5, 0.12, '通航后海运直达东南亚', fontsize=11, color=self.accent, ha='center', va='center', transform=fig.transFigure)
        fig.text(0.5, 0.06, '比绕行广州珠江口缩短560公里', fontsize=10, color='#8899AA', ha='center', va='center', transform=fig.transFigure)
        out = os.path.join(out_dir, 'scene4_sea_end.png'); fig.savefig(out, dpi=100, facecolor=self.bg, pad_inches=0); plt.close(fig)
        scenes['scene4'] = out; logger.info(f"Scene4: {out} ({os.path.getsize(out)} bytes)")

        return scenes

if __name__ == '__main__':
    drawer = GuangxiMapDrawerV2()
    out_dir = os.path.join(BASE_DIR, 'data', 'maps', '20260917', 'pinglu_canal_scenes')
    print("Generating 4 scenes for Pinglu Canal geography story...")
    results = drawer.draw_all(out_dir)
    ok = sum(1 for v in results.values() if v)
    print(f"Done: {ok}/{len(results)} scenes")
