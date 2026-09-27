# -*- coding: utf-8 -*-
"""
题材匹配决策器 v2 — 根据选题特征自动选择表现手法

核心逻辑：
1. 识别选题类型（基于标题/关键词/数据特征）
2. 匹配表现手法（地图形式+叙事结构+视觉重点）
3. 生成渲染配置（传给对应模板）

题材类型与表现手法映射：
- 单一热点事件 → 实景地图+飞线动画，强调空间关系
- 数据排名对比 → 榜单滚动，强调排序和异常值
- 产业结构分析 → 多层叠加图，强调构成关系
- 历史地理变迁 → 地形剖面+时间线，强调演变过程
- 人口流动迁徙 → 动态流向图，强调路径和规模
"""

import re
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 题材类型定义
TYPE_SINGLE_EVENT = "single_event"       # 单一事件/热点
TYPE_DATA_RANKING = "data_ranking"       # 数据排名对比
TYPE_INDUSTRY_ANALYSIS = "industry_analysis"  # 产业结构分析
TYPE_HISTORICAL_GEO = "historical_geo"   # 历史地理变迁
TYPE_POPULATION_FLOW = "population_flow" # 人口流动迁徙
TYPE_POLICY_EFFECT = "policy_effect"     # 政策影响分析
TYPE_COMPARISON = "comparison"           # 区域对比分析
TYPE_COMPARISON_GEO = "comparison_geo"   # 地理对比分析
TYPE_INSTITUTION_ORIGIN = "institution_origin"  # 制度起源分析

# 表现手法定义
VISUAL_MAP_REALSCENE = "real_scene_map"      # 实景地图
VISUAL_MAP_FLOW = "flow_map"                 # 流向地图
VISUAL_MAP_HEAT = "heatmap"                  # 热力图
VISUAL_MAP_RIBBON = "ribbon_map"             # 带状地图
VISUAL_CHART_LIST = "list_chart"             # 列表图表
VISUAL_CHART_COMPARE = "compare_chart"       # 对比图表
VISUAL_CHART_STACK = "stack_chart"           # 堆叠图表
VISUAL_CHART_RING = "ring_chart"             # 环形进度图

# 叙事结构定义
NARRATIVE_HOOK_DATA = "hook_data"            # 数据钩子开场
NARRATIVE_HOOK_QUESTION = "hook_question"    # 悬念提问开场
NARRATIVE_THREE_LAYER = "three_layer"        # 三层递进（现象→数据→本质）
NARRATIVE_COMPARISON = "comparison"          # 对比贯穿
NARRATIVE_STORY = "story"                    # 故事叙述

