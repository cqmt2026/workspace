# -*- coding: utf-8 -*-
"""
视觉匹配决策器 — 根据题材类型和文案特征自动匹配最佳视觉技术组合

核心逻辑：
1. 分析题材类型（8种）
2. 分析文案特征（节奏、情绪、数据密度）
3. 匹配最佳视觉技术组合（地图+可视化+动画+特效+声音）
4. 输出完整视觉方案

输出格式：
{
    'map_type': 'heatmap',           # 地图类型
    'chart_type': 'bar_chart',       # 数据可视化类型
    'transition': 'push_slide',      # 动画转场
    'text_effect': 'number_roll',    # 文字特效
    'lighting': 'neon',              # 光影特效
    'dynamic': 'wave',               # 动态图形
    'interaction': 'ripple',         # 交互反馈
    'sound': 'whoosh',               # 声音设计
    'particle': 'burst',             # 粒子特效
    'pacing': 'fast',                # 节奏控制
    'duration': 50,                  # 预估时长（秒）
    'confidence': 0.85,              # 匹配置信度
}
"""

import re
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ========== 题材类型（与 match_maker_v2 保持一致） ==========
TYPE_SINGLE_EVENT = "single_event"
TYPE_DATA_RANKING = "data_ranking"
TYPE_INDUSTRY_ANALYSIS = "industry_analysis"
TYPE_HISTORICAL_GEO = "historical_geo"
TYPE_POPULATION_FLOW = "population_flow"
TYPE_POLICY_EFFECT = "policy_effect"
TYPE_COMPARISON = "comparison"
TYPE_INSTITUTION_ORIGIN = "institution_origin"

# ========== 节奏类型 ==========
PACING_FAST = "fast"       # 快速（1-2分钟，轻快节奏）
PACING_MEDIUM = "medium"   # 中速（2-3分钟，平稳节奏）
PACING_SLOW = "slow"       # 慢速（3-5分钟，深度节奏）

# ========== 情绪类型 ==========
EMOTION_POSITIVE = "positive"     # 积极/振奋
EMOTION_NEGATIVE = "negative"     # 消极/担忧
EMOTION_NEUTRAL = "neutral"       # 中性/客观
EMOTION_SURPRISE = "surprise"     # 震撼/惊讶
EMOTION_NOSTALGIA = "nostalgia"   # 怀旧/感慨


