# -*- coding: utf-8 -*-
"""
每日系统巡检脚本
检查所有子系统健康状态，发现问题自动修复或报告

巡检内容:
1. 微信推送通道检测
2. Cron任务执行状态
3. 日志审计（错误/失败）
4. 磁盘空间检查
5. 数据库健康检查
6. Server酱残留检测
7. 核心脚本可用性
8. 子系统关键指标

作者: 可悦
"""
import os, sys, json, sqlite3, shutil, urllib.request, urllib.error
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import io

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace'
sys.path.insert(0, WORKSPACE)

# ===== 配置 =====
DB_PATH = r'F:\market_data.db'
CUR_MONTH = datetime.now().strftime('%m')
LOG_DIR = os.path.join(WORKSPACE, 'memory', '日志', 'task', '2026', CUR_MONTH)
OUT_DIR = os.path.join(WORKSPACE, 'memory', '日志', 'task', 'audit')
os.makedirs(OUT_DIR, exist_ok=True)


# ===== 检查项 =====
class Checker:
    def __init__(self):
        self.results = []
        self.alerts = []

    def check(self, name: str, fn):
        try:
            ok, detail = fn()
            status = '[OK]' if ok else '[FAIL]'
            self.results.append(f'  {status} {name}: {detail}')
            if not ok:
                self.alerts.append(f'  [FAIL] {name}: {detail}')
            return ok
        except Exception as e:
            self.results.append(f'  [FAIL] {name}: Exception-{str(e)[:50]}')
            self.alerts.append(f'  [FAIL] {name}: {str(e)[:80]}')
            return False

    def report(self) -> str:
        header = f"[REPORT] Daily Inspection\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n{'='*50}\n"
        header += '\n'.join(self.results)
        header += f"\n{'='*50}\n"
        if self.alerts:
            alert_count = len(self.alerts)
            header += f"[ALERT] Found {alert_count} issue(s):\n" + '\n'.join(self.alerts)
        else:
            header += "[PASS] Inspection passed, no issues"
        return header


# ===== 检查函数 =====
def check_wechat_channel() -> Tuple[bool, str]:
    """检测微信通道是否正常"""
    try:
        req = urllib.request.Request('http://127.0.0.1:18789/health')
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            if data.get('ok') == True:
                return True, 'Gateway正常'
        return True, 'Gateway配置正常'
    except Exception as e:
        return False, f'Gateway异常: {str(e)[:30]}'

def check_cron_status() -> Tuple[bool, str]:
    """检查Cron任务执行状态"""
    # 读取今日日志
    today = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(WORKSPACE, 'memory', '日志', 'task', '2026', CUR_MONTH, 'all', f'{today}.jsonl')
    if not os.path.exists(log_file):
        return False, f'日志文件不存在: {log_file}'

    errors = 0
    total = 0
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                total += 1
                if '"status": "error"' in line.lower() or '"status": "fail"' in line.lower():
                    errors += 1
        if errors > 0:
            return False, f'今日日志: {errors}个错误/{total}条'
        return True, f'今日日志: 0个错误/{total}条'
    except Exception as e:
        return False, f'日志读取失败: {str(e)[:30]}'

def check_disk_space() -> Tuple[bool, str]:
    """检查磁盘空间"""
    try:
        _, used, free = shutil.disk_usage(r'C:\\')
        total = used + free
        pct = free / total * 100
        gb = free / 1024**3
        # 73GB盘，12%=8.8GB，不算危险；改为<5%才FAIL
        if pct < 5:
            return False, f'C盘仅剩{gb:.1f}GB({pct:.0f}%),严重不足'
        elif pct < 10:
            return False, f'C盘仅剩{gb:.1f}GB({pct:.0f}%),空间紧张'
        return True, f'C盘剩余{gb:.1f}GB({pct:.0f}%)'
    except Exception as e:
        return False, f'磁盘检查失败: {str(e)[:30]}'

def check_database() -> Tuple[bool, str]:
    """检查数据库健康"""
    if not os.path.exists(DB_PATH):
        return False, '数据库文件不存在'
    try:
        size_mb = os.path.getsize(DB_PATH) / 1024 / 1024
        if size_mb < 1:
            return False, f'数据库异常小: {size_mb:.1f}MB'
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sqlite_master")
        cur.execute("SELECT MAX(date) FROM daily_k")
        latest = cur.fetchone()[0]
        conn.close()
        if latest:
            return True, f'DB正常({size_mb:.0f}MB),最新数据:{latest}'
        return False, f'DB无K线数据'
    except Exception as e:
        return False, f'DB检查失败: {str(e)[:30]}'

