# -*- coding: utf-8 -*-
"""
WebNovel-Writer 集成层
======================
将 WebNovel-Writer 的核心功能暴露给 V7.0 流程引擎调用
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

# 添加 WebNovel-Writer 路径
WEBNOVEL_PATH = Path(r'C:\Users\Administrator\.openclaw\workspace\skills\webnovel-writer\webnovel-writer')
if WEBNOVEL_PATH.exists():
    sys.path.insert(0, str(WEBNOVEL_PATH))
    sys.path.insert(0, str(WEBNOVEL_PATH / 'scripts'))

class WebNovelIntegration:
    """WebNovel-Writer 集成器"""
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = Path(project_path) if project_path else None
        self.state = None
        self._load_state()
    
    def _load_state(self):
        """加载项目状态"""
        if self.project_path:
            state_file = self.project_path / '.webnovel' / 'state.json'
            if state_file.exists():
                with open(state_file, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
    
    def init_project(self, title: str, genre: str, word_count_target: int = 1000000) -> Dict:
        """
        初始化项目（对应 /webnovel-init）
        
        Args:
            title: 小说标题
            genre: 题材类型
            word_count_target: 目标字数
        
        Returns:
            初始化结果
        """
        try:
            from init_project import init_project as wn_init
            
            result = wn_init(
                title=title,
                genre=genre,
                word_count_target=word_count_target,
                project_path=self.project_path
            )
            
            return {
                'success': True,
                'message': f'项目 {title} 初始化成功',
                'state': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'note': 'WebNovel-Writer 初始化失败，可降级使用 V7.0 本地流程'
            }
    
    def plan_outline(self, volume_num: int, chapter_range: str = None) -> Dict:
        """
        大纲规划（对应 /webnovel-plan）
        
        Args:
            volume_num: 卷号
            chapter_range: 章节范围（如 "1-10"）
        
        Returns:
            大纲规划结果
        """
        try:
            # 调用 WebNovel-Writer 的大纲规划功能
            from workflow_manager import WorkflowManager
            
            wm = WorkflowManager(project_path=self.project_path)
            result = wm.plan_volume(volume_num, chapter_range)
            
            return {
                'success': True,
                'outline': result,
                'source': 'WebNovel-Writer'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'fallback': '可使用 V7.0 知识卡片推荐进行大纲设计'
            }
    
    def write_chapter(self, chapter_num: int, context: Dict = None) -> Dict:
        """
        章节创作（对应 /webnovel-write）
        
        Args:
            chapter_num: 章节号
            context: 上下文信息
        
        Returns:
            创作结果
        """
        try:
            from workflow_manager import WorkflowManager
            
            wm = WorkflowManager(project_path=self.project_path)
            result = wm.write_chapter(chapter_num, context)
            
            return {
                'success': True,
                'content': result,
                'source': 'WebNovel-Writer'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'fallback': '可使用 V7.0 流程引擎进行章节创作'
            }
    
    def review_chapter(self, chapter_num: int, chapter_content: str) -> Dict:
        """
        内容审核（对应 /webnovel-review）
        
        Args:
            chapter_num: 章节号
            chapter_content: 章节内容
        
        Returns:
            审核结果
        """
        try:
            # 调用 WebNovel-Writer 的多维审查
            from golden_three_checker import GoldenThreeChecker
            
            checker = GoldenThreeChecker(project_path=self.project_path)
            result = checker.check_chapter(chapter_num, chapter_content)
            
            return {
                'success': True,
                'review': result,
                'source': 'WebNovel-Writer 六维审查'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'fallback': '可使用 V7.0 规则审核器'
            }
    
    def query_entity(self, entity_name: str) -> Dict:
        """
        信息查询（对应 /webnovel-query）
        
        Args:
            entity_name: 实体名称（角色/地点/伏笔等）
        
        Returns:
            查询结果
        """
        try:
            from query_router import QueryRouter
            
            qr = QueryRouter(project_path=self.project_path)
            result = qr.query(entity_name)
            
            return {
                'success': True,
                'data': result,
                'source': 'WebNovel-Writer 知识库'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_project_status(self) -> Dict:
        """
        获取项目状态（对应 /webnovel-dashboard）
        
        Returns:
            项目状态报告
        """
        try:
            from status_reporter import StatusReporter
            
            sr = StatusReporter(project_path=self.project_path)
            result = sr.generate_report()
            
            return {
                'success': True,
                'status': result,
                'source': 'WebNovel-Writer'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def resume_from_checkpoint(self) -> Dict:
        """
        断点恢复（对应 /webnovel-resume）
        
        Returns:
            恢复结果
        """
        try:
            from workflow_manager import WorkflowManager
            
            wm = WorkflowManager(project_path=self.project_path)
            result = wm.resume()
            
            return {
                'success': True,
                'resumed': result,
                'source': 'WebNovel-Writer'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# 便捷函数
def get_webnovel_integration(project_path: str = None) -> WebNovelIntegration:
    """获取 WebNovel-Writer 集成器实例"""
    return WebNovelIntegration(project_path)


# 测试
if __name__ == '__main__':
    print('=== WebNovel-Writer 集成测试 ===')
    
    integration = WebNovelIntegration()
    
    # 测试项目状态查询
    print('\n测试项目状态查询:')
    result = integration.get_project_status()
    print(f'  状态：{result.get("success", False)}')
    if result.get('success'):
        print(f'  数据：{str(result.get("status", {}))[:200]}...')
    else:
        print(f'  错误：{result.get("error", "Unknown")}')
