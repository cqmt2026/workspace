"""
持仓公告监控 v1.0 (2026-06-17)
===============================
监控当前持仓股票的公告，按信号分类输出

信号分类:
- [POS] 重大合同、订单、招标、中标、突破
- [NEG] 减持、解禁、亏损、ST
- [NEU] 股权激励、回购、分红

数据来源: 东方财富公告API
持仓来源: memory/L2-核心/持仓/当前持仓.json
"""
import requests
import json
import io
import sys
import os
from datetime import datetime

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ==== 路径配置 ====
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
OUT = os.path.join(WORKSPACE, 'out_data')
PORTFOLIO_FILE = os.path.join(WORKSPACE, 'memory', 'L2-核心', '持仓', '当前持仓.json')
os.makedirs(OUT, exist_ok=True)

headers = {'User-Agent': 'Mozilla/5.0'}

# ==== 信号关键词 ====

# POS: 正面信号 - 合同/订单/中标/突破
POS_KEYWORDS = {
    '合同': '重大合同签订',
    '订单': '新订单/采购合同',
    '中标': '招标中标',
    '签约': '战略合作协议',
    '重大': '重大业务突破',
    '突破': '技术/市场突破',
    '量产': '量产/产能扩张',
    '合作': '战略合作',
    '采购': '采购合同',
    '投资': '对外投资',
    '扩产': '扩产计划',
}

# NEG: 负面信号 - 减持/解禁/亏损/ST
NEG_KEYWORDS = {
    '减持': '股东减持',
    '解禁': '限售股解禁',
    '亏损': '业绩亏损',
    'ST': 'ST/退市风险',
    '立案': '立案调查',
    '调查': '监管调查',
    '退市': '退市/终止上市',
    '终止': '终止上市/重组',
    '警示': '风险警示',
    '诉讼': '重大诉讼',
    '仲裁': '仲裁事项',
    '资产': '资产减值/计提',
}

# NEU: 中性信号 - 股权激励/回购/分红
NEU_KEYWORDS = {
    '股权激励': '股权激励计划',
    '回购': '股份回购',
    '分红': '分红派息',
    '高管': '高管变动',
    '辞职': '高管辞职',
    '任命': '高管任命',
    '董事会': '董事会变动',
    '换届': '董事会换届',
}


def get_market(code):
    """判断市场代码"""
    if code.startswith('6') or code.startswith('9'):
        return 'SH'
    elif code.startswith('0') or code.startswith('1'):
        return 'SZ'
    elif code.startswith('3'):
        return 'CYB'
    return 'SZ'


def fetch_announcements(code, market='SH', page_size=30):
    """获取单只股票最新公告"""
    market_codes = {
        'SH': ('SHA', 'SZA'),
        'SZ': ('SZA', 'SHA'),
        'CYB': ('CYB', 'SZA')
    }
    ann_types = ','.join(market_codes.get(market, ('SHA', 'SZA')))
    
    url = (
        f'https://np-anotice-stock.eastmoney.com/api/security/ann?'
        f'sr=-1&page_size={page_size}&page_index=1&ann_type={ann_types}'
        f'&client_source=web&stock_list={code}'
    )
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get('data') and data['data'].get('list'):
                return data['data']['list']
    except Exception as e:
        print(f"  [!] 获取 {code} 公告失败: {e}")
    return []


def classify_announcement(title, summary=''):
    """分类公告"""
    text = title + summary
    
    for kw, meaning in POS_KEYWORDS.items():
        if kw in text:
            return 'POS', meaning
    
    for kw, meaning in NEG_KEYWORDS.items():
        if kw in text:
            return 'NEG', meaning
    
    for kw, meaning in NEU_KEYWORDS.items():
        if kw in text:
            return 'NEU', meaning
    
    return 'INFO', ''


def load_portfolio():
    """加载持仓数据"""
    holdings = []
    
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                stocks = data.get('stocks', {})
                
                if isinstance(stocks, dict):
                    for code, info in stocks.items():
                        if isinstance(info, dict):
                            name = info.get('name', '')
                        else:
                            name = str(info)
                        market = get_market(code)
                        holdings.append({'code': code, 'name': name, 'market': market})
                elif isinstance(stocks, list):
                    for item in stocks:
                        if isinstance(item, dict):
                            code = item.get('code', '')
                            name = item.get('name', '')
                        else:
                            code = str(item)
                            name = ''
                        market = get_market(code)
                        holdings.append({'code': code, 'name': name, 'market': market})
                        
        except Exception as e:
            print(f"  [!] 读取持仓文件失败: {e}")
    
    return holdings


