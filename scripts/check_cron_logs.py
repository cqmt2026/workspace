# -*- coding: utf-8 -*-
import os, json

log_dir = r'C:\Users\Administrator\.openclaw\workspace\memory\日志\task\2026\08\all'

for day in ['20260819','20260818','20260817','20260816','20260815']:
    fp = os.path.join(log_dir, f'{day}.jsonl')
    if not os.path.exists(fp):
        continue
    with open(fp, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                task = d.get('task_name', '?')
                status = d.get('status', '?')
                error = d.get('error_msg', '')
                if 'Daily-Inspection' in task:
                    print(f'{day} | {task} | {status} | {error[:100]}')
                if status in ('error', 'fail'):
                    print(f'  ERR {day} | {task} | {error[:100]}')
            except Exception as e:
                pass
