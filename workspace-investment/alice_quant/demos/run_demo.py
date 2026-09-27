"""AliceQuant 完整演示 - 启动器"""
import sys, os
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\alice_quant_pkg')
os.chdir(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\alice_quant')

import alice_quant
print(f"AliceQuant v0.1.0 loaded from {alice_quant.__file__}")

# 执行演示
demo_path = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\alice_quant\demos\full_demo.py'
exec(open(demo_path, encoding='utf-8').read())