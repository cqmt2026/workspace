# -*- coding: utf-8 -*-
"""
光伏获客系统 - 追踪ID生成器 v0.1
为每次内容生成/发布生成唯一追踪ID，确保归因链路可追溯
"""
import sys, os
from pathlib import Path
from datetime import datetime
from typing import Optional

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))


class Tracker:
    """追踪ID生成和管理"""

    @staticmethod
    def generate_id(channel: str = "pv") -> str:
        """生成唯一追踪ID"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:18]
        return f"{channel.upper()}_{ts}"

    @staticmethod
    def extract_info(tracking_id: str) -> Optional[dict]:
        """从追踪ID提取信息"""
        try:
            parts = tracking_id.split("_")
            if len(parts) >= 2:
                channel = parts[0]
                from datetime import datetime as dt
                try:
                    created = dt.strptime("_".join(parts[1:3]), "%Y%m%d_%H%M%S%f")
                except:
                    created = None
                return {"channel": channel, "created_at": created}
        except:
            pass
        return None

    @staticmethod
    def inject_url(content_id: str, base_url: str) -> str:
        """在URL中注入追踪参数"""
        sep = "&" if "?" in base_url else "?"
        return f"{base_url}{sep}utm_source=pv&utm_content={content_id}"


if __name__ == "__main__":
    tid = Tracker.generate_id()
    info = Tracker.extract_info(tid)
    url = Tracker.inject_url(tid, "https://example.com/video/123")
    print(f"  Tracking ID: {tid}")
    print(f"  Info: {info}")
    print(f"  URL: {url}")