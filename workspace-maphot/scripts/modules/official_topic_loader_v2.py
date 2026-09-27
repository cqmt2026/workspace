# -*- coding: utf-8 -*-
"""
官方数据源选题采集模块 v2 — 真实数据源

数据源优先级：
1. 国家统计局（权威数据）
2. 各省市统计局（区域数据）
3. 发改委/工信部（政策动向）
4. 东方财富数据API（金融数据）
5. 百度热搜（社会热点）
6. 微博热搜（舆论热点）
"""

import os
import sys
import json
import re
import io
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 设置stdout为utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

# 官方数据源
OFFICIAL_SOURCES = {
    'stats_china': {
        'name': '国家统计局',
        'base_url': 'http://www.stats.gov.cn',
        'api_endpoints': [
            '/tjsj/tjbz/tjyqhdmhcxhfdm/',
            '/sfsk/tjfx/',
            '/zxfb/',
        ],
        'topics_keywords': [
            'GDP', '人口', '就业', '收入', '消费', '投资', '贸易',
            '工业生产', '服务业', '房地产', '金融', '物价',
            '十四五', '高质量发展', '共同富裕', '乡村振兴',
            '经济普查', '统计公报', '国民经济', '社会发展',
        ],
        'priority': 1,
    },
    'ndrc': {
        'name': '国家发改委',
        'base_url': 'http://www.ndrc.gov.cn',
        'api_endpoints': ['/xwdt/tzgg/', '/zc/zcjz/', '/gzdt/'],
        'topics_keywords': [
            '重大项目', '基础设施', '一带一路', '京津冀', '长三角',
            '粤港澳大湾区', '成渝双城', '新型城镇化', '碳达峰', '碳中和',
            '投资计划', '区域规划', '产业政策',
        ],
        'priority': 2,
    },
    'miit': {
        'name': '工信部',
        'base_url': 'http://www.miit.gov.cn',
        'api_endpoints': ['/xthsjgb/tjsj/', '/zc/zcwj/', '/gxzt/ztzl/'],
        'topics_keywords': [
            '制造业', '数字经济', '人工智能', '5G', '工业互联网',
            '新能源汽车', '半导体', '芯片', '新材料', '生物医药',
            '智能制造', '专精特新', '战略性新兴产业',
        ],
        'priority': 3,
    },
    'province_stats': {
        'name': '各省市统计局',
        'base_urls': {
            '北京': 'https://tjj.beijing.gov.cn',
            '上海': 'https://tjj.sh.gov.cn',
            '广东': 'https://tjd.gd.gov.cn',
            '江苏': 'https://tjj.jiangsu.gov.cn',
            '浙江': 'https://tjj.zj.gov.cn',
            '山东': 'https://tjj.shandong.gov.cn',
            '四川': 'https://tjj.sc.gov.cn',
            '湖北': 'https://tjj.hubei.gov.cn',
            '河南': 'https://tjj.henan.gov.cn',
        },
        'topics_keywords': [
            'GDP', '常住人口', '固定资产投资', '社会消费品零售总额',
            '进出口', '高技术产业', '数字经济', '人均收入',
            '经济数据', '上半年', '下半年', '季度',
        ],
        'priority': 4,
    },
    'city_stats': {
        'name': '主要城市统计局',
        'base_urls': {
            '深圳': 'https://tjj.sz.gov.cn',
            '广州': 'https://tjj.gz.gov.cn',
            '杭州': 'https://tjj.hangzhou.gov.cn',
            '成都': 'https://tjj.chengdu.gov.cn',
            '武汉': 'https://tjj.wuhan.gov.cn',
            '南京': 'https://tjj.nanjing.gov.cn',
        },
        'topics_keywords': [
            'GDP', '人口', '财政', '税收', '外贸', '消费',
            '上半年', '前三季度', '全年',
        ],
        'priority': 5,
    },
}

HOT_SOURCES = {
    'baidu': {'name': '百度热搜', 'url': 'https://top.baidu.com/board', 'priority': 6},
    'toutiao': {'name': '头条热榜', 'url': 'https://www.toutiao.com', 'priority': 7},
}


