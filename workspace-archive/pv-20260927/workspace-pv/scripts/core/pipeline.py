# -*- coding: utf-8 -*-
"""
光伏获客系统 - 流水线编排器 v0.2
修复：Windows emoji编码问题 + 日期查询逻辑
"""
import time
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

BASE = Path(__file__).parent.parent.parent
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(scripts_dir))
os.chdir(str(BASE))

# Windows console encoding fix (only if stdout is open)
if sys.platform == 'win32' and sys.stdout and hasattr(sys.stdout, 'buffer'):
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except ValueError:
        pass  # stdout was closed, skip encoding fix

from core.database import init_db, PVDatabase
from core.hot_topic_collector import HotTopicCollector
from core.policy_monitor import PolicyMonitor
from core.pv_analyzer import PVAnalyzer


class PVPipeline:
    """光伏获客系统主流水线"""

    def __init__(self):
        init_db()
        self.db = PVDatabase()
        self.collector = HotTopicCollector()
        self.policy = PolicyMonitor()
        self.analyzer = PVAnalyzer()
        self.start_time = None

    def run_full(self, verbose: bool = True) -> Dict:
        """执行完整流水线"""
        self.start_time = time.time()
        result = {
            "start": datetime.now().isoformat(),
            "steps": {},
            "summary": {}
        }

        # Step 1: 数据采集
        if verbose:
            print("[1/3] Starting data collection...")
        step1 = self._collect_data()
        result["steps"]["collect"] = step1

        # Step 2: 数据分析
        if verbose:
            print("[2/3] Running analysis...")
        step2 = self._analyze()
        result["steps"]["analyze"] = step2

        # Step 3: 生成简报
        if verbose:
            print("[3/3] Generating report...")
        step3 = self._report()
        result["steps"]["report"] = step3

        # 汇总
        elapsed = round(time.time() - self.start_time, 2)
        pv_related = step1.get("pv_related", 0)
        result["summary"] = {
            "elapsed": elapsed,
            "status": "ok",
            "topics_collected": step1.get("total", 0),
            "pv_related": pv_related,
        }

        if verbose:
            self._print_result(result)

        self.db.close()
        return result

    def _collect_data(self) -> Dict:
        try:
            collector_result = self.collector.collect_all()
            policy_result = self.policy.collect_all()

            return {
                "status": "ok",
                "hot_topics": collector_result,
                "policies": policy_result,
                "by_source": collector_result.get("by_source", {}),
                "pv_related": collector_result.get("pv_related", 0),
                "total": collector_result.get("total", 0),
            }
        except Exception as e:
            self.db.log_action("pipeline", "collect", "error", str(e)[:500])
            return {"status": "error", "message": str(e)}

    def _analyze(self) -> Dict:
        try:
            # 修复：使用更宽松的日期范围
            analysis = self.db.get_pv_analysis(days=30)
            hot = self.collector.get_latest_pv_topics(10)
            policy = self.db.get_latest_policies(10)

            return {
                "status": "ok",
                "today_pv_topics": analysis.get("today_pv_topics", 0),
                "total_pv_topics_30d": analysis.get("total_pv_topics", 0),
                "hot_topics": hot,
                "recent_policies": policy,
                "trends": analysis.get("trends", []),
            }
        except Exception as e:
            self.db.log_action("pipeline", "analyze", "error", str(e))
            return {"status": "error", "message": str(e)}

    def _report(self) -> str:
        try:
            report = []
            report.append("=" * 55)
            report.append("Solar PV System - Data Briefing")
            report.append("=" * 55)
            report.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            report.append("")

            # PV topics
            pv_topics = self.collector.get_latest_pv_topics(8)
            if pv_topics:
                report.append("Hot PV Topics:")
                for i, t in enumerate(pv_topics[:8], 1):
                    report.append(f"  {i}. [{t['source']}] {t['title'][:50]}")
            else:
                report.append("No PV topics found.")

            # Policies
            policies = self.db.get_latest_policies(5)
            if policies:
                report.append("\nRecent Policies:")
                for p in policies[:5]:
                    report.append(f"  - [{p['level']}] {p['title'][:45]}")

            # Analysis summary
            analysis = self.db.get_pv_analysis(days=30)
            report.append(f"\nSummary (30 days):")
            report.append(f"  PV topics: {analysis['today_pv_topics']} today, {analysis.get('total_pv_topics', 0)} total")
            report.append(f"  Sources: {analysis.get('sources', {})}")
            report.append(f"  Policies: {analysis['policy_count']}")

            elapsed = round(time.time() - self.start_time, 2)
            report.append(f"\nElapsed: {elapsed}s")
            report.append("=" * 55)

            report_text = "\n".join(report)

            output_dir = BASE / "data" / "output"
            output_dir.mkdir(exist_ok=True)
            date_str = datetime.now().strftime("%Y%m%d_%H%M")
            filepath = output_dir / f"report_{date_str}.txt"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report_text)

            self.db.log_action("pipeline", "report", "ok", f"Saved to {filepath}")
            return {"status": "ok", "report": report_text}
        except Exception as e:
            self.db.log_action("pipeline", "report", "error", str(e))
            return {"status": "error", "message": str(e)}

    def _print_result(self, result: Dict):
        summary = result["summary"]
        print(f"\n{'='*55}")
        print(f"Pipeline complete | Elapsed: {summary['elapsed']}s")
        print(f"  Collected: {summary['topics_collected']} total | PV-related: {summary['pv_related']}")
        print(f"{'='*55}\n")


def main():
    pipeline = PVPipeline()
    result = pipeline.run_full()
    print("\n" + result["steps"]["report"]["report"])
    return result


if __name__ == "__main__":
    main()
