# -*- coding: utf-8 -*-
"""
形态捕手（PatternCatcher）集成模块
将QUANTSKILLS skill-xingtai-catcher 集成到投资决策系统

功能：
1. 文字模板扫描（强趋势延续/底部反转/W底等）
2. 固定模板每日收盘后自动执行
3. 输出候选合并到候选信号
"""
import subprocess, json, os, re, sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from datetime import datetime, date
from pathlib import Path

WORKSPACE = Path(r"C:\Users\Administrator\.openclaw\workspace\workspace-investment")
SCRIPT = WORKSPACE / "skills" / "xingtai-catcher" / "scripts" / "xingtai_search.py"
OUT_DIR = WORKSPACE / "out_data" / "xingtai"
RESULT_FILE = WORKSPACE / ".xingtai_result.txt"

# 固定模板
TEMPLATES = {
    "强趋势延续": "强趋势延续",
    "底部反转": "底部反转",
    "W底": "W底",
    "趋势回踩": "趋势回踩",
    "震荡整理": "震荡整理",
    "M头": "M头",
}


def search_text(query: str, universe: str = "stock",
                timeframe: str = "1d", window_bars: int = 120,
                top_n: int = 5, print_output: bool = False) -> list:
    """
    文字搜索形态
    
    参数:
        query: 搜索文字（如"底部反转"、"W底右侧抬升"）
        universe: stock / future / all
        timeframe: 1d(日线) / 60min(60分钟)
        window_bars: 30 / 60 / 120
        top_n: 1~10
        print_output: 是否打印结果
    
    返回:
        [{"rank":1, "code":"000056", "name":"*ST皇庭", "score":71.9, "url":"..."}, ...]
    """
    cmd = [
        sys.executable, str(SCRIPT),
        "text", query,
        "--universe", universe,
        "--timeframe", timeframe,
        "--window-bars", str(window_bars),
        "--top-n", str(top_n),
        "--print"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(WORKSPACE), encoding='utf-8', errors='replace')
        output = (result.stdout or '') + (result.stderr or '')
        if print_output:
            print(output)
        return _parse_output(output)
    except subprocess.TimeoutExpired:
        print(f"[形态捕手] 搜索超时: {query}")
        return []
    except Exception as e:
        print(f"[形态捕手] 搜索异常: {e}")
        return []


def run_template(template: str, universe: str = "stock",
                 top_n: int = 5, print_output: bool = False) -> list:
    """
    执行固定模板搜索（今日形态雷达）
    
    参数:
        template: 强趋势延续 / 底部反转 / W底 / 趋势回踩 / 震荡整理 / M头
        universe: stock / future / all
        top_n: 1~10
        print_output: 是否打印结果
    
    返回:
        [{"rank":1, "code":"000056", "name":"*ST皇庭", "score":71.9, "url":"..."}, ...]
    """
    if template not in TEMPLATES:
        print(f"[形态捕手] 未知模板: {template}，可选: {list(TEMPLATES.keys())}")
        return []
    return search_text(template, universe=universe, 
                       timeframe="1d", window_bars=120,
                       top_n=top_n, print_output=print_output)


def _record_recommendations(results: dict):
    """将形态捕手结果记录到推荐追踪系统"""
    try:
        sys.path.insert(0, str(WORKSPACE))
        from scripts.recommendation_tracker import record_recommendation, get_stock_price, DB
        
        today = date.today().isoformat()
        templates = [k for k in results if not k.startswith("_")]
        
        for name in templates:
            candidates = results.get(name, [])
            for c in candidates[:3]:  # 只记录Top3
                if c.get("score", 0) < 50:
                    continue
                code = c.get("code", "")
                name_str = c.get("name", "?")
                # 获取当日收盘价
                price = get_stock_price(code, today)
                record_recommendation(
                    source=f"xingtai_{name}",
                    code=code,
                    name=name_str,
                    price=price,
                    reason=f"形态捕手-{name} 评分{c.get('score', 0)}"
                )
    except Exception as e:
        print(f"[形态捕手] 记录推荐失败: {e}")


