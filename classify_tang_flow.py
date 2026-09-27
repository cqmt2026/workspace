# -*- coding: utf-8 -*-
"""唐斐男银行账户流水分类整理脚本"""
import pdfplumber, re, json
from collections import defaultdict

def extract_year_data(year):
    """提取单一年份的交易数据"""
    path = rf'C:\Users\Administrator\Desktop\流水\tang\{year}.pdf'
    try:
        with pdfplumber.open(path) as pdf:
            all_text = ''
            for page in pdf.pages:
                t = page.extract_text()
                if t: all_text += t + '\n'
            
            trans_lines = [l for l in all_text.split('\n') if l.strip().startswith('卡 ')]
            transactions = []
            
            for line in trans_lines:
                amounts = re.findall(r'[-]?\s*[\d,]+\.\d{2}', line)
                date_match = re.search(r'(\d{4}/\d{2}/\d{2})', line)
                summary_match = re.search(r'(手机转账|转账|消费|取现|利息|存款|存入|支取)', line)
                name_match = re.search(r'([\u4e00-\u9fa5]+?)/\d+', line)
                
                if len(amounts) >= 2:
                    amount_str = amounts[0].replace(' ', '').replace(',', '')
                    amount = float(amount_str)
                    
                    transactions.append({
                        'date': date_match.group(1) if date_match else '',
                        'summary': summary_match.group(1) if summary_match else '其他',
                        'amount': amount,
                        'direction': '收入' if amount > 0 else '支出',
                        'counterparty': name_match.group(1) if name_match else '未知',
                        'balance_after': amounts[1].replace(' ', '').replace(',', '') if len(amounts) > 1 else ''
                    })
            
            return {
                'income': sum(t['amount'] for t in transactions if t['amount'] > 0),
                'expense': sum(abs(t['amount']) for t in transactions if t['amount'] < 0),
                'count': len(transactions),
                'transactions': transactions
            }
    except Exception as e:
        return {'income': 0, 'expense': 0, 'count': 0, 'transactions': [], 'error': str(e)}

def classify_transactions(transactions):
    """对交易进行分类统计"""
    type_stats = defaultdict(lambda: {'count': 0, 'income': 0, 'expense': 0})
    counter_stats = defaultdict(lambda: {'count': 0, 'income': 0, 'expense': 0})
    
    for t in transactions:
        # 按类型统计
        key = t['summary']
        type_stats[key]['count'] += 1
        if t['amount'] > 0:
            type_stats[key]['income'] += t['amount']
        else:
            type_stats[key]['expense'] += abs(t['amount'])
        
        # 按对手统计
        cp = t['counterparty']
        counter_stats[cp]['count'] += 1
        if t['amount'] > 0:
            counter_stats[cp]['income'] += t['amount']
        else:
            counter_stats[cp]['expense'] += abs(t['amount'])
    
    return dict(type_stats), dict(counter_stats)

def generate_report():
    """生成完整报告"""
    all_data = {}
    grand_income = 0
    grand_expense = 0
    grand_count = 0
    all_transactions = []
    
    for year in range(2017, 2027):
        data = extract_year_data(year)
        all_data[year] = data
        grand_income += data['income']
        grand_expense += data['expense']
        grand_count += data['count']
        all_transactions.extend(data['transactions'])
    
    # 分类统计
    type_stats, counter_stats = classify_transactions(all_transactions)
    
    # 构建报告
    report = {
        'account_info': {
            'holder': '唐斐男',
            'account_number': '6216911100376933',
            'bank': '中国民生银行重庆分行营业部',
            'period': '2017-01-01 至 2026-01-01',
            'id_card': '511203198305272574'
        },
        'summary': {
            'total_income': grand_income,
            'total_expense': grand_expense,
            'net_flow': grand_income - grand_expense,
            'total_transactions': grand_count
        },
        'yearly': {},
        'type_stats': {k: dict(v) for k, v in type_stats.items()},
        'counterparty_stats': {k: dict(v) for k, v in counter_stats.items()},
        'insights': []
    }
    
    for year in range(2017, 2027):
        d = all_data[year]
        report['yearly'][str(year)] = {
            'income': d['income'],
            'expense': d['expense'],
            'net': d['income'] - d['expense'],
            'count': d['count']
        }
    
    # 关键发现
    max_in_year = max(report['yearly'].items(), key=lambda x: x[1]['income'])
    max_out_year = max(report['yearly'].items(), key=lambda x: x[1]['expense'])
    max_counter = max(counter_stats.items(), key=lambda x: x[1]['income'] + x[1]['expense'])
    
    report['insights'] = [
        f'收入最高年份: {max_in_year[0]}年 ({max_in_year[1]["income"]:,.0f}元)',
        f'支出最高年份: {max_out_year[0]}年 ({max_out_year[1]["expense"]:,.0f}元)',
        f'主要交易对手: {max_counter[0]}',
        f'10年累计净流出: {grand_expense - grand_income:,.0f}元',
        f'资金主要流向: 手机转账(支出) / 存款+转账(收入)'
    ]
    
    return report, all_data

