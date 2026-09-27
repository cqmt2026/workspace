# -*- coding: utf-8 -*-
"""
公告采集器 (Announcement Fetcher)
==============================
基于东方财富公告API，专门给论文追踪和红线检查使用。

核心功能：
1. 按持仓股票获取最新公告
2. 自动分类（正面/负面/中性）
3. 提取关键信号（立案/减持/解禁/业绩变脸等）
4. 供论文追踪的否决条件检查使用

用法：
  python ann_fetcher.py                    # 获取所有持仓公告
  python ann_fetcher.py sh688102           # 获取单只
  python ann_fetcher.py --days 30          # 查近30天
  python ann_fetcher.py --signal           # 只输出有信号的公告
"""
import sys, os, json, urllib.request, re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

WORK_DIR = Path(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment')
DB = r'F:\market_data.db'
OUT_DIR = WORK_DIR / 'out_data'
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://np-anotice-stock.eastmoney.com/',
}

# 负面信号关键词（直接对应论文否决条件+红线检查）
NEGATIVE_SIGNALS = {
    '立案': '立案调查',
    '调查': '监管调查',
    '处罚': '监管处罚',
    '警示': '风险警示',
    'ST': 'ST/退市',
    '退市': '退市风险',
    '终止上市': '终止上市',
    '暂停上市': '暂停上市',
    '诉讼': '重大诉讼',
    '仲裁': '仲裁事项',
    '违约': '债务违约',
    '逾期': '债务逾期',
    '冻结': '资产冻结',
    '质押': '股权质押',
    '减持': '股东减持',
    '解禁': '限售股解禁',
    '亏损': '业绩亏损',
    '预亏': '业绩预亏',
    '减值': '资产减值',
    '计提': '计提减值',
    '辞职': '高管辞职',
    '违规': '违规操作',
    '造假': '财务造假',
    '通报': '监管通报',
    '整改': '责令整改',
}

# 正面信号关键词
POSITIVE_SIGNALS = {
    '合同': '重大合同',
    '订单': '新订单',
    '中标': '中标通知',
    '签约': '签约协议',
    '突破': '技术突破',
    '量产': '量产/扩产',
    '回购': '股份回购',
    '增持': '股东增持',
    '分红': '分红派息',
    '增长': '业绩增长',
    '扭亏': '扭亏为盈',
    '预增': '业绩预增',
    '获批': '获批/核准',
}


def get_market(code: str) -> str:
    """判断市场代码"""
    c = code.replace('sh', '').replace('sz', '').replace('.', '')
    if c.startswith('6') or c.startswith('68'):
        return 'SH'
    elif c.startswith('3'):
        return 'CYB'
    return 'SZ'


def fetch_announcements(code: str, days: int = 30) -> List[Dict]:
    """获取单只股票公告（通过统一接口）"""
    from scripts.data_api import eastmoney_announcements
    notices = eastmoney_announcements(code, days)
    return notices or []


def classify_announcement(title: str) -> Dict:
    """分类公告并提取信号"""
    signals = []

    # 检查负面信号
    for kw, meaning in NEGATIVE_SIGNALS.items():
        if kw in title:
            signals.append({'type': 'negative', 'signal': meaning, 'keyword': kw})

    # 检查正面信号
    for kw, meaning in POSITIVE_SIGNALS.items():
        if kw in title:
            signals.append({'type': 'positive', 'signal': meaning, 'keyword': kw})

    if not signals:
        return {'category': 'neutral', 'signals': []}

    # 判断整体类别
    has_neg = any(s['type'] == 'negative' for s in signals)
    has_pos = any(s['type'] == 'positive' for s in signals)

    if has_neg and has_pos:
        return {'category': 'mixed', 'signals': signals}
    elif has_neg:
        return {'category': 'negative', 'signals': signals}
    else:
        return {'category': 'positive', 'signals': signals}


