# Skill路由配置 - 根据触发词自动调用Skill
SKILL_ROUTER = {
    "视频脚本": {
        "skill": "video-script-generator",
        "trigger": ["视频脚本", "分镜", "storyboard", "script", "脚本生成"]
    },
    "抖音下载": {
        "skill": "douyin-video",
        "trigger": ["抖音下载", "下载抖音"]
    },
    "抖音发布": {
        "skill": "douyin-video-publish",
        "trigger": ["抖音发布", "发布视频"]
    },
    "内容改写": {
        "skill": "content-remix-studio",
        "trigger": ["改写", "多平台分发", "remix"]
    },
    "去AI味": {
        "skill": "humanizer-zh",
        "trigger": ["去AI味", "humanizer", "更像人写的", "去味"]
    },
    "热点": {
        "skill": "hot-topic-finder",
        "trigger": ["热点", "热搜", "热门话题", "找话题"]
    },
    "全网热点": {
        "skill": "web-hot",
        "trigger": ["全网热点", "微博热搜", "知乎热榜", "各平台热点"]
    },
    "股票分析": {
        "skill": "investment-analyst",
        "trigger": ["股票", "A股", "投资分析", "选股", "涨跌"]
    },
    "系统诊断": {
        "skill": "capability-evolver-pro",
        "trigger": ["诊断", "系统问题", "卡", "变慢", "报错"]
    },
    "自动化": {
        "skill": "automation-workflows",
        "trigger": ["自动化", "workflow", "工作流"]
    },
    "小说创作": {
        "skill": "novel-generator",
        "trigger": ["写小说", "章节", "续写", "第", "小说创作"]
    },
    "数学动画": {
        "skill": "video-frames",
        "trigger": ["数学动画", "manim", "做动画", "EP", "动画制作"]
    },
    "文案优化": {
        "skill": "ai-prompt-optimizer-cn",
        "trigger": ["优化文案", "标题优化", "prompt", "标题"]
    }
}

def match_skill(task_text):
    """根据任务文本匹配最合适的Skill"""
    matched = []
    for category, config in SKILL_ROUTER.items():
        for trigger in config["trigger"]:
            if trigger in task_text:
                matched.append({"category": category, "skill": config["skill"], "trigger": trigger})
                break
    return matched

SKILL_PATHS = {
    "video-script-generator": "skills\\video-script-generator",
    "douyin-video": "skills\\douyin-video",
    "douyin-video-publish": "skills\\douyin-video-publish",
    "content-remix-studio": "skills\\content-remix-studio",
    "humanizer-zh": "skills\\humanizer-zh",
    "hot-topic-finder": "skills\\hot-topic-finder",
    "web-hot": "skills\\web-hot",
    "investment-analyst": "skills\\investment-analyst",
    "capability-evolver-pro": "skills\\capability-evolver-pro",
    "automation-workflows": "skills\\automation-workflows",
    "novel-generator": "skills\\novel-generator",
    "video-frames": "workspace-math",
    "ai-prompt-optimizer-cn": "skills\\ai-prompt-optimizer-cn"
}

if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    tests = [
        "帮我写一个视频脚本",
        "今天的热点是什么",
        "这篇文案去AI味",
        "分析一下茅台股票",
        "系统变慢了",
        "写第二章",
        "帮我做数学动画",
        "优化一下标题"
    ]
    for q in tests:
        r = match_skill(q)
        skill_list = ", ".join([m["skill"] for m in r]) or "无匹配"
        print(f"Q: {q:<20} -> {skill_list}")
