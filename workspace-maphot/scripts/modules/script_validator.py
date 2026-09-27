# -*- coding: utf-8 -*-
"""
脚本信息密度检测模块
职责：检测生成的脚本是否达到信息密度要求（≥75字/分钟，目标90字/分钟）
输入：脚本JSON + 时长
输出：检测结果（PASS/WARN/FAIL）+ 建议
"""

import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

# 密度标准（字/分钟）
DENSITY_TARGET = 90   # 目标密度
DENSITY_WARN = 80     # 警告阈值
DENSITY_FAIL = 75     # 失败阈值


def check_density(script_json, duration_seconds=None):
    """
    检查脚本信息密度
    
    Args:
        script_json: 脚本JSON字符串或字典
        duration_seconds: 视频总时长（秒），如果为None则从metadata读取
    
    Returns:
        dict: {
            'status': 'PASS' | 'WARN' | 'FAIL',
            'density': 实际密度（字/分钟）,
            'word_count': 总字数,
            'duration_min': 时长（分钟）,
            'pass': bool,
            'messages': [str, ...]
        }
    """
    if isinstance(script_json, str):
        try:
            script = json.loads(script_json)
        except json.JSONDecodeError as e:
            return {'status': 'FAIL', 'pass': False, 'messages': [f'JSON解析失败: {e}']}
    else:
        script = script_json

    # 获取字数
    full_text = script.get('full_text', '')
    word_count = len(full_text)
    
    # 获取时长
    if duration_seconds is None:
        metadata = script.get('metadata', {})
        duration_seconds = metadata.get('estimated_duration_seconds', 0)
    
    if duration_seconds <= 0:
        return {'status': 'FAIL', 'pass': False, 'messages': ['无法获取视频时长']}
    
    duration_min = duration_seconds / 60.0
    density = word_count / duration_min if duration_min > 0 else 0
    
    messages = []
    status = 'PASS'
    pass_ = True
    
    if density >= DENSITY_TARGET:
        status = 'PASS'
        messages.append(f'✅ 密度优秀: {density:.1f}字/分钟（目标{DENSITY_TARGET}）')
    elif density >= DENSITY_WARN:
        status = 'WARN'
        messages.append(f'⚠️ 密度偏低: {density:.1f}字/分钟（目标{DENSITY_TARGET}，建议≥90）')
        messages.append('   建议：增加数据点或解读深度')
        pass_ = True
    elif density >= DENSITY_FAIL:
        status = 'WARN'
        messages.append(f'⚠️ 密度接近下限: {density:.1f}字/分钟（最低{DENSITY_FAIL}）')
        messages.append('   建议：必须增加内容')
        pass_ = True
    else:
        status = 'FAIL'
        pass_ = False
        messages.append(f'❌ 密度不足: {density:.1f}字/分钟（最低{DENSITY_FAIL}）')
        messages.append('   建议：大幅增加数据点、解读深度或比喻说明')
    
    result = {
        'status': status,
        'pass': pass_,
        'density': round(density, 1),
        'word_count': word_count,
        'duration_seconds': int(duration_seconds),
        'duration_min': round(duration_min, 2),
        'messages': messages,
    }
    
    logger.info(f'密度检测: {result["density"]:.1f}字/分钟 | {status} | {word_count}字/{int(duration_seconds)}s')
    return result


def check_story_structure(script_json):
    """
    检查脚本是否采用三层递进结构
    
    Args:
        script_json: 脚本JSON
    
    Returns:
        dict: {
            'has_three_layers': bool,
            'layers': ['现象', '数据', '本质'],
            'issues': [str, ...]
        }
    """
    if isinstance(script_json, str):
        try:
            script = json.loads(script_json)
        except json.JSONDecodeError:
            return {'has_three_layers': False, 'issues': ['JSON解析失败']}
    else:
        script = script_json
    
    sections = script.get('sections', [])
    hook = script.get('hook', {})
    outro = script.get('outro', {})
    
    issues = []
    has_phenomenon = False
    has_essence = False
    
    # 检查钩子是否有认知冲突/反差
    hook_text = hook.get('text', '')
    if any(kw in hook_text for kw in ['为什么', '你以为', '反差', '输了', '出乎', '意外']):
        has_phenomenon = True
    
    # 检查sections是否有数据+解读
    data_sections = 0
    for s in sections:
        narration = s.get('narration', '')
        interpretation = s.get('interpretation', '')
        data_point = s.get('data_point', '')
        if data_point and interpretation:
            data_sections += 1
        # 检查解读是否有比喻词
        if any(kw in interpretation for kw in ['像', '如同', '好比', '就像', '相当于', '相当于']):
            has_phenomenon = True
    
    # 检查结尾是否有金句
    golden = outro.get('golden_sentence', '')
    if golden and len(golden) > 5:
        has_essence = True
    
    # 检查full_text是否有转折词
    full_text = script.get('full_text', '')
    if any(kw in full_text for kw in ['但', '然而', '其实', '真正', '本质', '根子', '关键在于']):
        has_essence = True
    
    has_three_layers = has_phenomenon and data_sections >= 1 and has_essence
    
    if not has_phenomenon:
        issues.append('钩子缺少认知冲突/反差')
    if data_sections < 1:
        issues.append('缺少数据+解读的组合')
    if not has_essence:
        issues.append('缺少本质揭示（第三层）或金句')
    
    return {
        'has_three_layers': has_three_layers,
        'data_sections': data_sections,
        'has_phenomenon': has_phenomenon,
        'has_essence': has_essence,
        'issues': issues,
    }


def validate_script(script_json):
    """
    综合验证脚本质量
    
    Args:
        script_json: 脚本JSON字符串或字典
    
    Returns:
        dict: {
            'overall_pass': bool,
            'density_check': dict,
            'structure_check': dict,
            'warnings': [str, ...],
            'errors': [str, ...]
        }
    """
    if isinstance(script_json, str):
        try:
            script = json.loads(script_json)
        except json.JSONDecodeError as e:
            return {'overall_pass': False, 'errors': [f'JSON解析失败: {e}']}
    else:
        script = script_json
    
    density_result = check_density(script)
    structure_result = check_story_structure(script)
    
    warnings = []
    errors = []
    
    # 合并所有消息
    for msg in density_result.get('messages', []):
        if msg.startswith('❌'):
            errors.append(msg.replace('❌ ', ''))
        elif msg.startswith('⚠️'):
            warnings.append(msg.replace('⚠️ ', ''))
        else:
            warnings.append(msg.replace('✅ ', ''))
    
    for issue in structure_result.get('issues', []):
        warnings.append(f'结构: {issue}')
    
    overall_pass = density_result.get('pass', False) and len(errors) == 0
    
    return {
        'overall_pass': overall_pass,
        'density_check': density_result,
        'structure_check': structure_result,
        'warnings': warnings,
        'errors': errors,
    }


if __name__ == '__main__':
    import argparse
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description='脚本密度检测')
    parser.add_argument('script_path', help='脚本JSON文件路径')
    args = parser.parse_args()
    
    with open(args.script_path, 'r', encoding='utf-8') as f:
        script = json.load(f)
    
    result = validate_script(script)
    
    print(f'=== 脚本质量报告 ===')
    print(f'整体通过: {result["overall_pass"]}')
    print(f'密度: {result["density_check"]["density"]}字/分钟')
    print(f'字数: {result["density_check"]["word_count"]}')
    print(f'时长: {result["density_check"]["duration_seconds"]}s')
    for w in result['warnings']:
        print(f'  ⚠️ {w}')
    for e in result['errors']:
        print(f'  ❌ {e}')
