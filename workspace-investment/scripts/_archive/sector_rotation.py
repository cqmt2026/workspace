# -*- coding: utf-8 -*-
"""
行业超图动态 - 板块轮动方向识别 v1.0
=====================================
Hermes V3.0组件

核心功能：
  1. 板块动量传播追踪：识别资金从哪些板块流出、流入哪些板块
  2. 板块聚类：按RPS变化方向聚类板块群
  3. 轮动信号生成：具体的「从X流向Y」判断

数据来源：
  - out_data/rps_history/ 下的 RPS_board_*.json 文件（每日采集）
  - 需至少5个交易日历史数据

输出：
  - out_data/sector_rotation_YYYY-MM-DD.json
  - out_data/sector_rotation_YYYY-MM-DD.md
"""

import json
import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from datetime import datetime, date, timedelta
from collections import defaultdict

WORK_DIR = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment'
HIST_DIR = os.path.join(WORK_DIR, 'out_data', 'rps_history')
OUT_DIR = os.path.join(WORK_DIR, 'out_data')
os.makedirs(OUT_DIR, exist_ok=True)


def load_rps_history(days=20) -> list:
    """
    加载最近的RPS历史数据
    返回: [{'date': '20260625', 'boards': [{board_rps_fields}, ...]}, ...]
    按日期升序排列
    """
    if not os.path.exists(HIST_DIR):
        print(f"[轮动] RPS历史目录不存在: {HIST_DIR}")
        return []
    
    files = sorted([f for f in os.listdir(HIST_DIR) 
                    if f.startswith('RPS_board_') and f.endswith('.json')])
    if not files:
        print("[轮动] 无RPS历史文件")
        return []
    
    # 只取最近的 days 个
    files = files[-days:]
    
    history = []
    for fn in files:
        date_str = fn.replace('RPS_board_', '').replace('.json', '')
        with open(os.path.join(HIST_DIR, fn), 'r', encoding='utf-8') as f:
            data = json.load(f)
        rps_list = data.get('rps_data', [])
        if rps_list:
            history.append({
                'date': date_str,
                'boards': rps_list
            })
    
    print(f"[轮动] 加载RPS历史: {len(history)}个交易日, 每期{len(history[0]['boards']) if history else 0}个板块")
    return history


