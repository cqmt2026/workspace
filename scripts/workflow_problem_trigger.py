"""
流程问题触发检查脚本
功能：
1. 检查各子系统是否有重复踩坑
2. 检查 Cron 任务是否有连续失败
3. 如发现问题，立即推送报告
"""
import os
import sys
from datetime import datetime, timedelta
import json
import io

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

WORKSPACE = r'C:\Users\Administrator\.openclaw\workspace'


def check_cron_failures():
    """检查 Cron 任务是否有连续失败"""
    cron_state_file = os.path.join(WORKSPACE, 'state', 'cron_failures.json')
    issues = []

    if os.path.exists(cron_state_file):
        try:
            with open(cron_state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            for job_id, info in state.items():
                if info.get('consecutive_errors', 0) >= 3:
                    issues.append(f'Cron任务连续失败: {info.get("name", job_id)} ({info.get("consecutive_errors")}次)')
        except Exception:
            pass

    return issues


def check_corrections_patterns():
    """检查 corrections 是否有重复模式"""
    subsystems = ['novel', 'social', 'investment', 'math', 'jianying', 'weixin']
    issues = []

    for name in subsystems:
        if name == 'weixin':
            corr_path = os.path.join(WORKSPACE, 'workspace-weixin', 'memory', 'corrections.md')
        else:
            corr_path = os.path.join(WORKSPACE, f'workspace-{name}', 'memory', 'corrections.md')

        if not os.path.exists(corr_path):
            continue

        try:
            with open(corr_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            problems = []
            for l in lines:
                if '| 问题 |' in l:
                    # 提取问题描述
                    idx = content.find(l)
                    next_lines = content[idx:idx+200].split('\n')
                    if len(next_lines) > 1:
                        prob = next_lines[0].split('|')[2].strip() if '|' in next_lines[0] else ''
                        problems.append(prob)

            # 检查是否有相似问题重复出现
            if len(problems) >= 3:
                # 简单检查：最近3条是否有相同的根因关键词
                recent = problems[:3]
                keywords = []
                for p in recent:
                    for kw in ['canvas', 'setData', 'ocr', '云函数', '权限']:
                        if kw in p.lower():
                            keywords.append(kw)
                if len(keywords) >= 2 and len(set(keywords)) == 1:
                    issues.append(f'{name}: 重复踩坑 "{keywords[0]}"')

        except Exception:
            pass

    return issues


def main():
    print('[流程问题触发检查] 开始...')

    issues = []

    # 检查 Cron 失败
    cron_issues = check_cron_failures()
    issues.extend(cron_issues)

    # 检查重复踩坑
    corr_issues = check_corrections_patterns()
    issues.extend(corr_issues)

    if issues:
        print(f'⚠️ 发现 {len(issues)} 个流程问题:')
        for i in issues:
            print(f'  - {i}')

        # 生成问题报告
        report = f'''# 流程问题触发报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 发现问题

'''
        for i in issues:
            report += f'- ⚠️ {i}\n'

        report += '''
## 建议

请总经办审查并给出整改意见。

'''
        report_file = os.path.join(WORKSPACE, 'memory', 'L1-日志', f'流程问题_{datetime.now().strftime("%Y-%m-%d")}.md')
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f'\n报告已生成: {report_file}')
    else:
        print('✅ 无流程问题')


if __name__ == '__main__':

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
