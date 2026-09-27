# -*- coding: utf-8 -*-
"""
热点选题采集 v5 — 多源采集优化版

数据来源优先级：
1. 百度热搜 ✅
2. 微博热搜（移动端API）
3. 头条热榜（首页解析）
4. 抖音热榜（API）
5. 36氪热榜
"""

import os
import sys
import json
import re
import io
import warnings
import requests
from datetime import datetime

warnings.filterwarnings('ignore')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

GEO_ANGLES = {
    '台风': {'angle': '台风路径及影响区域', 'map_type': 'flow_map'},
    '暴雨': {'angle': '降雨量省份分布', 'map_type': 'heatmap'},
    '高温': {'angle': '城市高温排名', 'map_type': 'choropleth'},
    '寒潮': {'angle': '寒潮影响区域', 'map_type': 'heatmap'},
    '降温': {'angle': '降温幅度省份排名', 'map_type': 'choropleth'},
    '地震': {'angle': '地震带区域分布', 'map_type': 'heatmap'},
    '北京': {'angle': '北京数据地图', 'map_type': 'choropleth'},
    '上海': {'angle': '上海数据地图', 'map_type': 'choropleth'},
    '广州': {'angle': '广州数据地图', 'map_type': 'choropleth'},
    '深圳': {'angle': '深圳数据地图', 'map_type': 'choropleth'},
    '杭州': {'angle': '杭州数据地图', 'map_type': 'choropleth'},
    '成都': {'angle': '成都数据地图', 'map_type': 'choropleth'},
    '武汉': {'angle': '武汉数据地图', 'map_type': 'choropleth'},
    '重庆': {'angle': '重庆数据地图', 'map_type': 'choropleth'},
    '西安': {'angle': '西安数据地图', 'map_type': 'choropleth'},
    '日本': {'angle': '日本各地区分布', 'map_type': 'choropleth'},
    '美国': {'angle': '美国各州分布', 'map_type': 'choropleth'},
    '欧洲': {'angle': '欧洲各国分布', 'map_type': 'choropleth'},
    '台湾': {'angle': '台湾省数据地图', 'map_type': 'choropleth'},
    '全球': {'angle': '全球各国分布', 'map_type': 'choropleth'},
    '高考': {'angle': '各省分数线对比', 'map_type': 'choropleth'},
    '考研': {'angle': '报考人数省份排名', 'map_type': 'choropleth'},
    '大学': {'angle': '大学数量城市排名', 'map_type': 'bubble_map'},
    '演唱会': {'angle': '演唱会城市分布', 'map_type': 'bubble_map'},
    '电影': {'angle': '票房城市排名', 'map_type': 'bubble_map'},
    '离婚': {'angle': '离婚率省份排名', 'map_type': 'choropleth'},
    '结婚': {'angle': '结婚率省份排名', 'map_type': 'choropleth'},
    '房价': {'angle': '房价城市排名', 'map_type': 'choropleth'},
    '消费': {'angle': '消费力城市排名', 'map_type': 'bubble_map'},
}



# P1-A: 动态地域提取（从标题中提取中国城市名）
_CITIES_CN = [
    '北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '重庆', '西安',
    '南京', '苏州', '天津', '长沙', '郑州', '济南', '青岛', '大连', '宁波',
    '福州', '合肥', '昆明', '沈阳', '哈尔滨', '长春', '石家庄', '太原',
    '贵阳', '南宁', '海口', '兰州', '乌鲁木齐', '银川', '西宁', '拉萨',
    '香港', '澳门', '台湾',
]

def extract_regions(text):
    """从文本中提取所有匹配的中国城市/地区名"""
    found = []
    for city in _CITIES_CN:
        if city in text:
            found.append(city)
    # 去重保持顺序
    seen = set()
    unique = []
    for c in found:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


