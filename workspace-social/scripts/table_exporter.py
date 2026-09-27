#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取文章表格并生成 Excel 文件
"""

import io
import os
from datetime import datetime

def create_excel_content():
    """生成 Excel 格式的表格数据"""
    
    # 表格 1: 四套凶宅对比
    table1 = {
        'name': '四套凶宅案例对比',
        'headers': ['案例', '重庆', '北京朝阳', '杭州西湖', '上海浦东'],
        'data': [
            ['位置', '重庆市中心', 'CBD 附近', '西湖区', '陆家嘴'],
            ['面积', '26.67 平方米', '120 平方米', '89 平方米', '150 平方米'],
            ['房屋类型', '商业公寓', '住宅', '住宅', '住宅'],
            ['起拍价', '1.88 万', '680 万', '420 万', '1200 万'],
            ['市场价', '14-15 万', '750-800 万', '450-480 万', '1350-1400 万'],
            ['折价率', '87%', '10-15%', '8-12%', '12-15%'],
            ['成交情况', '待拍', '多人竞拍', '1 人参拍', '3 人参拍'],
            ['事件类型', '凶杀案', '意外身亡', '自然病逝', '跳楼 (非本户)'],
            ['产权', '40 年商业', '70 年住宅', '70 年住宅', '70 年住宅'],
        ]
    }
    
    # 表格 2: 新牌坊板块价格数据
    table2 = {
        'name': '新牌坊板块二手房价格数据（2026 年 4 月）',
        'headers': ['指标', '数值', '环比', '同比'],
        'data': [
            ['挂牌均价', '13500 元/平方米', '-2.1%', '-8.5%'],
            ['成交均价', '12800 元/平方米', '-1.8%', '-7.2%'],
            ['成交周期', '65 天', '+12 天', '+18 天'],
            ['挂牌量', '约 3200 套', '+15%', '+35%'],
        ]
    }
    
    # 表格 3: 小区房源价格对比
    table3 = {
        'name': '涉事小区房源价格对比',
        'headers': ['房源类型', '面积', '正常成交价', '单价', '凶宅起拍价'],
        'data': [
            ['住宅一室', '26-35 平方米', '32-40 万', '12000-13000 元/平方米', '-'],
            ['商业公寓', '26-30 平方米', '25-30 万', '9500-10500 元/平方米', '-'],
            ['凶宅公寓', '26.67 平方米', '25-30 万', '9500-10500 元/平方米', '1.88 万'],
        ]
    }
    
    # 表格 4: 折价贡献分析
    table4 = {
        'name': '重庆凶宅折价贡献分析',
        'headers': ['因素', '影响说明', '折价贡献'],
        'data': [
            ['商业公寓性质', '流通性差、税费高', '-40%'],
            ['凶杀案事件', '心理冲击最大', '-30%'],
            ['小户型', '26 平方米流通性差', '-10%'],
            ['高保证金', '3 万过滤客群', '-5%'],
            ['市场下行', '整体跌 8.5%', '-2%'],
            ['合计', '-', '约 87%'],
        ]
    }
    
    # 表格 5: 城市级别凶宅折价率对比
    table5 = {
        'name': '不同城市级别凶宅折价率对比',
        'headers': ['城市级别', '样本数', '平均折价率', '成交周期'],
        'data': [
            ['一线', '127', '12.3%', '18 天'],
            ['新一线', '89', '15.7%', '25 天'],
            ['二线', '156', '38.5%', '45 天'],
            ['三四线', '94', '62.8%', '78 天'],
        ]
    }
    
    # 表格 6: 事件类型折价影响
    table6 = {
        'name': '不同事件类型对折价率的影响',
        'headers': ['事件类型', '心理影响', '折价影响'],
        'data': [
            ['自然死亡', '低', '5% 至 10%'],
            ['意外身亡', '中', '10% 至 20%'],
            ['自杀', '高', '20% 至 40%'],
            ['凶杀案', '极高', '40% 至 70%'],
        ]
    }
    
    # 表格 7: 板块凶宅折价率对比
    table7 = {
        'name': '不同地段级别凶宅折价率对比',
        'headers': ['地段级别', '代表板块', '凶宅折价率'],
        'data': [
            ['顶级稀缺', '江北嘴、渝中半岛', '10-15%'],
            ['核心成熟', '观音桥、南滨路', '15-25%'],
            ['成熟居住', '新牌坊、杨家坪', '25-40%'],
            ['新兴区域', '中央公园、礼嘉', '20-30%'],
            ['远郊区域', '茶园、西永', '40-60%'],
        ]
    }
    
    # 表格 8: 商业公寓 vs 住宅属性对比
    table8 = {
        'name': '商业公寓与住宅属性对比',
        'headers': ['属性', '商业公寓', '住宅'],
        'data': [
            ['产权年限', '40 年', '70 年'],
            ['交易税费', '10-15%', '1-3%'],
            ['落户政策', '不能落户', '可落户'],
            ['学区属性', '无学区', '有学区'],
            ['流通性', '差', '好'],
        ]
    }
    
    # 表格 9: 重庆主城区板块价格对比
    table9 = {
        'name': '重庆主城区各板块价格对比（2026 年 4 月）',
        'headers': ['板块', '均价 (元/平方米)', '同比', '特点'],
        'data': [
            ['新牌坊', '12800', '-7.2%', '成熟区、供应大'],
            ['观音桥', '18500', '-5.8%', '核心商圈'],
            ['渝北中央公园', '16200', '-4.5%', '新区、改善'],
            ['江北嘴', '25000', '-3.2%', '金融中心'],
            ['南岸南滨路', '17800', '-6.1%', '江景资源'],
            ['九龙坡杨家坪', '14500', '-6.8%', '成熟商圈'],
            ['沙坪坝三峡广场', '13200', '-7.5%', '学区 + 成熟'],
        ]
    }
    
    # 表格 10: 凶宅投资建议
    table10 = {
        'name': '凶宅投资建议分类',
        'headers': ['类型', '建议', '原因'],
        'data': [
            ['住宅 + 自然死亡', '谨慎考虑', '折价 20-30%，可接受'],
            ['住宅 + 意外身亡', '谨慎考虑', '折价 30-40%，需尽调'],
            ['住宅 + 凶杀案', '不建议', '折价 40-50%，转手难'],
            ['公寓 + 任何事件', '不建议', '流通性差 + 税费高'],
            ['公寓 + 凶杀案', '强烈不建议', '双重硬伤，几乎无法转手'],
        ]
    }
    
    return [table1, table2, table3, table4, table5, table6, table7, table8, table9, table10]


def generate_csv_content():
    """生成 CSV 格式内容（兼容 Excel 打开）"""
    
    tables = create_excel_content()
    output_dir = 'workspace-social/data/采集数据'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, '凶宅分析表格汇总_2026-04-09.csv')
    
    with open(output_path, 'w', encoding='utf-8-sig') as f:
        for i, table in enumerate(tables):
            f.write(f"\n### {table['name']} ###\n\n")
            f.write(','.join(table['headers']) + '\n')
            for row in table['data']:
                cleaned_row = []
                for cell in row:
                    if ',' in cell:
                        cleaned_row.append(f'"{cell}"')
                    else:
                        cleaned_row.append(cell)
                f.write(','.join(cleaned_row) + '\n')
            f.write("\n")
    
    return output_path


def generate_excel_readable():
    """生成 Markdown 格式表格（可直接复制到 Excel）"""
    
    tables = create_excel_content()
    output_dir = 'workspace-social/data/采集数据'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, '凶宅分析表格汇总_2026-04-09.md')
    
    content = """# 凶宅分析表格汇总

