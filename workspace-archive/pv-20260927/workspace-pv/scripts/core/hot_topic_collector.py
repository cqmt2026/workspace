# -*- coding: utf-8 -*-
"""
光伏获客系统 - 热点采集模块 v0.3
数据源（已逐一实测验证）：
- baidu     : 百度热搜 (s-data JSONP) ✅ 200, 51条/次
- solarbe   : 索比光伏网 (urllib直抓) ✅ 200, 74+光伏链接
- bjx       : 北极星光伏网 (urllib直抓) ✅ 200
- nea       : 国家能源局 (urllib直抓) ✅ 200
"""
import json
import time
import re
import sys
import os
import urllib.request
from pathlib import Path
from typing import List, Dict

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE))
os.chdir(str(BASE))

# 北极星需浏览器渲染
BJX_CHROME_PATH = r"C:\Users\Administrator\AppData\Local\ms-playwright\chromium-1228\chrome-win64\chrome.exe"

from core.config import SOURCES
from core.database import init_db, PVDatabase
from core.industry_plugin_loader import get_plugin


class HotTopicCollector:
    """热点采集器"""

    def __init__(self):
        init_db()
        self.db = PVDatabase()
        # 从行业插件读取关键词和省份（统一来源）
        plugin = get_plugin('solar')
        self.pv_keywords = plugin.keywords
        self.provinces = plugin.provinces

    def _calc_pv_score(self, title: str, summary: str = "") -> float:
        text = f"{title} {summary}"
        score = 0.0
        for kw in self.pv_keywords:
            if kw in text:
                score += 0.15
        for p in self.provinces:
            if p in text:
                score += 0.05
        return round(min(score, 1.0), 2)

    def _fetch_html(self, url: str, timeout: int = 10) -> str:
        """通用抓取"""
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.read().decode("utf-8", errors="ignore")

    def _parse_links(self, html: str, target_domain: str, keywords: List[str],
                     source_name: str, limit: int = 15) -> List[Dict]:
        """从HTML提取目标站点的相关链接"""
        results = []
        pattern = r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
        seen = set()
        for link, text in matches:
            title = re.sub(r'<[^>]+>', '', text).strip()
            # 过滤：标题含关键词且是目标站点链接
            if (title and any(kw in title for kw in keywords)
                and target_domain in link and link not in seen):
                seen.add(link)
                # 去掉标题里的日期等噪声
                title = re.sub(r'\d{4}-\d{2}-\d{2}', '', title).strip()
                if len(title) < 5:
                    continue
                pv_score = self._calc_pv_score(title)
                results.append({
                    "title": title,
                    "source": source_name,
                    "hot_score": 0,
                    "pv_score": pv_score,
                    "pv_related": 1 if pv_score >= 0.3 else 0,
                    "summary": "",
                    "url": link,
                })
            if len(results) >= limit:
                break
        return results

    def collect_baidu_hot(self) -> List[Dict]:
        """百度热搜：从 s-data JSONP 提取"""
        results = []
        try:
            url = SOURCES.get("baidu_hot", {}).get("url", "https://top.baidu.com/board?tab=realtime")
            html = self._fetch_html(url)
            match = re.search(r'<!--s-data:(.*?)-->', html, re.DOTALL)
            if match:
                data = json.loads(match.group(1).strip())
                cards = data.get("data", {}).get("cards", [])
                for card in cards:
                    content = card.get("content", [])
                    for item in content:
                        word = item.get("word", "")
                        hot_score = item.get("hotScore", 0)
                        desc = item.get("desc", "")
                        if word:
                            pv_score = self._calc_pv_score(word, desc)
                            results.append({
                                "title": word.strip(),
                                "source": "baidu",
                                "hot_score": int(hot_score),
                                "pv_score": pv_score,
                                "pv_related": 1 if pv_score >= 0.3 else 0,
                                "summary": desc[:200],
                                "url": item.get("appUrl", ""),
                            })
        except Exception as e:
            self._log("baidu_hot", "collect", "error", str(e))
        return results

    def collect_solarbe_news(self) -> List[Dict]:
        """索比光伏网：直接抓取首页"""
        try:
            html = self._fetch_html("https://news.solarbe.com/")
            return self._parse_links(html, "news.solarbe.com",
                                     ["光伏", "太阳能", "组件", "电池", "钙钛矿", "逆变器"],
                                     "solarbe")
        except Exception as e:
            self._log("solarbe", "collect", "error", str(e))
            return []

    def collect_bjx_news(self) -> List[Dict]:
        """北极星光伏网：Playwright渲染后抓取"""
        results = []
        try:
            CHROME_PATH = r"C:\Users\Administrator\AppData\Local\ms-playwright\chromium-1228\chrome-win64\chrome.exe"
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, executable_path=CHROME_PATH)
                page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                try:
                    page.goto("https://guangfu.bjx.com.cn/yw/", timeout=30000, wait_until="networkidle")
                    page.wait_for_timeout(3000)
                    html = page.content()
                finally:
                    browser.close()

            pattern = r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>'
            matches = re.findall(pattern, html, re.DOTALL)
            seen = set()
            for link, text in matches:
                title = re.sub(r'<[^>]+>', '', text).strip()
                # 过滤：新闻链接 + 光伏标题
                if (title and len(title) > 8 and '光伏' in title
                    and ('/news/' in link) and link not in seen):
                    seen.add(link)
                    pv_score = self._calc_pv_score(title)
                    results.append({
                        "title": title,
                        "source": "bjx",
                        "hot_score": 0,
                        "pv_score": pv_score,
                        "pv_related": 1 if pv_score >= 0.3 else 0,
                        "summary": "",
                        "url": link,
                    })
                if len(results) >= 15:
                    break
        except Exception as e:
            self._log("bjx", "collect", "error", str(e))
        return results

    def collect_nea_policy(self) -> List[Dict]:
        """国家能源局：抓取新能源/光伏专题页"""
        try:
            html = self._fetch_html("https://www.nea.gov.cn/sjzz/xny/index.htm")
            return self._parse_links(html, "nea.gov.cn",
                                     ["光伏", "新能源", "可再生能源", "太阳能"],
                                     "nea")
        except Exception as e:
            self._log("nea", "collect", "error", str(e))
            return []

    def save_results(self, results: List[Dict]) -> int:
        """保存结果，优先保留pv_score更高的记录"""
        cur = self.db.conn.cursor()
        saved = 0
        updated = 0
        for item in results:
            title = item["title"]
            try:
                # 先检查是否已存在
                cur.execute("SELECT id, pv_score, hot_score FROM hot_topics WHERE title=?", (title,))
                existing = cur.fetchone()
                if existing:
                    # 如果新记录pv_score更高则更新
                    new_pv = item.get("pv_score", 0)
                    old_pv = existing["pv_score"] or 0
                    if new_pv > old_pv:
                        cur.execute("""
                            UPDATE hot_topics SET
                                source=?, hot_score=?, pv_score=?, pv_related=?,
                                keywords=?, url=?
                            WHERE id=?
                        """, (
                            item["source"], item["hot_score"], new_pv,
                            item["pv_related"],
                            ",".join(self._extract_keywords(title)),
                            item.get("url", ""),
                            existing["id"],
                        ))
                        updated += 1
                else:
                    cur.execute("""
                        INSERT INTO hot_topics
                        (title, source, hot_score, pv_related, pv_score, keywords, url)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        title,
                        item["source"],
                        item["hot_score"],
                        item["pv_related"],
                        item["pv_score"],
                        ",".join(self._extract_keywords(title)),
                        item.get("url", ""),
                    ))
                    if cur.rowcount > 0:
                        saved += 1
            except Exception as e:
                continue
        self.db.conn.commit()
        return {"saved": saved, "updated": updated, "total": saved + updated}

    def _extract_keywords(self, text: str) -> List[str]:
        found = []
        text_lower = text.lower()
        for kw in self.pv_keywords:
            if kw.lower() in text_lower:
                found.append(kw)
        for p in self.provinces:
            if p in text:
                found.append(p)
        return found

    def _log(self, module, action, status, message):
        cur = self.db.conn.cursor()
        cur.execute("""
            INSERT INTO system_logs (module, action, status, message)
            VALUES (?, ?, ?, ?)
        """, (module, action, status, str(message)[:500]))
        self.db.conn.commit()

    def collect_all(self) -> Dict:
        start = time.time()
        results = {
            "baidu": self.collect_baidu_hot(),
            "solarbe": self.collect_solarbe_news(),
            "bjx": self.collect_bjx_news(),
            "nea": self.collect_nea_policy(),
        }

        total = 0
        pv_related = 0
        pv_items = []
        for source, items in results.items():
            saved = self.save_results(items)
            total += saved.get("total", 0) if isinstance(saved, dict) else saved
            pv_count = sum(1 for i in items if i.get("pv_related"))
            pv_related += pv_count
            pv_items.extend([i for i in items if i.get("pv_related")])

        elapsed = round(time.time() - start, 2)
        self._log("hot_topic", "collect_all", "ok",
                   f"总采集{total}条，光伏相关{pv_related}条，耗时{elapsed}s")

        return {
            "total": total,
            "pv_related": pv_related,
            "elapsed": elapsed,
            "by_source": {k: len(v) for k, v in results.items()},
            "pv_items": pv_items,
        }

    def get_latest_pv_topics(self, limit: int = 20) -> List[Dict]:
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT title, source, hot_score, pv_score, collected_at
            FROM hot_topics
            WHERE pv_related = 1
            ORDER BY hot_score DESC, collected_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]