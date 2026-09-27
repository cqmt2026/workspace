# L1监控Cron超时修复

**日期**: 2026-09-06
**问题**: `Self-Heal-L1-Monitor` Cron任务agentTurn超时（180s），脚本正常但被强杀
**根因**: timeoutSeconds=180 太短，模型生成汇报文本需要更长时间
**修复**: 
1. timeout 180s → 300s
2. 切换脚本 `self_heal_l1.py` → `l1_check_v2.py`（更稳定，KNOW_ISSUES更完整）
3. 模型改为 `agnes-2.0-flash`（更轻量，减少超时风险）
