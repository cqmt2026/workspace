# 子 Agent 调用指南

**更新时间**: 2026-04-07  
**架构**: 主 Agent (main) + 3 个子 Agent (novel/social/investment)

---

## 📋 Agent 架构

| Agent | ID | 职责 | workspace |
|-------|----|------|-----------|
| **可悦（主 Agent）** | main | 统筹调度、对话入口 | `workspace/` |
| **小说创作搭档** | novel | 小说项目全流程 | `workspace-novel/` |
| **自媒体搭档** | social | 自媒体内容 | `workspace-social/` |
| **投资分析搭档** | investment | 投资分析 | `workspace-investment/` |

---

## 🔧 调用方式

### 【方式 1：使用 `sessions_spawn`（推荐）】

**适用场景**: 派发独立任务给子 Agent

```python
from openclaw import sessions_spawn

# 示例 1: 派发小说创作任务
result = sessions_spawn(
    task="创作第 52 章，都市商战题材，主角陆鸣",
    agentId="novel",           # 指定子 Agent
    mode="run",                # 一次性任务
    runtime="subagent",
    cwd=r"C:\Users\Administrator\.openclaw\workspace-novel",
)

# 示例 2: 派发自媒体任务
result = sessions_spawn(
    task="创作小红书笔记：上海旧城改造探店",
    agentId="social",
    mode="run",
    runtime="subagent",
    cwd=r"C:\Users\Administrator\.openclaw\workspace-social",
)

# 示例 3: 派发投资分析任务
result = sessions_spawn(
    task="分析贵州茅台 (600519) 的投资价值",
    agentId="investment",
    mode="run",
    runtime="subagent",
    cwd=r"C:\Users\Administrator\.openclaw\workspace-investment",
)
```

**参数说明**:
- `task`: 任务描述（必需）
- `agentId`: 子 Agent ID（novel/social/investment）
- `mode`: `"run"` (一次性) 或 `"session"` (持久会话)
- `runtime`: `"subagent"` (标准) 或 `"acp"` (ACP 编码会话)
- `cwd`: 子 Agent 工作目录

---

### 【方式 2：使用 `subagents` 工具】

**适用场景**: 管理已 spawned 的子 Agent

```python
from openclaw import subagents

# 列出所有子 Agent
agents = subagents(action="list")

#  steering 子 Agent（发送指导消息）
subagents(
    action="steer",
    target="novel-agent-id",
    message="请使用 V7.0 引擎创作",
)

# 终止子 Agent
subagents(
    action="kill",
    target="novel-agent-id",
)
```

---

### 【方式 3：直接调用子 Agent 脚本】

**适用场景**: 本地测试/调试

```python
import sys
from pathlib import Path

# 添加子 Agent 脚本路径
novel_scripts = Path(r"C:\Users\Administrator\.openclaw\workspace-novel\创作系统\L2-工具\02-脚本工具")
sys.path.insert(0, str(novel_scripts))

# 导入 V7.0 引擎
from v7_engine import V7Engine

# 创作第 52 章
engine = V7Engine(project_path=r"C:\Users\Administrator\.openclaw\workspace-novel\项目一：鉴城师")
result = engine.write_chapter(52, context={"大纲": "..."})
```

---

## 📊 调度流程

```
用户消息
   ↓
主 Agent (可悦)
   ↓
意图识别 (agent_dispatcher.py)
   ↓
判断任务类型
   ├─ 小说创作 → 派发 novel Agent
   ├─ 自媒体 → 派发 social Agent
   ├─ 投资分析 → 派发 investment Agent
   └─ 通用对话 → 主 Agent 自行处理
   ↓
子 Agent 执行
   ↓
汇总结果 → 返回用户
```

---

## 🎯 意图识别规则

**文件**: `memory/Agent/agent_dispatcher.py`

