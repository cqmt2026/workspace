# -*- coding: utf-8 -*-
"""重启 supermemory 服务"""
import subprocess
import time
import socket
import os

print("=== 重启 supermemory 服务 ===")
print()

# 1. 找到 supermemory 启动脚本
ws = r'C:\Users\Administrator\.openclaw\workspace'
supermemory_dir = os.path.join(ws, 'memory', 'supermemory_db')

# 查找启动脚本
start_scripts = []
for root, dirs, files in os.walk(ws):
    if '\\backup\\' in root or '\\workspace-git\\' in root:
        continue
    for f in files:
        if 'start' in f.lower() and f.endswith('.py'):
            start_scripts.append(os.path.join(root, f))
        if 'server' in f.lower() and f.endswith('.py'):
            start_scripts.append(os.path.join(root, f))
        if 'supermemory' in f.lower() and f.endswith('.py'):
            start_scripts.append(os.path.join(root, f))

print(f"找到的启动脚本: {len(start_scripts)}个")
for s in start_scripts[:10]:
    print(f"  {s.replace(ws, '')}")

# 2. 尝试找到 lancedb 或 supermemory 相关进程
print()
print("检查当前进程...")
result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                       capture_output=True, text=True)
print(result.stdout)

# 3. 尝试重启 Gateway（这会重启所有服务）
print()
print("尝试重启 Gateway...")
try:
    subprocess.run(['openclaw', 'restart'], capture_output=True, timeout=10)
    print("Gateway 重启命令已发送")
except Exception as e:
    print(f"重启命令失败: {e}")

# 4. 等待服务启动
print()
print("等待服务启动...")
time.sleep(5)

# 5. 检查端口
print()
print("检查端口 8642...")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(3)
try:
    s.connect(('127.0.0.1', 8642))
    print("端口 8642: OPEN - 服务已启动")
    s.close()
except:
    print("端口 8642: CLOSED - 服务未启动")
