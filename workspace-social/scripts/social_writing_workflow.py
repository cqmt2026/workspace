# -*- coding: utf-8 -*-
"""
自媒体爆款写作工作流 v1.0
基于：米宅(3篇) + 楼市新观 + 掌楼牛市(2篇) + 城市财经 + 子木聊房，共8账号
更新：2026-06-20
"""
import os, json, sys
from datetime import datetime

# ========== 路径配置 ==========
WS = r"C:\Users\Administrator\.openclaw\workspace\workspace-social"
TEMPLATE_SHORT = os.path.join(WS, "scripts", "爆款写作模板-速查版.md")
TEMPLATE_FULL = os.path.join(WS, "scripts", "viral_writing_template_v3.md")
DRAFTS_DIR = os.path.join(WS, "drafts")
HOTSPOT_DIR = os.path.join(WS, "memory", "热点采集")
DATA_SOURCES = os.path.join(WS, "scripts", "数据源渠道清单.md")

# ========== 八种风格速查表 ==========
STYLE_TABLE = """
【八种爆款风格速查】

1. 米宅A【市场判断型】
   话题：市场预测/房价判断
   标题：「XX再次XX的可能性不存在了！」「XX的本质：不是XX，是XX」
   开头：时间线事件 → 转折「但要看真相」
   结尾：金句 + 埋钩子引下篇

2. 米宅B【数据解读型】
   话题：数据解读/趋势分析
   标题：「XX月份XX数据，把真相揭开了！」
   开头：直接扔密集数据
   结尾：反常识判断

3. 米宅C【政策财政型】
   话题：政策解读/财税分析
   标题：「XX成XX，改变来了！」
   开头：概念拆解 → 逻辑链
   结尾：预判方向

4. 楼市新观【故事争议型】
   话题：政策落地/争议性话题
   标题：「XX，真的能XX吗？」
   开头：我朋友的故事 → 代入感
   结尾：平衡结论（各方都觉得有道理）

5. 掌楼牛市-案例【跌价案例型】
   话题：具体楼盘/区域跌价案例
   标题：「比XX更可怕的，是XX也XX了……」
   开头：系列前篇引流
   结尾：「临X盘，请注意避雷」

6. 掌楼牛市-软文【楼盘软文型】
   话题：具体楼盘要推广
   标题：[规划兑现日期] + [地段确立] + [感叹]
   开头：规划利好事件（里程碑感）
   结尾：CTA → 私域引流

7. 城市财经【数据密集型】
   话题：宏观数据/区域竞争力
   标题：核心事实直述
   开头：数据排名先行
   结尾：七层深度分析

8. 子木聊房【哲学散文型】
   话题：国运判断/需要建立信任
   标题：「千万别急，XX正在扭转！」
   开头：先抑后扬，建立共情
   结尾：哲学金句 + 时间节点建议
"""

# ========== 风格决策树 ==========
STYLE_DECISION_TREE = """
【风格决策树】（按顺序判断）

Q1: 话题有具体楼盘要推广？
  → YES → 掌楼牛市-软文（规划兑现+地段绑定+场景+CTA）
  → NO ↓

Q2: 话题是具体楼盘/区域跌价案例？
  → YES → 掌楼牛市-案例（价格时间线+避雷指南+系列化）
  → NO ↓

Q3: 话题是政策落地/争议性话题？
  → YES → 楼市新观（争议挖掘+平衡结论）
  → NO ↓

Q4: 话题需要建立账号信任/国运判断？
  → YES → 子木聊房（先抑后扬+哲学金句+时间节点）
  → NO ↓

Q5: 话题是宏观数据/区域竞争力分析？
  → YES → 城市财经（数据密集+七层深度分析）
  → NO ↓

Q6: 话题有反常识判断空间？
  → YES → 米宅A（案例+强结论）
  → NO ↓

Q7: 话题是数据解读/趋势？
  → YES → 米宅B（领先指标+递进）
  → NO ↓

Q8: 话题是政策财税/制度？
  → YES → 米宅C（概念翻译+预判）
"""

# ========== 自检清单 ==========
SELF_CHECK = """
【写作自检清单】（每篇必须检查）

□ 标题有反常识/数据/悬念之一？
□ 开头150字内给核心判断？
□ 数据有A或B级来源，标注了来源？
□ 数据有纵向或横向对比？
□ 每个论点有具体楼盘/价格/事件？
□ 每300字有一个金句？
□ 结尾有核心判断/预判/避雷指引？
□ 无C级来源的具体数字？（自媒体/朋友圈中介数据禁用）
□ 无模糊词？（大概/可能/也许禁用）
□ 字数1200-1800字？
□ 有一个「别家自媒体不敢说」的判断？
□ 读者看完知道「该怎么做」？
□ 和热点库已有文章角度有差异化？

【差异化检查】
□ 这个角度热点库有吗？（没有=差异化）
□ 这个判断别家自媒体敢给吗？（不敢=价值）
□ 有具体到街道/楼盘/价格的案例吗？
□ 有一句话能让读者记住吗？（金句）
"""

