#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web爬虫模板 - 数据采集/解析/存储

用法：
    python web_scraper.py --url https://example.com --output data.json
    python web_scraper.py --urls urls.txt --output data.csv
"""

import os
import sys
import json
import argparse
import time
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


@dataclass
class ScrapeResult:
    """爬取结果"""
    url: str
    title: str
    text: str
    links: List[str]
    status_code: int
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class WebScraper:
    """Web爬虫"""
    
    def __init__(self, delay: float = 1.0, max_retries: int = 3):
        """初始化
        
        Args:
            delay: 请求间隔（秒）
            max_retries: 最大重试次数
        """
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        })
    
    def fetch(self, url: str) -> Optional[BeautifulSoup]:
        """获取页面
        
        Args:
            url: 目标URL
            
        Returns:
            BeautifulSoup对象或None
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # 检测编码
                encoding = response.encoding or 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser', from_encoding=encoding)
                
                time.sleep(self.delay)
                return soup
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    print(f"请求失败 [{url}]: {e}", file=sys.stderr)
                    return None
                print(f"重试 [{url}] 第{attempt+1}次...", file=sys.stderr)
                time.sleep(self.delay * (attempt + 1))
        
        return None
    
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """提取链接
        
        Args:
            soup: BeautifulSoup对象
            base_url: 基础URL
            
        Returns:
            list: 链接列表
        """
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            
            # 过滤有效链接
            if full_url.startswith(('http://', 'https://')):
                links.append(full_url)
        
        return links
    
    def extract_text(self, soup: BeautifulSoup) -> str:
        """提取文本内容
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            str: 文本内容
        """
        # 移除脚本和样式
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        
        # 提取文本
        text = soup.get_text(separator='\n', strip=True)
        
        # 清理空白行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def scrape(self, url: str) -> Optional[ScrapeResult]:
        """爬取单个页面
        
        Args:
            url: 目标URL
            
        Returns:
            ScrapeResult对象或None
        """
        soup = self.fetch(url)
        if soup is None:
            return ScrapeResult(
                url=url,
                title='',
                text='',
                links=[],
                status_code=0,
                error='请求失败'
            )
        
        # 提取标题
        title = ''
        if soup.title:
            title = soup.title.string or ''
        
        # 提取文本
        text = self.extract_text(soup)
        
        # 提取链接
        links = self.extract_links(soup, url)
        
        return ScrapeResult(
            url=url,
            title=title,
            text=text,
            links=links,
            status_code=200
        )
    
    def scrape_batch(self, urls: List[str]) -> List[ScrapeResult]:
        """批量爬取
        
        Args:
            urls: URL列表
            
        Returns:
            list: 爬取结果列表
        """
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] 爬取: {url[:50]}...")
            result = self.scrape(url)
            results.append(result)
            
            # 保存进度
            if (i % 10) == 0:
                print(f"  已完成 {i}/{len(urls)} 个页面")
        
        return results
    
    @staticmethod
    def save_results(results: List[ScrapeResult], filepath: str, fmt: str = 'json'):
        """保存结果
        
        Args:
            results: 爬取结果列表
            filepath: 输出文件路径
            fmt: 格式 (json/csv)
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        if fmt == 'json':
            data = [r.to_dict() for r in results]
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif fmt == 'csv':
            import csv
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['url', 'title', 'text', 'links', 'status_code'])
                writer.writeheader()
                for r in results:
                    row = r.to_dict()
                    row['links'] = ';'.join(row['links'])
                    writer.writerow(row)
        
        print(f"结果已保存到: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Web爬虫 - 数据采集/解析/存储",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python web_scraper.py --url https://example.com --output result.json
  python web_scraper.py --urls urls.txt --output results.csv --format csv
        """
    )
    
    parser.add_argument('--url', '-u', help='单个URL')
    parser.add_argument('--urls', help='URL文件路径（每行一个）')
    parser.add_argument('--output', '-o', required=True, help='输出文件路径')
    parser.add_argument('--format', '-f', choices=['json', 'csv'], default='json',
                        help='输出格式')
    parser.add_argument('--delay', '-d', type=float, default=1.0,
                        help='请求间隔（秒）')
    
    args = parser.parse_args()
    
    try:
        # 创建爬虫
        scraper = WebScraper(delay=args.delay)
        
        # 单URL模式
        if args.url:
            print(f"爬取: {args.url}")
            result = scraper.scrape(args.url)
            
            if result.error:
                print(f"错误: {result.error}", file=sys.stderr)
                sys.exit(1)
            
            # 保存结果
            scraper.save_results([result], args.output, args.format)
        
        # 批量模式
        elif args.urls:
            # 读取URL列表
            urls = [line.strip() for line in open(args.urls, 'r', encoding='utf-8') 
                    if line.strip() and not line.startswith('#')]
            
            print(f"批量爬取 {len(urls)} 个URL")
            results = scraper.scrape_batch(urls)
            
            # 保存结果
            scraper.save_results(results, args.output, args.format)
        
        else:
            parser.print_help()
        
        print("\n爬取完成")
        
    except Exception as e:
        print(f"执行失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
