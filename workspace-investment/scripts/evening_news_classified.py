# -*- coding: utf-8 -*-
"""
晚间资讯分类报告 v2
按P0-P3优先级分类，当日收盘后运行
P0: 紧急 P1: 重要 P2: 参考 P3: 观察
"""
import requests, re, json, sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORKSPACE = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-investment")

P0_KEYWORDS = [
    "降准", "降息", "加息", "量化宽松", "股灾", "熔断",
    "国家队", "证监会立案", "退市", "st", "ST",
    "减持", "违规", "操纵", "造假", "停牌核查", "黑天鹅",
]

P1_KEYWORDS = [
    "业绩预增", "业绩预减", "扭亏", "暴雷", "业绩",
    "定增", "回购", "股权激励", "并购", "重组",
    "政策利好", "政策扶持", "补贴", "关税",
    "华为", "比亚迪", "宁德", "特斯拉", "英伟达",
    "北向", "外资", "净流入", "MSCI", "富时",
    "涨停", "跌停", "龙头",
]

P2_KEYWORDS = [
    "美股", "纳斯达克", "道琼斯", "港股", "A50",
    "IPO", "新股", "解禁",
    "央行", "逆回购", "shibor",
    "期货", "大宗商品", "原油", "黄金",
]


def fetch_eastmoney_kx(count=20):
    """东财快讯"""
    try:
        url = ("https://newsapi.eastmoney.com/kuaixun/v1/getlist_126_ajaxResult_"
               + str(count) + "_1_.html")
        r = requests.get(url, timeout=8, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.eastmoney.com"
        })
        m = re.search(r'ajaxResult=(.+)', r.text)
        if m:
            d = json.loads(m.group(1))
            items = d.get("LivesList", [])
            result = []
            for item in items:
                title = item.get("title", "")
                t = item.get("showtime", "")
                result.append((title, t))
            return result
    except Exception as e:
        print(f"[WARN] eastmoney_kx: {e}")
    return []


def fetch_eastmoney_ajs(count=15):
    """东财A股资讯"""
    try:
        url = ("https://np-anotice-stock.eastmoney.com/api/security/ann?"
               "sr=-1&page_size=" + str(count) + "&page_index=1&ann_type=A")
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        d = r.json()
        if d.get("data"):
            items = d["data"].get("announcements", [])
            result = []
            for item in items:
                title = item.get("title", "")
                t = str(item.get("publish_time", ""))[:16]
                result.append((title, t))
            return result
    except Exception as e:
        print(f"[WARN] eastmoney_ajs: {e}")
    return []


def fetch_xinhua_news(count=10):
    """新华网A股新闻"""
    try:
        url = "http://www.xinhuanet.com/fortune/xml/ajs.xml"
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        r.encoding = "utf-8"
        titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', r.text)
        times = re.findall(r'<pubDate>(.*?)</pubDate>', r.text)
        result = []
        for i in range(min(count, len(titles))):
            result.append((titles[i], times[i] if i < len(times) else ""))
        return result
    except Exception as e:
        print(f"[WARN] xinhua: {e}")
    return []


def classify(text):
    for kw in P0_KEYWORDS:
        if kw in text:
            return "P0"
    for kw in P1_KEYWORDS:
        if kw in text:
            return "P1"
    for kw in P2_KEYWORDS:
        if kw in text:
            return "P2"
    return "P3"


def build_report():
    em_kx = fetch_eastmoney_kx(20)
    em_ajs = fetch_eastmoney_ajs(15)
    xinhua = fetch_xinhua_news(10)
    print(f"[DEBUG] 东财快讯={len(em_kx)} 东财A股={len(em_ajs)} 新华={len(xinhua)}")

    p0, p1, p2, p3 = [], [], [], []

    def add(entries, label):
        for title, t in entries:
            if not title:
                continue
            level = classify(title)
            entry = f"[{label}] {title[:55]}"
            if t:
                entry = entry + f" ({t})"
            if level == "P0":
                p0.append(entry)
            elif level == "P1":
                p1.append(entry)
            elif level == "P2":
                p2.append(entry)
            else:
                p3.append(entry)

    add(em_kx, "东财快讯")
    add(em_ajs, "东财A股")
    add(xinhua, "新华网")

    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M")

    lines = []
    lines.append(f"📰 **晚间资讯分类 · {today} {now}**")
    lines.append("=" * 60)

    total = len(p0) + len(p1) + len(p2) + len(p3)
    src_info = f"东财快讯{len(em_kx)} + 东财A股{len(em_ajs)} + 新华{len(xinhua)}"
    lines.append(f"\n共抓取{total}条（{src_info}）")

    if p0:
        lines.append(f"\n🚨 **P0 紧急** ({len(p0)}条)")
        lines.extend(p0[:5])
    else:
        lines.append("\n🚨 **P0 紧急** (0条) ✅ 无紧急事项")

    if p1:
        lines.append(f"\n📋 **P1 重要** ({len(p1)}条)")
        lines.extend(p1[:8])
    else:
        lines.append("\n📋 **P1 重要** (0条)")

    if p2:
        lines.append(f"\n📊 **P2 参考** ({len(p2)}条)")
        lines.extend(p2[:5])

    if p3:
        lines.append(f"\n📝 **P3 观察** ({len(p3)}条)")
        lines.extend(p3[:5])

    lines.append(f"\n{'='*60}")
    lines.append("_P0=5分钟内响应 / P1=当日处理 / P2=次日参考 / P3=长期观察_")

    report = "\n".join(lines)
    out_file = WORKSPACE / "out_data" / f"evening_news_{today}.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\n[已保存: {out_file}]")
    return report


def push_to_wechat(content):
    """微信推送已由Cron delivery统一处理，此函数仅打印"""
    print(content)
    return True


if __name__ == "__main__":
    report = build_report()
    if "--push" in sys.argv:
        push_to_wechat(report)
