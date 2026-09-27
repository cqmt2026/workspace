@echo off
chcp 65001 >nul
cd /d C:\Users\Administrator\.openclaw\workspace\workspace-investment\alice_quant
"C:\Program Files\Python312\python.exe" -c "
import sys
sys.path.insert(0, 'C:\\Users\\Administrator\\.openclaw\\workspace\\workspace-investment\\alice_quant_pkg')
sys.path.insert(0, 'C:\\Users\\Administrator\\.openclaw\\workspace\\workspace-investment\\alice_quant')

# 清理所有缓存
import importlib
for mod in list(sys.modules.keys()):
    if 'alice_quant' in mod:
        del sys.modules[mod]

# 重新导入
import alice_quant

# 执行演示
demo_path = 'C:\\Users\\Administrator\\.openclaw\\workspace\\workspace-investment\\alice_quant\\demos\\full_demo.py'
exec(compile(open(demo_path, encoding='utf-8').read(), demo_path, 'exec'))
"
pause