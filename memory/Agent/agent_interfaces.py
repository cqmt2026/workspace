# -*- coding: utf-8 -*-
"""
Agent 接口增强
支持编辑、优化、审核等小说创作功能
"""

import sys
from pathlib import Path

# 添加路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

class NovelAgent:
    """小说创作 Agent"""
    
    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        self.workflow_engine = self._load_workflow_engine()
    
    def _load_knowledge_base(self):
        """加载知识库"""
        import json
        kb_path = BASE_DIR / 'knowledge_base.json'
        with open(kb_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_workflow_engine(self):
        """加载流程引擎"""
        from creation_workflow_engine import CreationWorkflowEngine
        return CreationWorkflowEngine()
    
    def _edit_chapter(self, params):
        """编辑章节"""
        chapter_num = params.get('chapter_num')
        edits = params.get('edits', [])
        
        # 读取章节
        chapter_path = self._get_chapter_path(chapter_num)
        with open(chapter_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 应用编辑
        for edit in edits:
            old = edit.get('old')
            new = edit.get('new')
            if old and new:
                content = content.replace(old, new)
        
        # 保存
        with open(chapter_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {'success': True, 'chapter_num': chapter_num}
    
    def _optimize_chapter(self, params):
        """优化章节（融合 content-writer-pro）"""
        chapter_num = params.get('chapter_num')
        
        # 使用 V7.0 引擎进行优化
        result = self.workflow_engine.execute_stage('quality_review', {
            'chapter_num': chapter_num
        })
        
        return result
    
    def _review_chapter(self, params):
        """审核章节（增强一致性审核 + ML 审核）"""
        chapter_num = params.get('chapter_num')
        chapter_path = self._get_chapter_path(chapter_num)
        
        results = {}
        
        # 1. 基础质量检查
        from auto_quality_checker import AutoQualityChecker
        checker = AutoQualityChecker()
        basic_result = checker.check_on_save(chapter_path, chapter_num)
        results['basic'] = basic_result
        
        # 2. 规则审核（基础检查，非 ML）
        try:
            import sys
            sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-novel\创作系统\L2-工具\02-脚本工具')
            from rule_based_reviewer import RuleBasedReviewer
            reviewer = RuleBasedReviewer(chapter_path)
            rule_result = reviewer.review_all()
            results['rule_based'] = rule_result
        except Exception as e:
            results['rule_based'] = {'success': False, 'error': str(e)}
        
        # 3. 综合判断
        passed = basic_result.get('passed', False)
        if 'rule_based' in results and results['rule_based'].get('success'):
            rule_passed = results['rule_based'].get('result', {}).get('total_score', {}).get('passed', False)
            passed = passed and rule_passed
        
        results['overall_passed'] = passed
        results['note'] = '规则检查仅供参考，建议人工审核'
        return results
    
    def _get_chapter_path(self, chapter_num):
        """获取章节文件路径"""
        # 默认路径
        base = BASE_DIR.parent.parent / '项目一：鉴城师' / 'L4-shared' / '正文'
        return base / f'第{chapter_num}章.md'


# 测试
if __name__ == '__main__':
    agent = NovelAgent()
    print('[OK] NovelAgent 初始化完成')
    print(f'  - 知识卡片：{agent.knowledge_base["total_cards"]}篇')
    print(f'  - 流程节点：{agent.workflow_engine.get_workflow_status()["total_stages"]}个')
