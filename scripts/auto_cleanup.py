"""
C盘清理脚本 - 每周自动执行
清理内容：npm-cache/uv/pip/CrashDumps/Temp/obsidian-updater/pirate-updater/node-gyp + cron_run_logs
"""
import io
import os, shutil, subprocess, sys, sqlite3

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


ADMIN_LOCAL = r'C:\Users\Administrator\AppData\Local'
WSZ_LOCAL = r'C:\Users\wsz\AppData\Local'

TARGETS = [
    ('pip', 'pip缓存'),
    ('CrashDumps', '崩溃转储'),
    ('obsidian-updater', 'Obsidian安装包'),
    ('pirate-updater', 'pirate安装包'),
    ('node-gyp', 'node-gyp缓存'),
]

# 额外缓存清理（可安全删除的缓存目录）
CACHE_TARGETS = [
    (r'C:\Users\Administrator\AppData\Local\uv\cache', 'uv cache'),
    (r'C:\Users\Administrator\AppData\Roaming\douyin', 'douyin缓存'),
    (r'C:\Users\Administrator\AppData\Local\OpenAI', 'OpenAI缓存'),
    (r'C:\Users\Administrator\AppData\Local\camoufox', 'camoufox缓存'),
]

def get_size(path):
    try:
        return sum(os.path.getsize(os.path.join(r,f)) for r,ds,fs in os.walk(path) for f in fs)
    except: return 0

def delete_dir(path, name):
    if not os.path.exists(path): return 0
    size = get_size(path)
    try:
        shutil.rmtree(path)
        return size
    except Exception as e:
        print(f'  ERROR {name}: {e}')
        return 0

def run_npm_cache_clean():
    try:
        r = subprocess.run(['npm','cache','clean','--force'],
                          capture_output=True, text=True, timeout=30)
        return 'ok' in r.stdout.lower() or 'cleaned' in r.stdout.lower()
    except: return False

results = []
total_freed = 0

# Admin user targets
for dirname, label in TARGETS:
    path = os.path.join(ADMIN_LOCAL, dirname)
    freed = delete_dir(path, label)
    if freed > 0:
        total_freed += freed
        results.append(f'{label}: {freed//1024//1024}MB')

# npm cache
path = os.path.join(ADMIN_LOCAL, 'npm-cache')
if os.path.exists(path):
    freed = get_size(path)
    ok = run_npm_cache_clean()
    if not ok:
        freed = delete_dir(path, 'npm-cache')
    if freed > 0:
        total_freed += freed
        results.append(f'npm-cache: {freed//1024//1024}MB')

# Temp
path = os.path.join(ADMIN_LOCAL, 'Temp')
if os.path.exists(path):
    try:
        for r, ds, fs in os.walk(path):
            for f in fs:
                try: os.remove(os.path.join(r, f))
                except: pass
        freed = get_size(path)
        if freed > 0:
            results.append(f'Temp残留: {freed//1024//1024}MB')
    except: pass

# wsx user
path = os.path.join(WSZ_LOCAL, 'npm-cache')
if os.path.exists(path):
    freed = delete_dir(path, 'wsz-npm-cache')
    if freed > 0:
        total_freed += freed
        results.append(f'wsz-npm-cache: {freed//1024//1024}MB')

path = os.path.join(WSZ_LOCAL, 'Temp')
if os.path.exists(path):
    try:
        for r, ds, fs in os.walk(path):
            for f in fs:
                try: os.remove(os.path.join(r, f))
                except: pass
    except: pass

# === Cache cleanup ===
for cache_path, cache_label in CACHE_TARGETS:
    if os.path.exists(cache_path):
        freed = delete_dir(cache_path, cache_label)
        if freed > 0:
            total_freed += freed
            results.append(f'{cache_label}: {freed//1024//1024}MB')

# === Database cleanup ===
db_path = r'C:\Users\Administrator\.openclaw\state\openclaw.sqlite'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM cron_run_logs WHERE created_at < datetime("now", "-30 days")')
        deleted = cur.rowcount
        if deleted > 0:
            conn.commit()
            results.append(f'cron_run_logs清理: {deleted}行')
    except: pass
    try:
        cur.execute('VACUUM')
        results.append('DB: vacuumed')
    except: pass
    conn.close()

# Report
import shutil as s
_, _, free = s.disk_usage('C:')
print(f'=== C盘清理报告 ===')
for r in results:
    print(f'  {r}')
print(f'共释放: {total_freed//1024//1024}MB')
print(f'C盘当前剩余: {free//1024**3}GB')