# ========== 数据红线 ==========
DATA_RULES = """
【数据使用标准】（硬性）

A级（直接引用）：
  国家统计局 / 住建部 / 央行 / 财政部

B级（标注来源）：
  地方住建局 / 中指院 / 铭腾 / 克而瑞 / 锐理

C级（禁用）：
  自媒体 / 朋友圈中介
  → 只用定性描述，不引用具体数字

数据呈现方式：
  ① 纵向对比（2021 vs 2025）
  ② 横向对比（一线 vs 二线 vs 三线）
  ③ 拆解对比（均价背后的结构）
  ④ 领先指标（新开工面积 → 未来2年供应）

禁区：
  ❌ 模糊词（大概/可能/也许/一些）
  ❌ 无法核实数字
  ❌ 「业内人士透露」+ 具体数字
"""

# ========== 金句公式 ==========
GOLDEN_SENTENCES = """
【金句公式】（每300字至少一个，结尾必须有）

1. 「要XX，不要XX」（方法论）
   示例：要看数据蕴含的真相，不要看标题

2. 「不是XX，是XX」（反常识）
   示例：不是需求回暖，是供给收缩

3. 「XX是XX的」（判断）
   示例：二手房是另一个逻辑

4. 「XX是确定的/XX是XX的开始」（预判）
   示例：房产税+城市更新税是地方新方向

5. 一个比喻讲清楚专业概念
   示例：契税是房地产的活体心跳指标
"""

# ========== 工作流程 ==========
def print_workflow():
    print("=" * 60)
    print("📝 自媒体爆款写作工作流 v1.0")
    print("=" * 60)
    print()
    print("【Step 1】采集热点")
    print("  → cron推送热点文件，或手动读取 hotspot_xxx.md")
    print()
    print("【Step 2】分析热点 → 选角度")
    print("  → 避开热点库已有角度，找差异化切入点")
    print()
    print("【Step 3】选风格")
    print(STYLE_DECISION_TREE)
    print()
    print("【Step 4】加载模板")
    print(f"  → 速查版: {TEMPLATE_SHORT}")
    print(f"  → 完整版: {TEMPLATE_FULL}")
    print()
    print("【Step 5】数据采集")
    print("  → 重庆网上房地产: https://www.cq315house.com/ (政府备案数据)")
    print("  → 克而瑞: https://www.cric.com/ (部分需订阅)")
    print("  → 房天下BrowserAct: chrome模式可用")
    print("  → 通过微信文章获取铭腾/中指数据（二次引用）")
    print()
    print("【Step 6】写作")
    print("  → 按所选风格的标题/开头/正文/结尾公式执行")
    print()
    print("【Step 7】自检")
    print(SELF_CHECK)
    print()
    print("【Step 8】定稿输出")
    print(f"  → 输出到: {DRAFTS_DIR}")
    print("=" * 60)

def load_template():
    """加载模板内容"""
    if os.path.exists(TEMPLATE_SHORT):
        with open(TEMPLATE_SHORT, encoding="utf-8") as f:
            return f.read()
    return "模板文件未找到"

def get_latest_hotspot():
    """获取最新热点文件"""
    if not os.path.exists(HOTSPOT_DIR):
        return None, "热点目录不存在"
    files = [f for f in os.listdir(HOTSPOT_DIR) if f.startswith("hotspot_") and f.endswith(".md")]
    if not files:
        return None, "无热点文件"
    latest = sorted(files)[-1]
    path = os.path.join(HOTSPOT_DIR, latest)
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()
    return content, latest

def save_draft(title, content, filename_hint=""):
    """保存草稿"""
    if not os.path.exists(DRAFTS_DIR):
        os.makedirs(DRAFTS_DIR)
    if not filename_hint:
        filename_hint = title[:20]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"草稿_{filename_hint}_{ts}.md"
    path = os.path.join(DRAFTS_DIR, filename)
    full_content = f"# {title}\n\n---\n\n{content}\n\n---\n_可悦🌸 {datetime.now().strftime('%Y-%m-%d')}_\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(full_content)
    return path

if __name__ == "__main__":
    print_workflow()
    print()
    print("【当前最新热点】")
    content, name = get_latest_hotspot()
    if content:
        print(f"文件: {name}")
        print(f"预览（前500字）:\n{content[:500]}")
    else:
        print(name)
