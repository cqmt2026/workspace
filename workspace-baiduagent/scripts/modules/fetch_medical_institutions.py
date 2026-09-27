"""
从公开数据源抓取重庆民营医院和体检中心名单
数据来源：
1. 重庆市卫健委官网公示
2. 全国医疗机构查询平台
3. 第三方企业数据平台（如有公开API）

注意：本脚本需要手动执行，因为涉及网站访问限制
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3
import requests
from lxml import etree
import time
import json
from datetime import datetime

# 数据库连接
DB_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\baidu_crm.db'

def fetch_cq_health_commission():
    """尝试从重庆市卫健委获取数据"""
    print("=== 尝试从重庆市卫健委获取数据 ===")
    
    # 卫健委官网URL
    urls = [
        "https://wsjkw.cq.gov.cn/wsjkw/ywgz/202307/t20230712_12246168.html",  # 医疗机构公示
        "https://wsjkw.cq.gov.cn/wsjkw/ywgz/ylws/",  # 医政医管
    ]
    
    for url in urls:
        try:
            resp = requests.get(url, timeout=10)
            print(f"访问 {url} 状态码: {resp.status_code}")
            if resp.status_code == 200:
                print(f"页面标题: {resp.text[:500]}")
        except Exception as e:
            print(f"访问失败: {e}")
    
    return []

def fetch_national_medical_institutions():
    """从国家医疗机构查询平台获取"""
    print("\n=== 尝试从国家医疗机构查询平台获取 ===")
    
    # 国家卫健委医疗机构查询
    url = "http://www.nhc.gov.cn/"
    try:
        resp = requests.get(url, timeout=10)
        print(f"访问国家卫健委状态码: {resp.status_code}")
    except Exception as e:
        print(f"访问失败: {e}")
    
    return []

def manual_data_entry():
    """手动录入数据（需要用户提供）"""
    print("\n=== 手动录入数据 ===")
    print("请提供以下数据源之一：")
    print("1. 重庆市卫健委公开的医疗机构名录（Excel/CSV格式）")
    print("2. 爱企查/天眼查导出的重庆医院/体检中心名单")
    print("3. 其他公开数据源链接")
    return []

def save_to_db(data_list):
    """保存数据到数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    saved_count = 0
    for item in data_list:
        try:
            # 检查是否已存在
            c.execute("SELECT id FROM customers WHERE name = ?", (item['name'],))
            if c.fetchone():
                continue
            
            c.execute("""
                INSERT INTO customers (name, industry, phone, address, district, source, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item['name'],
                item.get('industry', '医院'),
                item.get('phone', ''),
                item.get('address', ''),
                item.get('district', ''),
                '美团医疗_手动录入',
                '待联系',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            saved_count += 1
        except Exception as e:
            print(f"保存失败 {item.get('name')}: {e}")
    
    conn.commit()
    conn.close()
    print(f"成功保存 {saved_count} 条数据")
    return saved_count

if __name__ == "__main__":
    print("重庆民营医院/体检中心数据抓取工具")
    print("=" * 50)
    
    # 尝试自动抓取
    data = fetch_cq_health_commission()
    if not data:
        data = fetch_national_medical_institutions()
    
    # 如果自动抓取失败，提示手动录入
    if not data:
        print("\n自动抓取未获取到数据，请手动提供数据源")
        data = manual_data_entry()
    
    # 保存到数据库
    if data:
        save_to_db(data)
        print(f"\n总计导入 {len(data)} 条数据")
    else:
        print("\n未获取到有效数据，请手动录入")
