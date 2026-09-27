# -*- coding: utf-8 -*-
"""光伏内容质量修复 - 模板增强版（不依赖LLM）
基于真实热点数据，用改进模板直接生成可发布内容
"""
import sys, os, json, time, re
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

def safe_print(msg):
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'):
            print(msg)
    except: pass

import sqlite3
from core.database import init_db
init_db()

# ========== 工具函数定义 ==========

def classify_direction(title):
    policy_kw = ["政策", "规划", "补贴", "征求意见", "通知", "办法", "意见", "规定"]
    tech_kw = ["技术", "组件", "电池", "效率", "转化率", "技术路线", "技术原理"]
    benefit_kw = ["收益", "赚钱", "回本", "投资", "回报", "电价", "成本"]
    avoid_kw = ["避坑", "陷阱", "风险", "骗局", "注意", "警告"]
    for kw in policy_kw:
        if kw in title: return "policy"
    for kw in tech_kw:
        if kw in title: return "tech"
    for kw in benefit_kw:
        if kw in title: return "benefit"
    for kw in avoid_kw:
        if kw in title: return "avoid"
    return "news"

def extract_key_info(title):
    info = {"entities": [], "numbers": [], "location": None}
    info["numbers"] = re.findall(r'[\d,.]+(?:GW|MW|kW|万|亿|%)?', title)
    company_patterns = [r'(?:正泰|晶澳|通威|英利|隆基|天合|协鑫|阳光|阿特斯|皇明|鑫铂|立新)']
    for pat in company_patterns:
        matches = re.findall(pat, title)
        info["entities"].extend(matches)
    province_kw = ["江苏","浙江","上海","广东","北京","山东","河北","河南","云南","山西","四川","安徽","湖北","湖南","福建","江西","陕西","甘肃","黑龙江","吉林","辽宁","内蒙古","新疆","西藏","宁夏","青海"]
    city_kw = ["温州","洞头","镇江","黄浦","冀东","油田"]
    for p in province_kw:
        if p in title: info["location"] = p; break
    else:
        for c in city_kw:
            if c in title: info["location"] = c; break
    return info

def generate_content(title, source, direction):
    info = extract_key_info(title)
    numbers = info["numbers"]
    entities = list(set(info["entities"]))[:2]
    location = info["location"]

    if direction == "policy":
        hook = generate_policy_hook(title, info)
        body = generate_policy_body(title, info, entities, location)
        cta = "你家屋顶能装几kW？私信我'省份+面积'，免费出当地补贴政策+收益测算表。"
    elif direction == "tech":
        hook = generate_tech_hook(title, info)
        body = generate_tech_body(title, info, entities)
        cta = "不懂怎么选组件？私信我'城市+屋顶类型'，帮你推荐适合的光伏方案。"
    elif direction == "benefit":
        hook = generate_benefit_hook(title, info)
        body = generate_benefit_body(title, info, entities)
        cta = "你家适不适合装光伏？补贴能拿多少？点关注私信我，免费帮你测算当地政策+收益方案。"
    elif direction == "avoid":
        hook = "装光伏前必看！这5个坑踩一个亏几万"
        body = generate_avoid_body()
        cta = "装光伏前多看这条，少踩一个坑就省几万块。想找人帮你避坑？私信留言你的城市和屋顶情况。"
    else:
        hook = generate_news_hook(title, info)
        body = generate_news_body(title, info, entities, location)
        cta = "想看更多光伏行业深度解读？私信'关注'，每天一条行业情报。"

    return {"title": title, "source": source, "direction": direction,
            "hook": hook, "body": body, "cta": cta}

def generate_policy_hook(title, info):
    numbers = info["numbers"]
    location = info["location"]
    if numbers:
        return f"{location or ''}光伏新政！{numbers[0]}装机目标，这样装最划算"
    elif location:
        return f"{location}光伏新政来了！装光伏的前先看清楚这3点"
    else:
        return "光伏政策有变！2026年最新解读，装光伏前必看"