class HotTopicCollectorV5:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.output_dir = os.path.join(BASE_DIR, 'data', 'topics', 'hot')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _fetch(self, url, headers=None, timeout=10):
        try:
            h = headers or {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            r = self.session.get(url, headers=h, timeout=timeout)
            return r.text if r.status_code == 200 else None
        except:
            return None
    
    def match_geo_angle(self, title):
        for kw, info in GEO_ANGLES.items():
            if kw in title:
                return info['angle'], info['map_type']
        # P1-A: 动态地域匹配
        regions = extract_regions(title)
        if regions:
            region_str = '/'.join(regions)
            return f'{region_str}数据地图', 'choropleth'
        return None, None


    def analyze_potential(self, title, geo_angle):
        score = 0
        reasons = []
        if geo_angle:
            score += 30
            reasons.append(f'地理角度: {geo_angle}')
        if re.search(r'\d+', title):
            score += 15
            reasons.append('含数字')
        locations = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '重庆', '西安',
                     '日本', '美国', '台湾', '全球', '中国', '欧洲', '亚洲']
        for loc in locations:
            if loc in title:
                score += 10
                reasons.append(f'地名: {loc}')
                break
        score += 5
        return min(score, 100), reasons
    
    def collect_baidu(self):
        print("  [百度热搜] ", end='')
        html = self._fetch('https://top.baidu.com/board')
        if not html:
            print("失败")
            return []
        
        titles = re.findall(r'"word":"([^"]+)"', html)
        if not titles:
            titles = re.findall(r'<div[^>]*class="[^"]*c-single-text-ellipsis[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
            titles = [re.sub(r'<[^>]+>', '', t).strip() for t in titles]
        
        titles = [t for t in titles if len(t) > 6]
        print(f"获取{len(titles)}条")
        return [{'title': t, 'source': 'baidu', 'rank': i+1} for i, t in enumerate(titles[:50])]
    
    def collect_web_search(self, query=None):
        """P1-A2: 通过 web_search 获取热点（备选数据源）
        
        注意：此方法需要通过 openclaw 的 web_search 工具调用，
        这里返回结构化数据格式，实际调用由外部完成。
        """
        print("  [web_search] ", end='')
        # web_search 是 agent 工具，这里返回空列表表示需要外部调用
        # 实际使用时，pipeline 会调用 sessions_spawn 触发 web_search
        return []
    
    def merge_and_rank(self, topics, top_n=15):
        """合并多源选题并去重排名"""
        # 按来源分组
        sources = {}
        for t in topics:
            src = t.get('source', 'unknown')
            if src not in sources:
                sources[src] = []
            sources[src].append(t)
        
        # 去重：按标题模糊匹配
        seen = set()
        unique = []
        for t in topics:
            title = t['title'].strip()
            # 简化匹配：取前10个字符作为key
            key = title[:10]
            if key not in seen:
                seen.add(key)
                unique.append(t)
        
        print(f"合并后: {len(unique)}条")
        return unique[:top_n]



    def collect_weibo(self):
        print("  [微博热搜] ", end='')
        url = 'https://m.weibo.cn/api/container/getIndex?containerid=106003type%3D25%26t%3D3%26filter_type%3Drealtimehot'
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'}
        html = self._fetch(url, headers=headers)
        if not html:
            print("失败")
            return []
        
        titles = []
        try:
            d = json.loads(html)
            if 'data' in d and 'cards' in d['data']:
                for card in d['data']['cards']:
                    if 'desc' in card:
                        titles.append(card['desc'])
        except:
            pass
        
        if not titles:
            titles = re.findall(r'"text":"([^"]+)"', html)
        
        titles = [t for t in titles if len(t) > 5 and '#' not in t]
        titles = list(dict.fromkeys(titles))
        print(f"获取{len(titles)}条")
        return [{'title': t, 'source': 'weibo', 'rank': i+1} for i, t in enumerate(titles[:50])]
    
    def collect_toutiao(self):
        print("  [头条热榜] ", end='')
        html = self._fetch('https://www.toutiao.com')
        if not html:
            print("失败")
            return []
        
        titles = []
        
        # 方式1: JSON数据中的title
        json_titles = re.findall(r'"title":"([^"]+)"', html)
        titles.extend(json_titles)
        
        # 方式2: 查找hotBoard相关数据
        hot_board = re.findall(r'"hotBoard":(.*?)},', html, re.DOTALL)
        if hot_board:
            try:
                for hb in hot_board[:3]:
                    d = json.loads(hb + '}')
                    if 'title' in d:
                        titles.append(d['title'])
            except:
                pass
        
        # 过滤和去重
        titles = [t for t in titles if len(t) > 8 and '广告' not in t]
        titles = list(dict.fromkeys(titles))[:40]
        
        print(f"获取{len(titles)}条")
        return [{'title': t, 'source': 'toutiao', 'rank': i+1} for i, t in enumerate(titles)]
    
    def collect_douyin(self):
        print("  [抖音热榜] ", end='')
        # 抖音API需要特殊参数，尝试通用API
        url = 'https://www.douyin.com/aweme/v1/web/hot/search/list/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
            'Accept': 'application/json',
        }
        html = self._fetch(url, headers=headers)
        if not html:
            print("失败")
            return []
        
        titles = []
        try:
            d = json.loads(html)
            if 'data' in d:
                for item in d['data']:
                    word = item.get('word', '')
                    if word:
                        titles.append(word)
        except:
            pass
        
        # 备用: 从网页提取
        if not titles:
            html2 = self._fetch('https://www.douyin.com/hot')
            if html2:
                titles = re.findall(r'"title":"([^"]+)"', html2)
        
        titles = [t for t in titles if len(t) > 6]
        titles = list(dict.fromkeys(titles))[:40]
        print(f"获取{len(titles)}条")
        return [{'title': t, 'source': 'douyin', 'rank': i+1} for i, t in enumerate(titles)]
    
    def collect_36kr(self):
        print("  [36氪热榜] ", end='')
        html = self._fetch('https://36kr.com/hot-list/catalog')
        if not html:
            print("失败")
            return []
        
        titles = []
        titles += re.findall(r'"title":"([^"]+)"', html)
        titles += re.findall(r'<h[23][^>]*>(.*?)</h[23]>', html, re.DOTALL)
        titles = [re.sub(r'<[^>]+>', '', t).strip() for t in titles if len(re.sub(r'<[^>]+>', '', t)) > 8]
        titles = list(dict.fromkeys(titles))[:30]
        print(f"获取{len(titles)}条")
        return [{'title': t, 'source': '36kr', 'rank': i+1} for i, t in enumerate(titles)]
    
    def run(self):
        print("\n" + "=" * 70)
        print("社会热点选题采集 v5 — 多源采集")
        print("=" * 70)
        
        all_topics = []
        all_topics.extend(self.collect_baidu())
        all_topics.extend(self.collect_weibo())
        all_topics.extend(self.collect_toutiao())
        all_topics.extend(self.collect_douyin())
        all_topics.extend(self.collect_36kr())
        
        print(f"\n原始选题: {len(all_topics)}条")
        
        # 去重
        seen = set()
        deduped = []
        for t in all_topics:
            key = t['title'][:15]
            if key not in seen:
                seen.add(key)
                deduped.append(t)
        
        print(f"去重后: {len(deduped)}条")
        
        # 匹配地理角度
        enriched = []
        for t in deduped:
            angle, map_type = self.match_geo_angle(t['title'])
            t['geo_angle'] = angle
            t['map_type'] = map_type
            t['has_geo_angle'] = bool(angle)
            score, reasons = self.analyze_potential(t['title'], angle)
            t['video_score'] = score
            t['score_reasons'] = reasons
            enriched.append(t)
        
        enriched.sort(key=lambda x: (not x['has_geo_angle'], -x['video_score']))
        
        with_angle = [t for t in enriched if t['has_geo_angle']]
        without = [t for t in enriched if not t['has_geo_angle']]
        
        print(f"\n有地理角度: {len(with_angle)}条")
        print(f"无地理角度: {len(without)}条")
        
        print(f"\n【TOP20 热点选题】")
        print(f"{'='*70}")
        for i, t in enumerate(with_angle[:20], 1):
            rank = t.get('rank', '?')
            title = t['title'][:50]
            angle = t['geo_angle']
            score = t['video_score']
            source = t['source']
            print(f"  {i:2d}. [#{rank}] {title}...")
            print(f"      地图角度: {angle} | 潜力: {score}分 | {source}")
        
        # 保存
        filename = os.path.join(self.output_dir, f'hot_topics_{datetime.now().strftime("%Y%m%d_%H%M")}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'date': datetime.now().strftime('%Y%m%d'),
                'total': len(enriched),
                'with_angle': len(with_angle),
                'without_angle': len(without),
                'topics': enriched,
            }, f, ensure_ascii=False, indent=2)
        print(f"\n已保存: {filename}")
        
        return with_angle


if __name__ == '__main__':
    collector = HotTopicCollectorV5()
    collector.run()