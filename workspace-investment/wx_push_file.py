import sys
sys.path.insert(0, '.')
# Read text from summary file
with open('memory/推送/top10_summary.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Import wx_push module and call its main logic
import importlib.util
spec = importlib.util.spec_from_file_location('wx_push', 'scripts/wx_push.py')
mod = importlib.util.module_from_spec(spec)
# Override sys.argv
saved_argv = sys.argv
sys.argv = ['wx_push.py', text]
try:
    spec.loader.exec_module(mod)
finally:
    sys.argv = saved_argv
