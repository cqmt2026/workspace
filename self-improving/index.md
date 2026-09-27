# Self-Improving Storage Index
**最后更新**: 2026-05-23

---

## 目录结构
```
self-improving/
├── memory.md          # HOT 记忆
├── corrections.md     # 纠正日志
├── index.md           # 本文件（存储索引）
├── heartbeat-state.md # 心跳状态
├── projects/          # 项目级学习
├── domains/           # 领域级学习
└── archive/           # 冷存储
```

---

## 领域索引

| 领域 | 路径 |
|------|------|
| 小说创作 | `domains/小说创作.md` |
| 自媒体运营 | `domains/自媒体运营.md` |
| 投资分析 | `domains/投资分析.md` |
| 数学动画 | `domains/数学动画.md` |
| 微信小程序开发 | `domains/微信小程序开发.md` |

---

## 文件路由规则

| 信息类型 | 存储位置 |
|---------|---------|
| 已确认的持久偏好 | `self-improving/memory.md` |
| 最近的纠正和教训 | `self-improving/corrections.md` |
| 项目级学习 | `self-improving/projects/<项目名>.md` |
| 领域级学习 | `self-improving/domains/<领域名>.md` |
| 当前任务状态 | `proactivity/session-state.md` |
| 脆弱/长期任务的volatile状态 | `proactivity/memory/working-buffer.md` |
| 周期性心跳检查项 | `proactivity/heartbeat.md` |
| 反复有效的主动模式 | `proactivity/patterns.md` |
| 最近的主动行动记录 | `proactivity/log.md` |

---

## 晋升规则

- 7天内重复3次 → 晋升到 HOT memory
- 30天未用 → 降级到 WARM storage
- 90天未用 → 归档到 archive/
- 已确认的偏好不经询问不删除

---

## 冲突解决

1. 项目 > 领域 > 全局
2. 同级内：新的 > 旧的
3. 仍模糊 → 询问主人

---

_由 可悦🌸 管理_