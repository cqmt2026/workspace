# -*- coding: utf-8 -*-
"""
Humanizer 脚本 - 去除 AI 写作痕迹
用法：
  python humanize_text.py <输入文件> <输出文件>
  python humanize_text.py <输入文件>             # 输出到 输入_humanized.txt
"""

import re
import sys
import argparse
from pathlib import Path
import io


# ========== AI 模式识别规则 ==========

FILLER_PHRASES = [
    "为了实现这一目标", "由于下雨的事实", "在这个时间点",
    "在您需要帮助的情况下", "系统具有处理的能力",
    "值得注意的是数据显示",
]

AI_VOCAB = [
    "此外", "与……保持一致", "至关重要", "深入探讨",
    "强调", "持久的", "增强", "培养", "获得", "突出",
    "相互作用", "复杂/复杂性", "关键（形容词）",
    "格局（抽象名词）", "关键性的", "展示", "织锦",
    "证明", "强调（动词）", "宝贵的", "充満活力的",
]

OVER_EMPHASIS = [
    "作为……的体现", "标志着", "见证了",
    "极其重要的", "至关重要的", "核心的", "关键性的作用",
    "凸显/强调/彰显了其重要性", "反映了更广泛的",
    "象征着其持续的", "为……做出贡献",
    "为……奠定基础", "标志着/塑造着",
    "代表/标志着一个转变", "关键转折点",
    "不断演变的格局", "焦点", "不可磨灭的印记",
]

ADVERTISING_LANGUAGE = [
    "坐落于", "位于……的中心", "开创性的", "著名的",
    "令人叹为观止的", "必游之地", "迷人的",
    "充満活力的（比喻）", "丰富的（比喻）", "深刻的",
]

TRIPLES = [
    "首先、其次、最后", "第一、第二、第三",
    "一方面、另一方面", "不仅、而且",
    "然而、与此同时", "因此、所以",
]


def remove_filler_phrases(text: str) -> str:
    for phrase in FILLER_PHRASES:
        text = text.replace(phrase, phrase.replace("为了", "").replace("由于", "因为").replace("在这个时间点", "现在"))
    return text


