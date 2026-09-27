# -*- coding: utf-8 -*-
"""
ASR 修正器 - 规则修正 + LLM 润色
"""
import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# ========== 规则修正词典 ==========
RULE_CORRECTIONS = [
    # 平台名称
    ("Doubao", "DeepSeek"),
    ("豆包", "豆包"),  # 保持
    ("deepseek", "DeepSeek"),
    ("qwen", "通义千问"),
    ("kimi", "Kimi"),
    
    # GEO 相关术语
    ("机OU", "GEO"),
    ("只O", "GEO"),
    ("ZO", "GEO"),
    ("基欧", "GEO"),
    ("一欧", "GEO"),
    ("之欧", "GEO"),
    ("夜5", "GEO"),
    ("夜欧", "GEO"),
    ("耶欧", "GEO"),
    ("汁欧", "GEO"),
    ("做自由", "做GEO"),
    ("著自由", "做GEO"),
    ("著GEO", "做GEO"),
    
    # 常见 ASR 错误
    ("包牌名", "包排名"),
    ("精英信息", "精确信息"),
    ("多走", "夺走"),
    ("温度", "问到"),
    ("问度", "问到"),
    ("不让完子", "不绕弯子"),
    ("本制", "本质"),
    ("皮配", "匹配"),
    ("皮不配", "匹不匹配"),
    ("皮什么时候", "什么时候"),
    ("开电", "开店"),
    ("反饋", "反馈"),
    ("交律", "焦虑"),
    ("銅航鏡片", "同城曝光"),
    ("唐購", "团购"),
    ("蘇國", "搜索过"),
    ("江澤坦", "江浙沪"),
    ("電名", "店名"),
    ("歸格", "价格"),
    ("削出", "跳出"),
    ("肺率", "费率"),
    ("取到", "高出"),
    ("商顏", "案例"),
    ("這一位", "这意味着"),
    ("幸元密度", "内容密度"),
    ("付績店", "连锁店铺"),
    ("內容吸收", "内容覆盖"),
    ("可憐症", "可验证"),
    ("上加", "商家"),
    ("质疑歐", "做 GEO"),
    ("路景", "路径"),
    ("優先集", "优先级"),
    ("验面", "页面"),
    ("關鍵此", "关键词"),
    ("實體天", "实体几天"),
    ("時別後拉", "识别后拉"),
    ("取到", "抓到"),
    ("規依畫", "归一化"),
    ("地機地機", "地图地图"),
    ("投降", "投放"),
    ("清量啟動", "轻量启动"),
    ("其分中", "几分钟"),
    ("錄境", "路径"),
    ("鋪射", "铺设"),
    ("場單", "订单"),
    ("精英信息", "精确信息"),
    ("產電", "产出"),
    ("信員庫", "信源库"),
    ("更新更", "更新更"),
    ("招揮級", "发挥作用"),
    ("委護", "维护"),
    ("吹字", "几次"),
    ("長警", "长尾"),
    ("監冊", "监测"),
    ("地擊打勞", "地基打牢"),
    ("勞想", "劳心"),
    ("條路", "套路"),
    
    # 标点修正
    ("？ ", "？"),
    (" ！", "！"),
]

# 构建修正正则（长的优先）
def build_correction_pattern(corrections):
    # 按长度排序，长的优先
    sorted_pairs = sorted(corrections, key=lambda x: len(x[0]), reverse=True)
    pattern = "|".join(re.escape(pair[0]) for pair in sorted_pairs)
    return re.compile(pattern), sorted_pairs

correction_pattern, sorted_corrections = build_correction_pattern(RULE_CORRECTIONS)

def rule_correct(text: str) -> str:
    """应用规则修正"""
    def replace_match(match):
        original = match.group(0)
        for wrong, right in sorted_corrections:
            if original == wrong:
                return right
        return original
    return correction_pattern.sub(replace_match, text)


def llm_polish(text: str, context: str = "") -> str:
    """
    LLM 润色（可选，需要 API key）
    
    Args:
        text: 规则修正后的文本
        context: 视频主题上下文
    
    Returns:
        润色后的文本
    """
    # 这里预留 LLM 调用接口
    # 当前返回原文本，后续可接入通义千问/DeepSeek
    return text


def correct_asr(text: str, context: str = "") -> str:
    """完整修正流程：规则修正 + LLM 润色"""
    # Step 1: 规则修正
    corrected = rule_correct(text)
    
    # Step 2: LLM 润色（可选）
    # polished = llm_polish(corrected, context)
    
    return corrected


if __name__ == "__main__":
    # 测试
    test_text = "所有的企业都是适合豆包GEO优化嘛什么样的企业做了才会有效果呢"
    print(f"原始: {test_text}")
    print(f"修正: {rule_correct(test_text)}")
    
    # 从文件读取并修正
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
        output_path = input_path.parent / f"{input_path.stem}_corrected{input_path.suffix}"
        
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        
        corrected_text = correct_asr(raw_text)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(corrected_text)
        
        print(f"\n已修正并保存到: {output_path}")
        print(f"修正前长度: {len(raw_text)}")
        print(f"修正后长度: {len(corrected_text)}")
