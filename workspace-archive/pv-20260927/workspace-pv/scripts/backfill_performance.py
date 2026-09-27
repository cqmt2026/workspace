# -*- coding: utf-8 -*-
"""
光伏获客系统 - 效果数据回填脚本
用途：为已发布内容回填模拟播放数据，生成测试线索
触发：手动执行 或 后续接入真实API
"""
import sys, os, random
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

from core.database import PVDatabase


def fill_plays_data(days_back: int = 7, seed: int = 42):
    """为最近N天的已发布内容回填模拟播放数据"""
    random.seed(seed)
    db = PVDatabase()
    cur = db.conn.cursor()

    # 获取最近N天的已发布内容
    cur.execute("""
        SELECT content_id, channel, created_at 
        FROM content_items 
        WHERE status = 'published' 
          AND created_at >= datetime('now', 'localtime', ?)
        ORDER BY created_at DESC
    """, (f"-{days_back} days",))
    rows = cur.fetchall()
    print(f"Found {len(rows)} published items in last {days_back} days")

    filled = 0
    for row in rows:
        content_id = row['content_id']
        channel = row['channel']
        created_at = row['created_at']
        try:
            age_hours = max(1, (datetime.now() - datetime.strptime(created_at[:19], "%Y-%m-%d %H:%M:%S")).total_seconds() / 3600)
        except:
            age_hours = 24

        # 模拟播放数据：基于发布时间和渠道
        if channel == 'douyin':
            plays = max(0, int(age_hours * random.uniform(0.5, 3.0)))
        else:  # toutiao
            plays = max(0, int(age_hours * random.uniform(0.3, 1.5)))

        # 更新content_items
        cur.execute("""
            UPDATE content_items 
            SET plays=?
            WHERE content_id=?
        """, (plays, content_id))

        filled += 1

    db.conn.commit()
    print(f"Filled plays data for {filled} items")
    db.close()
    return filled


def generate_test_leads(count: int = 10):
    """生成测试线索数据（用于测试L4线索层）"""
    db = PVDatabase()
    cur = db.conn.cursor()

    lead_names = ['张**', '李**', '王**', '刘**', '陈**', '杨**', '赵**', '黄**', '周**', '吴**']
    lead_tags = ['报价', '安装', '政策咨询', '屋顶面积', '电费疑问', '逆变器', '补贴', '并网']
    lead_levels = ['A', 'B', 'C']

    # 获取已发布内容的content_id
    cur.execute("SELECT content_id FROM content_items WHERE status='published' ORDER BY created_at DESC LIMIT 20")
    content_ids = [r['content_id'] for r in cur.fetchall()]

    new_leads = 0
    for i in range(count):
        name = random.choice(lead_names)
        tag = random.choice(lead_tags)
        level = random.choice(lead_levels)
        cid = random.choice(content_ids) if content_ids else "PV_test_001"
        cur.execute("""
            INSERT INTO leads (source_channel, source_content_id, name, phone, level, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            'douyin' if random.random() > 0.3 else 'toutiao',
            cid,
            name,
            f'1{random.randint(300000000, 1999999999)}',
            level,
            tag,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        new_leads += 1

    db.conn.commit()
    print(f"Generated {new_leads} new test leads")
    db.close()
    return new_leads


if __name__ == "__main__":
    print("=" * 50)
    print("  PV System - Performance Data Backfill")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Step 1: Fill plays
    filled = fill_plays_data(days_back=7)
    print(f"Plays data: {filled} items filled")

    # Step 2: Generate test leads
    leads = generate_test_leads(count=10)
    print(f"Test leads: {leads} new leads")

    print("\nDone!")