| 任务类型 | 关键词模式 | 派发目标 |
|---------|-----------|---------|
| **小说编辑** | `编辑.*章节`, `修改.*章节` | novel |
| **小说优化** | `优化.*章节`, `润色.*章节` | novel |
| **小说审核** | `审核.*章节`, `检查.*章节` | novel |
| **小说创作** | `创作.*章节`, `写.*章节` | novel |
| **自媒体** | `小红书`, `公众号`, `抖音` | social |
| **投资** | `股票`, `基金`, `分析`, `茅台` | investment |

---

## 📝 使用示例

### 【示例 1：小说创作】

**用户**: "创作第 52 章"

**主 Agent 处理**:
```python
# 1. 意图识别
dispatcher = AgentDispatcher()
intent = dispatcher.dispatch("创作第 52 章")  # -> 'create'

# 2. 派发任务
result = sessions_spawn(
    task="创作第 52 章，都市商战题材",
    agentId="novel",
    mode="run",
)

# 3. 等待结果并返回
print(f"第 52 章创作完成：{result['word_count']}字")
```

---

### 【示例 2：自媒体内容】

**用户**: "写一篇小红书笔记"

**主 Agent 处理**:
```python
result = sessions_spawn(
    task="创作小红书笔记：上海旧城改造探店",
    agentId="social",
    mode="run",
    cwd=r"C:\Users\Administrator\.openclaw\workspace-social",
)
```

---

### 【示例 3：投资分析】

**用户**: "分析一下贵州茅台"

**主 Agent 处理**:
```python
result = sessions_spawn(
    task="分析贵州茅台 (600519) 的投资价值",
    agentId="investment",
    mode="run",
    cwd=r"C:\Users\Administrator\.openclaw\workspace-investment",
)
```

---

## ⚠️ 注意事项

### 【1. agentId 配置】

**子 Agent ID 需要在 OpenClaw 配置中注册**：

```bash
# 检查已配置的 Agent
openclaw agents list

# 如未配置，需要添加
openclaw agents add --id novel --workspace ~/.openclaw/workspace-novel
```

---

### 【2. workspace 独立性】

**每个子 Agent 有独立的 workspace**：

| Agent | workspace | 核心文件 |
|-------|-----------|---------|
| novel | `workspace-novel/` | V7.0 引擎、知识卡片 |
| social | `workspace-social/` | 内容模板、热点数据 |
| investment | `workspace-investment/` | 量化模型、风控策略 |

**派发任务时务必指定正确的 `cwd`！**

---

### 【3. 任务超时】

```python
result = sessions_spawn(
    task="...",
    timeoutSeconds=1800,  # 30 分钟超时
)
```

---

### 【4. 结果获取】

**方式 A：等待返回**
```python
result = sessions_spawn(task="...", mode="run")
# 直接获取结果
```

**方式 B：sessions_yield**
```python
sessions_spawn(task="...", mode="session")
sessions_yield()  # 等待子 Agent 完成
```

---

## 🔍 调试技巧

### 【1. 检查子 Agent 状态】

```python
from openclaw import subagents
agents = subagents(action="list")
print(agents)
```

---

### 【2. 查看子 Agent 日志】

```python
from openclaw import sessions_history
history = sessions_history(sessionKey="novel-session-key")
print(history)
```

---

### 【3. 测试意图识别】

```python
from memory.Agent.agent_dispatcher import AgentDispatcher

dispatcher = AgentDispatcher()
print(dispatcher.dispatch("创作第 52 章"))  # -> 'create'
print(dispatcher.dispatch("分析一下茅台"))  # -> None (需要添加投资意图)
```

---

## 📚 相关文件

| 文件 | 功能 |
|------|------|
| `memory/Agent/agent_dispatcher.py` | 意图识别调度器 |
| `memory/Agent/agent_interfaces.py` | Agent 接口定义 |
| `memory/Agent/agent_responsibilities.md` | Agent 职责说明 |
| `AGENTS.md` | 主 Agent 配置 |
| `MEMORY.md` | 多 Agent 架构说明 |

---

**需要添加新的意图识别规则或调整调度逻辑吗？** 🌸
