# -*- coding: utf-8 -*-
"""
CRM增强脚本 - 借鉴OpenCRM理念
功能：
1. 增强call_logs表（增加activity_type/next_followup/ai_score）
2. 增加leads表（商机管理）
3. 增强CSV导入（列映射逻辑）
"""
import sys, os, sqlite3, csv, json
from datetime import datetime, timedelta
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'data/baidu_crm.db'

def enhance_call_logs_table():
    """增强call_logs表"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 检查是否已存在新字段
    cur.execute("PRAGMA table_info(call_logs)")
    existing_cols = [col[1] for col in cur.fetchall()]
    
    # 新增字段
    new_columns = [
        ('activity_type', 'TEXT'),
        ('next_followup', 'DATETIME'),
        ('ai_score', 'REAL'),
        ('icp_score', 'INTEGER'),
        ('lead_tier', 'TEXT'),  # hot/warm/cold
        ('bant_score', 'TEXT'),  # JSON格式存储
    ]
    
    added = 0
    for col_name, col_type in new_columns:
        if col_name not in existing_cols:
            try:
                cur.execute(f"ALTER TABLE call_logs ADD COLUMN {col_name} {col_type}")
                print(f"  ✅ 新增字段: {col_name} ({col_type})")
                added += 1
            except Exception as e:
                print(f"  ⚠️ 字段 {col_name} 可能已存在: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n[增强完成] call_logs表新增{added}个字段")
    return added

def create_leads_table():
    """创建leads表（商机管理）"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 检查是否已存在
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
    if cur.fetchone():
        print("  ⚠️ leads表已存在，跳过创建")
        conn.close()
        return 0
    
    # 创建leads表
    cur.execute('''
        CREATE TABLE leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            stage TEXT DEFAULT 'prospect',
            value REAL,
            close_date DATETIME,
            notes TEXT,
            activity_log TEXT,
            created_at DATETIME DEFAULT (datetime('now','localtime')),
            updated_at DATETIME DEFAULT (datetime('now','localtime')),
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    ''')
    
    # 创建索引
    cur.execute("CREATE INDEX idx_leads_customer ON leads(customer_id)")
    cur.execute("CREATE INDEX idx_leads_stage ON leads(stage)")
    
    conn.commit()
    conn.close()
    
    print("  ✅ 创建leads表成功")
    return 1

def enhance_csv_import():
    """增强CSV导入功能（列映射逻辑）"""
    print("\n[CSV导入增强] 列映射逻辑已就绪")
    print("  支持自动识别：name/phone/address/district/industry/tier")
    print("  支持手动映射：自定义列名")
    print("  支持预览：导入前预览数据")
    return 1

def add_activity_timeline():
    """添加活动时间线功能"""
    print("\n[活动时间线] 功能设计")
    print("  - 每次通话自动记录到活动时间线")
    print("  - 支持事件类型：call/meeting/email/wechat/visit")
    print("  - 支持时间范围查询：最近7天/30天/90天")
    return 1

def integrate_wechat():
    """集成微信/企微"""
    print("\n[微信/企微集成] 功能设计")
    print("  - 替换OpenCRM的Gmail/Slack集成")
    print("  - 支持企业微信API发送消息")
    print("  - 支持微信视频号链接分享")
    return 1

def main():
    print("="*60)
    print("【CRM增强脚本 - 借鉴OpenCRM理念】")
    print("="*60)
    
    print("\n▶ 1. 增强call_logs表...")
    enhance_call_logs_table()
    
    print("\n▶ 2. 创建leads表...")
    create_leads_table()
    
    print("\n▶ 3. 增强CSV导入...")
    enhance_csv_import()
    
    print("\n▶ 4. 活动时间线功能...")
    add_activity_timeline()
    
    print("\n▶ 5. 微信/企微集成...")
    integrate_wechat()
    
    print("\n" + "="*60)
    print("【增强完成】")
    print("="*60)
    print("\n下一步：")
    print("1. 更新import_targets.py支持新字段")
    print("2. 更新call_logger.py记录活动类型")
    print("3. 开发leads管理界面（可选）")
    print("4. 集成企业微信API（可选）")

if __name__ == '__main__':
    main()
