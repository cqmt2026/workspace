# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

text = """【模拟盘交易 2026-08-14】

本轮无交易

账户状态：
资金: 97,818元 (初始100,000元)
持仓: 0只
亏损: -2.18%

历史交易：
301019宁波色母 亏损-2,177元 (手动止损)

结论：候选196只，无满足条件。"""

with open(r'C:\Users\Administrator\.openclaw\workspace\workspace-investment\scripts\wx_push_msg.txt', 'w', encoding='utf-8') as f:
    f.write(text)

print('File written successfully')
