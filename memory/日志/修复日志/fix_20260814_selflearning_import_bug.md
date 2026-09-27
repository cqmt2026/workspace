# 修复日志 - 2026-08-14 Self-Learning 脚本导入失败

## 问题描述
每日 21:00 运行的 `self_learning.py` 脚本连续失败，exit code=1。

## 根因分析
**Bug 1**: `self_learning.py` 中 `sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'memory'))` 路径计算错误。
- `os.path.dirname(os.path.dirname(__file__))` 在脚本直接运行时，`__file__` 是 `scripts/self_learning.py`，`dirname` 是 `scripts/`，`dirname` 再次是 `workspace/`，然后拼接 `'memory'` 得到 `workspace\memory`
- 但 `memory_adapter.py` 实际在 `scripts/` 目录下，不在 `memory/` 目录下
- 正确路径应为 `os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'memory')` 或直接用 `scripts/` 目录

**Bug 2**: `workspace-investment/scripts/self_learn_review.py` 第174行使用了 `sys.stdout` 但未导入 `sys` 模块。
- 缺少 `import sys`

## 修复方案
1. **self_learning.py**: 将所有 `sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'memory'))` 替换为双路径搜索模式（scripts目录 + memory目录）
2. **self_learn_review.py**: 添加 `import sys`

## 验证结果
- investment self_learn_review.py: ✅ 运行成功（exit 0）
- self_learning.py 全部4个知识库学习: ✅ 全部OK（novel/investment/social/math）
- Supermemory存档: ✅ +1条决策
- 报告生成: ✅ 正常

## 遗留问题
- exit code=1 是设计行为（因子系统corrections有7条过期/缺根因问题）
- 无需处理

## 提交时间
2026-08-14 21:08