def analyze_announcement(ann, code, name):
    """分析单条公告"""
    title = ann.get('title', '')
    notice_date = ann.get('notice_date', '')
    if notice_date:
        notice_date = notice_date[:10]
    
    signal, keyword = classify_announcement(title)
    
    return {
        'code': code,
        'name': name,
        'date': notice_date,
        'title': title,
        'signal': signal,
        'keyword': keyword,
        'url': ann.get('art_url', '')
    }


def format_report(results, title=''):
    """格式化输出报告"""
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    pos = [r for r in results if r['signal'] == 'POS']
    neg = [r for r in results if r['signal'] == 'NEG']
    neu = [r for r in results if r['signal'] == 'NEU']
    
    print(f"\n{'='*60}")
    print(f"【持仓公告监控】{now_str}")
    if title:
        print(f"  {title}")
    print(f"{'='*60}")
    
    total_signals = len(pos) + len(neg) + len(neu)
    
    if total_signals == 0:
        print("\n✅ 持仓股无重大公告信号")
        return
    
    print(f"\n📊 共发现 {total_signals} 条重要公告")
    
    if pos:
        print(f"\n🟢 [POS] 正面信号 ({len(pos)}条):")
        for r in pos:
            name = r['name'] or r['code']
            print(f"  {r['date']} {name} {r['keyword']}: {r['title'][:35]}...")
    
    if neg:
        print(f"\n🔴 [NEG] 负面信号 ({len(neg)}条):")
        for r in neg:
            name = r['name'] or r['code']
            print(f"  {r['date']} {name} {r['keyword']}: {r['title'][:35]}...")
    
    if neu:
        print(f"\n🟡 [NEU] 中性信号 ({len(neu)}条):")
        for r in neu:
            name = r['name'] or r['code']
            print(f"  {r['date']} {name} {r['keyword']}: {r['title'][:35]}...")
    
    print()


def save_results(results):
    """保存结果到文件"""
    date_str = datetime.now().strftime('%Y%m%d')
    out_file = os.path.join(OUT, f'portfolio_ann_{date_str}.json')
    
    report = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'total': len(results),
        'signals': results
    }
    
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📁 结果已保存: {out_file}")


def monitor_portfolio(holdings):
    """监控持仓股票公告"""
    if not holdings:
        print("\n⚠️ 当前无持仓数据，跳过监控")
        return []
    
    print(f"\n🔍 开始监控 {len(holdings)} 只持仓股票公告...")
    print("-" * 50)
    
    all_results = []
    
    for i, stock in enumerate(holdings):
        code = stock['code']
        name = stock['name']
        market = stock['market']
        
        print(f"[{i+1}/{len(holdings)}] 获取 {code} {'('+name+')' if name else ''} 公告...", end=' ')
        
        anns = fetch_announcements(code, market)
        
        stock_results = []
        for ann in anns:
            result = analyze_announcement(ann, code, name)
            if result['signal'] != 'INFO':
                stock_results.append(result)
        
        if stock_results:
            print(f"发现 {len(stock_results)} 条信号")
            all_results.extend(stock_results)
        else:
            print("无重大信号")
    
    return all_results


def main():
    print("=" * 60)
    print("持仓公告监控 v1.0 (2026-06-17)")
    print("=" * 60)
    
    # 加载持仓
    holdings = load_portfolio()
    
    if not holdings:
        print("\n⚠️ 未找到持仓数据，尝试使用示例股票演示...")
        # 使用示例股票
        holdings = [
            {'code': '600118', 'name': '中国卫星', 'market': 'SH'},
            {'code': '000001', 'name': '平安银行', 'market': 'SZ'},
            {'code': '300750', 'name': '宁德时代', 'market': 'SZ'},
        ]
    
    # 监控
    results = monitor_portfolio(holdings)
    
    # 格式化输出
    format_report(results, f"监控 {len(holdings)} 只股票")
    
    # 保存
    if results:
        save_results(results)
    
    print("\n✅ 监控完成")
    
    return results


if __name__ == '__main__':
    main()
