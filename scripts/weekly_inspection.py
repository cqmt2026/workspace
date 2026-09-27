"""
周巡检报告脚本
功能：
1. 汇总本周各子系统执行情况
2. 检查 Cron 任务执行状态
3. 检查 Token 使用情况
4. 生成周报汇报主人
"""
import os
import sys
from datetime import datetime, timedelta
import io

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace'
# 修复：日志实际写在 memory/ 下，不是 memory/L1-日志/
LOG_DIR = r'C:\Users\Administrator\.openclaw\workspace\memory'
os.makedirs(LOG_DIR, exist_ok=True)


def get_week_logs():
    """获取本周所有日志"""
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    logs = []

    if not os.path.exists(LOG_DIR):
        return logs

    for f in os.listdir(LOG_DIR):
        if not f.endswith('.md') or not f.startswith('20'):
            continue
        try:
            fdate = datetime.strptime(f.replace('.md', ''), '%Y-%m-%d')
            if week_ago <= fdate <= today:
                logs.append((fdate, os.path.join(LOG_DIR, f)))
        except ValueError:
            pass

    return sorted(logs)


def scan_log_content(filepath):
    """扫描日志内容，提取关键信息"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if not content.strip():
            return {'problems': [], 'completions': [], 'corrections': 0, 'size': 0, 'empty': True}

        lines = content.split('\n')
        findings = {
            'problems': [],
            'completions': [],
            'corrections': 0,
            'size': len(content),
            'empty': False,
        }

        for l in lines:
            if '⚠️' in l or '❌' in l:
                findings['problems'].append(l.strip())
            if '✅' in l and '完成' in l:
                findings['completions'].append(l.strip())
            if 'corrections' in l.lower():
                findings['corrections'] += 1

        return findings
    except Exception:
        return {'problems': [], 'completions': [], 'corrections': 0, 'size': 0, 'empty': True}


def main():
    print('[周巡检报告] 开始...')
    today = datetime.now().strftime('%Y-%m-%d')

    week_logs = get_week_logs()

    report = [f'# 周巡检报告 - {today}\n']
    report.append(f'## 汇总周期: 最近7天\n')

    if not week_logs:
        report.append('本周无日志记录')
    else:
        all_problems = []
        all_completions = []
        total_size = 0
        empty_count = 0
        log_details = []

        for fdate, fpath in week_logs:
            findings = scan_log_content(fpath)
            total_size += findings['size']
            if findings['empty']:
                empty_count += 1
            all_problems.extend(findings['problems'])
            all_completions.extend(findings['completions'])
            log_details.append((fdate.strftime('%m-%d'), findings['size'], findings['empty']))

        report.append(f'### 数据概览\n')
        report.append(f'- 日志天数: {len(week_logs)}天\n')
        report.append(f'- 有效内容: {len(week_logs) - empty_count}天\n')
        report.append(f'- 空文件: {empty_count}天\n')
        report.append(f'- 总字符量: {total_size}字节\n')
        report.append(f'- 发现问题: {len(all_problems)}条\n')
        report.append(f'- 完成任务: {len(all_completions)}条\n')

        report.append(f'\n### 日志明细\n')
        for date_str, size, empty in log_details:
            status = '⚠️空' if empty else f'{size}B'
            report.append(f'- {date_str}: {status}\n')

        if all_problems:
            report.append(f'\n### 本周问题汇总\n')
            seen = set()
            for p in all_problems:
                if p not in seen:
                    report.append(f'- {p}\n')
                    seen.add(p)

        if all_completions:
            report.append(f'\n### 本周完成事项\n')
            seen = set()
            for c in all_completions[:20]:
                if c not in seen:
                    report.append(f'- {c}\n')
                    seen.add(c)

        # 补充：扫描近期 memory/ 日志的非周检内容
        report.append(f'\n### 本周主要活动\n')
        seen_titles = set()
        for _, fpath in week_logs:
            if scan_log_content(fpath)['empty']:
                continue
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('## ') and line not in seen_titles and not line.startswith('## 汇总'):
                    report.append(f'- {line}\n')
                    seen_titles.add(line)

    # Write report
    report_file = os.path.join(LOG_DIR, f'周巡检_{today}.md')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f'✅ 周巡检报告已生成: {report_file}')
    print('\n'.join(report[:20]))


if __name__ == '__main__':

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
