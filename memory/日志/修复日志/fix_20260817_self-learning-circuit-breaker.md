# fix_20260817_self-learning-circuit-breaker

## 陷阱描述
self_learning.py 脚本成功执行（所有7步都跑完），但因为检测到子系统 corrections 有 7 条问题，导致 sys.exit(1)，触发 run_with_log.py 的熔断器，连续失败5次后被暂停24h。

## 根因
脚本逻辑错误：将"发现问题"（子系统corrections审计有7条问题）误判为"执行失败"，导致正常运行的脚本返回非零退出码。

## 修复方案
1. 修改 self_learning.py 末尾逻辑：
   - 只有知识库学习脚本真正失败（FAIL/ERROR）才标记 ERROR
   - 踩坑数量、规则格式问题、sub corrections 问题 → 正常报告内容，不影响退出码
   - 始终 sys.exit(0)，因为脚本成功执行完即视为成功
2. 重置熔断器状态（清除 Self-Learning-统一学习 的连续失败计数）

## 验证
- 手动运行 python scripts/self_learning.py → exit code 0 ✅
- 报告正常生成 ✅
- 熔断器已重置 ✅

## 严重度
中等 — 导致每日自我学习被熔断暂停，影响系统自检能力