def analyze_rotation(history: list) -> dict:
    """
    板块轮动分析主函数
    
    返回:
    {
        'date': '2026-07-02',
        'summary': { ... },
        'momentum_leaders': [...],      # 动量领涨板块TOP10
        'momentum_laggards': [...],     # 动量领跌板块TOP10
        'rotation_pairs': [...],        # 轮动信号对
        'clusters': [...],              # 板块聚类
        'rotation_intensity': float,    # 轮动强度指数 0~100
        'all_board_analysis': [...]     # 全板块分析
    }
    """
    if len(history) < 2:
        return {'error': '历史数据不足，至少需要2个交易日'}
    
    latest = history[-1]
    prev = history[-2]
    
    # ============================================================
    # 1. 板块动量计算（当前RPS vs 前一日RPS变化）
    # ============================================================
    board_map = {}
    for b in latest['boards']:
        name = b['name']
        board_map[name] = {
            'name': name,
            'rps_5d': b.get('rps_5d', 50),
            'rps_10d': b.get('rps_10d', 50),
            'rps_20d': b.get('rps_20d', 50),
            'ret_5d': b.get('returns', {}).get('5', 0),
            'ret_10d': b.get('returns', {}).get('10', 0),
            'ret_20d': b.get('returns', {}).get('20', 0),
            'change_pct': b.get('change_pct', 0),
        }
    
    # 前一日数据
    prev_map = {}
    for b in prev['boards']:
        prev_map[b['name']] = {
            'rps_5d': b.get('rps_5d', 50),
            'rps_10d': b.get('rps_10d', 50),
        }
    
    # 计算RPS变化
    for name, info in board_map.items():
        prev_rps = prev_map.get(name, {})
        info['rps_5d_chg'] = info['rps_5d'] - prev_rps.get('rps_5d', 50)
        info['rps_10d_chg'] = info['rps_10d'] - prev_rps.get('rps_10d', 50)
        info['rps_momentum'] = info['rps_5d_chg'] * 0.6 + info['rps_10d_chg'] * 0.4
    
    # 如果有3天以上历史，计算3日动量变化
    if len(history) >= 3:
        prev3 = history[-3]
        prev3_map = {}
        for b in prev3['boards']:
            prev3_map[b['name']] = b.get('rps_5d', 50)
        for name, info in board_map.items():
            rps_3d_ago = prev3_map.get(name, 50)
            info['rps_3d_chg'] = info['rps_5d'] - rps_3d_ago
            info['rps_momentum'] = info['rps_momentum'] * 0.5 + info['rps_3d_chg'] * 0.5
    
    # ============================================================
    # 2. 动量排序
    # ============================================================
    all_boards = sorted(board_map.values(), key=lambda x: -x['rps_momentum'])
    
    momentum_leaders = [b for b in all_boards if b['rps_momentum'] > 5][:10]
    momentum_laggards = [b for b in reversed(all_boards) if b['rps_momentum'] < -5][:10]
    
    # ============================================================
    # 3. 板块聚类（按RPS变化方向 + 当前RPS水平）
    # ============================================================
    clusters = {
        '强势加速': [],     # RPS>70, 动量>0
        '强势减速': [],     # RPS>70, 动量<0
        '弱势回暖': [],     # RPS<30, 动量>0
        '弱势加速': [],     # RPS<30, 动量<0
        '中间偏强': [],     # 30<=RPS<=70, 动量>0
        '中间偏弱': [],     # 30<=RPS<=70, 动量<0
    }
    
    for b in all_boards:
        rps = b['rps_5d']
        momentum = b['rps_momentum']
        if rps >= 70:
            if momentum > 0:
                clusters['强势加速'].append(b)
            else:
                clusters['强势减速'].append(b)
        elif rps <= 30:
            if momentum > 0:
                clusters['弱势回暖'].append(b)
            else:
                clusters['弱势加速'].append(b)
        else:
            if momentum > 0:
                clusters['中间偏强'].append(b)
            else:
                clusters['中间偏弱'].append(b)
    
    # ============================================================
    # 4. 轮动信号对检测
    # ============================================================
    rotation_pairs = []
    # 找出最可能发生轮动的板块对：强势减速 + 弱势回暖
    for strong in clusters['强势减速'][:5]:
        for weak in clusters['弱势回暖'][:5]:
            if strong['name'] != weak['name']:
                # 计算轮动置信度
                confidence = min(abs(strong['rps_momentum']), abs(weak['rps_momentum'])) / 20.0
                confidence = min(confidence, 1.0)
                if confidence > 0.3:
                    rotation_pairs.append({
                        'from_board': strong['name'],
                        'from_rps': strong['rps_5d'],
                        'from_momentum': round(strong['rps_momentum'], 1),
                        'to_board': weak['name'],
                        'to_rps': weak['rps_5d'],
                        'to_momentum': round(weak['rps_momentum'], 1),
                        'confidence': round(confidence * 100, 1),
                    })
    
    # 排序
    rotation_pairs.sort(key=lambda x: -x['confidence'])
    
    # ============================================================
    # 5. 轮动强度指数
    # ============================================================
    # 轮动强度 = 动量变化 > 5 的板块占比 * 50 + 动量变化 < -5 的板块占比 * 50
    high_momentum_ratio = sum(1 for b in all_boards if b['rps_momentum'] > 5) / max(len(all_boards), 1)
    low_momentum_ratio = sum(1 for b in all_boards if b['rps_momentum'] < -5) / max(len(all_boards), 1)
    rotation_intensity = round((high_momentum_ratio + low_momentum_ratio) * 50, 1)
    
    # ============================================================
    # 6. 板块分类统计
    # ============================================================
    category_stats = {}
    for cat, boards in clusters.items():
        category_stats[cat] = {
            'count': len(boards),
            'boards': [b['name'] for b in boards[:8]],  # 取前8个
            'avg_rps': round(sum(b['rps_5d'] for b in boards) / max(len(boards), 1), 1) if boards else 0,
            'avg_momentum': round(sum(b['rps_momentum'] for b in boards) / max(len(boards), 1), 1) if boards else 0,
        }
    
    # ============================================================
    # 构建返回结果
    # ============================================================
    today_str = date.today().strftime('%Y-%m-%d')
    
    return {
        'date': today_str,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'rotation_intensity': rotation_intensity,
        'total_boards': len(all_boards),
        'history_days': len(history),
        'summary': {
            'rotation_intensity': rotation_intensity,
            'intensity_label': '高' if rotation_intensity > 50 else '中' if rotation_intensity > 25 else '低',
            'strong_accelerating': len(clusters['强势加速']),
            'strong_decelerating': len(clusters['强势减速']),
            'weak_recovering': len(clusters['弱势回暖']),
            'weak_deteriorating': len(clusters['弱势加速']),
        },
        'momentum_leaders': [{
            'name': b['name'],
            'rps_5d': b['rps_5d'],
            'rps_momentum': round(b['rps_momentum'], 1),
            'ret_5d': b['ret_5d'],
        } for b in momentum_leaders],
        'momentum_laggards': [{
            'name': b['name'],
            'rps_5d': b['rps_5d'],
            'rps_momentum': round(b['rps_momentum'], 1),
            'ret_5d': b['ret_5d'],
        } for b in momentum_laggards],
        'rotation_pairs': rotation_pairs[:8],  # 取前8个信号
        'clusters': {
            cat: {
                'count': stats['count'],
                'boards': stats['boards'],
                'avg_rps': stats['avg_rps'],
                'avg_momentum': stats['avg_momentum'],
            }
            for cat, stats in category_stats.items()
        },
        'all_board_analysis': [{
            'name': b['name'],
            'rps_5d': b['rps_5d'],
            'rps_10d': b['rps_10d'],
            'rps_momentum': round(b['rps_momentum'], 1),
            'ret_5d': b['ret_5d'],
            'ret_10d': b['ret_10d'],
            'cluster': next((cat for cat, boards in clusters.items() if any(b2['name'] == b['name'] for b2 in boards)), '其他'),
        } for b in all_boards],
    }