class VisualMatcher:
    """视觉匹配决策器"""
    
    # ========== 视觉技术库 ==========
    VISUAL_LIBRARY = {
        # 地图类型
        'map_type': {
            'real_scene': {'name': '实景地图', 'desc': '高德瓦片+点位标注', 'complexity': 3},
            'heatmap': {'name': '热力图', 'desc': '密度聚类+色彩分级', 'complexity': 2},
            'flow_map': {'name': '流向图', 'desc': '贝塞尔曲线+箭头动画', 'complexity': 4},
            'profile': {'name': '剖面图', 'desc': 'DEM数据+时间轴', 'complexity': 5},
            'choropleth': {'name': '分区图', 'desc': 'GeoJSON+颜色填充', 'complexity': 2},
            'overlay': {'name': '叠加图', 'desc': '多层GeoJSON+透明度', 'complexity': 4},
            'contour': {'name': '等值线图', 'desc': '插值算法+等高线', 'complexity': 5},
            'grid': {'name': '网格图', 'desc': '六边形/方形网格', 'complexity': 3},
            'terrain_3d': {'name': '3D地形', 'desc': 'Three.js+DEM高程', 'complexity': 6},
            'dynamic_boundary': {'name': '动态边界', 'desc': 'SVG path变形', 'complexity': 4},
        },
        # 数据可视化
        'chart_type': {
            'donut': {'name': '圆环进度', 'desc': 'SVG stroke-dasharray', 'complexity': 2},
            'bar_chart': {'name': '柱状图', 'desc': 'CSS height动画', 'complexity': 1},
            'line_chart': {'name': '折线图', 'desc': 'SVG path动画', 'complexity': 3},
            'table': {'name': '表格', 'desc': 'HTML table+移动画', 'complexity': 1},
            'bubble_map': {'name': '地图+气泡', 'desc': '地图底图+动态大小', 'complexity': 3},
            'treemap': {'name': '树状图', 'desc': '矩形嵌套+颜色', 'complexity': 4},
            'sankey': {'name': '桑基图', 'desc': '贝塞尔曲线+宽度', 'complexity': 5},
            'radar': {'name': '雷达图', 'desc': 'SVG多边形+动画', 'complexity': 4},
            'sunburst': {'name': '旭日图', 'desc': '同心圆+扇形', 'complexity': 5},
            'funnel': {'name': '漏斗图', 'desc': '梯形堆叠+收缩', 'complexity': 3},
            'scatter': {'name': '散点图', 'desc': 'SVG circle+大小', 'complexity': 3},
            'chain': {'name': '链条形', 'desc': '产业链可视化', 'complexity': 3},
        },
        # 动画转场
        'transition': {
            'zoom_through': {'name': '穿越转场', 'desc': 'scale 0.6→1+blur', 'complexity': 3},
            'push_slide': {'name': '推入转场', 'desc': 'x偏移+opacity', 'complexity': 1},
            'fade_blur': {'name': '渐显转场', 'desc': 'opacity+filter blur', 'complexity': 2},
            'split_screen': {'name': '分屏转场', 'desc': '左右分屏+stagger', 'complexity': 3},
            'flip_card': {'name': '翻转转场', 'desc': 'rotateY 180deg', 'complexity': 2},
            'morph_path': {'name': '变形转场', 'desc': 'SVG path变形', 'complexity': 5},
            'particle_burst': {'name': '粒子爆发转场', 'desc': '粒子随机扩散', 'complexity': 4},
            'wave_distort': {'name': '波浪扭曲转场', 'desc': 'SVG filter', 'complexity': 5},
        },
        # 文字特效
        'text_effect': {
            'typewriter': {'name': '打字机', 'desc': '逐字显示', 'complexity': 1},
            'number_roll': {'name': '数字滚动', 'desc': 'GSAP innerHTML', 'complexity': 1},
            'gradient': {'name': '文字渐色', 'desc': 'background-clip', 'complexity': 2},
            'shake': {'name': '文字抖动', 'desc': '随机位移', 'complexity': 2},
            'shatter': {'name': '文字碎裂', 'desc': '字符扩散', 'complexity': 4},
            'reveal': {'name': '文字浮现', 'desc': 'clip-path揭示', 'complexity': 2},
            'outline': {'name': '文字描边', 'desc': 'text-stroke', 'complexity': 1},
            'flip_3d': {'name': '文字3D翻转', 'desc': 'perspective+rotate', 'complexity': 3},
        },
        # 光影特效
        'lighting': {
            'neon': {'name': '霓虹发光', 'desc': 'text-shadow多层', 'complexity': 1},
            'glass': {'name': '玻璃态', 'desc': 'backdrop-filter blur', 'complexity': 2},
            'gradient_flow': {'name': '渐变流动', 'desc': 'background-size动画', 'complexity': 2},
            'glitch': {'name': '故障艺术', 'desc': 'clip随机裁剪', 'complexity': 4},
            'scanline': {'name': '扫描线', 'desc': 'repeating-gradient', 'complexity': 2},
            'flare': {'name': '光晕', 'desc': 'radial-gradient旋转', 'complexity': 3},
        },
        # 动态图形
        'dynamic': {
            'wave': {'name': '波形线', 'desc': 'requestAnimationFrame', 'complexity': 3},
            'ring': {'name': '旋转星环', 'desc': 'SVG rotate', 'complexity': 2},
            'pulse': {'name': '脉冲圆环', 'desc': 'scale+opacity', 'complexity': 1},
            'skeleton': {'name': '骨架屏', 'desc': 'CSS shimmer', 'complexity': 1},
            'dot_matrix': {'name': '点阵矩阵', 'desc': '随机闪烁', 'complexity': 3},
        },
        # 声音设计
        'sound': {
            'beep': {'name': '提示音效', 'desc': '单音提示', 'complexity': 1},
            'whoosh': {'name': '滑动音效', 'desc': '频率滑动', 'complexity': 2},
            'success': {'name': '成功音效', 'desc': '三音符上升', 'complexity': 2},
            'click': {'name': '点击音效', 'desc': '短促点击', 'complexity': 1},
            'bgm': {'name': 'BGM控制', 'desc': '背景音乐', 'complexity': 3},
            'beat_sync': {'name': '节拍同步', 'desc': '节奏检测', 'complexity': 5},
        },
    }
    
    # ========== 题材-视觉匹配矩阵 ==========
    MATCH_MATRIX = {
        TYPE_SINGLE_EVENT: {
            'map_type': ['real_scene', 'heatmap', 'terrain_3d'],
            'chart_type': ['bubble_map', 'donut'],
            'transition': ['zoom_through', 'fade_blur'],
            'text_effect': ['typewriter', 'reveal'],
            'lighting': ['neon', 'glass'],
            'dynamic': ['pulse', 'wave'],
            'sound': ['whoosh', 'beep'],
            'particle': True,
            'pacing': PACING_MEDIUM,
            'duration_range': (45, 70),
        },
        TYPE_DATA_RANKING: {
            'map_type': ['choropleth', 'heatmap'],
            'chart_type': ['bar_chart', 'donut', 'table', 'bubble_map'],
            'transition': ['push_slide', 'fade_blur'],
            'text_effect': ['number_roll', 'gradient'],
            'lighting': ['neon', 'gradient_flow'],
            'dynamic': ['pulse', 'dot_matrix'],
            'sound': ['beep', 'click', 'success'],
            'particle': False,
            'pacing': PACING_FAST,
            'duration_range': (40, 60),
        },
        TYPE_INDUSTRY_ANALYSIS: {
            'map_type': ['overlay', 'choropleth', 'heatmap'],
            'chart_type': ['chain', 'sankey', 'treemap', 'sunburst'],
            'transition': ['zoom_through', 'fade_blur'],
            'text_effect': ['reveal', 'typewriter'],
            'lighting': ['glass', 'neon'],
            'dynamic': ['wave', 'dot_matrix'],
            'sound': ['whoosh', 'beep'],
            'particle': False,
            'pacing': PACING_SLOW,
            'duration_range': (60, 90),
        },
        TYPE_HISTORICAL_GEO: {
            'map_type': ['profile', 'terrain_3d', 'dynamic_boundary'],
            'chart_type': ['line_chart', 'scatter'],
            'transition': ['morph_path', 'fade_blur', 'wave_distort'],
            'text_effect': ['typewriter', 'flip_3d', 'shatter'],
            'lighting': ['glitch', 'scanline'],
            'dynamic': ['wave', 'ring'],
            'sound': ['whoosh', 'bgm'],
            'particle': True,
            'pacing': PACING_SLOW,
            'duration_range': (60, 120),
        },
        TYPE_POPULATION_FLOW: {
            'map_type': ['flow_map', 'heatmap'],
            'chart_type': ['sankey', 'bubble_map', 'scatter'],
            'transition': ['morph_path', 'fade_blur'],
            'text_effect': ['number_roll', 'reveal'],
            'lighting': ['neon', 'gradient_flow'],
            'dynamic': ['wave', 'pulse'],
            'sound': ['whoosh', 'beep'],
            'particle': True,
            'pacing': PACING_MEDIUM,
            'duration_range': (50, 80),
        },
        TYPE_POLICY_EFFECT: {
            'map_type': ['heatmap', 'choropleth'],
            'chart_type': ['bar_chart', 'funnel', 'donut'],
            'transition': ['fade_blur', 'push_slide'],
            'text_effect': ['number_roll', 'typewriter'],
            'lighting': ['glass', 'neon'],
            'dynamic': ['pulse', 'dot_matrix'],
            'sound': ['beep', 'click'],
            'particle': False,
            'pacing': PACING_MEDIUM,
            'duration_range': (45, 70),
        },
        TYPE_COMPARISON: {
            'map_type': ['real_scene', 'choropleth'],
            'chart_type': ['radar', 'bar_chart', 'table'],
            'transition': ['split_screen', 'flip_card'],
            'text_effect': ['number_roll', 'gradient'],
            'lighting': ['neon', 'glass'],
            'dynamic': ['pulse', 'ring'],
            'sound': ['beep', 'click'],
            'particle': False,
            'pacing': PACING_FAST,
            'duration_range': (40, 60),
        },
        TYPE_INSTITUTION_ORIGIN: {
            'map_type': ['dynamic_boundary', 'choropleth'],
            'chart_type': ['table', 'line_chart'],
            'transition': ['fade_blur', 'morph_path'],
            'text_effect': ['typewriter', 'flip_3d'],
            'lighting': ['glitch', 'scanline', 'glass'],
            'dynamic': ['wave', 'ring', 'pulse'],
            'sound': ['whoosh', 'bgm'],
            'particle': True,
            'pacing': PACING_SLOW,
            'duration_range': (60, 90),
        },
    }
    
    # ========== 文案分析 ==========
    @classmethod
    def analyze_script(cls, script_text):
        """分析文案特征"""
        if not script_text:
            return {'pacing': PACING_MEDIUM, 'emotion': EMOTION_NEUTRAL, 'data_density': 0.5}
        
        # 节奏检测
        char_count = len(script_text)
        sentence_count = max(1, len(re.findall(r'[。！？\n]', script_text)))
        avg_sentence_length = char_count / sentence_count
        
        if avg_sentence_length < 30:
            pacing = PACING_FAST
        elif avg_sentence_length < 60:
            pacing = PACING_MEDIUM
        else:
            pacing = PACING_SLOW
        
        # 情绪检测
        positive_words = ['增长', '突破', '创新', '第一', '最强', '领先', '成功', '崛起', '超越', '新高']
        negative_words = ['下降', '亏损', '流失', '危机', '风险', '衰退', '落后', '失败', '问题', '萎缩']
        surprise_words = ['震撼', '惊人', '意外', '竟然', '没想到', '颠覆', '爆发', '奇迹']
        nostalgia_words = ['回忆', '曾经', '过去', '变迁', '历史', '年代', '记忆', '当年']
        
        pos_count = sum(1 for w in positive_words if w in script_text)
        neg_count = sum(1 for w in negative_words if w in script_text)
        surp_count = sum(1 for w in surprise_words if w in script_text)
        nost_count = sum(1 for w in nostalgia_words if w in script_text)
        
        max_count = max(pos_count, neg_count, surp_count, nost_count)
        if max_count == 0:
            emotion = EMOTION_NEUTRAL
        elif max_count == pos_count:
            emotion = EMOTION_POSITIVE
        elif max_count == neg_count:
            emotion = EMOTION_NEGATIVE
        elif max_count == surp_count:
            emotion = EMOTION_SURPRISE
        else:
            emotion = EMOTION_NOSTALGIA
        
        # 数据密度检测
        number_count = len(re.findall(r'\d+', script_text))
        data_density = min(1.0, number_count / max(1, sentence_count) * 0.2)
        
        return {
            'pacing': pacing,
            'emotion': emotion,
            'data_density': data_density,
            'char_count': char_count,
            'sentence_count': sentence_count,
            'avg_sentence_length': avg_sentence_length,
        }
    
    # ========== 视觉技术匹配 ==========
    @classmethod
    def match_visual(cls, topic_type, script_text='', data=None):
        """
        根据题材和文案匹配最佳视觉技术组合
        
        Args:
            topic_type: 题材类型
            script_text: 文案文本（可选）
            data: 数据（可选）
        
        Returns:
            dict: 完整视觉方案
        """
        # 1. 获取题材匹配模板
        matrix = cls.MATCH_MATRIX.get(topic_type, cls.MATCH_MATRIX[TYPE_SINGLE_EVENT])
        
        # 2. 分析文案
        script_analysis = cls.analyze_script(script_text)
        
        # 3. 选择最佳视觉技术
        # 地图类型：取第一个推荐
        map_type = matrix['map_type'][0]
        
        # 数据可视化：根据数据密度选择
        if data and len(data) > 5:
            chart_type = matrix['chart_type'][1] if len(matrix['chart_type']) > 1 else matrix['chart_type'][0]
        else:
            chart_type = matrix['chart_type'][0]
        
        # 动画转场：根据节奏选择
        if script_analysis['pacing'] == PACING_FAST:
            transition = matrix['transition'][0]
        elif script_analysis['pacing'] == PACING_SLOW:
            transition = matrix['transition'][-1]
        else:
            transition = matrix['transition'][len(matrix['transition'])//2]
        
        # 文字特效：根据数据密度选择
        if script_analysis['data_density'] > 0.6:
            text_effect = 'number_roll'
        elif script_analysis['emotion'] == EMOTION_NOSTALGIA:
            text_effect = 'typewriter'
        else:
            text_effect = matrix['text_effect'][0]
        
        # 光影特效：根据情绪选择
        emotion_map = {
            EMOTION_POSITIVE: 'neon',
            EMOTION_NEGATIVE: 'glitch',
            EMOTION_SURPRISE: 'flare',
            EMOTION_NOSTALGIA: 'scanline',
            EMOTION_NEUTRAL: 'glass',
        }
        lighting = emotion_map.get(script_analysis['emotion'], matrix['lighting'][0])
        
        # 动态图形
        dynamic = matrix['dynamic'][0]
        
        # 声音设计
        sound = matrix['sound'][0]
        
        # 粒子特效
        particle = matrix.get('particle', False)
        
        # 4. 计算时长
        duration_min, duration_max = matrix['duration_range']
        if script_analysis['pacing'] == PACING_FAST:
            duration = duration_min + (duration_max - duration_min) * 0.3
        elif script_analysis['pacing'] == PACING_SLOW:
            duration = duration_min + (duration_max - duration_min) * 0.8
        else:
            duration = (duration_min + duration_max) / 2
        
        # 数据越多，时长越长
        if data:
            duration = min(duration_max, duration + len(data) * 2)
        
        # 5. 计算置信度
        confidence = 0.7
        if script_text:
            confidence += 0.1
        if data:
            confidence += 0.1
        if script_analysis['char_count'] > 100:
            confidence += 0.05
        confidence = min(confidence, 0.95)
        
        return {
            'topic_type': topic_type,
            'pacing': script_analysis['pacing'],
            'emotion': script_analysis['emotion'],
            'data_density': script_analysis['data_density'],
            
            # 视觉技术选择
            'map_type': map_type,
            'chart_type': chart_type,
            'transition': transition,
            'text_effect': text_effect,
            'lighting': lighting,
            'dynamic': dynamic,
            'sound': sound,
            'particle': particle,
            
            # 时长
            'duration': round(duration),
            
            # 置信度
            'confidence': round(confidence, 2),
            
            # 原始数据
            'script_analysis': script_analysis,
        }
    
    @classmethod
    def get_visual_description(cls, visual_scheme):
        """生成视觉方案的描述文本"""
        tech_names = []
        
        # 地图
        map_info = cls.VISUAL_LIBRARY['map_type'].get(visual_scheme['map_type'], {})
        tech_names.append('地图: %s (%s)' % (map_info.get('name', '未知'), map_info.get('desc', '')))
        
        # 图表
        chart_info = cls.VISUAL_LIBRARY['chart_type'].get(visual_scheme['chart_type'], {})
        tech_names.append('图表: %s (%s)' % (chart_info.get('name', '未知'), chart_info.get('desc', '')))
        
        # 转场
        trans_info = cls.VISUAL_LIBRARY['transition'].get(visual_scheme['transition'], {})
        tech_names.append('转场: %s' % trans_info.get('name', '未知'))
        
        # 文字
        text_info = cls.VISUAL_LIBRARY['text_effect'].get(visual_scheme['text_effect'], {})
        tech_names.append('文字: %s' % text_info.get('name', '未知'))
        
        # 光影
        light_info = cls.VISUAL_LIBRARY['lighting'].get(visual_scheme['lighting'], {})
        tech_names.append('光影: %s' % light_info.get('name', '未知'))
        
        # 动态
        dynamic_info = cls.VISUAL_LIBRARY['dynamic'].get(visual_scheme['dynamic'], {})
        tech_names.append('动态: %s' % dynamic_info.get('name', '未知'))
        
        # 声音
        sound_info = cls.VISUAL_LIBRARY['sound'].get(visual_scheme['sound'], {})
        tech_names.append('声音: %s' % sound_info.get('name', '未知'))
        
        # 粒子
        if visual_scheme['particle']:
            tech_names.append('粒子: 爆发效果')
        
        # 节奏
        pacing_names = {PACING_FAST: '快速', PACING_MEDIUM: '中速', PACING_SLOW: '慢速'}
        tech_names.append('节奏: %s' % pacing_names.get(visual_scheme['pacing'], '中速'))
        
        return '\n'.join(['  - ' + t for t in tech_names])
    
    @classmethod
    def to_render_config(cls, visual_scheme):
        """转换为渲染配置"""
        return {
            'map_type': visual_scheme['map_type'],
            'chart_type': visual_scheme['chart_type'],
            'transition': visual_scheme['transition'],
            'text_effect': visual_scheme['text_effect'],
            'lighting': visual_scheme['lighting'],
            'dynamic': visual_scheme['dynamic'],
            'sound': visual_scheme['sound'],
            'particle': visual_scheme['particle'],
            'duration': visual_scheme['duration'],
            'pacing': visual_scheme['pacing'],
            'emotion': visual_scheme['emotion'],
        }


def demo():
    """演示各种题材的视觉匹配"""
    # 测试用例
    test_cases = [
        (TYPE_SINGLE_EVENT, "穿山跨海的黄金大外环正式通车！这条全长超过1万公里的国道环线，串联起中国最壮观的景观大道。" * 2, []),
        (TYPE_DATA_RANKING, "3340亿！北京公积金缴存额全国第一！上海2660亿排第二，广州1376亿第三..." * 3, [
            {'name': '北京', 'value': '3340亿'}, {'name': '上海', 'value': '2660亿'},
            {'name': '广州', 'value': '1376亿'}, {'name': '深圳', 'value': '1340亿'},
        ]),
        (TYPE_INDUSTRY_ANALYSIS, "新能源汽车产业链从上游锂矿到下游整车，谁在赚钱？" * 3, [
            {'name': '上游', 'value': 30}, {'name': '中游', 'value': 40}, {'name': '下游', 'value': 30},
        ]),
        (TYPE_HISTORICAL_GEO, "巫山26个乡镇的前世今生，三峡库区移民背后的地理变迁，让人感慨万千。" * 3, []),
        (TYPE_POPULATION_FLOW, "103万人流入广东！为什么年轻人更愿意去广东？" * 2, []),
        (TYPE_POLICY_EFFECT, "公积金新规落地！5000万人将受影响，你的钱袋子还能保住吗？" * 2, []),
        (TYPE_COMPARISON, "杭州vs苏州，谁才是最强地级市？两城GDP相差不到1000亿。" * 2, [
            {'name': '杭州', 'value': '18700亿'}, {'name': '苏州', 'value': '19200亿'},
        ]),
        (TYPE_INSTITUTION_ORIGIN, "1984年，一个决定改变了5座城市的命运。计划单列市的由来，你知道吗？" * 3, []),
    ]
    
    print("=" * 80)
    print("视觉匹配决策器 演示")
    print("=" * 80)
    
    for i, (topic_type, script, data) in enumerate(test_cases, 1):
        print("\n【案例 %d】题材: %s" % (i, topic_type))
        print("-" * 60)
        
        scheme = VisualMatcher.match_visual(topic_type, script, data)
        
        print("文案分析:")
        print("  - 节奏: %s | 情绪: %s | 数据密度: %.1f%%" % (
            scheme['pacing'], scheme['emotion'], scheme['data_density']*100))
        print("  - 预估时长: %d秒" % scheme['duration'])
        print("  - 匹配置信度: %.0f%%" % (scheme['confidence']*100))
        
        print("\n匹配视觉方案:")
        print(VisualMatcher.get_visual_description(scheme))
    
    print("\n" + "=" * 80)
    print("视觉匹配决策器可用函数:")
    print("- VisualMatcher.match_visual(topic_type, script_text, data)")
    print("- VisualMatcher.get_visual_description(scheme)")
    print("- VisualMatcher.to_render_config(scheme)")
    print("=" * 80)


if __name__ == '__main__':
    demo()