class OfficialTopicLoaderV2:
    """官方数据源选题采集器 v2"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.verify = False  # 跳过SSL验证
        
        # 输出目录
        self.output_dir = os.path.join(BASE_DIR, 'data', 'topics', datetime.now().strftime('%Y%m'))
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _safe_fetch(self, url, timeout=10):
        """安全请求"""
        try:
            resp = self.session.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp.text
            return None
        except Exception as e:
            return None
    
    def _extract_titles(self, html):
        """从HTML中提取可能的标题"""
        if not html:
            return []
        titles = []
        # 提取标题标签
        matches = re.findall(r'<title>(.*?)</title>', html, re.DOTALL)
        titles.extend(matches)
        # 提取h标签
        matches = re.findall(r'<h[1-4][^>]*>(.*?)</h[1-4]>', html, re.DOTALL)
        for m in matches:
            clean = re.sub(r'<[^>]+>', '', m).strip()
            if clean and len(clean) > 5:
                titles.append(clean)
        # 提取a标签
        matches = re.findall(r'<a[^>]*>(.*?)</a>', html, re.DOTALL)
        for m in matches:
            clean = re.sub(r'<[^>]+>', '', m).strip()
            if clean and len(clean) > 8:
                titles.append(clean)
        return titles
    
    def _match_category(self, title, keywords_map):
        """匹配选题类型"""
        for kw, cat in keywords_map.items():
            if kw in title:
                return cat
        return 'single_event'
    
    def fetch_url(self, name, url, keywords, source_name, priority, category_map=None):
        """统一采集方法"""
        topics = []
        print(f"  [{name}] {url}")
        
        html = self._safe_fetch(url)
        if not html:
            print(f"    ⚠️ 无法访问")
            return topics
        
        titles = self._extract_titles(html)
        print(f"    获取到{len(titles)}个标题")
        
        if category_map is None:
            category_map = {}
        
        for title in titles[:10]:
            score = 70
            category = 'single_event'
            
            # 关键词匹配提分
            for kw in keywords:
                if kw in title:
                    score += 5
                    category = self._match_category(title, category_map) if category_map else category
                    break
            
            topics.append({
                'title': title[:50],
                'source': source_name,
                'score': min(score, 95),
                'category': category,
                'has_map': True,
                'data_type': 'official',
                'url': url,
                'collected_at': datetime.now().isoformat(),
            })
        
        return topics
    
    def fetch_stats_china(self) -> List[Dict]:
        """采集国家统计局"""
        config = OFFICIAL_SOURCES['stats_china']
        all_topics = []
        
        for ep in config['api_endpoints']:
            url = config['base_url'] + ep
            topics = self.fetch_url(
                config['name'], url, config['topics_keywords'],
                'stats_china', 1,
                {'GDP': 'data_ranking', '人口': 'data_ranking', '就业': 'data_ranking',
                 '房地产': 'data_ranking', '统计公报': 'data_ranking'}
            )
            all_topics.extend(topics)
        
        return all_topics
    
    def fetch_ndrc(self) -> List[Dict]:
        """采集发改委"""
        config = OFFICIAL_SOURCES['ndrc']
        all_topics = []
        
        for ep in config['api_endpoints']:
            url = config['base_url'] + ep
            topics = self.fetch_url(
                config['name'], url, config['topics_keywords'],
                'ndrc', 2,
                {'重大项目': 'policy_effect', '基础设施': 'policy_effect',
                 '区域规划': 'policy_effect', '产业政策': 'policy_effect'}
            )
            all_topics.extend(topics)
        
        return all_topics
    
    def fetch_miit(self) -> List[Dict]:
        """采集工信部"""
        config = OFFICIAL_SOURCES['miit']
        all_topics = []
        
        for ep in config['api_endpoints']:
            url = config['base_url'] + ep
            topics = self.fetch_url(
                config['name'], url, config['topics_keywords'],
                'miit', 3,
                {'制造业': 'industry_analysis', '数字经济': 'industry_analysis',
                 '新能源汽车': 'industry_analysis', '半导体': 'industry_analysis'}
            )
            all_topics.extend(topics)
        
        return all_topics
    
    def fetch_province_stats(self) -> List[Dict]:
        """采集各省市统计局"""
        config = OFFICIAL_SOURCES['province_stats']
        all_topics = []
        
        for prov, url in config['base_urls'].items():
            topics = self.fetch_url(
                f'{prov}统计局', url, config['topics_keywords'],
                f'province_{prov}', 4,
                {'GDP': 'data_ranking', '人口': 'data_ranking', '经济数据': 'data_ranking'}
            )
            all_topics.extend(topics)
        
        return all_topics
    
    def fetch_city_stats(self) -> List[Dict]:
        """采集主要城市统计局"""
        config = OFFICIAL_SOURCES['city_stats']
        all_topics = []
        
        for city, url in config['base_urls'].items():
            topics = self.fetch_url(
                f'{city}统计局', url, config['topics_keywords'],
                f'city_{city}', 5,
                {'GDP': 'data_ranking', '人口': 'data_ranking', '财政': 'data_ranking'}
            )
            all_topics.extend(topics)
        
        return all_topics
    
    def fetch_baidu_hot(self) -> List[Dict]:
        """采集百度热搜"""
        topics = []
        print("  [百度热搜] 采集中...")
        
        url = 'https://top.baidu.com/board'
        html = self._safe_fetch(url)
        if not html:
            print("    ⚠️ 无法访问")
            return topics
        
        # 尝试提取热搜标题
        titles = re.findall(r'"word":"([^"]+)"', html)
        if not titles:
            # 备用提取
            titles = re.findall(r'<div[^>]*class="[^"]*c-single-text-ellipsis[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
            titles = [re.sub(r'<[^>]+>', '', t).strip() for t in titles]
        
        titles = [t for t in titles if len(t) > 5]
        print(f"    获取到{len(titles)}个热搜")
        
        for i, title in enumerate(titles[:15]):
            topics.append({
                'title': title[:50],
                'source': 'baidu_hot',
                'score': 65 - i,  # 第1名65分，递减
                'category': 'single_event',
                'has_map': True,
                'data_type': 'hot',
                'url': url,
                'collected_at': datetime.now().isoformat(),
            })
        
        return topics
    
    def fetch_toutiao_hot(self) -> List[Dict]:
        """采集头条热榜"""
        topics = []
        print("  [头条热榜] 采集中...")
        
        url = 'https://www.toutiao.com/trending/'
        html = self._safe_fetch(url)
        if not html:
            print("    ⚠️ 无法访问")
            return topics
        
        titles = re.findall(r'"title":"([^"]+)"', html)
        titles = [t for t in titles if len(t) > 5]
        print(f"    获取到{len(titles)}个热榜")
        
        for i, title in enumerate(titles[:15]):
            topics.append({
                'title': title[:50],
                'source': 'toutiao_hot',
                'score': 65 - i,
                'category': 'single_event',
                'has_map': True,
                'data_type': 'hot',
                'url': url,
                'collected_at': datetime.now().isoformat(),
            })
        
        return topics
    
    def collect_all(self) -> List[Dict]:
        """采集所有数据源"""
        print("\n" + "=" * 60)
        print("官方数据源选题采集 v2")
        print("=" * 60)
        
        all_topics = []
        
        # 官方数据源
        print("\n[一级来源] 官方数据")
        all_topics.extend(self.fetch_stats_china())
        all_topics.extend(self.fetch_ndrc())
        all_topics.extend(self.fetch_miit())
        all_topics.extend(self.fetch_province_stats())
        all_topics.extend(self.fetch_city_stats())
        
        # 热点数据
        print("\n[二级来源] 热点话题")
        all_topics.extend(self.fetch_baidu_hot())
        all_topics.extend(self.fetch_toutiao_hot())
        
        # 去重
        seen = set()
        unique = []
        for t in all_topics:
            key = t['title'][:20]
            if key not in seen:
                seen.add(key)
                unique.append(t)
        
        # 排序
        unique.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        print(f"\n采集完成: 共{len(unique)}个选题")
        print(f"  官方来源: {sum(1 for t in unique if t['data_type']=='official')}个")
        print(f"  热点来源: {sum(1 for t in unique if t['data_type']=='hot')}个")
        print(f"\n  前5高分:")
        for t in unique[:5]:
            print(f"    [{t['score']:2d}分] {t['title'][:40]} ({t['source']})")
        
        return unique
    
    def save_topics(self, topics: List[Dict], date_str: str = None):
        """保存选题"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        filename = os.path.join(self.output_dir, f'topics_{date_str}.json')
        data = {
            'date': date_str,
            'collected_at': datetime.now().isoformat(),
            'total': len(topics),
            'topics': topics,
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n已保存: {filename}")
        return filename


def main():
    """执行采集"""
    import warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    warnings.filterwarnings('ignore', category=requests.packages.urllib3.exceptions.InsecureRequestWarning)
    
    loader = OfficialTopicLoaderV2()
    topics = loader.collect_all()
    if topics:
        loader.save_topics(topics)


if __name__ == '__main__':
    main()