class MatchMakerV2:
    """题材匹配决策器"""
    
    # 题材关键词库
    KEYWORDS = {
        TYPE_SINGLE_EVENT: [
            '开通', '建成', '贯通', '开工', '封顶', '投用', '启用',
            '发现', '出土', '建成通车', '正式通车', '开通运营',
            '发现遗址', '出土文物', '重大发现'
        ],
        TYPE_DATA_RANKING: [
            '排名', 'TOP', '榜单', '排行', '最强', '最多', '最少',
            '增长', '下降', '涨幅', '跌幅', '全国第一', '榜首'
        ],
        TYPE_INDUSTRY_ANALYSIS: [
            '产业', '产能', '产量', '产值', '集群', '链条',
            '供应链', '产业链', '上游', '下游', '龙头', '支柱'
        ],
        TYPE_HISTORICAL_GEO: [
            '历史', '古城', '遗址', '故都', '朝代', '千年',
            '变迁', '演变', '兴衰', '前世今生', '原来', '竟然'
        ],
        TYPE_POPULATION_FLOW: [
            '人口', '流入', '流出', '迁移', '迁徙', '打工',
            '招工', '人才', '抢人', '净流出', '净流入'
        ],
        TYPE_POLICY_EFFECT: [
            '政策', '新规', '落地', '影响', '利好', '利空',
            '调控', '限制', '放开', '补贴', '减税'
        ],
        TYPE_COMPARISON: [
            'vs', '对比', '区别', '差异', '不如', '胜过',
            '差距', '吊打', '碾压', '完胜'
        ],
        TYPE_INSTITUTION_ORIGIN: [
            '起源', '由来', '背景', '历史', '设立', '建立',
            '为什么', '是什么', '制度', '政策', '改革'
        ]
    }
    
    # 题材特征权重（用于综合评分）
    FEATURE_WEIGHTS = {
        'has_numbers': 0.3,      # 包含数字
        'has_locations': 0.2,    # 包含地点
        'has_comparison': 0.2,   # 包含对比词
        'has_time': 0.1,         # 包含时间词
        'has_event': 0.2,        # 包含事件词
    }
    
    # 开场钩子库（根据题材类型匹配）
    HOOK_TEMPLATES = {
        TYPE_DATA_RANKING: [
            '数字冲击型：{badge_text}！全国第一！',
            '悬念提问型：{title}，你知道排第几吗？',
            '场景代入型：每个{subtitle}的人，都关心这个排名',
        ],
        TYPE_SINGLE_EVENT: [
            '悬念提问型：{title}，背后是什么逻辑？',
            '场景代入型：{title}，改变了多少人的命运？',
        ],
        TYPE_COMPARISON: [
            '反差对比型：{south_label} vs {north_label}，谁更强？',
            '悬念提问型：为什么{north_label}能超越{south_label}？',
        ],
        TYPE_HISTORICAL_GEO: [
            '历史钩子型：{year}年，一个决定改变了{location}的命运',
            '悬念揭秘型：{title}，真相让人意外',
        ],
        TYPE_POPULATION_FLOW: [
            '数字冲击型：{flow_number}万人流入，谁是最大赢家？',
            '悬念提问型：为什么{source}的人都要去{target}？',
        ],
        TYPE_INDUSTRY_ANALYSIS: [
            '场景代入型：{industry}产业链，到底谁在赚钱？',
            '悬念提问型：{title}，背后藏着什么秘密？',
        ],
        TYPE_POLICY_EFFECT: [
            '数字冲击型：{policy_number}条新规，影响多少人的钱袋子？',
            '场景代入型：{title}，和你有什么关系？',
        ],
        TYPE_COMPARISON_GEO: [
            '反差对比型：{location_a} vs {location_b}，差距有多大？',
            '悬念提问型：为什么{location_a}比{location_b}强这么多？',
        ],
        TYPE_INSTITUTION_ORIGIN: [
            '历史钩子型：{year}年，一个决定改变了{location}的命运',
            '悬念揭秘型：{title}，真相让人意外',
            '概念澄清型：你知道{concept}吗？',
        ],
    }
    
    # 表现手法库（根据题材类型匹配）
    NARRATIVE_TECHNIQUES = {
        TYPE_DATA_RANKING: {
            'technique': '榜单滚动型',
            'description': 'N行逐条slide-in，每行2-3秒，异常值红色强调',
            'animation': 'scroll_list',
            'pacing': 'fast',
            'key_elements': ['rank_row_slide_in', 'anomaly_highlight', 'ring_progress'],
        },
        TYPE_SINGLE_EVENT: {
            'technique': '场景展示型',
            'description': '实景地图+飞线动画，突出空间关系',
            'animation': 'flyline',
            'pacing': 'medium',
            'key_elements': ['map_real_scene', 'flyline_animation', 'point_marker'],
        },
        TYPE_COMPARISON_GEO: {
            'technique': '剖面对比型',
            'description': '地形剖面图+数据并排对比',
            'animation': 'profile_compare',
            'pacing': 'medium',
            'key_elements': ['terrain_profile', 'side_by_side', 'data_highlight'],
        },
        TYPE_HISTORICAL_GEO: {
            'technique': '时间轴推进型',
            'description': '历史节点逐个展示，时间轴动画',
            'animation': 'timeline',
            'pacing': 'slow',
            'key_elements': ['timeline_navigation', 'node_popup', 'map_evolve'],
        },
        TYPE_POPULATION_FLOW: {
            'technique': '流向可视化型',
            'description': '贝塞尔曲线流动动画，箭头表示方向',
            'animation': 'flow_lines',
            'pacing': 'medium',
            'key_elements': ['flow_curve_animation', 'arrow_indicator', 'scale_by_volume'],
        },
        TYPE_INDUSTRY_ANALYSIS: {
            'technique': '多层叠加型',
            'description': '产业链条可视化，上下游关系箭头',
            'animation': 'stack_layers',
            'pacing': 'slow',
            'key_elements': ['layer_overlay', 'chain_visualization', 'relationship_arrow'],
        },
        TYPE_POLICY_EFFECT: {
            'technique': '热力图脉冲型',
            'description': '热力图展示影响范围，数据对比面板',
            'animation': 'heatmap_pulse',
            'pacing': 'medium',
            'key_elements': ['heatmap_gradient', 'pulse_effect', 'data_panel'],
        },
        TYPE_COMPARISON_GEO: {
            'technique': '剖面对比型',
            'description': '地形剖面图+数据并排对比',
            'animation': 'profile_compare',
            'pacing': 'medium',
            'key_elements': ['terrain_profile', 'side_by_side', 'data_highlight'],
        },
        TYPE_INSTITUTION_ORIGIN: {
            'technique': '时间轴推进型',
            'description': '历史节点逐个展示，时间轴动画',
            'animation': 'timeline',
            'pacing': 'slow',
            'key_elements': ['timeline_navigation', 'node_popup', 'map_evolve'],
        },
    }
    
    @classmethod
    def classify_topic(cls, title, subtitle='', data=None):
        """
        识别选题类型
        
        Args:
            title: 标题
            subtitle: 副标题/说明
            data: 可选的数据特征（如是否有数值列、是否有多城市等）
        
        Returns:
            str: 题材类型
            dict: 识别特征和置信度
        """
        text = f"{title} {subtitle}".lower()
        scores = {}
        
        # 关键词匹配
        for topic_type, keywords in cls.KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text)
            scores[topic_type] = score
        
        # 数字特征检测（排名类通常有数值）
        if data and isinstance(data, list):
            numeric_count = sum(1 for item in data if isinstance(item, dict) and 'value' in item)
            if numeric_count > 3:
                scores[TYPE_DATA_RANKING] += 1
        
        # 地点特征检测
        location_keywords = ['省', '市', '县', '区', '镇', '村', '国', '城']
        loc_count = sum(1 for kw in location_keywords if kw in text)
        if loc_count >= 2:
            scores[TYPE_COMPARISON] += 1
            scores[TYPE_SINGLE_EVENT] += 1
        
        # 选择最高分
        if not scores:
            return TYPE_SINGLE_EVENT, {'confidence': 0.5, 'reason': 'default'}
        
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        total_score = sum(scores.values())
        confidence = best_score / max(total_score, 1)
        
        return best_type, {
            'scores': scores,
            'confidence': min(confidence, 0.95),
            'reason': cls._get_reason(best_type, scores)
        }
    
    @classmethod
    def _get_reason(cls, topic_type, scores):
        """获取分类理由"""
        reasons = {
            TYPE_SINGLE_EVENT: '检测到事件关键词（开通/建成/发现等）',
            TYPE_DATA_RANKING: '检测到排名关键词（排名/TOP/榜单等）或数值数据',
            TYPE_INDUSTRY_ANALYSIS: '检测到产业关键词（产能/产业链/集群等）',
            TYPE_HISTORICAL_GEO: '检测到历史关键词（古城/遗址/变迁等）',
            TYPE_POPULATION_FLOW: '检测到人口关键词（流入/流出/迁移等）',
            TYPE_POLICY_EFFECT: '检测到政策关键词（新规/落地/影响等）',
            TYPE_COMPARISON: '检测到对比关键词（vs/对比/差距等）',
            TYPE_INSTITUTION_ORIGIN: '检测到起源/制度关键词（起源/由来/设立等）'
        }
        return reasons.get(topic_type, '默认分类')
    
    @classmethod
    def get_visual_config(cls, topic_type, data=None):
        """
        根据题材类型获取表现配置
        
        Returns:
            dict: 包含地图形式、叙事结构、视觉重点的配置
        """
        configs = {
            TYPE_SINGLE_EVENT: {
                'map_style': VISUAL_MAP_REALSCENE,
                'narrative': NARRATIVE_HOOK_DATA,
                'visual_focus': 'space_relation',  # 强调空间关系
                'animation_type': 'flyline',        # 飞线动画
                'template': 'hyperframes_real_scene',
                'duration_range': (45, 70),         # 秒
                'style_notes': '实景地图底图，飞线标注路径，点位突出关键位置'
            },
            TYPE_DATA_RANKING: {
                'map_style': VISUAL_MAP_HEAT,
                'narrative': NARRATIVE_THREE_LAYER,
                'visual_focus': 'ranking',          # 强调排序
                'animation_type': 'scroll_list',    # 榜单滚动
                'template': 'hyperframes_ranking',
                'duration_range': (40, 60),
                'style_notes': '榜单逐条slide-in，异常值红色强调，圆环进度展示关键数据'
            },
            TYPE_INDUSTRY_ANALYSIS: {
                'map_style': VISUAL_MAP_HEAT,
                'narrative': NARRATIVE_THREE_LAYER,
                'visual_focus': 'structure',        # 强调结构
                'animation_type': 'stack_layers',   # 多层叠加
                'template': 'hyperframes_industry',
                'duration_range': (60, 90),
                'style_notes': '产业链条可视化，上下游关系箭头，产业集群分布'
            },
            TYPE_HISTORICAL_GEO: {
                'map_style': VISUAL_MAP_RIBBON,
                'narrative': NARRATIVE_STORY,
                'visual_focus': 'timeline',         # 强调时间线
                'animation_type': 'timeline_fade',  # 时间线淡入淡出
                'template': 'hyperframes_historical',
                'duration_range': (60, 120),
                'style_notes': '地形剖面图，历史点位逐个标注，时间轴推进'
            },
            TYPE_POPULATION_FLOW: {
                'map_style': VISUAL_MAP_FLOW,
                'narrative': NARRATIVE_COMPARISON,
                'visual_focus': 'flow',             # 强调流向
                'animation_type': 'flow_lines',     # 流动线条
                'template': 'hyperframes_flow',
                'duration_range': (50, 80),
                'style_notes': '流向线条动画，箭头表示方向，粗细表示规模'
            },
            TYPE_POLICY_EFFECT: {
                'map_style': VISUAL_MAP_HEAT,
                'narrative': NARRATIVE_THREE_LAYER,
                'visual_focus': 'impact',           # 强调影响
                'animation_type': 'heatmap_pulse',  # 热力图脉冲
                'template': 'hyperframes_policy',
                'duration_range': (45, 70),
                'style_notes': '热力图展示影响范围，数据对比面板，影响程度分级'
            },
            TYPE_COMPARISON: {
                'map_style': VISUAL_MAP_REALSCENE,
                'narrative': NARRATIVE_COMPARISON,
                'visual_focus': 'contrast',         # 强调对比
                'animation_type': 'split_screen',   # 分屏对比
                'template': 'hyperframes_comparison',
                'duration_range': (40, 60),
                'style_notes': '对比双栏布局，stagger入场，数据面板并排'
            },
            TYPE_INSTITUTION_ORIGIN: {
                'map_style': VISUAL_MAP_RIBBON,
                'narrative': NARRATIVE_STORY,
                'visual_focus': 'timeline',         # 强调时间线
                'animation_type': 'timeline_fade',  # 时间线淡入淡出
                'template': 'hyperframes_institution',
                'duration_range': (60, 90),
                'style_notes': '时间轴推进，历史节点逐个标注，地图变迁动画'
            }
        }
        
        return configs.get(topic_type, configs[TYPE_SINGLE_EVENT])
    
    @classmethod
    def generate_config(cls, title, subtitle='', data=None, custom_config=None):
        """
        生成完整渲染配置
        
        Args:
            title: 标题
            subtitle: 副标题
            data: 数据（可选）
            custom_config: 自定义配置（可选，会覆盖自动检测的部分）
        
        Returns:
            dict: 完整配置
        """
        # 1. 题材分类
        topic_type, classify_info = cls.classify_topic(title, subtitle, data)
        
        # 2. 获取表现配置
        visual_config = cls.get_visual_config(topic_type, data)
        
        # 3. 合并配置
        config = {
            'topic_type': topic_type,
            'classify_info': classify_info,
            'visual_config': visual_config,
            'title': title,
            'subtitle': subtitle,
            'data': data or [],
        }
        
        # 4. 应用自定义配置
        if custom_config:
            for key, value in custom_config.items():
                if key in config:
                    config[key] = value
                elif key in visual_config:
                    visual_config[key] = value
        
        # 5. 计算时长
        duration_min, duration_max = visual_config['duration_range']
        data_count = len(data) if data else 0
        # 数据越多，时长越长
        config['estimated_duration'] = min(duration_max, duration_min + data_count * 3)
        
        return config
    
    @classmethod
    def to_render_config(cls, title, subtitle='', data=None, custom_config=None, map_image='egg_price_map.png'):
        """
        生成 pipeline 可直接使用的渲染配置
        
        返回 dict 格式与 pipeline 的 config 兼容，包含:
        - video_type: 'ranking' 或其他
        - template_name: 模板文件名
        - 模板参数: 直接传给 generate_html()
        """
        # 1. 获取题材分类和表现配置
        topic_type, classify_info = cls.classify_topic(title, subtitle, data)
        visual_config = cls.get_visual_config(topic_type, data)
        
        # 2. 生成基础配置
        config = cls.generate_config(title, subtitle, data, custom_config)
        
        # 3. 生成渲染专用配置
        render_config = {
            # 基础信息
            'title': title,
            'subtitle': subtitle,
            'video_type': 'ranking' if topic_type == TYPE_DATA_RANKING else 'city',
            'topic_type': topic_type,
            'map_image': map_image,
            
            # 模板选择
            'template': visual_config['template'],
            
            # 排名类参数（data_ranking）
            'rank_items': data or [],
            'ring_value': 0,
            'ring_label': '',
            
            # 对比类参数（comparison）
            'compare_south': {},
            'compare_north': {},
            'anomaly_highlight': None,
            
            # 通用参数
            'outro_question': '你怎么看？',
            'outro_sub': '评论区告诉我',
            'options': [],
            'cta_text': '点赞关注，每天看数据',
        }
        
        # 4. 根据题材类型填充参数
        if topic_type == TYPE_DATA_RANKING:
            render_config['video_type'] = 'ranking'
            render_config['ring_label'] = visual_config.get('visual_focus', '数据')
            
            # 提取排名数据
            if data:
                render_config['rank_items'] = data
                # 找异常值
                for i, item in enumerate(data):
                    if item.get('is_anomaly', False):
                        render_config['anomaly_highlight'] = item
                        break
                
                # 默认异常值：倒数第2名
                if not render_config['anomaly_highlight'] and len(data) > 2:
                    render_config['anomaly_highlight'] = data[-2]
            
            # 对比双栏（如果有两个主要对比对象）
            if len(data) >= 2:
                render_config['compare_south'] = {
                    'label': data[0].get('name', 'A'),
                    'value': data[0].get('value', ''),
                    'sub': data[0].get('note', '')
                }
                render_config['compare_north'] = {
                    'label': data[1].get('name', 'B'),
                    'value': data[1].get('value', ''),
                    'sub': data[1].get('note', '')
                }
        
        elif topic_type == TYPE_COMPARISON:
            render_config['video_type'] = 'comparison'
            # 从标题提取对比双方
            if 'vs' in title.lower() or '对比' in title:
                parts = re.split(r'[vsVS对比比]', title)
                if len(parts) >= 2:
                    render_config['compare_south'] = {
                        'label': parts[0].strip(),
                        'value': custom_config.get('south_val', '') if custom_config else '',
                        'sub': custom_config.get('south_sub', '') if custom_config else ''
                    }
                    render_config['compare_north'] = {
                        'label': parts[1].strip(),
                        'value': custom_config.get('north_val', '') if custom_config else '',
                        'sub': custom_config.get('north_sub', '') if custom_config else ''
                    }
        
        # 5. 应用自定义配置覆盖
        if custom_config:
            render_config.update(custom_config)
        
        # 6. 添加分类信息（供日志使用）
        render_config['classify_info'] = classify_info
        render_config['visual_config'] = visual_config
        
        return render_config


