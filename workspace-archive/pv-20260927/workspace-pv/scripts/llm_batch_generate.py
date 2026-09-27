# -*- coding: utf-8 -*-
"""批量LLM内容生成 - agnes-25"""
import sys, os, json, time, re, urllib.request
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

def safe_print(msg=""):
    try:
        if sys.stdout and hasattr(sys.stdout, 'buffer'):
            print(msg)
    except: pass

# agnes-25配置
API_URL = "https://api.agnes-ai.cn/v1/chat/completions"
API_KEY = None
config_path = os.path.expanduser('~/.openclaw/openclaw.json')
with open(config_path, 'r', encoding='utf-8') as f:
    cfg = json.load(f)
providers = cfg.get('models', {}).get('providers', {})
for name, p in providers.items():
    if name == 'agnes-25':
        API_KEY = p.get('apiKey', '')
        break

if not API_KEY:
    safe_print("未找到agnes-25 API Key")
    sys.exit(1)

def llm_call(prompt, max_tokens=400):
    data = json.dumps({"model": "agnes-2.5-flash", "max_tokens": max_tokens,
                        "temperature": 0.7,
                        "messages": [{"role": "user", "content": prompt}]},
                       ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data,
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
                                 method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        except Exception as e:
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
            else:
                return ""
    return ""

# 风格配置
STYLE_GUIDES = {
    "policy": {
        "hook": "权威+数字，体现政策重要性",
        "body": "准确解读政策原文，说清楚对谁有什么影响，引用来源",
        "tone": "专业可信但不生硬，像政策顾问在讲解",
    },
    "news": {
        "hook": "突出关键数字/企业名称，制造信息差感",
        "body": "先讲事实，再分析3个信号，最后总结趋势",
        "tone": "客观理性，有洞察力，数据说话",
    },
    "tech": {
        "hook": "用数字/对比制造好奇心",
        "body": "生活类比解释技术，给出可操作的判断标准",
        "tone": "通俗易懂但不失专业，像工程师朋友在聊天",
    },
    "benefit": {
        "hook": "直接给数字，算账感",
        "body": "真实数据+具体算式，不夸大不隐瞒",
        "tone": "实在靠谱，像懂行的朋友在帮你算账",
    },
    "avoid": {
        "hook": "警示感，突出损失",
        "body": "每个坑配具体场景+正确做法",
        "tone": "关切提醒，像过来人在分享经验",
    },
}

CTA_MAP = {
    "policy": "你家屋顶能装几kW？私信我'省份+面积'，免费出当地补贴政策+收益测算表。",
    "tech": "不懂怎么选组件？私信我'城市+屋顶类型'，帮你推荐适合的光伏方案。",
    "news": "想看更多光伏行业深度解读？私信'关注'，每天一条行业情报。",
    "benefit": "你家适不适合装光伏？补贴能拿多少？点关注私信我，免费帮你测算当地政策+收益方案。",
    "avoid": "装光伏前多看这条，少踩一个坑就省几万块。想找人帮你避坑？私信留言你的城市和屋顶情况。",
}

def classify_direction(title):
    for kw in ["政策","规划","补贴","征求意见","通知","办法","意见","规定"]:
        if kw in title: return "policy"
    for kw in ["技术","组件","电池","效率","转化率","技术路线","技术原理"]:
        if kw in title: return "tech"
    for kw in ["收益","赚钱","回本","投资","回报","电价","成本"]:
        if kw in title: return "benefit"
    for kw in ["避坑","陷阱","风险","骗局","注意","警告"]:
        if kw in title: return "avoid"
    return "news"

def extract_info(title):
    info = {"entities": [], "numbers": [], "location": None}
    info["numbers"] = re.findall(r'[\d,.]+(?:GW|MW|kW|万|亿|%)?', title)
    company_patterns = [r'(?:正泰|晶澳|通威|英利|隆基|天合|协鑫|阳光|阿特斯|皇明|鑫铂|立新|浙能|上能|特变)']
    for pat in company_patterns:
        matches = re.findall(pat, title)
        info["entities"].extend(matches)
    province_kw = ["江苏","浙江","上海","广东","北京","山东","河北","河南","云南","山西","四川","安徽","湖北","湖南","福建","江西","陕西","甘肃","黑龙江","吉林","辽宁","内蒙古","新疆","西藏","宁夏","青海"]
    city_kw = ["温州","洞头","镇江","黄浦","冀东","油田","鄂尔多斯","楚雄","康巴什"]
    for p in province_kw:
        if p in title: info["location"] = p; break
    else:
        for c in city_kw:
            if c in title: info["location"] = c; break
    return info

def generate_hook(title, direction):
    style = STYLE_GUIDES.get(direction, STYLE_GUIDES["news"])
    prompt = f"""你是光伏行业短视频专家。根据以下标题，写一个爆款钩子。

标题：{title}
方向：{direction}
风格：{style['hook']}

要求：
1. 必须含数字或问句
2. 30字以内
3. 口语化但有专业感
4. 直接输出，不加引号

只输出钩子。"""
    return llm_call(prompt, 100) or title[:25]

def generate_body(title, source, direction):
    style = STYLE_GUIDES.get(direction, STYLE_GUIDES["news"])
    prompt = f"""你是光伏行业短视频内容策划专家。根据标题生成一段150-200字的短视频正文。

标题：{title}
来源：{source}
方向：{direction}
风格：{style['body']}
语气：{style['tone']}

要求：
1. 开头1句话点出核心信息
2. 中间2-4个点展开（用→连接）
3. 每句话都有实际信息
4. 口语化但有专业感
5. 直接输出正文，不加引号，不解释

只输出正文。"""
    return llm_call(prompt, 400) or "内容生成中..."

# 加载热点
import sqlite3
conn = sqlite3.connect(str(BASE / "data" / "pv.db"))
c = conn.cursor()
c.execute("SELECT title, source FROM hot_topics WHERE pv_related=1 ORDER BY collected_at DESC LIMIT 12")
topics = c.fetchall()
conn.close()

safe_print(f"加载 {len(topics)} 条热点")

output_dir = BASE / "data" / "output" / "llm_generated"
output_dir.mkdir(parents=True, exist_ok=True)

RESULTS = []
for i, (title, source) in enumerate(topics):
    direction = classify_direction(title)
    safe_print(f"[{i+1}/{len(topics)}] {title[:40]}... ({direction})")

    hook = generate_hook(title, direction)
    time.sleep(1)
    body = generate_body(title, source, direction)
    time.sleep(1)

    content = {
        "title": title, "source": source, "direction": direction,
        "hook": hook, "body": body,
        "cta": CTA_MAP.get(direction, CTA_MAP["news"]),
        "tracking_id": f"PV_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "generated_at": datetime.now().isoformat(),
    }
    RESULTS.append(content)

    md = f"# {content['tracking_id']}\n来源: {content['source']}\n方向: {content['direction']}\n\n## 钩子\n{content['hook']}\n\n## 正文\n{content['body']}\n\n## CTA\n{content['cta']}\n\n---\n*PV获客系统生成*"
    md_file = output_dir / f"{content['tracking_id']}.md"
    md_file.write_text(md, encoding="utf-8")

    safe_print(f"  钩子: {hook[:40]}...")
    safe_print(f"  正文: {body[:60]}...")
    time.sleep(2)

# 保存JSON
out_json = output_dir / f"llm_generated_{datetime.now().strftime('%Y%m%d')}.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, ensure_ascii=False, indent=2)

safe_print(f"\n完成! 共生成 {len(RESULTS)} 条")
safe_print(f"JSON: {out_json}")

dir_count = {}
for r in RESULTS:
    d = r["direction"]
    dir_count[d] = dir_count.get(d, 0) + 1
safe_print(f"按方向: {json.dumps(dir_count, ensure_ascii=False)}")
