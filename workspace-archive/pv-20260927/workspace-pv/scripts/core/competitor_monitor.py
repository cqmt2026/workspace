# -*- coding: utf-8 -*-
"""
光伏获客系统 - 竞品监控模块 v0.1
监控抖音/头条上头部光伏账号的内容策略

竞品列表（可根据需要扩展）：
- 正泰安能、创维光伏、天合富家、皇明太阳能等
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

if sys.platform == 'win32':
    pass  # encoding handled by caller

from core.database import PVDatabase


class CompetitorMonitor:
    """光伏竞品监控器"""

    # 预设竞品账号（platform, account_name, account_id）
    DEFAULT_COMPETITORS = [
        ("douyin", "正泰安能", ""),
        ("douyin", "创维光伏", ""),
        ("douyin", "天合富家", ""),
        ("douyin", "皇明太阳能", ""),
        ("douyin", "阿特斯阳光电力", ""),
        ("douyin", "协鑫新能源", ""),
        ("douyin", "晶澳太阳能", ""),
        ("douyin", "隆基绿能", ""),
        ("douyin", "阳光电源", ""),
        ("douyin", "户用光伏", ""),
        ("toutiao", "正泰安能", ""),
        ("toutiao", "创维光伏", ""),
        ("toutiao", "天合富家", ""),
    ]

    def __init__(self):
        self.db = PVDatabase()

    def register_competitors(self) -> int:
        """注册默认竞品账号到数据库"""
        saved = 0
        for platform, name, account_id in self.DEFAULT_COMPETITORS:
            cur = self.db.conn.cursor()
            cur.execute("""
                INSERT OR IGNORE INTO competitors
                (platform, account_name, account_id, followers)
                VALUES (?, ?, ?, 0)
            """, (platform, name, account_id))
            if cur.rowcount > 0:
                saved += 1
        self.db.conn.commit()
        return saved

    def add_competitor(self, platform: str, account_name: str,
                       account_id: str = "", followers: int = 0) -> int:
        """添加单个竞品"""
        return self.db.add_competitor(platform, account_name, account_id, followers)

    def get_all_competitors(self) -> List[Dict]:
        """获取所有竞品"""
        return self.db.get_all_competitors()

    def collect_competitor_content(self, platform: str, account_name: str) -> List[Dict]:
        """
        采集竞品最新内容（预留接口，实际需对接各平台API）
        当前返回空列表，等待后续接入Playwright
        """
        results = []
        # TODO: 接入抖音/头条内容采集
        # 目前竞品监控以手动录入为主
        self.db.log_action("competitor", "collect", "info",
                           f"{platform}/{account_name}: not yet automated, need Playwright")
        return results

    def run(self, verbose: bool = True) -> Dict:
        """运行竞品监控"""
        # 注册默认竞品
        saved = self.register_competitors()
        if verbose:
            print(f"[Competitor] Registered {saved} new accounts")

        all_competitors = self.get_all_competitors()
        if verbose:
            print(f"\n[Competitor] Total tracked: {len(all_competitors)}")
            for c in all_competitors[:10]:
                print(f"  [{c['platform']}] {c['account_name']}")

        self.db.close()
        return {"registered": saved, "total": len(all_competitors),
                "competitors": all_competitors}


if __name__ == "__main__":
    monitor = CompetitorMonitor()
    result = monitor.run()
    print(f"\n[Done] Total competitors: {result['total']}")