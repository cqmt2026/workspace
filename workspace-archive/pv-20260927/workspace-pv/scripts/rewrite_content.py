# -*- coding: utf-8 -*-
"""用LLM重新生成高质量光伏内容 v0.2
修复C级（测试数据）和B级（空洞框架）内容，输出可直接发布的A级内容
"""
import sys, os, json, time, re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

def log(msg):
    """安全日志输出"""
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'):
            print(msg)
    except (ValueError, OSError):
        pass

# 不再覆盖sys.stdout，避免cron环境问题

from core.llm_enhancer import SolarLLMClient
from core.database import PVDatabase, init_db
from core.industry_plugin_loader import get_plugin

OUTPUT_DIR = BASE / "data" / "output" / "rewritten"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DIRECTION_MAP = {
    "policy": "政策",
    "benefit": "收益",
    "avoid": "避坑",
    "news": "新闻",
    "tech": "技术",
}


def load_hot_topics(db, limit=30):
    """从数据库加载今日PV相关热点"""
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT title, source, pv_score, collected_at 
        FROM hot_topics 
        WHERE pv_related = 1 
        ORDER BY collected_at DESC 
        LIMIT ?
    """, (limit,))
    return cursor.fetchall()


def load_policies(db, limit=10):
    """从数据库加载政策"""
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT title, level, province, policy_type, collected_at
        FROM policies
        ORDER BY collected_at DESC
        LIMIT ?
    """, (limit,))
    return cursor.fetchall()


def rewrite_policy_content(title, source, llm_client):
    """重写政策解读内容"""
    hook = llm_client.generate_hook(title, "policy")
    body = llm_client.generate_body(title, "policy", source)

    # 构造符合新模板的内容
    result = {
        "title": title,
        "source": source,
        "direction": "policy",
        "hook": hook or f"光伏新政来了！{title[:20]}...",
        "body": body or "政策具体内容待补充...",
        "cta": "你家屋顶能装几kW？私信我'省份+面积'，免费出当地补贴政策+收益测算表。",
        "tracking_id": f"POL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "generated_at": datetime.now().isoformat(),
    }
    return result


def rewrite_news_content(title, source, llm_client):
    """重写行业新闻内容"""
    hook = llm_client.generate_hook(title, "news")
    body = llm_client.generate_body(title, "news", source)

    result = {
        "title": title,
        "source": source,
        "direction": "news",
        "hook": hook or f"{title[:25]}...",
        "body": body or "行业分析待补充...",
        "cta": "想看更多光伏行业深度解读？私信'关注'，每天一条行业情报。",
        "tracking_id": f"NEWS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "generated_at": datetime.now().isoformat(),
    }
    return result


def rewrite_tech_content(title, source, llm_client):
    """重写技术科普内容"""
    hook = llm_client.generate_hook(title, "tech")
    body = llm_client.generate_body(title, "tech", source)

    result = {
        "title": title,
        "source": source,
        "direction": "tech",
        "hook": hook or f"光伏技术详解：{title[:20]}...",
        "body": body or "技术解释待补充...",
        "cta": "不懂怎么选组件？私信我'城市+屋顶类型'，帮你推荐适合的光伏方案。",
        "tracking_id": f"TECH_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "generated_at": datetime.now().isoformat(),
    }
    return result


def generate_benefit_content(llm_client):
    """生成收益计算内容（基于通用模板+LLM增强）"""
    # 用真实数据生成收益计算
    hook = llm_client.generate_hook(
        "2026年光伏收益真实计算：5kW屋顶一年能赚多少？",
        "benefit"
    )
    body = llm_client.generate_body(
        "2026年光伏收益真实计算：5kW屋顶一年能赚多少？",
        "benefit", ""
    )

    return {
        "title": "2026年光伏收益真实计算",
        "source": "calculated",
        "direction": "benefit",
        "hook": hook or "屋顶装光伏到底划不划算？算笔账给你看",
        "body": body or "以5kW屋顶光伏为例...",
        "cta": "你家适不适合装光伏？补贴能拿多少？点关注私信我，免费帮你测算当地政策+收益方案。",
        "tracking_id": f"BEN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "generated_at": datetime.now().isoformat(),
    }


