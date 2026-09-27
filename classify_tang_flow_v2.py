# -*- coding: utf-8 -*-
"""唐斐男银行账户流水分类整理脚本 - 完整版"""
import pdfplumber, re, json
from collections import defaultdict

def extract_all_transactions():
    """提取所有年份的交易数据"""
    all_transactions = []
    
    for year in range(2017, 2027):
        path = rf'C:\Users\Administrator\Desktop\流水\tang\{year}.pdf'
        try:
            with pdfplumber.open(path) as pdf:
                all_text = ''
                for page in pdf.pages:
                    t = page.extract_text()
                    if t: all_text += t + '\n'
                
                trans_lines = [l for l in all_text.split('\n') if l.strip().startswith('卡 ')]
                
                for line in trans_lines:
                    amounts = re.findall(r'[-]?\s*[\d,]+\.\d{2}', line)
                    date_match = re.search(r'(\d{4}/\d{2}/\d{2})', line)
                    summary_match = re.search(r'(手机转账|转账|消费|取现|利息|存款|存入|支取)', line)
                    name_match = re.search(r'([\u4e00-\u9fa5]+?)/\d+', line)
                    
                    if len(amounts) >= 2:
                        amount = float(amounts[0].replace(' ', '').replace(',', ''))
                        all_transactions.append({
                            'year': year,
                            'date': date_match.group(1) if date_match else '',
                            'summary': summary_match.group(1) if summary_match else '其他',
                            'amount': amount,
                            'counterparty': name_match.group(1) if name_match else '未知'
                        })
        except Exception as e:
            print(f'{year}年读取错误: {e}')
    
    return all_transactions

