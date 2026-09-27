# -*- coding: utf-8 -*-
"""
光伏获客系统 - 政策监控模块 v0.2
新增：国家能源局政策搜索、CPIA行业数据搜索
"""
import re
import json
import time
import sys
import os
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE))
os.chdir(str(BASE))

from core.industry_plugin_loader import get_plugin
from core.database import PVDatabase


class PolicyMonitor:
    """政策监控器"""

    def __init__(self):
        self.db = PVDatabase()
        plugin = get_plugin('solar')
        self.pv_keywords = plugin.keywords
        self.provinces = plugin.provinces

    def search_policy(self, query: str, source: str) -> List[Dict]:
        """通用搜索：绕过百度安全验证"""
        results = []
        try:
            url = f"https://www.baidu.com/s?wd={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            resp = urllib.request.urlopen(req, timeout=10)
            html = resp.read().decode("utf-8", errors="ignore")

            if len(html) < 3000 or "百度安全验证" in html:
                return results

            pattern = r'<h3[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html)
            seen = set()
            for link, title in matches:
                title = title.strip()
                if title and link not in seen:
                    seen.add(link)
                    pv_score = sum(1 for kw in self.pv_keywords if kw in title) * 0.15
                    results.append({
                        "title": title,
                        "url": link,
                        "source": source,
                        "level": "national",
                        "province": None,
                        "policy_type": self._detect_type(title),
                    })
                if len(results) >= 10:
                    break
        except Exception as e:
            self._log(source, "search", "error", str(e))
        return results

    def collect_nea_policy(self) -> List[Dict]:
        """国家能源局：搜索光伏相关公告"""
        queries = [
            "国家能源局 光伏 政策",
            "国家能源局 分布式光伏 通知",
            "国家能源局 光伏并网",
        ]
        all_results = []
        for query in queries:
            results = self.search_policy(query, "nea")
            all_results.extend(results)
            time.sleep(1)  # 避免被限速
        return all_results

    def collect_cpia_data(self) -> List[Dict]:
        """CPIA中国光伏行业协会：搜索行业数据"""
        queries = [
            "中国光伏行业协会 CPIA 光伏 数据",
            "中国光伏行业协会 装机 2026",
        ]
        all_results = []
        for query in queries:
            results = self.search_policy(query, "cpia")
            all_results.extend(results)
            time.sleep(1)
        return all_results

    def _detect_level(self, title: str) -> str:
        if any(kw in title for kw in ["国家", "全国", "国务院", "发改委", "能源局"]):
            return "national"
        for p in self.provinces:
            if p in title:
                return "province"
        return "national"

    def _detect_province(self, title: str):
        for p in self.provinces:
            if p in title:
                return p
        return None

    def _detect_type(self, title: str) -> str:
        if any(kw in title for kw in ["补贴", "补助", "奖励"]):
            return "subsidy"
        if any(kw in title for kw in ["并网", "接入", "备案"]):
            return "grid"
        if any(kw in title for kw in ["标准", "规范", "质量"]):
            return "standard"
        if any(kw in title for kw in ["规划", "目标", "十四五", "十五五"]):
            return "plan"
        return "other"

    def save_results(self, results: List[Dict]) -> int:
        cur = self.db.conn.cursor()
        saved = 0
        for item in results:
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO policies
                    (title, province, level, policy_type, url, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    item["title"],
                    item.get("province"),
                    item.get("level", self._detect_level(item["title"])),
                    item.get("policy_type", self._detect_type(item["title"])),
                    item.get("url", ""),
                    item.get("source", "web"),
                ))
                if cur.rowcount > 0:
                    saved += 1
            except:
                continue
        self.db.conn.commit()
        return saved

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
            "nea": self.collect_nea_policy(),
            "cpia": self.collect_cpia_data(),
        }

        total = 0
        for source, items in results.items():
            saved = self.save_results(items)
            total += saved

        elapsed = round(time.time() - start, 2)
        self._log("policy", "collect_all", "ok",
                   f"总采集{total}条，耗时{elapsed}s")

        return {
            "total": total,
            "elapsed": elapsed,
            "by_source": {k: len(v) for k, v in results.items()},
        }

    def get_latest_policies(self, limit: int = 10) -> List[Dict]:
        cur = self.db.conn.cursor()
        cur.execute("""
            SELECT title, province, level, policy_type, collected_at
            FROM policies
            ORDER BY collected_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]