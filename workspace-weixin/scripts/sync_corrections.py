"""
微信小程序 corrections 同步检查脚本
功能：
1. 检查 corrections.md 是否需要更新
2. 统计踩坑数量和最新日期
3. 与知识库其他踩坑文档交叉验证
"""
import io
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace\workspace-weixin'
CORRECTIONS = os.path.join(WORKSPACE, 'memory', 'corrections.md')


def count_entries(filepath):
    """统计 corrections.md 中的条目数"""
    if not os.path.exists(filepath):
        return 0, [], []

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    entries = []
    for i, line in enumerate(lines):
        if '| 问题 |' in line:
            date = ''
            for j in range(i+1, min(i+10, len(lines))):
                if '| 日期 |' in lines[j]:
                    parts = [p.strip() for p in lines[j].split('|')]
                    date = parts[2] if len(parts) > 2 else ''
                    break
            entries.append(date)

    valid_dates = [e for e in entries if e and e.strip()]
    return len(entries), valid_dates


def cross_check_with_knowledge():
    """与知识库其他文档交叉检查"""
    knowledge_dir = os.path.join(WORKSPACE, 'knowledge')
    issues_found = []

    doc_map = {
        '03-踩坑记录/C1-高频踩坑整理.md': 'C1',
        '03-踩坑记录/C3-云开发踩坑.md': 'C3',
    }

    for rel_path, tag in doc_map.items():
        full_path = os.path.join(knowledge_dir, rel_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            count = content.count('【踩坑】')
            if count > 0:
                issues_found.append(f'  {tag}: {count}条踩坑记录')

    return issues_found


def sync_report():
    """生成同步报告"""
    count, valid_dates = count_entries(CORRECTIONS)

    latest = valid_dates[-1] if valid_dates else '无'
    oldest = valid_dates[0] if valid_dates else '无'

    report = f"""# Corrections 同步报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## corrections.md 统计
- 总条目数: {count}
- 最新日期: {latest}
- 最早日期: {oldest}

## 知识库交叉检查
"""
    cross = cross_check_with_knowledge()
    if cross:
        report += '\n'.join(cross) + '\n'
    else:
        report += '  无交叉数据\n'

    report += f"""
## 建议
"""
    if count < 5:
        report += '- corrections 条目较少，建议增加踩坑记录\n'
    elif not valid_dates:
        report += '- corrections 无有效日期，请检查格式\n'
    else:
        try:
            from datetime import datetime as dt
            days_since = (datetime.now() - datetime.strptime(latest, '%Y-%m-%d')).days
            if days_since > 7:
                report += f'- 已{days_since}天无更新，请确认是否有新踩坑经历\n'
            else:
                report += f'- 最近更新于{latest}，状态正常\n'
        except Exception:
            pass

    report += '- 如有新的踩坑经历，请同步到 corrections.md\n'

    return report


def main():
    print('[Corrections同步检查] 开始...')

    report = sync_report()
    print(report)

    log_dir = os.path.join(WORKSPACE, 'memory', 'L1-日志')
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'{today}.md')

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write('\n## Corrections同步检查\n')
        f.write(report)
        f.write('\n\n')

    print(f'[完成] 报告已追加到 {log_file}')


if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if __name__ == '__main__':
    main()