"""Clean up supermemory files and config"""
import json, os, sqlite3

os.environ['PYTHONIOENCODING'] = 'utf-8'

# 1. 清理配置文件
cfg_path = os.path.expanduser('~/.openclaw/openclaw.json')
f = open(cfg_path, 'r', encoding='utf-8')
cfg = json.load(f)
f.close()

print('Memory slot:', cfg['plugins']['slots']['memory'])

if 'openclaw-supermemory' in cfg['plugins']['entries']:
    del cfg['plugins']['entries']['openclaw-supermemory']
    print('Removed openclaw-supermemory from config')

f = open(cfg_path, 'w', encoding='utf-8')
json.dump(cfg, f, ensure_ascii=False, indent=2)
f.close()

# 2. 清理文件
files_to_clean = [
    os.path.expanduser('~/.openclaw/supermemory.log'),
    os.path.expanduser('~/.openclaw/workspace/memory/supermemory.db'),
    os.path.expanduser('~/.openclaw/workspace/memory/supermemory.db.bak'),
    os.path.expanduser('~/.openclaw/workspace/memory/数据/supermemory.db'),
    os.path.expanduser('~/.openclaw/workspace/scripts/start_supermemory.bat'),
    os.path.expanduser('~/.openclaw/workspace/scripts/test_supermemory.py'),
    os.path.expanduser('~/.openclaw/workspace/scripts/check_supermemory_db.py'),
    os.path.expanduser('~/.openclaw/workspace/scripts/switch_memory.py'),
]

for fp in files_to_clean:
    if os.path.exists(fp):
        os.remove(fp)
        print('Deleted:', fp)
    else:
        print('Not found:', fp)

# 3. 清理测试记忆
db = os.path.expanduser('~/.openclaw/workspace/memory/memory_system.db')
if os.path.exists(db):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("DELETE FROM memories WHERE text LIKE 'Supermemory test%'")
    conn.commit()
    print('Cleaned test memories:', c.rowcount, 'rows')
    conn.close()

print('Done')