def generate_policy_body(title, info, entities, location):
    parts = []
    if "十五五" in title or "规划" in title:
        parts.append("【政策要点】国家/地方出台光伏发展规划，明确装机容量目标。")
        parts.append(f"→ 这意味着{location or '当地'}将大力推动分布式光伏建设，屋顶资源紧缺度上升。")
    elif "征求意见" in title or "通知" in title:
        parts.append("【政策要点】地方发布分布式光伏管理政策征求意见或通知。")
        parts.append(f"→ {location or '各地'}并网规则趋严，自发自用比例要求提高。")
    elif "补贴" in title or "电价" in title:
        parts.append("【政策要点】光伏补贴政策调整或电价机制变化。")
        parts.append("→ 收益测算要重新算，别再按老标准估算。")
    else:
        parts.append(f"【政策要点】{title}。")
        parts.append("→ 政策收紧趋势明确，分布式光伏进入规范化时代。")
    parts.append("")
    parts.append("【对业主的影响】")
    if location:
        parts.append(f"• {location}业主：尽快了解当地并网政策和补贴标准")
    else:
        parts.append("• 有屋顶的业主：抓紧窗口期，政策越收越紧")
    parts.append("• 想装光伏的家庭：先做收益测算再决定，别盲目跟风")
    parts.append("• 已安装的业主：关注运维效率，降低度电成本是关键")
    return "\n".join(parts)

def generate_tech_hook(title, info):
    numbers = info["numbers"]
    if numbers:
        return f"{numbers[0]}是什么水平？光伏组件技术解读"
    return "光伏组件怎么选？看完这篇不踩坑"

def generate_tech_body(title, info, entities):
    parts = []
    if "中核" in title or "集采" in title or "入围" in title:
        parts.append("【核心信息】多家光伏企业入围中核4.3GW组件集采订单。")
        parts.append("→ 央企集采相当于行业大考，入围的都是头部选手，质量有保障。")
        parts.append("→ 对企业：订单保障+品牌背书；对业主：选这些品牌更放心。")
    elif "效率" in title or "电池" in title:
        parts.append("【技术解读】光伏电池技术持续迭代。")
        parts.append("→ 现在主流是P型PERC，N型TOPCon正在快速替代，转换效率差距0.5%-1%。")
        parts.append("→ 选组件时认准N型 TOPCon或HJT，25年衰减更低。")
    else:
        parts.append(f"【技术要点】{title}")
        parts.append("→ 行业最新动态，技术路线持续优化。")
        parts.append("→ 对你来说：选大品牌、关注转换效率、看重质保条款。")
    parts.append("")
    parts.append("【怎么选】")
    parts.append("1. 看品牌：入围央企集采的=经过实战检验")
    parts.append("2. 看参数：转换效率≥21%是门槛，≥22.5%是优秀")
    parts.append("3. 看质保：组件25年线性功率质保是标配")
    parts.append("4. 看价格：别贪便宜，低价组件隐性成本很高")
    return "\n".join(parts)

def generate_benefit_hook(title, info):
    numbers = info["numbers"]
    if numbers:
        return f"光伏收益真实算账：{numbers[0]}能赚多少？"
    return "屋顶装光伏到底划不划算？2026年真实收益测算"

def generate_benefit_body(title, info, entities):
    parts = []
    parts.append("【2026年真实收益账】")
    parts.append("以5kW户用光伏为例（华北地区）：")
    parts.append("• 前期投入：约1.5-2万元（组件+逆变器+安装）")
    parts.append("• 年发电量：约5500-6000度（日均15-16度）")
    parts.append("• 年收益：自发自用省电费0.5元/度 + 余电上网卖0.4元/度 ≈ 2500-3000元")
    parts.append("• 回本周期：5-7年（系统寿命25年）")
    parts.append("• 25年总收益：约5-7万元（扣除运维成本）")
    parts.append("")
    parts.append("【关键变量】")
    parts.append("→ 日照条件：北方优于南方，年等效利用小时1200-1500")
    parts.append("→ 自用电价：工商业电价高，自发自用更划算")
    parts.append("→ 补贴政策：各地不同，部分地区还有地方补贴")
    parts.append("→ 屋顶条件：朝向、角度、遮挡都会影响发电量")
    return "\n".join(parts)

