# -*- coding: utf-8 -*-
"""
跨系统信息关联：投资热点 → 自媒体内容推荐

检测投资系统中新产生的热点/板块/策略信号，
如果与自媒体内容方向相关，主动推荐做内容素材。
"""
import os, sys, json
from datetime import datetime, timedelta
import io

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace'
INV = os.path.join(WORKSPACE, 'workspace-investment')
SOCIAL = os.path.join(WORKSPACE, 'workspace-social')
MAPHOT = os.path.join(WORKSPACE, 'workspace-maphot')

# 股票名称缓存
_STOCK_CACHE = {}
def _load_stock_cache():
    global _STOCK_CACHE
    if _STOCK_CACHE:
        return
    cache_file = os.path.join(INV, 'data', 'stock_name_cache.json')
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            _STOCK_CACHE = json.load(f)

def _get_stock_name(code):
    """通过代码获取股票名称"""
    _load_stock_cache()
    # 直接匹配
    if code in _STOCK_CACHE:
        return _STOCK_CACHE[code]
    # 去掉前缀匹配
    code_no_prefix = code.replace('sz.', '').replace('sh.', '').replace('bj.', '')
    for k, v in _STOCK_CACHE.items():
        k_no = k.replace('sz.', '').replace('sh.', '').replace('bj.', '')
        if k_no == code_no_prefix:
            return v
    return code

def get_investment_signals():
    """获取投资系统最新信号"""
    signals = []
    rps_dir = os.path.join(INV, 'out_data')
    if not os.path.exists(rps_dir):
        return signals

    # RPS推送
    rps_files = sorted([f for f in os.listdir(rps_dir) if f.startswith('rps_push_') and f.endswith('.json')], reverse=True)
    if rps_files:
        latest_rps = rps_files[0]
        try:
            with open(os.path.join(rps_dir, latest_rps), 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            signals.append({
                'source': 'RPS强势股',
                'data': data,
                'date': latest_rps.replace('rps_push_', '').replace('.json', ''),
                'filename': latest_rps,
            })
        except Exception as e:
            pass

    # 信号聚合
    sig_files = sorted([f for f in os.listdir(rps_dir) if f.startswith('signal_aggregated_') and f.endswith('.json')], reverse=True)
    if sig_files:
        latest_sig = sig_files[0]
        try:
            with open(os.path.join(rps_dir, latest_sig), 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            signals.append({
                'source': '信号聚合',
                'data': data,
                'date': latest_sig.replace('signal_aggregated_', '').replace('.json', ''),
                'filename': latest_sig,
            })
        except Exception as e:
            pass

    # 涨跌停分析
    zt_files = sorted([f for f in os.listdir(rps_dir) if f.startswith('zt_analysis_') and f.endswith('.txt')], reverse=True)
    if zt_files:
        latest_zt = zt_files[0]
        try:
            with open(os.path.join(rps_dir, latest_zt), 'r', encoding='utf-8') as fh:
                content = fh.read()
            signals.append({
                'source': '涨跌停分析',
                'data': content,
                'date': latest_zt.replace('zt_analysis_', '').replace('.txt', ''),
                'filename': latest_zt,
            })
        except Exception as e:
            pass

    return signals

def get_social_status():
    """获取自媒体系统状态"""
    drafts = os.path.join(SOCIAL, 'drafts')
    if not os.path.exists(drafts):
        return {'status': 'no_drafts', 'recent_count': 0, 'platforms': []}

    cutoff = datetime.now() - timedelta(days=7)
    recent = 0
    platforms = set()
    for root, dirs, files in os.walk(drafts):
        for f in files:
            fp = os.path.join(root, f)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(fp))
                if mtime > cutoff:
                    recent += 1
                    rel = os.path.relpath(root, drafts)
                    if rel != '.':
                        platforms.add(rel.split(os.sep)[0])
            except:
                pass

    # 检查热点采集
    hotspot_dir = os.path.join(SOCIAL, 'bank', '房产专业', 'pipeline_data', 'hotspots')
    hotspot_count = 0
    if os.path.exists(hotspot_dir):
        for f in os.listdir(hotspot_dir):
            if f.startswith('hotspots_') and f.endswith('.json'):
                fp = os.path.join(hotspot_dir, f)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(fp))
                    if mtime > cutoff:
                        hotspot_count += 1
                except:
                    pass

    return {
        'status': 'active' if recent > 0 else 'idle',
        'recent_count': recent,
        'hotspot_count': hotspot_count,
        'platforms': list(platforms)
    }

