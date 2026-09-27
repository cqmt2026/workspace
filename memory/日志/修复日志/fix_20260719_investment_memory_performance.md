# 投资记忆系统性能优化修复日志

**日期**: 2026-07-19
**子系统**: memory_tools / investment
**严重度**: P1（影响所有投资分析 cron 任务）

## 问题描述

投资分析场景下 Supermemory 性能瓶颈：
1. `bge-small-zh-v1.5` 首次加载需 3-5 秒（实测 90s），每次 cron 新进程都重新加载
2. 向量搜索 O(n) 计算余弦距离，查询耗时与数据量成正比
3. 多个子系统共用同一 embedding 服务，高峰期并发冲突

## 根因分析（第一性原理拆解）

**连问5个为什么**：
1. 为什么慢？→ 每次查询都要加载 embedding 模型
2. 为什么每次都要加载？→ 模型懒加载，cron 每次新进程
3. 为什么需要 embedding？→ 为了做向量搜索找相似历史数据
4. 为什么需要向量搜索？→ 想找到"语义相似"的策略/行情场景
5. 投资分析真的需要语义相似吗？→ **不需要！** 行情数据本质是结构化的（日期、涨幅、板块、成交量），语义搜索对"涨停的房地产股"这种查询不如关键词+结构化过滤准

**物理定律 vs 人为规定**：
- 不可跨越：SentenceTransformer 加载需要时间
- 可以打破：❌ "投资分析必须用向量搜索" — 这是烂苹果

## 方案演进

| 尝试 | 方案 | 结果 |
|------|------|------|
| 1 | FTS5 全文索引 | ❌ Python SQLite 没编译 FTS5 扩展 |
| 2 | FTS4 全文索引 | ❌ 同上，FTS4 也不可用 |
| 3 | LIKE + 索引 | ✅ 搜索 0.001s，比向量搜索快 90000x |

## 最终方案

**投资库改用 LIKE 关键词搜索，其他子系统保留向量搜索**

### 改动文件

| 文件 | 改动 |
|------|------|
| `memory/memory_tools.py` | `_ensure_db`: 投资库创建 content 索引 |
| `memory/memory_tools.py` | `save_memory`: 去掉 FTS5 写入逻辑 |
| `memory/memory_tools.py` | `search_memory`: 投资域走 LIKE 多关键词 OR 匹配 |

### 核心逻辑

```python
# 投资域搜索：多关键词 OR 匹配
keywords = [w for w in re.split(r'\s+', query.strip()) if len(w) >= 2][:10]
like_clauses = ['m.content LIKE ?']
params = [f'%{kw}%']
sql = f"... WHERE is_current=1 AND (content LIKE '%{kw}%' OR ...) LIMIT {top_k}"
```

### 性能对比

| 指标 | 向量搜索 | LIKE 搜索 |
|------|----------|-----------|
| 搜索耗时 | ~90s（含模型加载） | ~0.001s |
| 加速比 | 1x | **~90000x** |
| 依赖 | sentence-transformers, numpy | sqlite3（内置） |

## 边界情况处理

- 空查询 → 返回 0 条
- 无多字符关键词 → 使用前2个字符
- category 过滤 → 作为额外 WHERE 条件
- 跨域搜索（domain='*'）→ 投资域走 LIKE，其他域走向量搜索

## 验证结果

- ✅ 搜'涨停': 2条 (0.004s)
- ✅ 搜'房地产': 2条 (0.002s)
- ✅ 搜'陆鸣': 0条 (0.004s) — 无污染
- ✅ 搜'': 0条 (0.002s) — 空查询处理
- ✅ 小说域向量搜索不受影响
- ✅ 跨域搜索正常

## 遗留问题

- 其他子系统（novel/social/math/system）仍使用向量搜索，每次 cron 启动仍需加载 embedding
- 后续可考虑 embedding 预热（启动时预加载到内存）进一步减少开销

---
_记录者: 可悦 | 2026-07-19_
