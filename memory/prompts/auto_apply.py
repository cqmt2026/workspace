# -*- coding: utf-8 -*-
"""
模板自动应用系统（带钩子集成）
根据场景自动匹配和应用模板
"""

import re
from pathlib import Path

# 模板库路径
TEMPLATE_FILE = Path(__file__).parent / 'templates.md'


def load_templates():
    """加载模板库"""
    templates = {
        'novel_chapter': '',
        'social_media': '',
        'market_report': '',
        'session_summary': ''
    }
    
    if not TEMPLATE_FILE.exists():
        return templates
    
    # TODO: 实现模板加载逻辑
    return templates


def match_template(scene, context=None):
    """根据场景匹配模板"""
    template_map = {
        'novel': 'novel_chapter',
        'social_media': 'social_media',
        'analysis': 'market_report',
        'summary': 'session_summary'
    }
    
    template_key = template_map.get(scene, None)
    
    if template_key:
        templates = load_templates()
        return templates.get(template_key, None)
    
    return None


def apply_template(template, variables):
    """应用模板生成内容"""
    if not template:
        return ''
    
    content = template
    
    for key, value in variables.items():
        placeholder = f'[{key}]'
        content = content.replace(placeholder, str(value))
    
    return content


def auto_apply(scene, context):
    """自动应用模板"""
    result = {
        'success': False,
        'template': None,
        'content': '',
        'message': ''
    }
    
    template = match_template(scene, context)
    
    if not template:
        result['message'] = f'未找到 {scene} 场景的模板'
        return result
    
    result['template'] = template
    
    variables = prepare_variables(scene, context)
    content = apply_template(template, variables)
    
    if content:
        result['success'] = True
        result['content'] = content
        result['message'] = f'成功应用 {scene} 场景模板'
    else:
        result['message'] = '模板应用失败'
    
    return result


def prepare_variables(scene, context):
    """准备模板变量"""
    variables = {}
    
    if scene == 'novel':
        variables = {
            'chapter_num': context.get('chapter_num', 'XX'),
            'chapter_title': context.get('chapter_title', '章节名'),
            'outline': context.get('outline', ''),
            'shuangdian': context.get('shuangdian', '打脸/突破')
        }
    
    elif scene == 'social_media':
        variables = {
            'title': context.get('title', '标题'),
            'topic': context.get('topic', '主题'),
            'target_audience': context.get('target_audience', '读者画像')
        }
    
    elif scene == 'summary':
        variables = {
            'date': context.get('date', 'YYYY-MM-DD'),
            'completed': context.get('completed', []),
            'todos': context.get('todos', []),
            'decisions': context.get('decisions', [])
        }
    
    return variables


# ============= 钩子集成 =============

_hook_engine = None

def get_hook_engine():
    """获取钩子引擎（单例）"""
    global _hook_engine
    
    if _hook_engine is None:
        try:
            import sys
            workspace_root = Path(r'C:\Users\Administrator\.openclaw\workspace')
            sys.path.insert(0, str(workspace_root))
            
            from hooks.engine import HookEngine, Hook, Events, HookPriority
            from hooks.auto_save import AutoSaveHook
            
            _hook_engine = HookEngine()
            
            # 创建自动保存钩子
            auto_save = AutoSaveHook()
            
            def on_chapter_complete(data):
                """章节完成回调（带自动协作）"""
                chapter_num = data.get('chapter_num', '?')
                title = data.get('title', '无题')
                
                print(f"[钩子] 章节完成：第{chapter_num}章《{title}》")
                
                # 1. 自动保存
                auto_save_result = auto_save.execute(data)
                if auto_save_result['success']:
                    print(f"[钩子] 保存成功：{auto_save_result['path']}")
                
                # 2. 自动调用编排器协作
                collaboration_result = trigger_orchestrator(data)
                if collaboration_result['success']:
                    print(f"[钩子] 编排器协作已触发")
                else:
                    print(f"[WARN] 编排器协作失败：{collaboration_result.get('error', '未知错误')}")
                
                # 3. 记录日志
                log_collaboration({
                    'chapter': chapter_num,
                    'title': title,
                    'save': auto_save_result,
                    'collaboration': collaboration_result,
                    'timestamp': str(Path.home())
                })
                
                return {
                    'success': True,
                    'save': auto_save_result,
                    'collaboration': collaboration_result
                }
            
            # 注册钩子
            hook = Hook(
                name='chapter_auto_save',
                event=Events.CHAPTER_COMPLETE,
                callback=on_chapter_complete,
                priority=HookPriority.NORMAL
            )
            
            _hook_engine.register(hook)
            print('[OK] 钩子引擎已初始化')
            
        except Exception as e:
            print(f'[WARN] 钩子引擎初始化失败：{e}')
            _hook_engine = None
    
    return _hook_engine