def get_maphot_topics():
    """获取地图热点系统选题"""
    topics_file = os.path.join(MAPHOT, 'system', 'topics', 'topics_20260830.json')
    if os.path.exists(topics_file):
        try:
            with open(topics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []

def generate_recommendations(signals, social, maphot_topics):
    """根据投资信号生成自媒体内容推荐"""
    recs = []
    seen = set()

    # 1. RPS强势股推荐
    for sig in signals:
        if sig['source'] == 'RPS强势股':
            data = sig['data']
            date = sig['date']

            # RPS5
            for item in data.get('rps5', [])[:5]:
                code = item.get('code', '')
                name = _get_stock_name(code)
                rps = item.get('rps', 0)
                pct = item.get('return_pct', 0)
                key = f'rps5_{code}'
                if key not in seen:
                    seen.add(key)
                    recs.append({
                        'type': 'RPS强势股',
                        'subtype': '短期强势',
                        'source': f'RPS5-{date}',
                        'hint': f'📈 {name}({code}) RPS排名{rps:.0f}，5日涨幅{pct:.1f}%，市场最强梯队，可做强势股分析',
                        'code': code,
                        'name': name,
                        'return_pct': pct,
                        'rps': rps,
                        'date': date,
                        'angle': '可写：强势股逻辑拆解、RPS选股方法论、短期动能分析'
                    })

            # RPS20
            for item in data.get('rps20', [])[:5]:
                code = item.get('code', '')
                name = _get_stock_name(code)
                rps = item.get('rps', 0)
                pct = item.get('return_pct', 0)
                key = f'rps20_{code}'
                if key not in seen:
                    seen.add(key)
                    recs.append({
                        'type': 'RPS强势股',
                        'subtype': '中期强势',
                        'source': f'RPS20-{date}',
                        'hint': f'📈 {name}({code}) RPS排名{rps:.0f}，20日涨幅{pct:.1f}%，中期趋势强劲，可做趋势跟踪分析',
                        'code': code,
                        'name': name,
                        'return_pct': pct,
                        'rps': rps,
                        'date': date,
                        'angle': '可写：中期趋势股复盘、RPS20策略效果验证、持仓逻辑'
                    })

    # 2. 涨跌停分析推荐
    for sig in signals:
        if sig['source'] == '涨跌停分析':
            content = sig['data']
            date = sig['date']

            # 解析涨停数
            import re
            zt_match = re.search(r'涨停总数:\s*(\d+)家', content)
            zt_count = int(zt_match.group(1)) if zt_match else 0

            # 解析跌停数
            dt_match = re.search(r'跌停总数:\s*(\d+)家', content)
            dt_count = int(dt_match.group(1)) if dt_match else 0

            # 解析市场情绪
            sentiment_match = re.search(r'市场情绪:\s*([^\n]+)', content)
            sentiment = sentiment_match.group(1).strip() if sentiment_match else ''

            # 解析连板股
            board_match = re.search(r'连板股\((\d+)家\):(.*?)(?:\n\n|$)', content, re.DOTALL)
            boards = []
            if board_match:
                board_text = board_match.group(2)
                for line in board_text.strip().split('\n'):
                    line = line.strip()
                    if line and ':' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            boards.append({'name': parts[0].strip(), '连续': parts[1].strip()})

            # 解析热点板块
            sector_match = re.search(r'热点涨停板块:(.*?)(?:====|$)', content, re.DOTALL)
            sectors = []
            if sector_match:
                for line in sector_match.group(1).strip().split('\n'):
                    line = line.strip()
                    if line and ':' in line and '家涨停' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            sectors.append({'name': parts[0].strip(), 'count': parts[1].strip()})

            recs.append({
                'type': '市场情绪',
                'subtype': '每日复盘',
                'source': f'涨跌停-{date}',
                'hint': f'📊 市场情绪{sentiment}，涨停{zt_count}家 vs 跌停{dt_count}家，可做每日市场复盘内容',
                'zt_count': zt_count,
                'dt_count': dt_count,
                'sentiment': sentiment,
                'date': date,
                'angle': '可写：每日涨停复盘、情绪周期判断、连板股追踪'
            })

            # 连板股推荐
            for b in boards[:5]:
                key = f'board_{b["name"]}'
                if key not in seen:
                    seen.add(key)
                    recs.append({
                        'type': '连板股',
                        'subtype': b['连续'],
                        'source': f'涨跌停-{date}',
                        'hint': f'🔥 {b["name"]} {b["连续"]}，市场高度标，可做连板股分析',
                        'name': b['name'],
                        '连续板': b['连续'],
                        'date': date,
                        'angle': '可写：连板股逻辑拆解、情绪周期判断、高位股风险警示'
                    })

            # 热点板块推荐
            for s in sectors[:3]:
                key = f'sector_{s["name"]}'
                if key not in seen:
                    seen.add(key)
                    recs.append({
                        'type': '热点板块',
                        'subtype': s['name'],
                        'source': f'涨跌停-{date}',
                        'hint': f'🏭 {s["name"]} {s["count"]}，当日最热板块，可做板块轮动分析',
                        'sector': s['name'],
                        'count': s['count'],
                        'date': date,
                        'angle': '可写：板块轮动逻辑、热点持续性判断、资金流向分析'
                    })

    # 3. 地图热点选题推荐（与自媒体内容交叉）
    for topic in maphot_topics[:5]:
        title = topic.get('title', '')
        hot = topic.get('hot', 0)
        score = topic.get('score', 0)
        category = topic.get('category', '')

        # 只推荐高热度话题
        if hot > 100000 and score >= 5:
            key = f'maphot_{title[:20]}'
            if key not in seen:
                seen.add(key)
                recs.append({
                    'type': '热点选题',
                    'subtype': category,
                    'source': f'地图热点-{datetime.now().strftime("%Y%m%d")}',
                    'hint': f'🔥 微博热榜: {title} (热度{hot/10000:.0f}万)，可做热点解读',
                    'title': title,
                    'hot': hot,
                    'score': score,
                    'category': category,
                    'date': datetime.now().strftime('%Y%m%d'),
                    'angle': '可写：热点事件解读、数据可视化、地图展示'
                })

    # 4. 自媒体热点与投资建议交叉
    social_hotspot = os.path.join(SOCIAL, 'bank', '房产专业', 'pipeline_data', 'hotspots', 'hotspots_latest.json')
    if os.path.exists(social_hotspot):
        try:
            with open(social_hotspot, 'r', encoding='utf-8') as f:
                hotspots = json.load(f)
            for h in hotspots[:3]:
                title = h.get('title', '')
                angle = h.get('angle', '')
                key = f'social_{title[:20]}'
                if key not in seen:
                    seen.add(key)
                    recs.append({
                        'type': '自媒体热点',
                        'subtype': angle,
                        'source': '房产热点采集',
                        'hint': f'🏠 {title[:50]}...',
                        'title': title,
                        'angle': angle,
                        'date': datetime.now().strftime('%Y%m%d'),
                        'angle_note': '可写：房产市场分析、政策解读、区域价值评估'
                    })
        except:
            pass

    return recs

def main():
    signals = get_investment_signals()
    social = get_social_status()
    maphot_topics = get_maphot_topics()
    recs = generate_recommendations(signals, social, maphot_topics)

    lines = []
    lines.append('🔗 跨系统内容推荐')
    lines.append(f'   {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'   自媒体: {social["status"]}(近7天{social["recent_count"]}篇, 热点{social["hotspot_count"]}个)')
    lines.append('')

    if recs:
        # 按类型分组
        by_type = {}
        for r in recs:
            t = r['type']
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(r)

        for t, items in by_type.items():
            lines.append(f'━━━ {t} ({len(items)}条) ━━━')
            for r in items[:3]:  # 每类最多3条
                lines.append(f'💡 {r["hint"]}')
                lines.append(f'   📝 {r.get("angle", r.get("angle_note", ""))}')
            lines.append('')

        lines.append(f'📝 共{len(recs)}条推荐')
    else:
        lines.append('暂无跨系统内容推荐')

    print('\n'.join(lines))

    # 写入推荐文件
    if recs:
        out_dir = os.path.join(SOCIAL, 'recommendations')
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, f'cross_system_{datetime.now().strftime("%Y%m%d_%H%M")}.json')
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump({
                'time': datetime.now().isoformat(),
                'social_status': social,
                'recommendations': recs
            }, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
