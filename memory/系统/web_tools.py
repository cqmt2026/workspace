# -*- coding: utf-8 -*-
"""
Web Tools - 统一网页工具接口
融合 crawlee + web-hot + search
使用 requests 作为主要爬虫工具（更稳定）
"""

from typing import Dict, List, Any, Optional


class WebTools:
    """Web 工具统一接口"""
    
    def __init__(self):
        self.crawlee_available = self._check_crawlee()
        self.search_available = self._check_search()
        self.hot_available = self._check_hot()
    
    def _check_crawlee(self) -> bool:
        """检查 crawlee 是否可用"""
        try:
            import crawlee
            from crawlee._request import Request
            return True
        except (ImportError, TypeError, Exception):
            # crawlee 与 pydantic 版本不兼容
            return False
    
    def _check_search(self) -> bool:
        """检查搜索工具是否可用"""
        try:
            import requests
            return True
        except ImportError:
            return False
    
    def _check_hot(self) -> bool:
        """检查热点追踪是否可用"""
        import os
        return os.path.exists('skills/web-hot')
    
    def fetch_url(self, url: str, extract_text: bool = True) -> Dict[str, Any]:
        """
        爬取网页（使用 requests，更稳定）
        
        参数:
            url: 目标 URL
            extract_text: 是否提取文本
        
        返回:
            dict: {success, url, status, content, text, length, method}
        """
        try:
            import requests
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            resp = requests.get(url, headers=headers, timeout=30)
            
            result = {
                'success': True,
                'url': url,
                'status': resp.status_code,
                'content': resp.text,
                'length': len(resp.text),
                'method': 'requests'
            }
            
            if extract_text:
                import re
                text = re.sub(r'<[^>]+>', '', resp.text)
                result['text'] = text.strip()
            
            return result
            
        except ImportError:
            return {
                'success': False,
                'error': 'requests 未安装'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'爬取失败：{str(e)}'
            }
    
    def search(self, query: str, engine: str = 'multi', top_k: int = 10) -> Dict[str, Any]:
        """
        搜索（支持多引擎）
        
        参数:
            query: 搜索关键词
            engine: 搜索引擎 (multi/baidu/xcrawl)
            top_k: 返回结果数量
        
        返回:
            dict: {success, results, count}
        """
        if not self.search_available:
            return {
                'success': False,
                'error': '搜索工具未安装'
            }
        
        try:
            if engine == 'multi':
                results = self._multi_search(query, top_k)
            elif engine == 'baidu':
                results = self._baidu_search(query, top_k)
            elif engine == 'xcrawl':
                results = self._xcrawl_search(query, top_k)
            else:
                results = self._multi_search(query, top_k)
            
            return {
                'success': True,
                'query': query,
                'engine': engine,
                'results': results,
                'count': len(results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _multi_search(self, query: str, top_k: int) -> List[Dict]:
        """多引擎搜索"""
        return self._call_skill('multi-search-engine', {'query': query, 'top_k': top_k})
    
    def _baidu_search(self, query: str, top_k: int) -> List[Dict]:
        """百度搜索"""
        return self._call_skill('baidu-search', {'query': query, 'top_k': top_k})
    
    def _xcrawl_search(self, query: str, top_k: int) -> List[Dict]:
        """xcrawl 搜索"""
        return self._call_skill('xcrawl-search', {'query': query, 'top_k': top_k})
    
    def _call_skill(self, skill_name: str, params: Dict) -> List[Dict]:
        """调用技能（模拟）"""
        return []
    
    def track_hot_topics(self, platform: str = 'weibo', top_k: int = 10) -> Dict[str, Any]:
        """
        追踪热点
        
        参数:
            platform: 平台 (weibo/weixin/zhihu)
            top_k: 返回热点数量
        
        返回:
            dict: {success, topics, count}
        """
        if not self.hot_available:
            return {
                'success': False,
                'error': '热点追踪工具未安装'
            }
        
        try:
            topics = self._call_skill('web-hot', {'platform': platform, 'top_k': top_k})
            
            return {
                'success': True,
                'platform': platform,
                'topics': topics,
                'count': len(topics)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def collect_material(self, topic: str, sources: List[str] = None) -> Dict[str, Any]:
        """
        收集素材（小说创作使用）
        
        参数:
            topic: 主题
            sources: 来源列表
        
        返回:
            dict: {success, material, sources}
        """
        if sources is None:
            sources = ['search', 'hot']
        
        material = {
            'topic': topic,
            'search_results': [],
            'hot_topics': [],
            'web_content': []
        }
        
        if 'search' in sources:
            search_result = self.search(topic, top_k=5)
            if search_result['success']:
                material['search_results'] = search_result['results']
        
        if 'hot' in sources:
            hot_result = self.track_hot_topics(top_k=5)
            if hot_result['success']:
                material['hot_topics'] = hot_result['topics']
        
        return {
            'success': True,
            'topic': topic,
            'material': material
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取工具状态"""
        return {
            'name': 'web-tools',
            'crawlee': self.crawlee_available,
            'search': self.search_available,
            'hot': self.hot_available,
            'status': 'ready' if self.search_available else 'partial',
            'note': '使用 requests 作为主要爬虫工具（crawlee 有兼容性问题）'
        }


def get_web_tools() -> WebTools:
    """获取 Web Tools 实例"""
    return WebTools()


if __name__ == '__main__':
    web_tools = get_web_tools()
    
    print("=" * 60)
    print("Web Tools 测试")
    print("=" * 60)
    
    status = web_tools.get_status()
    print(f"\n工具状态：{status}")
    
    print("\n测试网页爬取...")
    result = web_tools.fetch_url("https://www.baidu.com", extract_text=True)
    if result['success']:
        print(f"[OK] 爬取成功（{result['length']}字节，使用{result['method']}）")
    else:
        print(f"[FAIL] 爬取失败：{result.get('error')}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