def print_human_report(report, all_data):
    """打印人类可读报告"""
    print('='*70)
    print('唐斐男银行账户流水分类整理报告')
    print('='*70)
    info = report['account_info']
    print(f'户名: {info["holder"]}')
    print(f'账号: {info["account_number"]} ({info["bank"]})')
    print(f'证件: {info["id_card"]}')
    print(f'统计期间: {info["period"]}')
    print()
    
    print('【一、总体概况】')
    s = report['summary']
    print(f'  总收入: {s["total_income"]:>14,.0f} 元')
    print(f'  总支出: {s["total_expense"]:>14,.0f} 元')
    print(f'  净流入: {s["net_flow"]:>14,.0f} 元')
    print(f'  总笔数: {s["total_transactions"]:>14} 笔')
    print()
    
    print('【二、年度收支明细】')
    print(f'{"年份":<8}{"收入":>14}{"支出":>14}{"净额":>14}{"笔数":>8}')
    print('-'*62)
    for year in range(2017, 2027):
        y = report['yearly'][str(year)]
        print(f'{year:<8}{y["income"]:>14,.0f}{y["expense"]:>14,.0f}{y["net"]:>14,.0f}{y["count"]:>8}')
    print('-'*62)
    print(f'{"合计":<8}{s["total_income"]:>14,.0f}{s["total_expense"]:>14,.0f}{s["net_flow"]:>14,.0f}{s["total_transactions"]:>8}')
    print()
    
    print('【三、交易类型分类】')
    for t, s in sorted(report['type_stats'].items(), key=lambda x: -(x[1]['income']+x[1]['expense'])):
        print(f'  {t}: {s["count"]}笔 | 收入{s["income"]:>12,.0f}元 | 支出{s["expense"]:>12,.0f}元')
    print()
    
    print('【四、交易对手分析】')
    for cp, s in sorted(report['counterparty_stats'].items(), key=lambda x: -(x[1]['income']+x[1]['expense'])):
        net = s['income'] - s['expense']
        print(f'  {cp}: {s["count"]}笔 | 收入{s["income"]:>12,.0f} | 支出{s["expense"]:>12,.0f} | 净{net:>12,.0f}')
    print()
    
    print('【五、关键发现】')
    for insight in report['insights']:
        print(f'  - {insight}')
    print()
    
    # 异常标注
    print('【六、异常提示】')
    for year in range(2017, 2027):
        y = report['yearly'][str(year)]
        if y['expense'] > 500000:
            print(f'  ! {year}年支出异常大额: {y["expense"]:,.0f}元')
        if y['net'] < -200000:
            print(f'  ! {year}年净流出过大: {y["net"]:,.0f}元')
    print()
    
    print('='*70)
    print('报告已保存至: C:\\Users\\Administrator\\Desktop\\流水\\tang\\流水分类报告.json')
    print('同时生成详细交易明细CSV')

def save_csv(all_data):
    """保存详细交易明细CSV"""
    import csv
    output_path = r'C:\Users\Administrator\Desktop\流水\tang\流水明细.csv'
    
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['年份', '日期', '摘要', '金额', '方向', '交易对手', '交易后余额'])
        
        for year in range(2017, 2027):
            for t in all_data[year]['transactions']:
                writer.writerow([
                    year,
                    t['date'],
                    t['summary'],
                    t['amount'],
                    t['direction'],
                    t['counterparty'],
                    t['balance_after']
                ])
    
    print(f'明细CSV已保存至: {output_path}')

if __name__ == '__main__':
    report, all_data = generate_report()
    print_human_report(report, all_data)
    save_csv(all_data)
    
    # 保存JSON报告
    json_path = r'C:\Users\Administrator\Desktop\流水\tang\流水分类报告.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