def demo():
    """演示各种题材的匹配结果"""
    test_cases = [
        # (标题, 副标题, 数据示例)
        ("穿山跨海的黄金大外环", "三条国道如何串联起中国最壮观的景观大道", []),
        ("公积金缴存20强城市排名", "2025年全国城市排名公布", [
            {'name': '北京', 'value': '3340亿', 'per_capita': '3.5万'},
            {'name': '上海', 'value': '2660亿', 'per_capita': '2.8万'},
            {'name': '广州', 'value': '1376亿', 'per_capita': '2.6万'},
            {'name': '深圳', 'value': '1340亿', 'per_capita': '1.78万'},
        ]),
        ("江苏GDP为何能超越广东", "经济总量第一的宝座易主？", []),
        ("巫山26个乡镇前世今生", "三峡库区移民背后的地理变迁", []),
        ("广东人口为何能逆势增长", "为什么年轻人更愿意去广东？", []),
        ("杭州vs苏州：谁才是最强地级市", "两城GDP相差不到1000亿", []),
    ]
    
    print("=" * 80)
    print("题材匹配决策器 v2 演示")
    print("=" * 80)
    
    for i, (title, subtitle, data) in enumerate(test_cases, 1):
        print(f"\n【案例 {i}】{title}")
        print("-" * 60)
        
        config = MatchMakerV2.generate_config(title, subtitle, data)
        
        print(f"题材类型: {config['topic_type']}")
        print(f"分类置信度: {config['classify_info']['confidence']:.1%}")
        print(f"分类理由: {config['classify_info']['reason']}")
        print(f"预估时长: {config['estimated_duration']:.0f}秒")
        print(f"地图形式: {config['visual_config']['map_style']}")
        print(f"叙事结构: {config['visual_config']['narrative']}")
        print(f"视觉重点: {config['visual_config']['visual_focus']}")
        print(f"动画类型: {config['visual_config']['animation_type']}")
        print(f"使用模板: {config['visual_config']['template']}")
        print(f"风格备注: {config['visual_config']['style_notes']}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    demo()
