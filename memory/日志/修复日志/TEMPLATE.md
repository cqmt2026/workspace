# 修复日志模板

# YAML frontmatter 必填，结构化标签便于自动化分析
---
type: schema_mismatch | timeout | stale_reference | doc_sync | config_missing | security | other
severity: P0 | P1 | P2 | P3
systems_affected: [main | investment | novel | social | math | weixin | maphot]
recurrence: yes | no | unknown
verified: yes | no | N/A
---

# {子系统} 修复日志 - {日期} {时间}

## 问题描述
- 现象：{具体错误信息/行为}
- 影响范围：{哪些功能受影响}
- 触发条件：{什么操作触发}

## 根因分析
- 直接原因：{第一个发现的问题}
- 深层原因：{为什么会出现这个问题}

## 修复方案
- 改了哪些文件：{文件列表}
- 改动说明：{具体做了什么}

## 验证结果
- 验证方法：{怎么确认修好了}
- 结果：通过/不通过

## 经验教训
- 这次学到的：{一句话总结}
- 如何防止复发：{写入陷阱手册的规则}
