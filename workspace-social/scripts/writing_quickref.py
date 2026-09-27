# -*- coding: utf-8 -*-
"""
爆款写作速查 - 一键调用
运行：python writing_quickref.py
"""
import io
from __future__ import print_function
import sys
import os

WS = r"C:\Users\Administrator\.openclaw\workspace\workspace-social"
DRAFTS = os.path.join(WS, "drafts")
HOTSPOT = os.path.join(WS, "memory", "热点采集")

def p(s):
    try:
        print(s)
    except UnicodeEncodeError:
        ascii_s = s.encode('ascii', errors='ignore').decode('ascii')
        print(ascii_s)

def latest_hotspot():
    if not os.path.exists(HOTSPOT):
        return None
    files = sorted([f for f in os.listdir(HOTSPOT) if f.startswith("hotspot_")])
    if not files:
        return None
    path = os.path.join(HOTSPOT, files[-1])
    with open(path, encoding="utf-8", errors="replace") as f:
        return files[-1], f.read()[:600]

def latest_draft():
    if not os.path.exists(DRAFTS):
        return None
    files = sorted([f for f in os.listdir(DRAFTS) if f.endswith(".md")])
    if not files:
        return None
    path = os.path.join(DRAFTS, files[-1])
    with open(path, encoding="utf-8", errors="replace") as f:
        return files[-1], f.read()[:400]

def main():
    p("=" * 58)
    p("[写作] 爆款写作速查")
    p("=" * 58)

    h = latest_hotspot()
    if h:
        p("\n[HOT] Latest: " + h[0])
        preview = h[1].replace("\n", " ").strip()[:300]
        preview = preview.encode('ascii', errors='ignore').decode('ascii')
        p("     " + preview)
    else:
        p("\n[HOT] No hotspot file")

    d = latest_draft()
    if d:
        p("\n[DRAFT] Latest: " + d[0])
        preview = d[1].replace("\n", " ").strip()[:200]
        preview = preview.encode('ascii', errors='ignore').decode('ascii')
        p("        " + preview)
    else:
        p("\n[DRAFT] No draft")

    p("\n" + "-" * 58)
    p("[决策树 - 5秒选风格]")
    p("-" * 58)
    p("Q1 楼盘推广？         -> 掌楼牛市-软文（规划+场景+CTA）")
    p("Q2 楼盘跌价案例？    -> 掌楼牛市-案例（价格时间线+避雷）")
    p("Q3 政策争议话题？    -> 楼市新观（两面挖掘+平衡结论）")
    p("Q4 国运/建立信任？   -> 子木聊房（先抑后扬+哲学金句）")
    p("Q5 宏观数据分析？    -> 城市财经（数据密集+七层分析）")
    p("Q6 反常识判断？      -> 米宅A（案例+强结论）")
    p("Q7 数据趋势解读？    -> 米宅B（领先指标+递进）")
    p("Q8 政策财税制度？    -> 米宅C（概念翻译+预判）")

    p("\n" + "-" * 58)
    p("[自检7项 - 写完必查]")
    p("-" * 58)
    p("1. 标题有反常识/数据/悬念？")
    p("2. 开头150字内核心判断？")
    p("3. 数据有A/B级来源+标注？")
    p("4. 每论点有楼盘/价格/事件？")
    p("5. 每300字一个金句？")
    p("6. 结尾有判断/避雷/钩子？")
    p("7. 无C级数字+无模糊词？")

    p("\n" + "-" * 58)
    p("[数据红线]")
    p("-" * 58)
    p("A级: 统计局/住建部/央行 -> 直接引用")
    p("B级: 铭腾/克而瑞/中指 -> 标注来源")
    p("C级: 自媒体/中介     -> 禁用具体数字")

    p("\n" + "-" * 58)
    p("[金句4公式]")
    p("-" * 58)
    p("1. 要XX，不要XX  （方法论）")
    p("2. 不是XX，是XX  （反常识）")
    p("3. XX是XX的      （判断）")
    p("4. XX是确定的    （预判）")

    p("\n" + "-" * 58)
    p("[数据渠道 - 已验证可用]")
    p("-" * 58)
    p("重庆网上房地产: cq315house.com (政府备案/预售)")
    p("克而瑞: cric.com (部分需订阅)")
    p("房天下BrowserAct: chrome模式可用")
    p("微信文章: BrowserAct eval提取全文")
    p("案例获取: 你提供(最快) / 手动找 / BrowserAct导航")

    p("\n" + "-" * 58)
    p("[模板文件]")
    p("-" * 58)
    p("速查版: scripts/爆款写作模板-速查版.md")
    p("完整版: scripts/viral_writing_template_v3.md")
    p("逐篇拆解: scripts/*分析*.md (共8篇)")
    p("数据渠道: scripts/数据源渠道清单.md")
    p("=" * 58)

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == "__main__":
    main()
