# -*- coding: utf-8 -*-
"""系统健康度全面检查"""
import sys, os, sqlite3, glob

sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\scripts')
from memory_adapter import save, search
from memory_tools import MemoryTools, DOMAIN_DB, GLOBAL_DB

print('=' * 60)
print('系统健康度检查 - 2026-07-12 00:49')
print('=' * 60)

mt = MemoryTools()

# === 1. 分库完整性 ===
print('\n[1/6] 分库完整性')
for domain in ['novel', 'investment', 'social', 'math', 'system']:
    status = mt.get_status(domain)
    healthy = status.get('status') == 'ready'
    if healthy:
        print(f'  [OK] {domain}: {status["memories"]}条 ({os.path.basename(status["db"])})')
    else:
        print(f'  [X] {domain}: 异常 - {status.get("error","")}')

# === 2. 记忆写入测试 ===
print('\n[2/6] 记忆写入测试')
r = save('系统健康度检查测试', category='test', source='healthcheck', domain='system')
if r.get('success'):
    print(f'  [OK] 写入正常 (id={r["memory_id"][:8]})')
else:
    print(f'  [X] 写入失败: {r}')

r = search('健康度检查', top_k=3, domain='system')
if r['count'] > 0:
    print(f'  [OK] 搜索正常 ({r["count"]}条)')
else:
    print(f'  [X] 搜索异常')

# === 3. 质量过滤器 ===
print('\n[3/6] 质量过滤器')
from memory_adapter import _is_junk
test_cases = [
    ('踩坑: contextToken过期，根因是未续期', False),  # 应保留
    ('写入失败: 连接超时', True),  # 应过滤
    ('太短', True),
    ('视频转写: 房屋裂缝检测方法详解', False),
]
all_pass = True
for text, should_junk in test_cases:
    is_junk = _is_junk(text)
    if is_junk == should_junk:
        print(f'  [OK] {"过滤" if is_junk else "保留"}: {text[:30]}')
    else:
        all_pass = False
        print(f'  [X] 预期{"过滤" if should_junk else "保留"}, 实际{"过滤" if is_junk else "保留"}: {text[:30]}')

if not all_pass:
    print('  ⚠️ 过滤器需要调整')

# === 4. 跨域隔离 ===
print('\n[4/6] 跨域隔离')
r = search('抖音', top_k=3, domain='novel')
if r['count'] == 0:
    print(f'  [OK] novel搜抖音: 0条 (隔离正常)')
else:
    print(f'  [WARN] novel搜抖音: {r["count"]}条 (可能污染)')

r = search('验房', top_k=3, domain='investment')
if r['count'] == 0:
    print(f'  [OK] investment搜验房: 0条 (隔离正常)')
else:
    print(f'  [WARN] investment搜验房: {r["count"]}条 (可能污染)')

# === 5. 旧数据清理 ===
print('\n[5/6] 旧数据清理')
if os.path.exists(GLOBAL_DB):
    conn = sqlite3.connect(GLOBAL_DB)
    count = conn.execute("SELECT count(*) FROM memories WHERE is_current=1").fetchone()[0]
    conn.close()
    if count <= 14:
        print(f'  [OK] 全局DB: {count}条 (旧数据未扩散)')
    else:
        print(f'  [WARN] 全局DB: {count}条 (不应继续增长)')
else:
    print('  [OK] 全局DB已不存在')

# === 6. 关键文件完整性 ===
print('\n[6/6] 关键文件完整性')
key_files = [
    r'C:\Users\Administrator\.openclaw\workspace\scripts\memory_adapter.py',
    r'C:\Users\Administrator\.openclaw\workspace\scripts\memory_ref.py',
    r'C:\Users\Administrator\.openclaw\workspace\scripts\memory_recall.py',
    r'C:\Users\Administrator\.openclaw\workspace\memory\memory_tools.py',
    r'C:\Users\Administrator\.openclaw\workspace\scripts\self_learning.py',
    r'C:\Users\Administrator\.openclaw\workspace\scripts\obsidian_sync.py',
]
all_ok = True
for path in key_files:
    exists = os.path.exists(path)
    if exists:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                compile(f.read(), path, 'exec')
            print(f'  [OK] {os.path.basename(path)}')
        except SyntaxError as e:
            all_ok = False
            print(f'  [X] {os.path.basename(path)}: 语法错误 L{e.lineno}')
    else:
        all_ok = False
        print(f'  [X] {os.path.basename(path)}: 文件不存在')

print()
print('=' * 60)
if all_ok:
    print('✅ 系统健康，无严重问题')
else:
    print('⚠️ 存在需要修复的问题')
print('=' * 60)