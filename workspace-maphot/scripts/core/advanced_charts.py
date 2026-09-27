# -*- coding: utf-8 -*-
"""
高级数据可视化组件 — 桑基图、雷达图、旭日图、树状图

适用题材：流量分配、多维度对比、层级占比、结构分析
"""

import os
import sys
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class AdvancedCharts:
    """高级数据可视化组件"""
    
    # ========== 桑基图 ==========
    @staticmethod
    def sankey_chart(data, width=800, height=400, node_width=20):
        """
        桑基图 - 流量分配可视化
        
        Args:
            data: {'nodes': ['A', 'B', 'C'], 'links': [{'source': 0, 'target': 1, 'value': 100}]}
            width: 宽度
            height: 高度
            node_width: 节点宽度
        """
        nodes = data.get('nodes', [])
        links = data.get('links', [])
        
        # 计算节点位置
        node_positions = {}
        node_heights = {}
        
        # 简单布局：按层分配
        layers = {}
        for link in links:
            s, t = link['source'], link['target']
            if s not in layers:
                layers[s] = 0
            if t not in layers:
                layers[t] = layers.get(s, 0) + 1
        
        max_layer = max(layers.values()) if layers else 0
        layer_width = width / (max_layer + 1)
        
        for i, node in enumerate(nodes):
            layer = layers.get(i, 0)
            x = layer * layer_width + node_width/2
            # 垂直位置按流入流出平衡
            node_positions[i] = {'x': x, 'y': 50 + i * 60}
            node_heights[i] = 40
        
        # 生成SVG
        svg = '<svg width="%d" height="%d" viewBox="0 0 %d %d">' % (width, height, width, height)
        
        # 绘制连线（贝塞尔曲线）
        for link in links:
            s, t, v = link['source'], link['target'], link.get('value', 100)
            s_pos = node_positions.get(s, {'x': 0, 'y': 0})
            t_pos = node_positions.get(t, {'x': width, 'y': 0})
            
            # 贝塞尔控制点
            c1x = s_pos['x'] + (t_pos['x'] - s_pos['x']) * 0.5
            c1y = s_pos['y']
            c2x = s_pos['x'] + (t_pos['x'] - s_pos['x']) * 0.5
            c2y = t_pos['y']
            
            path_d = 'M%d,%d C%d,%d %d,%d %d,%d' % (
                s_pos['x'] + node_width, s_pos['y'],
                c1x, c1y,
                c2x, c2y,
                t_pos['x'], t_pos['y']
            )
            
            svg += '<path d="%s" stroke="#3b82f6" stroke-width="%d" fill="none" opacity="0.3"/>' % (path_d, max(2, v/20))
        
        # 绘制节点
        for i, node in enumerate(nodes):
            pos = node_positions.get(i, {'x': 0, 'y': 0})
            h = node_heights.get(i, 40)
            svg += '<rect x="%d" y="%d" width="%d" height="%d" fill="#3b82f6" rx="4"/>' % (pos['x'], pos['y'], node_width, h)
            svg += '<text x="%d" y="%d" fill="#fff" font-size="12" text-anchor="middle">%s</text>' % (pos['x'] + node_width/2, pos['y'] + h/2 + 4, node)
        
        svg += '</svg>'
        return svg
    
    # ========== 雷达图 ==========
    @staticmethod
    def radar_chart(dimensions, values, max_value=100, size=300, color='#3b82f6'):
        """
        雷达图 - 多维度对比
        
        Args:
            dimensions: ['经济', '人口', '教育', '医疗', '交通']
            values: [85, 70, 90, 75, 60]
            max_value: 最大值
            size: 尺寸
        """
        n = len(dimensions)
        angle_step = 2 * math.pi / n
        center_x, center_y = size/2, size/2
        radius = size/2 - 40
        
        svg = '<svg width="%d" height="%d" viewBox="0 0 %d %d">' % (size, size, size, size)
        
        # 绘制网格
        for level in range(1, 6):
            r = radius * level / 5
            points = []
            for i in range(n):
                angle = i * angle_step - math.pi/2
                x = center_x + r * math.cos(angle)
                y = center_y + r * math.sin(angle)
                points.append('%d,%d' % (x, y))
            svg += '<polygon points="%s" fill="none" stroke="#334155" stroke-width="1" opacity="0.3"/>' % ' '.join(points)
        
        # 绘制轴线
        for i in range(n):
            angle = i * angle_step - math.pi/2
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            svg += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#475569" stroke-width="1"/>' % (center_x, center_y, x, y)
            # 标签
            lx = center_x + (radius + 20) * math.cos(angle)
            ly = center_y + (radius + 20) * math.sin(angle)
            svg += '<text x="%d" y="%d" fill="#e2e8f0" font-size="12" text-anchor="middle" dominant-baseline="middle">%s</text>' % (lx, ly, dimensions[i])
        
        # 绘制数据
        data_points = []
        for i, v in enumerate(values):
            angle = i * angle_step - math.pi/2
            r = radius * v / max_value
            x = center_x + r * math.cos(angle)
            y = center_y + r * math.sin(angle)
            data_points.append('%d,%d' % (x, y))
        
        svg += '<polygon points="%s" fill="rgba(59,130,246,0.3)" stroke="%s" stroke-width="2"/>' % (' '.join(data_points), color)
        
        # 数据点
        for i, v in enumerate(values):
            angle = i * angle_step - math.pi/2
            r = radius * v / max_value
            x = center_x + r * math.cos(angle)
            y = center_y + r * math.sin(angle)
            svg += '<circle cx="%d" cy="%d" r="4" fill="%s"/>' % (x, y, color)
        
        svg += '</svg>'
        return svg
    
    # ========== 旭日图 ==========
    @staticmethod
    def sunburst_chart(data, size=400, colors=None):
        """
        旭日图 - 层级占比可视化
        
        Args:
            data: {'name': '根', 'value': 100, 'children': [...]}
            size: 尺寸
            colors: 颜色列表
        """
        if colors is None:
            colors = ['#3b82f6', '#ef4444', '#f59e0b', '#8b5cf6', '#10b981', '#06b6d4']
        
        def explode(node, depth=0, start_angle=0, end_angle=2*math.pi):
            """递归展开节点"""
            items = []
            if 'children' in node and node['children']:
                total = sum(c.get('value', 1) for c in node['children'])
                current_angle = start_angle
                for i, child in enumerate(node['children']):
                    child_angle = current_angle + (child.get('value', 1) / total) * (end_angle - start_angle)
                    items.extend(explode(child, depth+1, current_angle, child_angle))
                    current_angle = child_angle
            else:
                r_inner = 60 + depth * 40
                r_outer = r_inner + 35
                items.append({
                    'node': node,
                    'depth': depth,
                    'start_angle': start_angle,
                    'end_angle': end_angle,
                    'r_inner': r_inner,
                    'r_outer': r_outer,
                    'color': colors[depth % len(colors)]
                })
            return items
        
        items = explode(data)
        
        svg = '<svg width="%d" height="%d" viewBox="0 0 %d %d">' % (size, size, size, size)
        cx, cy = size/2, size/2
        
        for item in items:
            start = item['start_angle']
            end = item['end_angle']
            r1 = item['r_inner']
            r2 = item['r_outer']
            
            # 计算路径
            x1_inner = cx + r1 * math.cos(start)
            y1_inner = cy + r1 * math.sin(start)
            x2_inner = cx + r1 * math.cos(end)
            y2_inner = cy + r1 * math.sin(end)
            x1_outer = cx + r2 * math.cos(start)
            y1_outer = cy + r2 * math.sin(start)
            x2_outer = cx + r2 * math.cos(end)
            y2_outer = cy + r2 * math.sin(end)
            
            large_arc = 1 if (end - start) > math.pi else 0
            
            path = 'M%d,%d L%d,%d A%d,%d 0 %d,1 %d,%d L%d,%d A%d,%d 0 %d,0 %d,%d Z' % (
                x1_inner, y1_inner, x1_outer, y1_outer,
                r2, r2, large_arc, x2_outer, y2_outer,
                x2_inner, y2_inner, r1, r1, large_arc, x1_inner, y1_inner
            )
            
            svg += '<path d="%s" fill="%s" stroke="#0a0f1a" stroke-width="2"/>' % (path, item['color'])
        
        svg += '</svg>'
        return svg
    
    # ========== 树状图 ==========
    @staticmethod
    def treemap(data, width=600, height=400, colors=None):
        """
        树状图 - 层级结构可视化
        
        Args:
            data: {'name': '根', 'value': 100, 'children': [...]}
            width: 宽度
            height: 高度
            colors: 颜色列表
        """
        if colors is None:
            colors = ['#3b82f6', '#ef4444', '#f59e0b', '#8b5cf6', '#10b981']
        
        def squarify(items, x, y, w, h):
            """递归分割矩形"""
            results = []
            if not items:
                return results
            
            total = sum(item.get('value', 1) for item in items)
            
            if len(items) == 1:
                results.append({'node': items[0], 'x': x, 'y': y, 'w': w, 'h': h})
                return results
            
            # 简单分割：按面积比例分割
            remaining = items[:]
            current_x, current_y = x, y
            current_w, current_h = w, h
            
            while remaining:
                item = remaining.pop(0)
                ratio = item.get('value', 1) / total
                total -= item.get('value', 1)
                
                if current_w >= current_h:
                    # 水平分割
                    split_w = current_w * ratio
                    results.append({'node': item, 'x': current_x, 'y': current_y, 'w': split_w, 'h': current_h})
                    current_x += split_w
                    current_w -= split_w
                else:
                    # 垂直分割
                    split_h = current_h * ratio
                    results.append({'node': item, 'x': current_x, 'y': current_y, 'w': current_w, 'h': split_h})
                    current_y += split_h
                    current_h -= split_h
            
            return results
        
        items = squarify([data], 0, 0, width, height)
        
        svg = '<svg width="%d" height="%d" viewBox="0 0 %d %d">' % (width, height, width, height)
        
        for i, item in enumerate(items):
            node = item['node']
            x = int(item['x'])
            y = int(item['y'])
            w = int(item['w'])
            h = int(item['h'])
            
            if w > 20 and h > 20:
                color = colors[i % len(colors)]
                svg += '<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="#0a0f1a" stroke-width="2" rx="4"/>' % (x, y, w, h, color)
                if w > 50 and h > 30:
                    svg += '<text x="%d" y="%d" fill="#fff" font-size="14" text-anchor="middle" dominant-baseline="middle">%s</text>' % (x + w/2, y + h/2, node.get('name', 'N/A'))
        
        svg += '</svg>'
        return svg
    
    # ========== 散点图 ==========
    @staticmethod
    def scatter_plot(data, width=600, height=400, x_label='X轴', y_label='Y轴', size_scale=1):
        """
        散点图 - 相关性分析
        
        Args:
            data: [{'x': 10, 'y': 20, 'size': 5, 'color': '#3b82f6'}]
            width: 宽度
            height: 高度
            x_label: X轴标签
            y_label: Y轴标签
            size_scale: 点大小缩放
        """
        if not data:
            return '<svg></svg>'
        
        max_x = max(d.get('x', 0) for d in data) or 1
        max_y = max(d.get('y', 0) for d in data) or 1
        padding = 50
        
        svg = '<svg width="%d" height="%d" viewBox="0 0 %d %d">' % (width, height, width, height)
        
        # 坐标轴
        svg += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#475569" stroke-width="2"/>' % (padding, height-padding, width-padding, height-padding)
        svg += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#475569" stroke-width="2"/>' % (padding, height-padding, padding, padding)
        
        # 标签
        svg += '<text x="%d" y="%d" fill="#94a3b8" font-size="12" text-anchor="middle">%s</text>' % (width/2, height-10, x_label)
        svg += '<text x="%d" y="%d" fill="#94a3b8" font-size="12" text-anchor="middle" transform="rotate(-90,%d,%d)">%s</text>' % (15, height/2, 15, height/2, y_label)
        
        # 数据点
        for i, point in enumerate(data):
            x = padding + (point.get('x', 0) / max_x) * (width - 2*padding)
            y = height - padding - (point.get('y', 0) / max_y) * (height - 2*padding)
            r = max(4, point.get('size', 5) * size_scale)
            color = point.get('color', '#3b82f6')
            
            svg += '<circle cx="%d" cy="%d" r="%d" fill="%s" opacity="0.7"/>' % (x, y, r, color)
            if r > 8:
                svg += '<text x="%d" y="%d" fill="#fff" font-size="10" text-anchor="middle" dy="4">%s</text>' % (x, y, point.get('label', ''))
        
        svg += '</svg>'
        return svg


