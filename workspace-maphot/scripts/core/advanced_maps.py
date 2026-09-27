# -*- coding: utf-8 -*-
"""
高级地图类型组件 — 等值线图、网格图、动态边界

适用题材：温度分布、人口密度、行政区划变更
"""

import os
import sys
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class AdvancedMaps:
    """高级地图类型组件"""
    
    # ========== 等值线图 ==========
    @staticmethod
    def contour_map(width=600, height=400, levels=10, colors=None):
        """
        等值线图 - 连续数据分布可视化
        
        Args:
            width: 宽度
            height: 高度
            levels: 等值线级别数
            colors: 颜色列表
        """
        if colors is None:
            colors = ['#1a2744', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
        
        # 生成模拟数据（二维高程场）
        data = []
        for y in range(height):
            row = []
            for x in range(width):
                # 模拟地形数据
                z = math.sin(x*0.02) * math.cos(y*0.02) * 50 + \
                    math.sin((x+y)*0.01) * 30 + \
                    math.exp(-((x-300)**2 + (y-200)**2)/10000) * 100
                row.append(z)
            data.append(row)
        
        # 计算等值线（ marching squares 简化版）
        svg = '<svg width="%d" height="%d" viewBox="0 0 %d %d">' % (width, height, width, height)
        
        # 绘制填色区域
        step = 10
        for y in range(0, height-step, step):
            for x in range(0, width-step, step):
                z = data[y][x]
                # 根据高度分配颜色
                color_idx = int((z + 100) / 200 * len(colors))
                color_idx = max(0, min(len(colors)-1, color_idx))
                color = colors[color_idx]
                svg += '<rect x="%d" y="%d" width="%d" height="%d" fill="%s" opacity="0.6"/>' % (x, y, step, step, color)
        
        # 绘制等值线
        for level in range(-80, 100, 20):
            svg += '<path d="M'
            points = []
            for y in range(0, height-1, 5):
                for x in range(0, width-1, 5):
                    if abs(data[y][x] - level) < 10:
                        points.append('%d,%d' % (x, y))
            if points:
                svg += ' '.join(points)
            svg += '" stroke="%s" stroke-width="1.5" fill="none" opacity="0.8"/>' % colors[3]
        
        svg += '</svg>'
        return svg
    
    # ========== 网格地图 ==========
    @staticmethod
    def grid_map(data, cell_size=30, colors=None):
        """
        网格地图 - 离散数据空间分布
        
        Args:
            data: 二维数组或字典 {(x,y): value}
            cell_size: 单元格大小
            colors: 颜色映射
        """
        if colors is None:
            colors = ['#1a2744', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444']
        
        # 找到数据范围
        if isinstance(data, dict):
            values = list(data.values())
            min_val, max_val = min(values), max(values)
            cells = [(k[0], k[1], v) for k, v in data.items()]
        else:
            values = [v for row in data for v in row]
            min_val, max_val = min(values), max(values)
            cells = []
            for y, row in enumerate(data):
                for x, v in enumerate(row):
                    cells.append((x, y, v))
        
        width = (max(c[0] for c in cells) + 1) * cell_size
        height = (max(c[1] for c in cells) + 1) * cell_size
        
        svg = '<svg width="%d" height="%d" viewBox="0 0 %d %d">' % (width, height, width, height)
        
        for x, y, v in cells:
            # 归一化颜色
            if max_val != min_val:
                ratio = (v - min_val) / (max_val - min_val)
            else:
                ratio = 0.5
            color_idx = int(ratio * (len(colors) - 1))
            color = colors[color_idx]
            
            svg += '<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="#0a0f1a" stroke-width="1"/>' % (
                x * cell_size, y * cell_size, cell_size-1, cell_size-1, color
            )
            
            # 添加数值标签（如果单元格够大）
            if cell_size >= 25:
                svg += '<text x="%d" y="%d" fill="#fff" font-size="10" text-anchor="middle" dominant-baseline="middle">%d</text>' % (
                    x * cell_size + cell_size/2, y * cell_size + cell_size/2, v
                )
        
        svg += '</svg>'
        return svg
    
    # ========== 动态边界图 ==========
    @staticmethod
    def dynamic_boundaryAnimation(boundary_points, stages=5, duration=3):
        """
        动态边界动画 - 展示边界变迁
        
        Args:
            boundary_points: 边界点列表 [(x1,y1), (x2,y2), ...]
            stages: 阶段数
            duration: 动画时长（秒）
        """
        # 简化版：生成多个阶段的边界
        svg_parts = []
        js_parts = []
        
        for i in range(stages):
            # 对边界点进行扰动
            current_points = []
            for j, (x, y) in enumerate(boundary_points):
                offset_x = math.sin(i + j * 0.5) * 10
                offset_y = math.cos(i + j * 0.3) * 10
                current_points.append('%d,%d' % (int(x + offset_x), int(y + offset_y)))
            
            path_d = 'M' + ' L'.join(current_points) + ' Z'
            svg_parts.append('<path id="boundary-%d" d="%s" fill="rgba(59,130,246,0.2)" stroke="#3b82f6" stroke-width="2" opacity="0"/>' % (i, path_d))
            
            # 动画：淡入淡出
            js_parts.append('gsap.fromTo("#boundary-%d", {opacity:0}, {opacity:1, duration:%s, delay:%s});' % (i, duration/stages, i*duration/stages))
            js_parts.append('gsap.to("#boundary-%d", {opacity:0, duration:%s, delay:%s+2};' % (i, duration/stages, i*duration/stages))
        
        js = '<script>\n' + '\n'.join(js_parts) + '\ngsap.delayedCall(0.5, function() {' + ''.join(js_parts) + '});\n</script>'
        
        return '<svg width="600" height="400" viewBox="0 0 600 400">' + ''.join(svg_parts) + '</svg>' + js
    
    # ========== 流向地图 ==========
    @staticmethod
    def flow_map(flow_data, width=600, height=400):
        """
        流向地图 - 展示移动轨迹
        
        Args:
            flow_data: [{'from': (x1,y1), 'to': (x2,y2), 'value': 100}]
            width: 宽度
            height: 高度
        """
        svg = '<svg width="%d" height="%d" viewBox="0 0 %d %d">' % (width, height, width, height)
        
        for i, flow in enumerate(flow_data):
            x1, y1 = flow['from']
            x2, y2 = flow['to']
            value = flow.get('value', 50)
            color = flow.get('color', '#3b82f6')
            
            # 贝塞尔曲线
            cx1 = (x1 + x2) / 2
            cy1 = min(y1, y2) - 50
            
            path_d = 'M%d,%d Q%d,%d %d,%d' % (x1, y1, cx1, cy1, x2, y2)
            stroke_width = max(2, value / 20)
            
            svg += '<path d="%s" stroke="%s" stroke-width="%d" fill="none" opacity="0.6" stroke-dasharray="8,4">\n' % (path_d, color, stroke_width)
            svg += '  <animate attributeName="stroke-dashoffset" from="24" to="0" dur="1s" repeatCount="indefinite"/>\n'
            svg += '</path>\n'
            
            # 起点和终点
            svg += '<circle cx="%d" cy="%d" r="5" fill="%s"/>' % (x1, y1, color)
            svg += '<circle cx="%d" cy="%d" r="5" fill="%s"/>' % (x2, y2, color)
        
        svg += '</svg>'
        return svg


def main():
    """演示所有高级地图类型"""
    print("=" * 80)
    print("高级地图类型组件演示")
    print("=" * 80)
    
    maps = AdvancedMaps()
    
    # 等值线图
    print("\n【1】等值线图:")
    contour = maps.contour_map(400, 300, 8)
    print(contour[:200] + "...")
    
    # 网格地图
    print("\n【2】网格地图:")
    grid_data = {(x, y): (x+y) % 5 for x in range(10) for y in range(8)}
    grid = maps.grid_map(grid_data, cell_size=30)
    print(grid[:200] + "...")
    
    # 动态边界
    print("\n【3】动态边界:")
    boundary = [(100, 100), (200, 80), (300, 120), (350, 200), (280, 280), (150, 300)]
    dyn_boundary = maps.dynamic_boundaryAnimation(boundary, stages=3)
    print(dyn_boundary[:200] + "...")
    
    # 流向地图
    print("\n【4】流向地图:")
    flows = [
        {'from': (100, 200), 'to': (300, 100), 'value': 80, 'color': '#ef4444'},
        {'from': (150, 250), 'to': (280, 150), 'value': 60, 'color': '#f59e0b'},
        {'from': (200, 300), 'to': (250, 120), 'value': 40, 'color': '#3b82f6'},
    ]
    flow = maps.flow_map(flows)
    print(flow[:200] + "...")
    
    print("\n" + "=" * 80)
    print("共4种高级地图类型已可用")
    print("=" * 80)


if __name__ == '__main__':
    main()