def generate_markdown_report(result: dict) -> str:
    """生成可读的板块轮动报告Markdown"""
    if 'error' in result:
        return f"# 板块轮动分析\n\n**错误**: {result['error']}"
    
    today = result['date']
    intensity = result['rotation_intensity']
    label = result['summary']['intensity_label']
    
    lines = [
        f"# 🔄 行业超图 - 板块轮动方向识别",
        f"**日期**: {today} | **强度**: {intensity}/100 ({label})",
        f"**数据**: 近{result['history_days']}个交易日, {result['total_boards']}个板块",
        f"",
    ]
    
    # 轮动强度
    lines.append(f"## 📊 轮动强度指数: {intensity}/100")
    if intensity > 50:
        lines.append("> ⚠️ **高轮动强度**：板块间资金剧烈切换，注意节奏")
    elif intensity > 25:
        lines.append("> 📊 **中等轮动**：存在明显板块轮动机会")
    else:
        lines.append("> 🔒 **低轮动**：市场风格稳定，聚焦强势板块")
    lines.append("")
    
    # 板块聚类统计
    s = result['summary']
    lines.append(f"## 🏷️ 板块聚类速览")
    lines.append(f"| 类别 | 数量 | 平均RPS | 平均动量 | 代表板块 |")
    lines.append(f"|------|------|---------|---------|---------|")
    for cat in ['强势加速', '强势减速', '弱势回暖', '弱势加速', '中间偏强', '中间偏弱']:
        c = result['clusters'].get(cat, {})
        boards_str = '、'.join(c.get('boards', [])[:5])
        lines.append(f"| **{cat}** | {c.get('count', 0)} | {c.get('avg_rps', 0)} | {c.get('avg_momentum', 0):+.1f} | {boards_str} |")
    lines.append("")
    
    # 动量领涨
    lines.append(f"## 🔥 动量领涨板块 (TOP{len(result['momentum_leaders'])})")
    lines.append(f"| 板块 | RPS_5d | 动量变化 | 5日涨幅 |")
    lines.append(f"|------|--------|---------|--------|")
    for b in result['momentum_leaders']:
        arrow = '🟢' if b['rps_momentum'] > 0 else '🔴'
        lines.append(f"| {arrow} {b['name']} | {b['rps_5d']} | {b['rps_momentum']:+.1f} | {b['ret_5d']:+.1f}% |")
    lines.append("")
    
    # 动量领跌
    lines.append(f"## 🧊 动量领跌板块 (TOP{len(result['momentum_laggards'])})")
    lines.append(f"| 板块 | RPS_5d | 动量变化 | 5日涨幅 |")
    lines.append(f"|------|--------|---------|--------|")
    for b in result['momentum_laggards']:
        lines.append(f"| 🔴 {b['name']} | {b['rps_5d']} | {b['rps_momentum']:+.1f} | {b['ret_5d']:+.1f}% |")
    lines.append("")
    
    # 轮动信号
    if result['rotation_pairs']:
        lines.append(f"## 🔄 轮动信号 (高置信度)")
        lines.append(f"| 资金流出 ← | → 资金流入 | 置信度 |")
        lines.append(f"|------------|-----------|--------|")
        for pair in result['rotation_pairs'][:6]:
            lines.append(f"| {pair['from_board']}(RPS:{pair['from_rps']},动量:{pair['from_momentum']:+.1f}) | {pair['to_board']}(RPS:{pair['to_rps']},动量:{pair['to_momentum']:+.1f}) | {pair['confidence']}% |")
        lines.append("")
    
    # 综合结论
    lines.append(f"## 💡 综合判断")
    sa = s['strong_accelerating']
    sd = s['strong_decelerating']
    wr = s['weak_recovering']
    wd = s['weak_deteriorating']
    
    if sa > sd:
        lines.append(f"- **风格偏进攻**：强势加速板块({sa}) > 强势减速板块({sd})，资金在强势板块中继续加仓")
    elif sd > sa:
        lines.append(f"- **风格偏防御**：强势减速板块({sd}) > 强势加速板块({sa})，强势板块有获利回吐压力")
    else:
        lines.append(f"- **风格均衡**：强势板块加速({sa})与减速({sd})数量相当")
    
    if wr > wd:
        lines.append(f"- **底部回暖信号**：弱势回暖板块({wr}) > 弱势加速板块({wd})，部分弱势板块有资金回流")
    else:
        lines.append(f"- **底部承压**：弱势板块持续走弱({wd}) > 回暖({wr})")
    
    lines.append("")
    lines.append(f"---")
    lines.append(f"_由 Hermes V3.0 行业超图自动生成 | {result['timestamp']}_")
    
    return '\n'.join(lines)