def main():
    transactions = extract_all_transactions()
    
    # 分类
    income_trans = [t for t in transactions if t['amount'] > 0]
    expense_trans = [t for t in transactions if t['amount'] < 0]
    
    total_income = sum(t['amount'] for t in income_trans)
    total_expense = sum(abs(t['amount']) for t in expense_trans)
    
    print('='*70)
    print('唐斐男银行账户流水分类整理报告（完整版）')
    print('='*70)
    print(f'账户: 6216911100376933 (民生银行)')
    print(f'统计期间: 2017-2026年，共{len(transactions)}笔交易')
    print()
    
    # ========== 一、收入汇总 ==========
    print('='*70)
    print('【一、收入汇总】')
    print('='*70)
    print(f'总收入: {total_income:,.0f} 元 ({len(income_trans)}笔)')
    print()
    
    # 按类型统计收入
    income_by_type = defaultdict(lambda: {'count': 0, 'amount': 0})
    for t in income_trans:
        income_by_type[t['summary']]['count'] += 1
        income_by_type[t['summary']]['amount'] += t['amount']
    
    print('按交易类型:')
    for t, s in sorted(income_by_type.items(), key=lambda x: -x[1]['amount']):
        pct = s['amount'] / total_income * 100
        print(f'  {t}: {s["count"]}笔, {s["amount"]:,.0f}元 ({pct:.1f}%)')
    print()
    
    # 按年份统计收入
    income_by_year = defaultdict(lambda: {'count': 0, 'amount': 0})
    for t in income_trans:
        income_by_year[t['year']]['count'] += 1
        income_by_year[t['year']]['amount'] += t['amount']
    
    print('按年份:')
    print(f'  {"年份":<8}{"笔数":>8}{"收入金额":>14}{"占比":>8}')
    print('  ' + '-'*42)
    for y in sorted(income_by_year.keys()):
        s = income_by_year[y]
        pct = s['amount'] / total_income * 100
        print(f'  {y}年{s["count"]:>8}{s["amount"]:>14,.0f}{pct:>7.1f}%')
    print()
    
    # 收入TOP10
    income_top10 = sorted(income_trans, key=lambda x: -x['amount'])[:10]
    print('收入TOP10最大交易:')
    for i, t in enumerate(income_top10, 1):
        print(f'  {i:2}. {t["date"]} {t["summary"]} {t["amount"]:>10,.0f}元')
    print()
    
    # ========== 二、支出汇总 ==========
    print('='*70)
    print('【二、支出汇总】')
    print('='*70)
    print(f'总支出: {total_expense:,.0f} 元 ({len(expense_trans)}笔)')
    print()
    
    # 按类型统计支出
    expense_by_type = defaultdict(lambda: {'count': 0, 'amount': 0})
    for t in expense_trans:
        expense_by_type[t['summary']]['count'] += 1
        expense_by_type[t['summary']]['amount'] += abs(t['amount'])
    
    print('按交易类型:')
    for t, s in sorted(expense_by_type.items(), key=lambda x: -x[1]['amount']):
        pct = s['amount'] / total_expense * 100
        print(f'  {t}: {s["count"]}笔, {s["amount"]:,.0f}元 ({pct:.1f}%)')
    print()
    
    # 按年份统计支出
    expense_by_year = defaultdict(lambda: {'count': 0, 'amount': 0})
    for t in expense_trans:
        expense_by_year[t['year']]['count'] += 1
        expense_by_year[t['year']]['amount'] += abs(t['amount'])
    
    print('按年份:')
    print(f'  {"年份":<8}{"笔数":>8}{"支出金额":>14}{"占比":>8}')
    print('  ' + '-'*42)
    for y in sorted(expense_by_year.keys()):
        s = expense_by_year[y]
        pct = s['amount'] / total_expense * 100
        print(f'  {y}年{s["count"]:>8}{s["amount"]:>14,.0f}{pct:>7.1f}%')
    print()
    
    # 支出TOP10
    expense_top10 = sorted(expense_trans, key=lambda x: abs(x['amount']))[:10]
    print('支出TOP10最大交易:')
    for i, t in enumerate(expense_top10, 1):
        print(f'  {i:2}. {t["date"]} {t["summary"]} {abs(t["amount"]):>10,.0f}元')
    print()
    
    # ========== 三、收支对比 ==========
    print('='*70)
    print('【三、收支对比】')
    print('='*70)
    print(f'  {"指标":<12}{"金额":>16}{"备注":>12}')
    print('  ' + '-'*44)
    print(f'  {"总收入":<12}{total_income:>16,.0f}元')
    print(f'  {"总支出":<12}{total_expense:>16,.0f}元')
    print(f'  {"净流出":<12}{total_income - total_expense:>16,.0f}元 {"(累计)" if total_income - total_expense < 0 else ""}')
    print()
    
    # 年度净额
    print('年度净额:')
    print(f'  {"年份":<8}{"收入":>14}{"支出":>14}{"净额":>14}{"状态":>8}')
    print('  ' + '-'*62)
    for y in range(2017, 2027):
        inc = income_by_year.get(y, {}).get('amount', 0)
        exp = expense_by_year.get(y, {}).get('amount', 0)
        net = inc - exp
        status = '净流入' if net > 0 else ('净流出' if net < 0 else '持平')
        print(f'  {y}年{inc:>14,.0f}{exp:>14,.0f}{net:>14,.0f}{status:>8}')
    print()
    
    # ========== 四、月度分布 ==========
    print('='*70)
    print('【四、月度收支分布】')
    print('='*70)
    
    monthly_income = defaultdict(float)
    monthly_expense = defaultdict(float)
    for t in transactions:
        month = t['date'][5:7] if t['date'] else ''
        key = f'{t["year"]}-{month}'
        if t['amount'] > 0:
            monthly_income[key] += t['amount']
        else:
            monthly_expense[key] += abs(t['amount'])
    
    print(f'  {"年月":<10}{"收入":>12}{"支出":>12}{"净额":>12}')
    print('  ' + '-'*50)
    for year in range(2017, 2027):
        for month in range(1, 13):
            key = f'{year}-{month:02d}'
            inc = monthly_income.get(key, 0)
            exp = monthly_expense.get(key, 0)
            if inc > 0 or exp > 0:
                net = inc - exp
                print(f'  {key:<10}{inc:>12,.0f}{exp:>12,.0f}{net:>12,.0f}')
    print()
    
    # ========== 五、关键发现 ==========
    print('='*70)
    print('【五、关键发现】')
    print('='*70)
    
    # 收入来源分析
    print('1. 收入来源分析:')
    deposit_income = income_by_type.get('存款', {}).get('amount', 0)
    transfer_income = income_by_type.get('转账', {}).get('amount', 0)
    print(f'   - 银行存款: {deposit_income:,.0f}元 ({deposit_income/total_income*100:.1f}%)')
    print(f'   - 他行转账: {transfer_income:,.0f}元 ({transfer_income/total_income*100:.1f}%)')
    print()
    
    # 支出去向分析
    print('2. 支出去向分析:')
    mobile_expense = expense_by_type.get('手机转账', {}).get('amount', 0)
    print(f'   - 手机转账支出: {mobile_expense:,.0f}元 ({mobile_expense/total_expense*100:.1f}%)')
    print()
    
    # 年度趋势
    print('3. 年度趋势:')
    max_income_year = max(income_by_year.items(), key=lambda x: x[1]['amount'])
    max_expense_year = max(expense_by_year.items(), key=lambda x: x[1]['amount'])
    print(f'   - 收入峰值: {max_income_year[0]}年 ({max_income_year[1]["amount"]:,.0f}元)')
    print(f'   - 支出峰值: {max_expense_year[0]}年 ({max_expense_year[1]["amount"]:,.0f}元)')
    print()
    
    # 异常标注
    print('4. 异常提示:')
    for y in range(2017, 2027):
        inc = income_by_year.get(y, {}).get('amount', 0)
        exp = expense_by_year.get(y, {}).get('amount', 0)
        net = inc - exp
        if exp > 500000:
            print(f'   ! {y}年支出异常大额: {exp:,.0f}元')
        if net < -200000:
            print(f'   ! {y}年净流出过大: {net:,.0f}元')
    print()
    
    print('='*70)

if __name__ == '__main__':
    main()