def format_output(content):
    """格式化为可读的Markdown输出"""
    lines = []
    lines.append(f"# {content['direction']} | {content['tracking_id']}")
    lines.append(f"来源: {content['source']}")
    lines.append(f"生成时间: {content['generated_at']}")
    lines.append("")
    lines.append("## 钩子")
    lines.append(content['hook'])
    lines.append("")
    lines.append("## 正文")
    lines.append(content['body'])
    lines.append("")
    lines.append("## CTA")
    lines.append(content['cta'])
    lines.append("")
    lines.append("---")
    lines.append(f"*PV获客系统自动生成 | 追踪ID: {content['tracking_id']}*")
    return "\n".join(lines)


def main():
    log("=" * 50)
    log("光伏内容质量修复 - LLM重生成")
    log(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log("=" * 50)

    # 初始化
    init_db()
    db = PVDatabase()
    llm = SolarLLMClient()

    if not llm.is_available():
        print("LLM不可用，跳过生成")
        return

    log(f"LLM可用: {llm.model}")
    log(f"API: {llm.api_url}")
    log("")

    all_contents = []
    delay = 3  # LLM请求间隔(秒)

    # 1. 处理今日热点
    log("[1/3] 处理今日PV热点...")
    topics = load_hot_topics(db, limit=10)
    for i, (title, source, score, at) in enumerate(topics[:8]):
        log(f"  [{i+1}/8] {title[:40]}... ({source})")
        
        # 根据标题关键词判断方向
        if any(w in title for w in ["政策", "规划", "补贴", "征求意见", "通知"]):
            content = rewrite_policy_content(title, source, llm)
        elif any(w in title for w in ["技术", "组件", "电池", "效率", "转化率"]):
            content = rewrite_tech_content(title, source, llm)
        else:
            content = rewrite_news_content(title, source, llm)

        all_contents.append(content)
        time.sleep(delay)

    # 2. 处理政策
    log("\n[2/3] 处理政策内容...")
    policies = load_policies(db, limit=5)
    for i, (title, level, province, ptype, at) in enumerate(policies[:4]):
        if "测试" in title:
            log(f"  [{i+1}/4] 跳过测试政策: {title[:30]}...")
            continue
        log(f"  [{i+1}/4] {title[:40]}...")
        content = rewrite_policy_content(title, f"{level}-{province or '全国'}", llm)
        all_contents.append(content)
        time.sleep(delay)

    # 3. 生成收益计算内容
    log("\n[3/3] 生成收益计算内容...")
    content = generate_benefit_content(llm)
    all_contents.append(content)
    print(f"  收益计算内容已生成")
    time.sleep(delay)

    # 保存结果
    log(f"\n{'='*50}")
    log(f"生成完成: {len(all_contents)}条内容")
    
    output_file = OUTPUT_DIR / f"rewritten_{datetime.now().strftime('%Y%m%d')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_contents, f, ensure_ascii=False, indent=2)

    # 同时保存为可读Markdown
    for content in all_contents:
        md_file = OUTPUT_DIR / f"{content['tracking_id']}.md"
        md_file.write_text(format_output(content), encoding="utf-8")

    # 写入DB
    for content in all_contents:
        db.save_content_item(
            tracking_id=content["tracking_id"],
            channel="pv_system",
            title=content["title"],
            direction=content["direction"],
            source=content["source"],
            status="draft",
            filepath=str(OUTPUT_DIR / f"{content['tracking_id']}.md"),
        )

    log(f"内容已保存到: {output_file}")
    log(f"Markdown文件: {OUTPUT_DIR}/")
    log("DB记录已写入")

    # 统计
    dir_count = {}
    for c in all_contents:
        d = c["direction"]
        dir_count[d] = dir_count.get(d, 0) + 1
    log(f"\n按方向统计: {json.dumps(dir_count, ensure_ascii=False)}")

    db.close()


if __name__ == "__main__":
    main()
