#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文章抓取工具 V1.0
集成 scrapling-article-fetch 功能
用于采集政策文件/竞品文章/新闻素材

作者：房地产自媒体团队
版本：V1.0
创建时间：2026-03-16 13:57
"""

import subprocess
import json
from datetime import datetime
from pathlib import Path
import sys

# 添加路径
sys.path.append(str(Path(__file__).parent))
from logger import logger


class ArticleFetcher:
    """文章抓取器（基于 scrapling-article-fetch）"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent.parent.parent / "skills" / "scrapling-article-fetch" / "scripts"
        self.output_dir = Path(__file__).parent.parent / "fetch_articles"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 默认配置
        self.max_chars = 50000  # 默认 50000 字上限
        self.python_cmd = "python3"  # 优先使用 python3
    
    def check_environment(self):
        """
        检查运行环境
        
        Returns:
            bool: 环境是否就绪
        """
        logger.info("检查运行环境...")
        
        try:
            # 检查 Python 版本
            result = subprocess.run(
                [self.python_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info(f"Python 环境：{result.stdout.strip()}")
                return True
            else:
                # 尝试 python
                self.python_cmd = "python"
                result = subprocess.run(
                    ["python", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    logger.info(f"Python 环境：{result.stdout.strip()}")
                    return True
                else:
                    logger.error("未找到 Python 环境")
                    return False
                    
        except Exception as e:
            logger.error(f"环境检查失败：{e}")
            return False
    
    def fetch_article(self, url, max_chars=None):
        """
        抓取文章
        
        Args:
            url: 文章 URL
            max_chars: 最大字符数（默认 50000）
        
        Returns:
            dict: 抓取结果 {title, content, source, fetch_time}
        """
        if max_chars is None:
            max_chars = self.max_chars
        
        logger.info(f"开始抓取文章：{url}")
        
        try:
            # 检查环境
            if not self.check_environment():
                return None
            
            # 运行抓取脚本
            fetch_script = self.script_dir / "scrapling_fetch.py"
            
            if not fetch_script.exists():
                logger.error(f"抓取脚本不存在：{fetch_script}")
                return None
            
            result = subprocess.run(
                [
                    self.python_cmd,
                    str(fetch_script),
                    url,
                    str(max_chars)
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"抓取失败：{result.stderr}")
                return None
            
            # 解析结果
            try:
                article_data = json.loads(result.stdout)
                
                # 标准化输出
                standardized = {
                    "title": article_data.get("title", "无标题"),
                    "content": article_data.get("content", ""),
                    "source": url,
                    "fetch_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "raw_data": article_data
                }
                
                logger.info(f"抓取成功：{standardized['title']}")
                return standardized
                
            except json.JSONDecodeError as e:
                logger.error(f"解析结果失败：{e}")
                logger.error(f"原始输出：{result.stdout[:500]}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("抓取超时（60 秒）")
            return None
        except Exception as e:
            logger.error(f"抓取失败：{e}")
            return None
    
    def save_article(self, article_data, filename=None):
        """
        保存抓取结果
        
        Args:
            article_data: 抓取结果字典
            filename: 文件名（默认自动生成）
        
        Returns:
            Path: 保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            title_safe = "".join(c for c in article_data['title'] if c.isalnum() or c in " -_").strip()[:50]
            filename = f"{timestamp}_{title_safe}.md"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {article_data['title']}\n\n")
            f.write(f"**原文链接**: {article_data['source']}\n")
            f.write(f"**抓取时间**: {article_data['fetch_time']}\n\n")
            f.write("---\n\n")
            f.write(article_data['content'])
        
        logger.info(f"文章已保存：{filepath}")
        return filepath
    
    def fetch_and_save(self, url, max_chars=None):
        """
        抓取并保存文章
        
        Args:
            url: 文章 URL
            max_chars: 最大字符数
        
        Returns:
            Path: 保存的文件路径，失败返回 None
        """
        article_data = self.fetch_article(url, max_chars)
        
        if article_data:
            filepath = self.save_article(article_data)
            return filepath
        else:
            logger.error("抓取失败，未保存")
            return None
    
    def batch_fetch(self, urls, max_chars=None):
        """
        批量抓取文章
        
        Args:
            urls: URL 列表
            max_chars: 最大字符数
        
        Returns:
            list: 抓取结果列表
        """
        logger.info(f"开始批量抓取 {len(urls)} 篇文章...")
        
        results = []
        for i, url in enumerate(urls, 1):
            logger.info(f"[{i}/{len(urls)}] 抓取：{url}")
            article_data = self.fetch_article(url, max_chars)
            
            if article_data:
                filepath = self.save_article(article_data)
                results.append({
                    "url": url,
                    "title": article_data['title'],
                    "filepath": str(filepath),
                    "status": "success"
                })
            else:
                results.append({
                    "url": url,
                    "title": None,
                    "filepath": None,
                    "status": "failed"
                })
        
        # 生成批量抓取报告
        report_path = self.output_dir / f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 批量抓取报告\n\n")
            f.write(f"**抓取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**总数**: {len(urls)}\n")
            f.write(f"**成功**: {sum(1 for r in results if r['status'] == 'success')}\n")
            f.write(f"**失败**: {sum(1 for r in results if r['status'] == 'failed')}\n\n")
            
            f.write("## 抓取结果\n\n")
            for r in results:
                status_icon = "✅" if r['status'] == 'success' else "❌"
                f.write(f"{status_icon} {r['title'] or '抓取失败'}\n")
                f.write(f"   - URL: {r['url']}\n")
                if r['filepath']:
                    f.write(f"   - 文件：{r['filepath']}\n")
                f.write("\n")
        
        logger.info(f"批量抓取报告：{report_path}")
        
        return results


def main():
    """主函数 - 测试示例"""
    fetcher = ArticleFetcher()
    
    # 测试单个文章抓取
    print("=" * 60)
    print("文章抓取工具测试")
    print("=" * 60)
    
    # 示例 URL（可替换为实际政策文件 URL）
    test_urls = [
        "https://example.com/policy1",  # 替换为实际 URL
        "https://example.com/policy2",  # 替换为实际 URL
    ]
    
    # 测试单个抓取
    print("\n[测试 1] 单个文章抓取...")
    # filepath = fetcher.fetch_and_save(test_urls[0])
    # if filepath:
    #     print(f"抓取成功：{filepath}")
    
    # 测试批量抓取
    print("\n[测试 2] 批量文章抓取...")
    # results = fetcher.batch_fetch(test_urls)
    # print(f"成功：{sum(1 for r in results if r['status'] == 'success')}")
    # print(f"失败：{sum(1 for r in results if r['status'] == 'failed')}")
    
    print("\n" + "=" * 60)
    print("测试完成！请替换 test_urls 为实际 URL 后运行")
    print("=" * 60)


if __name__ == '__main__':
    main()