def trigger_chapter_complete(chapter_num, title, content):
    """
    触发章节完成钩子
    
    参数:
        chapter_num: 章节号
        title: 章节标题
        content: 章节内容
    
    返回:
        dict: 执行结果
    """
    engine = get_hook_engine()
    
    if engine:
        try:
            from hooks.engine import Events
            
            result = engine.trigger(Events.CHAPTER_COMPLETE, {
                'chapter_num': chapter_num,
                'title': title,
                'content': content
            })
            
            return {
                'success': True,
                'hooks_executed': len(result),
                'results': [r.__dict__ for r in result]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    else:
        return {
            'success': False,
            'error': '钩子引擎未初始化'
        }


def trigger_orchestrator(data):
    """
    触发编排器协作
    
    参数:
        data: 章节数据
    
    返回:
        dict: 协作结果
    """
    try:
        import subprocess
        
        chapter_num = data.get('chapter_num', '?')
        title = data.get('title', '无题')
        content = data.get('content', '')
        
        # 构建编排器命令
        prompt = f"小说第{chapter_num}章《{title}》完成，字数{len(content)}，生成推广内容和分析报告"
        
        # 使用完整路径调用 openclaw
        openclaw_path = r'C:\Users\Administrator\AppData\Roaming\npm\openclaw.ps1'
        
        # 调用编排器（异步，不阻塞）- 使用正确的命令格式
        result = subprocess.run(
            [
                'powershell', '-ExecutionPolicy', 'Bypass', '-File', openclaw_path,
                'agency-agents',
                '--orchestrator',
                prompt
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 分钟超时
        )
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.returncode != 0 else ''
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': '编排器执行超时（>5 分钟）'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def log_collaboration(info):
    """
    记录协作日志
    
    参数:
        info: 协作信息
    """
    try:
        log_file = Path(__file__).parent.parent / 'workspace-novel/创作系统/L1-日志/collaboration.log'
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'chapter': info.get('chapter'),
            'title': info.get('title'),
            'save_success': info.get('save', {}).get('success', False),
            'collaboration_success': info.get('collaboration', {}).get('success', False),
        }
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{log_entry['timestamp']}] 第{log_entry['chapter']}章 - "
                   f"保存：{'✅' if log_entry['save_success'] else '❌'} - "
                   f"协作：{'✅' if log_entry['collaboration_success'] else '❌'}\n")
        
    except Exception as e:
        print(f'[WARN] 日志记录失败：{e}')

# ====================================


def main():
    """测试函数"""
    print('=' * 60)
    print('模板自动应用测试')
    print('=' * 60)
    
    # 测试场景 1：小说章节
    print('\n【测试 1】小说章节')
    context = {
        'chapter_num': 42,
        'chapter_title': '拒绝收买',
        'outline': '陆鸣拒绝赵德明的一百万收买',
        'shuangdian': '主角坚持原则'
    }
    result = auto_apply('novel', context)
    print(f"成功：{result['success']}")
    print(f"消息：{result['message']}")
    
    # 测试场景 2：会话摘要
    print('\n【测试 2】会话摘要')
    context = {
        'date': '2026-04-04',
        'completed': ['P0 任务 1', 'P0 任务 2'],
        'todos': ['P0 任务 3'],
        'decisions': ['分阶段实施方案 C']
    }
    result = auto_apply('summary', context)
    print(f"成功：{result['success']}")
    print(f"消息：{result['message']}")
    
    print('\n' + '=' * 60)


if __name__ == '__main__':
    main()
