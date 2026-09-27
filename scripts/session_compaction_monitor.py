# -*- coding: utf-8 -*-
"""
Session Compaction Monitor - 每5分钟检查token计数器健康度
检测token计数器损坏（tokensBefore=1000001而非真实值）
在 compaction 触发前强制写 memory 并备份 session
"""
import os, json, datetime, time, shutil
import io

SESSIONS_JSON = r'C:\Users\Administrator\.openclaw\agents\main\sessions\sessions.json'
BACKUP_DIR = r'C:\Users\Administrator\.openclaw\workspace\memory\session_backup'
os.makedirs(BACKUP_DIR, exist_ok=True)

def estimate_real_tokens(session_file):
    if not os.path.exists(session_file):
        return 0
    size = os.path.getsize(session_file)
    return int(size * 0.25)

def check_token_counter():
    with open(SESSIONS_JSON, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)

    main = data.get('agent:main:main', {})
    context_tokens = main.get('contextTokens', 0)
    total_tokens = main.get('totalTokens', 0)
    session_file = main.get('sessionFile', '')
    compaction_count = main.get('compactionCount', 0)
    cp_list = main.get('compactionCheckpoints', [])

    real_tokens = estimate_real_tokens(session_file) if session_file else 0

    alerts = []
    actions = []

    # 检测1: 当前 contextTokens 疑似固定值1M（MiniMax每次compaction后写入的损坏值）
    # 情况A: real_tokens 很小（<200K），文件很小但计数器报告1M → 明确损坏
    # 情况B: real_tokens > contextTokens → 真实值比报告值还高，计数器肯定错了
    if context_tokens == 1000000:
        if real_tokens < 200000:
            alerts.append('TOKEN_CORRUPT:tokensBefore={} (固定1M值，real~{}，疑似损坏)'.format(context_tokens, real_tokens))
            actions.append('force_memory_flush')
            actions.append('backup_session')
            actions.append('fix_counter')
        elif real_tokens > context_tokens:
            alerts.append('TOKEN_CORRUPT:tokensBefore={} (固定1M值，real~{}，真实值超过报告值，计数器损坏)'.format(context_tokens, real_tokens))
            actions.append('force_memory_flush')
            actions.append('backup_session')
            actions.append('fix_counter')

    # 检测1b: contextTokens 接近1M且real_tokens也很高（真实满载，不误报）
    if context_tokens > 900000 and real_tokens > 0 and real_tokens > context_tokens:
        alerts.append('TOKEN_MISMATCH:contextTokens={} vs real~{}'.format(context_tokens, real_tokens))
        actions.append('force_memory_flush')
        actions.append('backup_session')
        actions.append('fix_counter')

    # 检测2: compactionCount 未同步
    actual_cp = len(cp_list)
    if compaction_count != actual_cp:
        alerts.append('COMPACTION_COUNT_SYNC:compactionCount={} but {} checkpoints'.format(compaction_count, actual_cp))
        actions.append('fix_counter')

    # 检测3: contextTokens 接近触发阈值（>80% window）且 real 也很高
    if context_tokens > 800000 and real_tokens > 700000:
        alerts.append('TOKEN_HIGH:contextTokens={} (接近compaction阈值980K)'.format(context_tokens))
        actions.append('force_memory_flush')

    return {
        'alerts': alerts,
        'actions': actions,
        'contextTokens': context_tokens,
        'totalTokens': total_tokens,
        'realTokens': real_tokens,
        'compactionCount': compaction_count,
        'checkpointCount': actual_cp,
        'sessionFile': session_file
    }

def force_memory_flush():
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    log_dir = r'C:\Users\Administrator\.openclaw\workspace\memory\日志'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, '{}.md'.format(today))

    with open(SESSIONS_JSON, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)
    main = data.get('agent:main:main', {})
    session_file = main.get('sessionFile', '')

    content_lines = []
    if session_file and os.path.exists(session_file):
        with open(session_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        for line in lines[-50:]:
            try:
                obj = json.loads(line)
                if obj.get('type') == 'message':
                    msg = obj.get('message', {})
                    role = msg.get('role', '')
                    c = msg.get('content', '')
                    if isinstance(c, list):
                        for item in c:
                            if isinstance(item, dict) and item.get('type') == 'text':
                                txt = item.get('text', '')[:200]
                                if txt.strip():
                                    content_lines.append(role + ': ' + txt)
                    elif isinstance(c, str) and c.strip():
                        content_lines.append(role + ': ' + c[:200])
            except Exception as e:
                print("[CompactionMonitor] error: %s" % e)

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write('\n\n---\n')
        f.write('## Compaction Monitor 触发写入 {}\n'.format(
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        for line in content_lines[-20:]:
            f.write(line + '\n')
    return log_file

def backup_session():
    with open(SESSIONS_JSON, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)
    main = data.get('agent:main:main', {})
    session_file = main.get('sessionFile', '')
    if not session_file or not os.path.exists(session_file):
        return None
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = 'session_precompact_{}.jsonl'.format(ts)
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    shutil.copy2(session_file, backup_path)
    return backup_path

def fix_counter():
    with open(SESSIONS_JSON, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)
    main = data.get('agent:main:main', {})
    sf = main.get('sessionFile', '')
    if sf and os.path.exists(sf):
        real_tokens = int(os.path.getsize(sf) * 0.25)
        main['contextTokens'] = real_tokens
        main['totalTokens'] = int(real_tokens * 0.64)
        main['compactionCount'] = len(main.get('compactionCheckpoints', []))
        with open(SESSIONS_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return real_tokens
    return None

def main():
    result = check_token_counter()
    print('[Compaction Monitor] {}'.format(
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print('  contextTokens: {:,}'.format(result['contextTokens']))
    print('  totalTokens: {:,}'.format(result['totalTokens']))
    print('  realTokens(est): {:,}'.format(result['realTokens']))
    print('  compactionCount: {} (checkpoints: {})'.format(
        result['compactionCount'], result['checkpointCount']))

    if result['alerts']:
        print('\n=== ALERT ===')
        for a in result['alerts']:
            print('  !', a)
        if 'force_memory_flush' in result['actions']:
            print('\n[ACTION] 强制写 memory...')
            path = force_memory_flush()
            print('  -> memory 写入: {}'.format(path))
        if 'backup_session' in result['actions']:
            print('\n[ACTION] 备份 session...')
            path = backup_session()
            print('  -> 备份完成: {}'.format(path))
        if 'fix_counter' in result['actions']:
            print('\n[ACTION] 修复 token 计数器...')
            tokens = fix_counter()
            if tokens:
                print('  -> contextTokens 重置为: {:,}'.format(tokens))
    else:
        print('\n[NORMAL] token计数器正常，无异常')

    return result

if __name__ == '__main__':

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()