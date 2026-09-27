# -*- coding: utf-8 -*-
"""腾讯地图Key管理 - 使用环境变量保护安全"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

# 从环境变量读取Key，避免明文硬编码
TX_KEY = os.environ.get('TX_MAP_KEY', '')

if not TX_KEY:
    print("❌ 未配置TX_MAP_KEY环境变量")
    print("请执行以下命令设置：")
    print("  set TX_MAP_KEY=你的完整Key")
    print("  或添加到系统环境变量")
    sys.exit(1)

print(f"✅ 已加载腾讯Key（长度:{len(TX_KEY)}字符）")
print(f"   显示前4位: {TX_KEY[:4]}...")
print(f"   显示后4位: ...{TX_KEY[-4:]}")