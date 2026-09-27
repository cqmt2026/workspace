# -*- coding: utf-8 -*-
"""光伏获客系统 Dashboard API - 返回JSON数据给前端"""
import sys, os, json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

from core.database import PVDatabase

def get_dashboard_data():
    db = PVDatabase()
    cur = db.conn.cursor()

    # 核心指标
    cur.execute("SELECT count(*) FROM content_items")
    total = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM content_items WHERE status=?", ("published",))
    published = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM content_items WHERE status=?", ("draft",))
    draft = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM leads")
    leads = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM attribution")
    attributions = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(close_amount), 0) FROM attribution WHERE converted=1")
    revenue = cur.fetchone()[0]

    # 渠道分布
    cur.execute("""
        SELECT channel, 
               sum(case when status='published' then 1 else 0 end) as published_cnt,
               sum(case when status='draft' then 1 else 0 end) as draft_cnt
        FROM content_items GROUP BY channel
    """)
    channels = {r[0]: {"published": r[1], "draft": r[2]} for r in cur.fetchall()}

    # 日趋势（近7天）
    cur.execute("""
        SELECT date(published_at) as d, count(*) as c
        FROM content_items WHERE status='published'
        GROUP BY d ORDER BY d DESC LIMIT 7
    """)
    daily = [{"date": r[0], "count": r[1]} for r in cur.fetchall()]
    daily.reverse()

    # 最近20条内容
    cur.execute("""
        SELECT content_id, channel, status, published_at, tracking_id
        FROM content_items ORDER BY created_at DESC LIMIT 20
    """)
    recent = [dict(r) for r in cur.fetchall()]

    # 热点统计
    cur.execute("SELECT count(*) FROM hot_topics")
    hot_count = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM policies")
    policy_count = cur.fetchone()[0]

    db.close()

    return {
        "total": total,
        "published": published,
        "draft": draft,
        "leads": leads,
        "attributions": attributions,
        "revenue": float(revenue),
        "channels": channels,
        "daily": daily,
        "recent": recent,
        "hot_topics": hot_count,
        "policies": policy_count,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

if __name__ == "__main__":
    data = get_dashboard_data()
    out = BASE / "data" / "output" / "dashboard_data.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Dashboard data saved to {out}")