def remove_ai_vocab(text: str) -> str:
    """减少高频AI词汇，替换为更口语的表达"""
    replacements = {
        "此外": "还有",
        "与此同时": "同时",
        "至关重要": "很重要",
        "显而易见": "很明显",
        "毫无疑问": "没问题",
        "值得注意的是": "需要注意的是",
        "本质上": "说白了",
        "综上所述": "总之",
        "从某种程度上": "可以说",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def break_triple_structure(text: str) -> str:
    """打破三段式公式结构"""
    # 合并三项列举为两项
    text = re.sub(r"（一|二|三|四）", "", text)
    text = re.sub(r"第一[、，,]", "一方面", text)
    text = re.sub(r"第二[、，,]", "另一方面", text)
    return text


def remove_emDash(text: str) -> str:
    """减少破折号使用"""
    # 去除单独成段的破折号
    text = re.sub(r"\s*——\s*", "，", text)
    return text


def add_voice_and_personality(text: str) -> str:
    """增加真实感和个性"""
    # 检查是否缺少第一人称
    has_first_person = any(w in text for w in ["我", "我们", "我的", "我们的"])
    has_opinion = any(w in text for w in ["感觉", "觉得", "以为", "似乎", "可能"])

    # 检查句子节奏是否过于一致（简单判断：长度标准差）
    lines = [l.strip() for l in text.split("。") if l.strip()]
    if lines:
        lengths = [len(l) for l in lines]
        if len(lengths) > 3:
            import statistics
            stdev = statistics.stdev(lengths) if len(lengths) > 1 else 0
            # 如果句子长度都差不多，添加一个短句打断
            if stdev < 20 and len(lines) > 4:
                text = text + "。"
    return text


def humanize_text(text: str) -> str:
    """主处理函数：逐步去除 AI 痕迹"""
    if not text or len(text.strip()) < 10:
        return text

    # 1. 清理协作交流痕迹
    text = re.sub(r"希望这对您有帮助[！！]*", "", text)
    text = re.sub(r"当然！", "", text)
    text = re.sub(r"您说得完全正确[！，,]*", "", text)
    text = re.sub(r"请告诉我.*", "", text)

    # 2. 去除知识截止日期免责声明
    text = re.sub(r"截至.*?(?:，|。|$)", "", text)
    text = re.sub(r"根据我最后的训练更新.*?(?:，|。|$)", "", text)

    # 3. 删除填充短语
    text = remove_filler_phrases(text)

    # 4. 替换 AI 高频词汇
    text = remove_ai_vocab(text)

    # 5. 打破三段式
    text = break_triple_structure(text)

    # 6. 减少破折号
    text = remove_emDash(text)

    # 7. 去除过度强调象征意义
    for phrase in OVER_EMPHASIS:
        text = text.replace(phrase, "")

    # 8. 去除广告性语言
    for phrase in ADVERTISING_LANGUAGE:
        text = text.replace(phrase, "")

    # 9. 清理多余空格和空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)

    # 10. 增加节奏和个性（可选的最后步骤）
    text = add_voice_and_personality(text)

    # 11. 清理末尾残留
    text = re.sub(r"[。\n]+$", "。", text.strip())

    return text


def score_humanity(text: str) -> dict:
    """评分：评估文本的人类化程度"""
    score = 50
    reasons = []

    # 检查填充词
    filler_count = sum(1 for p in FILLER_PHRASES if p in text)
    if filler_count > 0:
        score -= min(filler_count * 3, 15)
        reasons.append(f"填充短语 {filler_count} 处")

    # 检查 AI 高频词
    ai_count = sum(1 for w in AI_VOCAB if w in text)
    if ai_count > 0:
        score -= min(ai_count * 2, 10)
        reasons.append(f"AI词汇 {ai_count} 处")

    # 检查三段式
    triple_count = sum(1 for t in TRIPLES if t in text)
    if triple_count > 0:
        score -= min(triple_count * 5, 15)
        reasons.append(f"三段式 {triple_count} 处")

    # 检查破折号
    dash_count = text.count("——") + text.count("—")
    if dash_count > 2:
        score -= min(dash_count * 2, 10)
        reasons.append(f"破折号 {dash_count} 处")

    score = max(0, min(50, score))

    grade = "优秀" if score >= 40 else "良好" if score >= 30 else "需修订"
    return {"score": score, "grade": grade, "reasons": reasons}


def process_file(input_path: str, output_path: str = None):
    """处理文件"""
    input_p = Path(input_path)
    if not input_p.exists():
        print(f"[Error] 文件不存在: {input_path}")
        return

    # 读取
    with open(input_p, "r", encoding="utf-8") as f:
        content = f.read()

    # 评分（处理前）
    before = score_humanity(content)

    # Humanize
    humanized = humanize_text(content)

    # 评分（处理后）
    after = score_humanity(humanized)

    # 输出
    if output_path:
        output_p = Path(output_path)
    else:
        output_p = input_p.parent / f"{input_p.stem}_humanized{input_p.suffix}"

    with open(output_p, "w", encoding="utf-8") as f:
        f.write(humanized)

    print(f"\n[Humanizer] 处理完成")
    print(f"  输入: {input_p}")
    print(f"  输出: {output_p}")
    print(f"  评分: {before['score']}/50 → {after['score']}/50 ({before['grade']} → {after['grade']})")
    if after["reasons"]:
        print(f"  剩余问题: {', '.join(after['reasons'])}")

    return str(output_p)


if __name__ == "__main__":

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description="去除 AI 写作痕迹")
    parser.add_argument("input", help="输入文件路径")
    parser.add_argument("output", nargs="?", help="输出文件路径（可选）")
    args = parser.parse_args()

    process_file(args.input, args.output)