def run_all_templates(universe: str = "stock", top_n: int = 3,
                      print_output: bool = False, record: bool = True) -> dict:
    """
    执行所有固定模板，返回全部结果
    
    返回:
        {
            "强趋势延续": [candidates...],
            "底部反转": [candidates...],
            ...
            "_meta": {"date": "2026-06-29", "universe": "stock", "top_n": 3}
        }
    """
    today = date.today().strftime("%Y-%m-%d")
    results = {"_meta": {"date": today, "universe": universe, "top_n": top_n}}
    
    for name in TEMPLATES:
        if print_output:
            print(f"\n{'='*60}")
            print(f"[形态捕手] 模板: {name}")
            print(f"{'='*60}")
        candidates = run_template(name, universe=universe, top_n=top_n, 
                                  print_output=print_output)
        results[name] = candidates
    
    # 保存结果
    os.makedirs(OUT_DIR, exist_ok=True)
    out_file = OUT_DIR / f"xingtai_radar_{today}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    if print_output:
        print(f"\n[形态捕手] 全部结果已保存: {out_file}")
    
    # 自动记录推荐到追踪系统
    if record:
        _record_recommendations(results)
        if print_output:
            print(f"[形态捕手] 推荐已记录到追踪系统")
    
    return results


def get_candidates_summary(results: dict) -> str:
    """
    将形态捕手结果格式化为文本摘要（供日报/决策使用）
    
    返回:
        格式化的文本
    """
    lines = []
    today = results.get("_meta", {}).get("date", date.today().strftime("%Y-%m-%d"))
    lines.append(f"🔍 **形态雷达 · {today}**")
    lines.append("=" * 50)
    
    templates = [k for k in results if not k.startswith("_")]
    
    for name in templates:
        candidates = results.get(name, [])
        if not candidates:
            continue
        # 只看评分50以上的
        valid = [c for c in candidates if c.get("score", 0) >= 50]
        if not valid:
            continue
        
        emoji = {"强趋势延续": "🔥", "底部反转": "💎", "W底": "📈", 
                 "趋势回踩": "🔁", "震荡整理": "⏸️", "M头": "⚠️"}
        e = emoji.get(name, "🔍")
        lines.append(f"\n{e} **{name}**")
        for c in valid[:3]:
            name_str = c.get("name", "?")
            code_str = c.get("code", "?")
            score = c.get("score", 0)
            lines.append(f"  {c['rank']}. {name_str}({code_str}) 评分{score:.1f}")
    
    if len(lines) <= 2:
        lines.append("今日形态雷达无结果")
    
    return "\n".join(lines)


def _parse_output(output: str) -> list:
    """
    解析 xingtai_search.py 的输出文本
    格式: "1. *ST皇庭 000056，评分 71.9，股票，数据日 2026-06-26"
    或: "1. 宏和科技 603256，评分 87.2，股票，数据日 2026-06-26"
    """
    candidates = []
    for line in output.split("\n"):
        line = line.strip()
        # 匹配候选行: "1. 名称 代码，评分 XX.X，..."
        m = re.match(r'(\d+)\.\s+(\S+?)\s+(\d{6}|\*?[A-Z]+\d+?)，评分\s+([\d.]+)', line)
        if m:
            rank = int(m.group(1))
            name = m.group(2).strip()
            code = m.group(3).strip()
            score = float(m.group(4))
            candidates.append({
                "rank": rank,
                "code": code,
                "name": name,
                "score": score
            })
    
    return candidates


if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if mode == "all":
        # 执行全部6个模板
        results = run_all_templates(universe="stock", top_n=3, print_output=True, record=True)
        summary = get_candidates_summary(results)
        print(f"\n\n{summary}")
    
    elif mode in TEMPLATES:
        # 执行指定模板
        run_template(mode, universe="stock", top_n=5, print_output=True)
    
    elif mode == "text":
        # 自定义文字搜索
        query = sys.argv[2] if len(sys.argv) > 2 else "W底右侧抬升"
        search_text(query, universe="stock", top_n=5, print_output=True)