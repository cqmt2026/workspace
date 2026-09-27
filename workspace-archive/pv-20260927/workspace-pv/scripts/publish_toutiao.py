# -*- coding: utf-8 -*-
"""
光伏获客系统 - 头条草稿批量审核+发布脚本
用途：审核今日头条草稿，标记为已发布
触发：手动执行
"""
import sys, os
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

from core.database import PVDatabase


def publish_toutiao_drafts(date_str: str = None):
    """批量审核并发布指定日期的头条草稿"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")

    db = PVDatabase()
    cur = db.conn.cursor()

    # 查找今日头条草稿
    cur.execute("""
        SELECT content_id, tracking_id, created_at 
        FROM content_items 
        WHERE channel = 'toutiao' 
          AND status = 'draft'
          AND created_at LIKE ?
        ORDER BY created_at
    """, (date_str + "%",))
    drafts = cur.fetchall()

    if not drafts:
        print(f"No toutiao drafts found for {date_str}")
        db.close()
        return 0

    published = 0
    for row in drafts:
        content_id = row['content_id']
        # 更新状态为published
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        cur.execute("""
            UPDATE content_items 
            SET status='published', published_at=?
            WHERE content_id=?
        """, (now, content_id))
        published += 1
        print(f"  Published: {content_id}")

    db.conn.commit()
    print(f"\nPublished {published}/{len(drafts)} drafts")
    db.close()
    return published


if __name__ == "__main__":
    print("=" * 50)
    print("  PV System - Toutiao Draft Publisher")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    count = publish_toutiao_drafts()
    print(f"\nDone! Published {count} items.")
