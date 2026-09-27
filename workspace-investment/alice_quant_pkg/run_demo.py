import sys
sys.path.insert(0, 'C:\\Users\\Administrator\\.openclaw\\workspace\\workspace-investment\\alice_quant_pkg')
import alice_quant
print('AliceQuant loaded')

# 逐个导入模块确保加载最新代码
import importlib
for name in ['alice_quant.models.evaluator']:
    if name in sys.modules:
        importlib.reload(sys.modules[name])

# 运行演示
demo = r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\alice_quant\demos\full_demo.py'
with open(demo, encoding='utf-8') as f:
    code = f.read()
exec(code)