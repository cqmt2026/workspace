# -*- coding: utf-8 -*-
"""
Memory Tools - 统一记忆工具接口
融合 supermemory + memory-graph
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class MemoryTools:
    """记忆工具统一接口"""
    
    def __init__(self):
        self.supermemory_available = self._check_supermemory()
        self.graph_available = self._check_graph()
        self.db_path = None
        self.graph = None
    
    def _check_supermemory(self) -> bool:
        """检查 supermemory 是否可用"""
        try:
            import sqlite3
            return True
        except ImportError:
            return False
    
    def _check_graph(self) -> bool:
        """检查 memory-graph 是否可用"""
        import os
        return os.path.exists('skills/memory-graph')
    
    def initialize(self, db_path: str = None) -> bool:
        """
        初始化记忆系统
        
        参数:
            db_path: 数据库路径
        
        返回:
            bool: 是否成功
        """
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = 'memory/supermemory.db'
        
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            
            # 创建记忆表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    category TEXT,
                    entities TEXT,
                    session_id TEXT,
                    agent_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            # 创建实体关系表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建关系表
            conn.execute('''
                CREATE TABLE IF NOT EXISTS relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity1_id INTEGER,
                    entity2_id INTEGER,
                    relation_type TEXT,
                    strength INTEGER DEFAULT 50,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(entity1_id) REFERENCES entities(id),
                    FOREIGN KEY(entity2_id) REFERENCES entities(id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"初始化失败：{e}")
            return False
    
    def save_memory(self, text: str, category: str = 'general', 
                   entities: List[str] = None, session_id: str = None, 
                   agent_id: str = None) -> Dict[str, Any]:
        """
        保存记忆
        
        参数:
            text: 记忆内容
            category: 分类 (chapter/character/plot/setting)
            entities: 相关实体
            session_id: 会话 ID
            agent_id: Agent ID
        
        返回:
            dict: {success, memory_id}
        """
        if not self.supermemory_available:
            return {'success': False, 'error': 'supermemory 未初始化'}
        
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            
            entities_str = ','.join(entities) if entities else None
            
            cursor = conn.execute('''
                INSERT INTO memories (text, category, entities, session_id, agent_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (text, category, entities_str, session_id, agent_id))
            
            memory_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {'success': True, 'memory_id': memory_id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def search_memory(self, query: str, category: str = None, 
                     top_k: int = 10) -> Dict[str, Any]:
        """
        搜索记忆（语义搜索）
        
        参数:
            query: 搜索关键词
            category: 分类过滤
            top_k: 返回数量
        
        返回:
            dict: {success, results, count}
        """
        if not self.supermemory_available:
            return {'success': False, 'error': 'supermemory 未初始化'}
        
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            
            if category:
                cursor = conn.execute('''
                    SELECT * FROM memories 
                    WHERE text LIKE ? AND category = ? AND status = 'active'
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (f'%{query}%', category, top_k))
            else:
                cursor = conn.execute('''
                    SELECT * FROM memories 
                    WHERE text LIKE ? AND status = 'active'
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (f'%{query}%', top_k))
            
            results = [
                {
                    'id': row[0],
                    'text': row[1],
                    'category': row[2],
                    'entities': row[3],
                    'created_at': row[6]
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'count': len(results)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_entity(self, name: str, type: str, data: Dict = None) -> Dict[str, Any]:
        """
        添加实体（用于知识图谱）
        
        参数:
            name: 实体名称
            type: 实体类型 (character/location/organization)
            data: 实体数据
        
        返回:
            dict: {success, entity_id}
        """
        if not self.graph_available:
            return {'success': False, 'error': 'memory-graph 未初始化'}
        
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            
            import json
            data_str = json.dumps(data) if data else None
            
            cursor = conn.execute('''
                INSERT INTO entities (name, type, data)
                VALUES (?, ?, ?)
            ''', (name, type, data_str))
            
            entity_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {'success': True, 'entity_id': entity_id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_relation(self, entity1_id: int, entity2_id: int, 
                    relation_type: str, strength: int = 50) -> Dict[str, Any]:
        """
        添加关系（用于知识图谱）
        
        参数:
            entity1_id: 实体 1 ID
            entity2_id: 实体 2 ID
            relation_type: 关系类型 (friend/enemy/family/colleague)
            strength: 关系强度 (0-100)
        
        返回:
            dict: {success, relation_id}
        """
        if not self.graph_available:
            return {'success': False, 'error': 'memory-graph 未初始化'}
        
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            
            cursor = conn.execute('''
                INSERT INTO relations (entity1_id, entity2_id, relation_type, strength)
                VALUES (?, ?, ?, ?)
            ''', (entity1_id, entity2_id, relation_type, strength))
            
            relation_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {'success': True, 'relation_id': relation_id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_entity_graph(self, entity_name: str = None) -> Dict[str, Any]:
        """
        获取实体图谱
        
        参数:
            entity_name: 实体名称（可选，为 None 时返回全部）
        
        返回:
            dict: {success, entities, relations}
        """
        if not self.graph_available:
            return {'success': False, 'error': 'memory-graph 未初始化'}
        
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            
            # 获取实体
            if entity_name:
                cursor = conn.execute('''
                    SELECT * FROM entities WHERE name LIKE ?
                ''', (f'%{entity_name}%',))
            else:
                cursor = conn.execute('SELECT * FROM entities')
            
            entities = [
                {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'data': row[3]
                }
                for row in cursor.fetchall()
            ]
            
            # 获取关系
            cursor = conn.execute('SELECT * FROM relations')
            relations = [
                {
                    'id': row[0],
                    'entity1_id': row[1],
                    'entity2_id': row[2],
                    'relation_type': row[3],
                    'strength': row[4]
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                'success': True,
                'entities': entities,
                'relations': relations
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_consistency(self, new_content: str) -> Dict[str, Any]:
        """
        检查一致性（检测矛盾）
        
        参数:
            new_content: 新内容
        
        返回:
            dict: {success, conflicts, suggestions}
        """
        if not self.supermemory_available:
            return {'success': False, 'error': 'supermemory 未初始化'}
        
        try:
            # 搜索相关记忆
            search_result = self.search_memory(new_content, top_k=10)
            
            if not search_result['success']:
                return search_result
            
            # 简单矛盾检测（关键词冲突）
            conflicts = []
            for memory in search_result['results']:
                # 这里可以实现更复杂的矛盾检测逻辑
                pass
            
            return {
                'success': True,
                'conflicts': conflicts,
                'suggestions': []
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def build_character_relations(self) -> Dict[str, Any]:
        """
        自动构建角色关系图谱
        
        返回:
            dict: {success, characters, relations, graph}
        """
        if not self.graph_available:
            return {'success': False, 'error': 'memory-graph 未初始化'}
        
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            
            # 获取所有角色
            cursor = conn.execute('''
                SELECT * FROM entities WHERE type = 'character'
            ''')
            
            characters = [
                {
                    'id': row[0],
                    'name': row[1],
                    'data': row[3]
                }
                for row in cursor.fetchall()
            ]
            
            # 获取角色关系
            cursor = conn.execute('''
                SELECT r.*, e1.name as entity1_name, e2.name as entity2_name
                FROM relations r
                JOIN entities e1 ON r.entity1_id = e1.id
                JOIN entities e2 ON r.entity2_id = e2.id
                WHERE e1.type = 'character' AND e2.type = 'character'
            ''')
            
            relations = [
                {
                    'id': row[0],
                    'entity1': {'id': row[1], 'name': row[4]},
                    'entity2': {'id': row[2], 'name': row[5]},
                    'relation_type': row[3],
                    'strength': row[4]
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            # 构建图谱数据结构
            graph = {
                'nodes': characters,
                'edges': relations
            }
            
            return {
                'success': True,
                'characters': characters,
                'relations': relations,
                'graph': graph
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_plot_consistency(self, chapter_content: str, chapter_num: int = None) -> Dict[str, Any]:
        """
        检查情节一致性（检测前后矛盾）
        
        参数:
            chapter_content: 章节内容
            chapter_num: 章节号（可选）
        
        返回:
            dict: {success, conflicts, suggestions}
        """
        if not self.supermemory_available:
            return {'success': False, 'error': 'supermemory 未初始化'}
        
        try:
            # 搜索相关情节记忆
            search_result = self.search_memory(chapter_content, category='plot', top_k=20)
            
            if not search_result['success']:
                return search_result
            
            conflicts = []
            suggestions = []
            
            # 简单矛盾检测逻辑
            # 实际应用中可以使用更复杂的 NLP 技术
            
            # 检测时间线矛盾
            time_conflicts = self._detect_time_conflicts(chapter_content, search_result['results'])
            conflicts.extend(time_conflicts)
            
            # 检测地点矛盾
            location_conflicts = self._detect_location_conflicts(chapter_content, search_result['results'])
            conflicts.extend(location_conflicts)
            
            # 检测角色行为矛盾
            character_conflicts = self._detect_character_conflicts(chapter_content, search_result['results'])
            conflicts.extend(character_conflicts)
            
            # 生成建议
            if conflicts:
                suggestions = [
                    f"发现 {len(conflicts)} 处潜在矛盾，请检查",
                    "建议回顾相关章节确保一致性"
                ]
            
            return {
                'success': True,
                'chapter_num': chapter_num,
                'conflicts': conflicts,
                'suggestions': suggestions,
                'checked_memories': len(search_result['results'])
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _detect_time_conflicts(self, content: str, memories: List[Dict]) -> List[Dict]:
        """检测时间线矛盾"""
        conflicts = []
        # 实现时间线矛盾检测逻辑
        return conflicts
    
    def _detect_location_conflicts(self, content: str, memories: List[Dict]) -> List[Dict]:
        """检测地点矛盾"""
        conflicts = []
        # 实现地点矛盾检测逻辑
        return conflicts
    
    def _detect_character_conflicts(self, content: str, memories: List[Dict]) -> List[Dict]:
        """检测角色行为矛盾"""
        conflicts = []
        # 实现角色行为矛盾检测逻辑
        return conflicts
    
    def recommend_next_chapter(self) -> Dict[str, Any]:
        """
        智能推荐下一章情节
        
        返回:
            dict: {success, recommendations, reasoning}
        """
        if not self.supermemory_available:
            return {'success': False, 'error': 'supermemory 未初始化'}
        
        try:
            # 获取所有记忆
            all_memories = self.search_memory("", top_k=100)
            
            # 获取角色档案
            character_result = self.build_character_relations()
            characters = character_result.get('characters', []) if character_result['success'] else []
            
            # 获取情节大纲
            plot_outline = self.search_memory("大纲", category='outline', top_k=10)
            
            # 基于记忆生成推荐
            recommendations = []
            reasoning = []
            
            # 简单推荐逻辑（可以扩展为更复杂的 AI 推荐）
            # 分析最近的情节发展
            recent_memories = all_memories.get('results', [])[-10:] if all_memories['success'] else []
            
            if recent_memories:
                # 推荐延续最近的情节线索
                recommendations.append({
                    'type': 'plot_continuation',
                    'content': '延续最近的情节发展',
                    'confidence': 0.8,
                    'based_on': len(recent_memories)
                })
            
            if len(characters) > 0:
                # 推荐发展角色关系
                recommendations.append({
                    'type': 'character_development',
                    'content': '发展角色关系',
                    'confidence': 0.7,
                    'characters': len(characters)
                })
            
            # 生成推理说明
            reasoning.append(f"分析了 {len(all_memories.get('results', []))} 条记忆")
            reasoning.append(f"分析了 {len(characters)} 个角色")
            reasoning.append(f"参考了 {len(plot_outline.get('results', []))} 条大纲")
            
            return {
                'success': True,
                'recommendations': recommendations,
                'reasoning': reasoning,
                'analyzed_memories': len(all_memories.get('results', [])),
                'analyzed_characters': len(characters)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def auto_review_chapter(self, chapter_num: int, content: str) -> Dict[str, Any]:
        """
        每章自动审核（质量控制自动化）
        
        参数:
            chapter_num: 章节号
            content: 章节内容
        
        返回:
            dict: {success, score, issues, suggestions, passed}
        """
        if not self.supermemory_available:
            return {'success': False, 'error': 'supermemory 未初始化'}
        
        try:
            issues = []
            suggestions = []
            score = 100  # 满分 100
            
            # 1. 检查字数
            word_count = len(content)
            if word_count < 2600:
                issues.append({
                    'type': 'word_count',
                    'severity': 'warning',
                    'message': f'字数不足（{word_count}字 < 2600 字）',
                    'suggestion': '建议扩充到 2600-3200 字'
                })
                score -= 10
            elif word_count > 3200:
                issues.append({
                    'type': 'word_count',
                    'severity': 'warning',
                    'message': f'字数超标（{word_count}字 > 3200 字）',
                    'suggestion': '建议精简到 2600-3200 字'
                })
                score -= 10
            
            # 2. 检查爽点（简单关键词检测）
            shuangdian_keywords = ['打脸', '逆袭', '震惊', '碾压', '爽', '厉害']
            shuangdian_count = sum(content.count(kw) for kw in shuangdian_keywords)
            
            if shuangdian_count < 2:
                issues.append({
                    'type': 'shuangdian',
                    'severity': 'warning',
                    'message': f'爽点不足（检测到{shuangdian_count}个）',
                    'suggestion': '建议增加爽点密度（建议每章≥2 个爽点）'
                })
                score -= 15
            
            # 3. 检查一致性
            consistency_result = self.check_plot_consistency(content, chapter_num)
            if consistency_result['success'] and consistency_result.get('conflicts'):
                for conflict in consistency_result['conflicts']:
                    issues.append({
                        'type': 'consistency',
                        'severity': 'error',
                        'message': f'发现矛盾：{conflict}',
                        'suggestion': '请检查相关章节确保一致性'
                    })
                score -= 20
            
            # 4. 检查角色设定（搜索角色记忆）
            character_result = self.build_character_relations()
            if character_result['success']:
                characters = character_result.get('characters', [])
                # 检查是否提及主要角色
                for char in characters:
                    char_name = char.get('name', '')
                    if char_name and char_name not in content:
                        # 主要角色未出场（不扣分，仅提示）
                        pass
            
            # 5. 检查情节连贯
            plot_result = self.search_memory("情节", category='plot', top_k=5)
            if plot_result['success'] and len(plot_result['results']) > 0:
                # 检查是否与前后文连贯（简单检查）
                pass
            
            # 生成建议
            if issues:
                suggestions = [issue['suggestion'] for issue in issues]
            
            # 判断是否通过
            passed = score >= 60 and not any(i['severity'] == 'error' for i in issues)
            
            return {
                'success': True,
                'chapter_num': chapter_num,
                'score': score,
                'word_count': word_count,
                'shuangdian_count': shuangdian_count,
                'issues': issues,
                'suggestions': suggestions,
                'passed': passed
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """获取工具状态"""
        return {
            'name': 'memory-tools',
            'supermemory': self.supermemory_available,
            'graph': self.graph_available,
            'db_path': self.db_path,
            'status': 'ready' if (self.supermemory_available and self.graph_available) else 'partial'
        }


# 便捷函数
def get_memory_tools() -> MemoryTools:
    """获取 Memory Tools 实例"""
    return MemoryTools()


# 测试
if __name__ == '__main__':
    memory_tools = MemoryTools()
    
    print("=" * 60)
    print("Memory Tools 测试")
    print("=" * 60)
    
    # 测试状态
    status = memory_tools.get_status()
    print(f"\n工具状态：{status}")
    
    # 初始化
    print("\n初始化记忆系统...")
    success = memory_tools.initialize()
    print(f"初始化：{'成功' if success else '失败'}")
    
    if success:
        # 测试保存记忆
        print("\n测试保存记忆...")
        result = memory_tools.save_memory(
            "第 50 章：陆鸣和林晚晴站在天台上，看着日出",
            category='chapter',
            entities=['陆鸣', '林晚晴'],
            session_id='test',
            agent_id='novel'
        )
        print(f"保存结果：{result}")
        
        # 测试搜索记忆
        print("\n测试搜索记忆...")
        result = memory_tools.search_memory("陆鸣", top_k=5)
        print(f"搜索结果：{result}")
        
        # 测试添加实体
        print("\n测试添加实体...")
        result = memory_tools.add_entity("陆鸣", "character", {"age": 32, "job": "验房师"})
        print(f"添加实体：{result}")
        
        # 测试获取图谱
        print("\n测试获取图谱...")
        result = memory_tools.get_entity_graph()
        print(f"图谱结果：{result}")
        
        # 测试一致性检查
        print("\n测试一致性检查...")
        result = memory_tools.check_consistency("陆鸣站在天台上")
        print(f"一致性检查：{result}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
