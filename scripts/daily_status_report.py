# -*- coding: utf-8 -*-
"""
子系统每日状态主动汇报
先刷新仪表盘数据，再生成格式化汇报推送给主人
"""
import io
import os, sys, json, shutil, urllib.request, sqlite3, re
from datetime import datetime, timedelta

if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace'
DASH_FILE = os.path.join(WORKSPACE, 'memory', '日志', 'subsystem_dashboard.json')

def api_get(url, timeout=5):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except:
        return None

def check_supermemory():
    h = api_get('http://127.0.0.1:8642/api/health')
    if not h: return 'DOWN', 0, 'cannot connect:8642'
    return 'OK', h.get('memories', 0), 'v' + h.get('version', '?')

def check_disk():
    _, used, free = shutil.disk_usage(r'C:\\')
    pct = free / (used + free) * 100
    gb = free / 1024**3
    if pct < 15: return 'WARN', '%.1fGB(%.0f%%)' % (gb, pct), 'C disk <15%'
    if pct < 20: return 'WARN', '%.1fGB(%.0f%%)' % (gb, pct), 'C disk <20%'
    return 'OK', '%.1fGB(%.0f%%)' % (gb, pct), ''

def check_session_state():
    ssm = os.path.join(WORKSPACE, 'memory', 'session-state.md')
    if not os.path.exists(ssm): return 'ERR', 'file not found', ''
    mtime = datetime.fromtimestamp(os.path.getmtime(ssm))
    age_min = (datetime.now() - mtime).total_seconds() / 60
    if age_min > 60: return 'WARN', '%.0fmin ago' % age_min, '>60min'
    return 'OK', '%.0fmin ago' % age_min, ''

def check_market_data():
    db_path = r'F:\market_data.db'
    if not os.path.exists(db_path): return 'WARN', 'DB not found', ''
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT MAX(date) FROM daily_k")
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            latest = row[0]
            age_days = (datetime.now() - datetime.strptime(str(latest), '%Y-%m-%d')).days
            if age_days > 3: return 'WARN', '%s(%dd)' % (latest, age_days), '>3d old'
            return 'OK', latest, ''
        return 'WARN', 'no data', ''
    except Exception as e: return 'ERR', str(e)[:30], ''

def check_ml_model():
    f = os.path.join(WORKSPACE, 'workspace-investment', 'ml_output_v6', 'lgb_v6_results.json')
    if not os.path.exists(f): return 'WARN', 'model not found', ''
    try:
        with open(f, encoding='utf-8') as fh: d = json.load(fh)
        r = d.get('rating','?'); auc = d.get('auc',0); dt = d.get('date','?')
        return 'OK' if r in ['A','B'] else 'WARN', 'Rating %s(AUC=%.3f) %s' % (r, auc, dt), ''
    except Exception as e: return 'ERR', str(e)[:30], ''

def check_holdings():
    f = os.path.join(WORKSPACE, 'workspace-investment', 'memory', 'L2-核心', '持仓', '当前持仓.json')
    if not os.path.exists(f): return 'WARN', 'file not found', ''
    try:
        with open(f, encoding='utf-8') as fh: d = json.load(fh)
        holdings = d.get('holdings', d) if isinstance(d, dict) else d
        return 'OK', '%d holdings' % (len(holdings) if isinstance(holdings, list) else 0), ''
    except Exception as e: return 'ERR', str(e)[:30], ''

def check_novel():
    d = os.path.join(WORKSPACE, 'workspace-novel', '项目三：都市重生', 'L3-正文')
    if not os.path.exists(d): return 'WARN', 'dir not found', ''
    chs = [f for f in os.listdir(d) if f.endswith('.md')]
    chs.sort()
    return ('WARN', '0ch', '') if not chs else ('OK', '%dch latest:%s' % (len(chs), chs[-1]), '')

def check_social():
    drafts = os.path.join(WORKSPACE, 'workspace-social', 'drafts')
    if not os.path.exists(drafts): return 'WARN', 'drafts not found', ''
    cutoff = datetime.now() - timedelta(days=7)
    recent = 0
    for root, _, files in os.walk(drafts):
        for f in files:
            if f.endswith(('.md', '.txt', '.json')):
                try:
                    fp = os.path.join(root, f)
                    if datetime.fromtimestamp(os.path.getmtime(fp)) > cutoff: recent += 1
                except: pass
    return ('WARN', '0 new 7d', '') if recent == 0 else ('OK', '%d new 7d' % recent, '')

def check_math():
    scripts = os.path.join(WORKSPACE, 'workspace-math', 'scripts')
    if not os.path.exists(scripts): return 'WARN', 'scripts not found', ''
    eps = sorted([f for f in os.listdir(scripts) if re.match(r'ep\d+_build', f)],
                 key=lambda x: int(re.search(r'\d+', x).group()), reverse=True)
    return ('WARN', 'no ep_build', '') if not eps else ('OK', eps[0], '')

def check_cron_failures():
    log_dir = os.path.join(WORKSPACE, 'memory', '日志', 'task')
    today = datetime.now().strftime('%Y-%m-%d')
    count = 0
    if os.path.exists(log_dir):
        for root, _, files in os.walk(log_dir):
            for fn in files:
                if fn.endswith('.jsonl'):
                    try:
                        with open(os.path.join(root, fn), encoding='utf-8', errors='ignore') as fh:
                            for line in fh:
                                try:
                                    e = json.loads(line.strip())
                                    if today in e.get('timestamp','') and e.get('status') in ('error','failed'):
                                        count += 1
                                except: pass
                    except: pass
    return ('WARN', '%d failures' % count, '>3') if count > 3 else ('OK', '%d failures' % count, '')

checks = {
    'Main': [check_supermemory, check_disk, check_session_state, check_cron_failures],
    'Investment': [check_market_data, check_ml_model, check_holdings],
    'Novel': [check_novel],
    'Social': [check_social],
    'Math': [check_math],
}

sections = []
all_issues = []
now_str = datetime.now().strftime('%Y-%m-%d %H:%M')

for sec_name, fns in checks.items():
    items = []
    for fn in fns:
        try: st, val, msg = fn()
        except Exception as e: st, val, msg = 'ERR', 'crash', str(e)[:40]
        items.append({'name': fn.__name__.replace('check_',''), 'status': st, 'value': val, 'msg': msg})
        if st in ('ERR','DOWN'): all_issues.append('[%s] %s: %s' % (st, fn.__name__, msg or val))
    sections.append({'section': sec_name, 'items': items})

overall = 'OK' if not all_issues else 'WARN'
sym_map = {'OK': '[OK]', 'WARN': '[WARN]', 'ERR': '[ERR]', 'DOWN': '[DOWN]'}

report = []
report.append('=' * 48)
report.append('[SUB-SYSTEM STATUS REPORT] %s' % now_str)
report.append('=' * 48)
report.append('')
report.append('Overall: %s | %d issues' % (sym_map.get(overall,'?'), len(all_issues)))
report.append('')
for sec in sections:
    has_issue = any(it['status'] in ('ERR','WARN','DOWN') for it in sec['items'])
    report.append('[%s] %s' % ('!' if has_issue else 'o', sec['section']))
    for it in sec['items']:
        s = sym_map.get(it['status'], '[?]')
        report.append('    %s %s: %s' % (s, it['name'], it['value']))
    report.append('')
report.append('-' * 48)
report.append('Dashboard: subsystem_dashboard.json')

text = '\n'.join(report)
print(text)