def run_fetch(codes: List[str], days: int = 30, signal_only: bool = False) -> List[Dict]:
    """获取并处理公告"""
    results = []
    for code in codes:
        items = fetch_announcements(code, days)
        if not items:
            continue

        # 取持仓名称
        name = ''
        try:
            import sqlite3
            db_code = code
            if not db_code.startswith('sh') and not db_code.startswith('sz'):
                db_code = 'sh.' + db_code if db_code.startswith('6') else 'sz.' + db_code
            else:
                db_code = code[:2] + '.' + code[2:]
            conn = sqlite3.connect(DB)
            row = conn.execute(
                "SELECT name FROM daily_k WHERE code=? LIMIT 1", (db_code,)
            ).fetchone()
            if row:
                name = row[0]
            conn.close()
        except:
            pass

        for item in items:
            title = item.get('title', '')
            notice_date = item.get('notice_date', '')
            if notice_date and len(notice_date) >= 10:
                notice_date = notice_date[:10]

            classification = classify_announcement(title)

            if signal_only and classification['category'] == 'neutral':
                continue

            results.append({
                'code': code,
                'name': name,
                'title': title,
                'date': notice_date,
                'category': classification['category'],
                'signals': classification['signals'],
                'attach_url': item.get('attach_path', ''),
            })

    return results


def format_results(results: List[Dict]) -> str:
    """格式化输出"""
    lines = []
    if not results:
        return '暂无公告'

    # 按类别分组
    negative = [r for r in results if r['category'] == 'negative']
    positive = [r for r in results if r['category'] == 'positive']
    neutral = [r for r in results if r['category'] == 'neutral']
    mixed = [r for r in results if r['category'] == 'mixed']

    if negative:
        lines.append(f"\n🔴 **负面信号 ({len(negative)}条)**")
        for r in negative:
            sigs = ', '.join(s['signal'] for s in r['signals'])
            lines.append(f"  [{r['date']}] {r['name']}({r['code']}): {r['title'][:60]}")
            lines.append(f"    → {sigs}")

    if mixed:
        lines.append(f"\n🟠 **混合信号 ({len(mixed)}条)**")
        for r in mixed:
            sigs = ', '.join(s['signal'] for s in r['signals'])
            lines.append(f"  [{r['date']}] {r['name']}({r['code']}): {r['title'][:60]}")
            lines.append(f"    → {sigs}")

    if positive:
        lines.append(f"\n🟢 **正面信号 ({len(positive)}条)**")
        for r in positive[:5]:
            sigs = ', '.join(s['signal'] for s in r['signals'])
            lines.append(f"  [{r['date']}] {r['name']}({r['code']}): {r['title'][:60]}")
            lines.append(f"    → {sigs}")

    if neutral:
        lines.append(f"\n⚪ **其他公告 ({len(neutral)}条)**")
        for r in neutral[:5]:
            lines.append(f"  [{r['date']}] {r['name']}({r['code']}): {r['title'][:60]}")

    return '\n'.join(lines)


def get_holdings() -> List[str]:
    """获取当前持仓代码列表"""
    portfolio_path = WORK_DIR / 'data' / 'portfolio.json'
    if not portfolio_path.exists():
        return []
    with open(portfolio_path, 'r', encoding='utf-8') as f:
        pf = json.load(f)
    return [h['code'] for h in pf.get('holdings', [])]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='公告采集器')
    parser.add_argument('code', nargs='?', help='股票代码（不填则查所有持仓）')
    parser.add_argument('--days', type=int, default=30, help='查近N天')
    parser.add_argument('--signal', action='store_true', help='只输出有信号的公告')
    args = parser.parse_args()

    if args.code:
        codes = [args.code]
    else:
        codes = get_holdings()
        if not codes:
            print('当前无持仓')
            sys.exit(0)

    results = run_fetch(codes, args.days, args.signal)
    print(format_results(results))

    # 保存
    today = datetime.now().strftime('%Y-%m-%d')
    out_path = OUT_DIR / f'announcements_{today}.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\n💾 已保存: {out_path}')