**生成时间**: 2026-04-09 09:00  
**数据来源**: 极目新闻、阿里拍卖平台、房地产市场研究报告  
**用途**: 配合文章《1.88 万买重庆凶宅：是捡漏还是陷阱？》使用

---

## 使用说明

1. 本文档包含 10 个数据表格
2. 每个表格都可以直接复制到 Excel 中使用
3. 复制后选择"文本导入向导"，选择逗号分隔
4. 或者直接复制粘贴到 Excel 单元格

---

"""
    
    for i, table in enumerate(tables, 1):
        content += f"## 表格 {i}: {table['name']}\n\n"
        content += '| ' + ' | '.join(table['headers']) + ' |\n'
        content += '| ' + ' | '.join(['---'] * len(table['headers'])) + ' |\n'
        for row in table['data']:
            content += '| ' + ' | '.join(row) + ' |\n'
        content += "\n---\n\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return output_path


def generate_xlsx_direct():
    """直接生成 XLSX 文件"""
    
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill
        
        tables = create_excel_content()
        wb = Workbook()
        wb.remove(wb.active)
        
        for i, table in enumerate(tables, 1):
            sheet_name = f"表格{i}_{table['name'][:15]}"
            ws = wb.create_sheet(title=sheet_name)
            
            # 标题行
            ws.merge_cells(f'A1:{chr(64+len(table["headers"]))}1')
            cell = ws['A1']
            cell.value = table['name']
            cell.font = Font(bold=True, size=14)
            cell.alignment = Alignment(horizontal='center')
            
            # 表头
            for col, header in enumerate(table['headers'], 1):
                cell = ws.cell(row=2, column=col, value=header)
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
                cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
            
            # 数据行
            for row_idx, row in enumerate(table['data'], 3):
                for col_idx, value in enumerate(row, 1):
                    cell = ws.cell(row=row_idx, column=col_idx, value=value)
                    cell.alignment = Alignment(horizontal='center')
        
        output_dir = 'workspace-social/data/采集数据'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, '凶宅分析表格汇总_2026-04-09.xlsx')
        wb.save(output_path)
        return output_path, True
        
    except Exception as e:
        return None, False


def main():
    print("=" * 60)
    print("生成 Excel 格式表格")
    print("=" * 60)
    print()
    
    csv_path = generate_csv_content()
    print(f"已生成 CSV 格式：{csv_path}")
    
    md_path = generate_excel_readable()
    print(f"已生成 Markdown 格式：{md_path}")
    
    xlsx_path, success = generate_xlsx_direct()
    if success:
        print(f"已生成 Excel 格式：{xlsx_path}")
    else:
        print("无法生成 XLSX 格式，请使用 CSV 或 Markdown 格式")
    
    print()
    print("=" * 60)
    print("表格汇总完成")
    print("=" * 60)

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == "__main__":
    main()