def save_output(result: dict, md_report: str):
    """保存JSON和Markdown到out_data"""
    today_str = date.today().strftime('%Y-%m-%d')
    
    json_path = os.path.join(OUT_DIR, f'sector_rotation_{today_str}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    md_path = os.path.join(OUT_DIR, f'sector_rotation_{today_str}.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    print(f"[轮动] JSON已保存: {json_path}")
    print(f"[轮动] MD已保存: {md_path}")
    return json_path, md_path


def main():
    print("=" * 60)
    print("🔄 行业超图 - 板块轮动方向识别")
    print("=" * 60)
    
    history = load_rps_history(days=20)
    if len(history) < 2:
        print("[轮动] 数据不足，退出")
        return None
    
    result = analyze_rotation(history)
    md_report = generate_markdown_report(result)
    
    # 打印摘要
    print(f"\n轮动强度: {result['rotation_intensity']}/100 ({result['summary']['intensity_label']})")
    print(f"强势加速: {result['summary']['strong_accelerating']}个 | 强势减速: {result['summary']['strong_decelerating']}个")
    print(f"弱势回暖: {result['summary']['weak_recovering']}个 | 弱势加速: {result['summary']['weak_deteriorating']}个")
    
    print(f"\n🔥 动量领涨TOP5:")
    for b in result['momentum_leaders'][:5]:
        print(f"  🟢 {b['name']} RPS:{b['rps_5d']} 动量:{b['rps_momentum']:+.1f}")
    
    print(f"\n🧊 动量领跌TOP5:")
    for b in result['momentum_laggards'][:5]:
        print(f"  🔴 {b['name']} RPS:{b['rps_5d']} 动量:{b['rps_momentum']:+.1f}")
    
    if result['rotation_pairs']:
        print(f"\n🔄 轮动信号TOP3:")
        for pair in result['rotation_pairs'][:3]:
            print(f"  {pair['from_board']} → {pair['to_board']} (置信度:{pair['confidence']}%)")
    
    print(f"\n{md_report}")
    
    save_output(result, md_report)
    return result


if __name__ == '__main__':
    main()