def main():
    """演示所有高级图表"""
    print("=" * 80)
    print("高级数据可视化组件演示")
    print("=" * 80)
    
    charts = AdvancedCharts()
    
    # 桑基图
    print("\n【1】桑基图示例:")
    sankey_data = {
        'nodes': ['上游', '中游', '下游', '终端'],
        'links': [
            {'source': 0, 'target': 1, 'value': 100},
            {'source': 0, 'target': 2, 'value': 50},
            {'source': 1, 'target': 3, 'value': 80},
            {'source': 2, 'target': 3, 'value': 30},
        ]
    }
    print(charts.sankey_chart(sankey_data)[:200] + "...")
    
    # 雷达图
    print("\n【2】雷达图示例:")
    radar = charts.radar_chart(['经济', '人口', '教育', '医疗', '交通'], [85, 70, 90, 75, 60])
    print(radar[:200] + "...")
    
    # 旭日图
    print("\n【3】旭日图示例:")
    sunburst = charts.sunburst_chart({'name': '产业', 'value': 100, 'children': [
        {'name': '电子', 'value': 40, 'children': [{'name': '芯片', 'value': 25}, {'name': '屏幕', 'value': 15}]},
        {'name': '汽车', 'value': 35, 'children': [{'name': '整车', 'value': 20}, {'name': '零部件', 'value': 15}]},
        {'name': '能源', 'value': 25},
    ]})
    print(sunburst[:200] + "...")
    
    # 树状图
    print("\n【4】树状图示例:")
    treemap = charts.treemap({'name': '区域', 'value': 100, 'children': [
        {'name': '华东', 'value': 40},
        {'name': '华南', 'value': 30},
        {'name': '华北', 'value': 20},
        {'name': '其他', 'value': 10},
    ]})
    print(treemap[:200] + "...")
    
    # 散点图
    print("\n【5】散点图示例:")
    scatter = charts.scatter_plot([
        {'x': 10, 'y': 20, 'size': 5, 'label': 'A'},
        {'x': 30, 'y': 40, 'size': 8, 'label': 'B'},
        {'x': 50, 'y': 30, 'size': 6, 'label': 'C'},
        {'x': 70, 'y': 60, 'size': 10, 'label': 'D'},
    ])
    print(scatter[:200] + "...")
    
    print("\n" + "=" * 80)
    print("共5种高级图表已可用")
    print("=" * 80)


if __name__ == '__main__':
    main()
