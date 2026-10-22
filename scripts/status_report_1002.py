"""系统状态检查报告 - 2026-10-02"""
import os
import psutil
import json
import urllib.request
from datetime import datetime

print("=" * 60)
print("系统状态检查报告")
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# 1. 系统资源
print("\n【系统资源】")
m = psutil.virtual_memory()
print(f"内存: {m.available/1024**3:.1f}GB 可用 / {m.total/1024**3:.1f}GB 总计 ({m.percent}% 使用)")

for letter in ['C', 'D']:
    d = psutil.disk_usage(letter + ':')
    print(f"{letter}盘: {d.free/1024**3:.1f}GB 可用 / {d.total/1024**3:.1f}GB 总计 ({d.percent}% 使用)")

# 2. Gateway状态
print("\n【Gateway】")
try:
    r = urllib.request.urlopen('http://127.0.0.1:18789/health', timeout=5)
    data = json.loads(r.read())
    print(f"状态: {data.get('status', '?')} (ok={data.get('ok')})")
except Exception as e:
    print(f"状态: 异常 - {e}")

# 3. 关键文件
print("\n【关键文件】")
base = r'C:\Users\Administrator\.openclaw\workspace'
for f in ['MEMORY.md', 'AGENTS.md', 'SOUL.md', 'USER.md']:
    path = os.path.join(base, f)
    exists = os.path.isfile(path)
    mtime = ''
    if exists:
        t = os.path.getmtime(path)
        mtime = datetime.fromtimestamp(t).strftime('%m-%d')
    print(f"  {f}: {'OK' if exists else 'MISSING'} {mtime}")

# 4. 子系统
print("\n【子系统目录】")
subdirs = {
    '投资': r'C:\Users\Administrator\.openclaw\workspace-investment',
    '小说': r'C:\Users\Administrator\.openclaw\workspace-novel',
    '自媒体': r'C:\Users\Administrator\.openclaw\workspace-social',
    '数学动画': r'C:\Users\Administrator\.openclaw\workspace-math',
    '地图热点': r'C:\Users\Administrator\.openclaw\workspace-maphot',
    '微信小程序': r'C:\Users\Administrator\.openclaw\workspace-weixin',
}
for name, path in subdirs.items():
    exists = os.path.isdir(path)
    print(f"  {name}: {'OK' if exists else 'MISSING'}")

# 5. 投资系统
print("\n【投资系统】")
inv_dir = r'C:\Users\Administrator\.openclaw\workspace-investment'
if os.path.exists(inv_dir):
    # MX模块
    mx_module = os.path.join(inv_dir, 'modules', 'mx_xuangu.py')
    print(f"  MX模块: {'OK' if os.path.exists(mx_module) else 'MISSING'}")
    
    # 数据
    data_dir = os.path.join(inv_dir, 'data')
    if os.path.exists(data_dir):
        data_files = os.listdir(data_dir)
        print(f"  数据文件: {len(data_files)} 个")
        for f in data_files[:5]:
            fp = os.path.join(data_dir, f)
            if os.path.isfile(fp):
                size = os.path.getsize(fp)
                print(f"    {f}: {size/1024:.1f}KB")

# 6. Obsidian
print("\n【Obsidian】")
obsidian = r'F:\Obsidian\Jarvis'
print(f"  知识库: {'OK' if os.path.isdir(obsidian) else 'MISSING'}")

# 7. 进程
print("\n【进程】")
for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
    try:
        n = proc.info['name'].lower()
        if 'openclaw' in n or 'node' in n:
            print(f"  PID {proc.info['pid']}: {proc.info['name']} CPU:{proc.info['cpu_percent']}%")
    except:
        pass

print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)