def generate_avoid_body():
    parts = []
    parts.append("【常见光伏安装坑】")
    parts.append("❌ 坑1：只看单价不看整体")
    parts.append("  → 低价组件+劣质逆变器=2年后故障率高，维修成本远超省下的钱")
    parts.append("❌ 坑2：不问清楚质保条款")
    parts.append("  → 有些只保产品不保功率，25年后发电量掉到70%没人管")
    parts.append("❌ 坑3：忽视屋顶承重和防水")
    parts.append("  → 安装不规范导致漏水，修屋顶的钱够装两套光伏")
    parts.append("❌ 坑4：选了没有本地服务的公司")
    parts.append("  → 出问题了找不到人修，售后全靠电话，一年白干")
    parts.append("❌ 坑5：不看电网接入条件")
    parts.append("  → 有些村子变压器容量满了，装了也发不出电")
    parts.append("")
    parts.append("【正确做法】")
    parts.append("1. 找本地有门店的服务商（跑得了和尚跑不了庙）")
    parts.append("2. 签合同前确认：组件品牌型号+逆变器品牌+质保条款+运维责任")
    parts.append("3. 问清楚：当地电网能否接入+电容余量够不够")
    return "\n".join(parts)

def generate_news_hook(title, info):
    numbers = info["numbers"]
    entities = info["entities"]
    if numbers and entities:
        return f"{entities[0]}:{numbers[0]}装机量释放关键信号"
    elif numbers:
        return f"{numbers[0]}释放光伏行业关键信号"
    elif entities:
        return f"{entities[0]}最新动态，光伏行业要变天？"
    else:
        return f"光伏圈突发：{title[:25]}..."

def generate_news_body(title, info, entities, location):
    parts = []
    parts.append(f"【核心事实】{title}")
    if entities:
        parts.append(f"→ {entities[0]}的动作，代表头部企业的战略方向。")
    if location:
        parts.append(f"→ {location}的政策动态，反映地方监管趋势。")
    if info["numbers"]:
        parts.append(f"→ {info['numbers'][0]}这个数字，说明行业规模仍在增长。")
    parts.append("")
    parts.append("【释放的信号】")
    parts.append("1. 行业集中度持续提升：头部企业市场份额扩大，小厂生存空间压缩")
    parts.append("2. 政策驱动转向市场驱动：补贴退坡后，竞争力成为核心")
    parts.append("3. 技术迭代加速：N型电池快速替代P型，效率竞赛白热化")
    parts.append("4. 渠道整合：安装服务商面临洗牌，有本地服务能力的人才活得下去")
    parts.append("")
    parts.append("【一句话总结】光伏行业正在从'政策红利期'进入'优胜劣汰期'。")
    return "\n".join(parts)

def format_markdown(content):
    lines = []
    lines.append(f"# {content['tracking_id']}")
    lines.append(f"来源: {content['source']}")
    lines.append(f"方向: {content['direction']}")
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
    lines.append(f"*PV获客系统生成 | tracking_id: {content['tracking_id']}*")
    return "\n".join(lines)

# ========== 主流程 ==========

safe_print("=" * 50)
safe_print("光伏内容质量修复 - 模板增强版")
safe_print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
safe_print("=" * 50)

# 从DB加载今日热点
conn = sqlite3.connect(str(BASE / "data" / "pv.db"))
c = conn.cursor()
c.execute("SELECT title, source, pv_score, collected_at FROM hot_topics WHERE pv_related=1 ORDER BY collected_at DESC LIMIT 15")
topics = c.fetchall()
conn.close()

safe_print(f"加载 {len(topics)} 条今日PV热点\n")

output_dir = BASE / "data" / "output" / "rewritten"
output_dir.mkdir(parents=True, exist_ok=True)

RESULTS = []
for i, (title, source, score, at) in enumerate(topics):
    safe_print(f"[{i+1}/{len(topics)}] {title[:45]}...")
    direction = classify_direction(title)
    content = generate_content(title, source, direction)
    content["tracking_id"] = f"PV_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    content["generated_at"] = datetime.now().isoformat()
    RESULTS.append(content)

    md = format_markdown(content)
    md_file = output_dir / f"{content['tracking_id']}.md"
    md_file.write_text(md, encoding="utf-8")

    safe_print(f"  方向: {direction} | 钩子: {content['hook'][:35]}...")
    safe_print(f"  保存: {md_file.name}")
    time.sleep(0.3)

# 保存JSON汇总
out_json = output_dir / f"rewritten_{datetime.now().strftime('%Y%m%d')}.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, ensure_ascii=False, indent=2)

safe_print(f"\n{'='*50}")
safe_print(f"完成! 共生成 {len(RESULTS)} 条内容")
safe_print(f"JSON: {out_json}")
safe_print(f"目录: {output_dir}/")

# 统计
dir_count = {}
for r in RESULTS:
    d = r["direction"]
    dir_count[d] = dir_count.get(d, 0) + 1
safe_print(f"按方向: {json.dumps(dir_count, ensure_ascii=False)}")
