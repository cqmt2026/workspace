# -*- coding: utf-8 -*-
"""
光伏获客系统 - 数据采集流水线 v0.3
策略：优先用web_search，备选用HTTP抓取
"""
import sys, os, re, json, time, urllib.request
from pathlib import Path
from typing import List, Dict
from datetime import datetime

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

from core.database import init_db, PVDatabase
from core.config import PV_KEYWORDS, PROVINCES


class PVPipeline:
    def __init__(self):
        init_db()
        self.db = PVDatabase()
        self.pv_keywords = PV_KEYWORDS

    def _calc_pv_score(self, title: str) -> float:
        text = title.lower()
        score = 0.0
        for kw in self.pv_keywords:
            if kw.lower() in text:
                score += 0.15
        return round(min(score, 1.0), 2)

    def collect_from_web_search(self) -> List[Dict]:
        """用web_search采集光伏热点"""
        results = []
        queries = [
            "光伏 2026年8月 热点 新闻",
            "分布式光伏 补贴 政策",
            "光伏发电 安装 收益",
            "光伏 龙头企业 业绩",
        ]
        for query in queries:
            try:
                import subprocess
                cmd = [
                    sys.executable, "-c",
                    f'''
import json, sys
sys.path.insert(0, r"C:/Users/Administrator/.openclaw/workspace")
try:
    from mx_search import search
    data = search({repr(query)})
    results = data.get("data", []) or data.get("results", [])
    for item in results[:8]:
        title = item.get("title","") or item.get("query","")
        url = item.get("url","")
        desc = item.get("description","")
        site = item.get("siteName","")
        pv_check_kw = ["光伏", "太阳能", "新能源", "储能", "分布式", "屋顶", "补贴政策"]
                        if title and any(kw in title for kw in pv_check_kw):
            print(json.dumps({{"title":title[:80],"source":"mx_search","url":url,"site":site}}))
except Exception as e:
    print(f"ERROR:{{e}}", file=sys.stderr)
'''
                ]
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=20, encoding='utf-8')
                for line in r.stdout.strip().split('\n'):
                    try:
                        item = json.loads(line)
                        title = item["title"]
                        pv_score = self._calc_pv_score(title)
                        results.append({
                            "title": title,
                            "source": "mx_search",
                            "hot_score": 0,
                            "pv_score": pv_score,
                            "pv_related": 1 if pv_score >= 0.2 else 0,
                            "url": item.get("url", ""),
                        })
                    except:
                        pass
            except Exception as e:
                self.db.log_action("search", "collect", "error", str(e)[:50])
        return results

    def collect_baidu_hot(self) -> List[Dict]:
        """百度热搜"""
        results = []
        try:
            url = "https://top.baidu.com/board?tab=realtime"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            resp = urllib.request.urlopen(req, timeout=10)
            html = resp.read().decode("utf-8", errors="ignore")

            pattern = r'"word":"([^"]+)"[^}]*"hotScore":(\d+)'
            matches = re.findall(pattern, html)
            for title, score in matches[:50]:
                title = title.strip()
                if title:
                    pv_score = self._calc_pv_score(title)
                    results.append({
                        "title": title,
                        "source": "baidu",
                        "hot_score": int(score) if score.isdigit() else 0,
                        "pv_score": pv_score,
                        "pv_related": 1 if pv_score >= 0.3 else 0,
                    })

            if not results:
                titles = re.findall(r'<div[^>]*class="c-single-text[^"]*"[^>]*>([^<]+)</div>', html)
                for title in titles[:50]:
                    title = title.strip()
                    if title:
                        pv_score = self._calc_pv_score(title)
                        results.append({
                            "title": title,
                            "source": "baidu",
                            "hot_score": 0,
                            "pv_score": pv_score,
                            "pv_related": 1 if pv_score >= 0.3 else 0,
                        })
        except Exception as e:
            self.db.log_action("baidu", "collect", "error", str(e))
        return results

    def save_results(self, results: List[Dict]) -> int:
        cur = self.db.conn.cursor()
        saved = 0
        for item in results:
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO hot_topics
                    (title, source, hot_score, pv_related, pv_score, url)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (item["title"], item["source"], item["hot_score"],
                      item["pv_related"], item["pv_score"], item.get("url", "")))
                if cur.rowcount > 0:
                    saved += 1
            except:
                continue
        self.db.conn.commit()
        return saved

    def run(self) -> Dict:
        start = time.time()
        print("📡 光伏数据采集 v0.3")
        print("=" * 40)

        all_results = []
        sources = [
            ("mx-search", self.collect_from_web_search()),
            ("百度热搜", self.collect_baidu_hot()),
        ]

        for name, results in sources:
            saved = self.save_results(results)
            pv_count = sum(1 for r in results if r.get("pv_related"))
            print(f"  {name}: {len(results)} 条 (光伏: {pv_count}, 保存: {saved})")
            all_results.extend(results)

        # 去重
        seen = set()
        unique = []
        for r in all_results:
            if r["title"] not in seen:
                seen.add(r["title"])
                unique.append(r)
        all_results = unique

        pv_related = sum(1 for r in all_results if r.get("pv_related"))
        elapsed = round(time.time() - start, 2)
        print(f"\n✅ 完成 | 总计: {len(all_results)} 条 | 光伏相关: {pv_related} 条 | 耗时: {elapsed}s")

        # 展示光伏话题
        pv_items = [r for r in all_results if r.get("pv_related")]
        if pv_items:
            print("\n🔥 光伏相关话题:")
            for i, r in enumerate(pv_items[:8], 1):
                print(f"  {i}. [{r['source']}] {r['title'][:50]}")
        else:
            print("\n⚠️ 今日热搜暂无光伏话题，但专业数据源有内容:")
            for i, r in enumerate(all_results[:5], 1):
                print(f"  {i}. [{r['source']}] {r['title'][:50]}")

        # 保存报告
        report_path = BASE / "data" / "output" / f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"光伏数据采集报告\n")
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"总条数: {len(all_results)}\n")
            f.write(f"光伏相关: {pv_related}\n\n")
            if pv_items:
                f.write("光伏热点:\n")
                for r in pv_items[:10]:
                    f.write(f"  [{r['source']}] {r['title'][:60]}\n")
        print(f"\n📄 报告: {report_path}")

        self.db.close()
        return {"total": len(all_results), "pv_related": pv_related, "elapsed": elapsed}


def main():
    pipeline = PVPipeline()
    return pipeline.run()


if __name__ == "__main__":
    main()