#!/usr/bin/env python3
"""Send WeChat message via openclaw CLI"""
import sys, os, subprocess, time

TARGET = "o9cq8092w_2W-BHmLsGGbleQEHKg@im.wechat"
_OPENCLAW_PATH = os.path.join(os.environ.get('APPDATA', ''), 'npm', 'openclaw.cmd')

text = """【四象共振底部反转扫描】2026-08-21

扫描条件：前10日跌10~50% + MACD柱加速下跌 + 量比>1.1 + 地量先于最低点 + 底部距今15~30日 + 距低5~50%

📊 结果：共 0 只候选

📋 近3日趋势：
- 08-21（今日）：0 只
- 08-20（昨日）：0 只
- 08-19：1 只（603986，但因假金叉仅25分）

⚠️ 市场暂无符合条件的底部反转候选，四象共振条件在当前行情中较为严格，建议持续关注。

风险提示：底部反转成功率约60-70%，需严格止损。"""

for attempt in range(3):
    try:
        result = subprocess.run(
            [_OPENCLAW_PATH, 'message', 'send', '--target', TARGET, '--message', text],
            capture_output=True, text=True, timeout=30,
            encoding='utf-8', errors='replace',
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
        )
        if result.returncode == 0:
            print(f'[OK] 已发送微信消息 ({len(text)} chars)')
            sys.exit(0)
        else:
            print(f'Attempt {attempt+1}: {result.stderr[:200]}')
    except Exception as e:
        print(f'Attempt {attempt+1} error: {e}')
    time.sleep(2)

print('Failed to send')