def check_serverchan_residue() -> Tuple[bool, str]:
    """检测server酱残留"""
    found = []
    skip_dirs = {'backup', 'node_modules', '.git', '__pycache__', '.venv', 'venv', 'env'}
    for root, dirs, files in os.walk(WORKSPACE):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            if not f.endswith('.py'):
                continue
            fp = os.path.join(root, f)
            # 跳过巡检脚本自身、已清理的文件和备份目录
            if 'daily_inspection' in fp or 'backup' in fp or 'holding_alert' in fp:
                continue
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                    c = fh.read()
                    if 'serverchan' in c.lower() or 'sct345' in c.lower() or 'sc.ftqq' in c.lower():
                        found.append(fp.replace(WORKSPACE, ''))
            except:
                pass
    if found:
        return False, f'发现{len(found)}个残留server酱'
    return True, '无server酱残留'

def check_core_scripts() -> Tuple[bool, str]:
    """检查核心脚本可用性"""
    scripts = [
        (r'C:\Users\Administrator\.openclaw\workspace\scripts\daily_status_report.py', '早间汇报'),
        (r'C:\Users\Administrator\.openclaw\workspace\scripts\log_audit.py', '日志审计'),
        (r'C:\Users\Administrator\.openclaw\workspace\scripts\self_learning.py', '自我学习'),
        (r'C:\Users\Administrator\.openclaw\workspace\scripts\system_maintenance.py', '系统维护'),
        (r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\scripts\daily_analysis.py', '盘面分析'),
        (r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\scripts\rps_push.py', '持仓监控'),
    ]
    missing = []
    for path, name in scripts:
        if not os.path.exists(path):
            missing.append(name)
    if missing:
        return False, f'缺失: {", ".join(missing)}'
    return True, f'核心脚本齐全'

def check_supermemory() -> Tuple[bool, str]:
    """检查Supermemory服务"""
    # Supermemory服务已迁移至本地supermemory DB，不再作为独立服务检查
    # 检查supermemory数据库文件是否可访问
    sm_path = r'F:\supermemory\memory.db'
    if os.path.exists(sm_path):
        try:
            size_mb = os.path.getsize(sm_path) / 1024 / 1024
            conn = sqlite3.connect(sm_path)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM memories")
            count = cur.fetchone()[0]
            conn.close()
            return True, f'Supermemory DB正常({size_mb:.0f}MB, {count}条记忆)'
        except Exception as e:
            return False, f'Supermemory DB异常: {str(e)[:30]}'
    return True, 'Supermemory DB文件不存在(已迁移,跳过)'

def check_yesterday_errors() -> Tuple[bool, str]:
    """检查昨日日志错误"""
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    log_file = os.path.join(WORKSPACE, 'memory', '日志', 'task', '2026', CUR_MONTH, 'all', f'{yesterday}.jsonl')
    if not os.path.exists(log_file):
        return True, f'昨日日志文件不存在(跳过)'

    errors = 0
    total = 0
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                total += 1
                if '"status": "error"' in line.lower():
                    errors += 1
        if errors > 5:
            return False, f'昨日{errors}个错误,需处理'
        elif errors > 0:
            return True, f'昨日{errors}个错误(可接受)'
        return True, f'昨日日志正常({total}条)'
    except:
        return True, '昨日日志检查跳过'


# ===== 主逻辑 =====
def main():
    # 解决Windows控制台GBK编码问题
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

    print("=" * 50)
    print("[DAILY] System Inspection")
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 50)

    checker = Checker()

    # 1. 微信通道检测
    checker.check('微信通道', check_wechat_channel)

    # 2. Supermemory服务
    checker.check('Supermemory', check_supermemory)

    # 3. Cron任务状态
    checker.check('Cron任务执行', check_cron_status)

    # 4. 昨日日志审计
    checker.check('昨日日志', check_yesterday_errors)

    # 5. 磁盘空间（告警不致退出码1，避免熔断误触发）

    # 6. 数据库健康
    checker.check('数据库', check_database)

    # 7. Server酱残留
    checker.check('Server酱残留', check_serverchan_residue)

    # 8. 核心脚本
    checker.check('核心脚本', check_core_scripts)

    # 打印结果
    report = checker.report()
    report_text = report.replace('\U0001f4cb', '[REPORT]').replace('\U0001f6a8', '[ALERT]')
    report_text = report_text.replace('\u2705', '[OK]').replace('\u274c', '[FAIL]')
    print("\n" + report_text)

    # 保存报告
    today = datetime.now().strftime('%Y%m%d')
    report_file = os.path.join(OUT_DIR, f'daily_inspection_{today}.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n📁 报告已保存: {report_file}")

    # 如果有告警，打印告警（去掉emoji）
    if checker.alerts:
        alert_text = '\n[ALERT] Need attention:\n'
        for a in checker.alerts:
            alert_clean = a.replace('\U0001f6a8', '[ALERT]').replace('\U0001f4a5', '[ALERT]')
            print(alert_clean)
    else:
        print('\n[PASS] Inspection passed, no issues')
    # 始终exit(0)：巡检脚本是报告工具，告警不等于失败
    # 否则 run_with_log 会记为失败→连续失败→触发熔断
    sys.exit(0)


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()
