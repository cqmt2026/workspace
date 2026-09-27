# 系统优化提升小助手

**版本**: V1.0  
**创建时间**: 2026-03-14 23:27  
**定位**: 系统守护者 + 优化顾问 + 清洁工

---

## 🎯 核心职责

### 1. 系统完整性检查
- ✅ 检查核心文件是否存在
- ✅ 检查小助手模块是否完整
- ✅ 检查必要目录是否齐全
- ✅ 检查磁盘空间是否充足
- ✅ 生成完整性评分（0-100 分）

### 2. BUG 评估
- ✅ 语法检查
- ✅ 导入测试
- ✅ 实例化测试
- ✅ 方法功能测试
- ✅ 生成问题报告

### 3. 学习提升
- ✅ 生成系统升级建议
- ✅ 提供学习参考资料
- ✅ 跟踪技术发展趋势
- ✅ 为系统升级提供决策参考

### 4. 定期清理
- ✅ 清理过期报告（>30 天）
- ✅ 清理过期缓存（>3 天）
- ✅ 清理临时文件（.tmp/.bak/.log）
- ✅ 清理__pycache__目录
- ✅ 释放磁盘空间

---

## 🚀 使用方法

### 初始化
```python
from stock_v13_system import StockV13System

system = StockV13System()

# 访问优化助手
optimizer = system.optimization
```

### 1. 系统完整性检查
```python
# 执行完整性检查
result = system.optimization.check_system_integrity()

# 输出:
# ============================================================
# 系统完整性检查
# ============================================================
# [OK] stock_v13_system.py (15,000 bytes)
# [OK] capital_flow_tencent.py (6,000 bytes)
# [OK] data_assistant.py
# [OK] trading_assistant.py
# ...
# ============================================================
# 系统完整性评分：95/100
```

### 2. 检查小助手 BUG
```python
# 检查指定小助手
result = system.optimization.check_assistant_bugs('data_assistant')

# 输出:
# ============================================================
# 检查小助手：data_assistant
# ============================================================
# [OK] 语法检查通过
# [OK] 模块导入成功
# [OK] 实例化成功
# [OK] 可用方法：5 个
#   方法测试:
#     [OK] get_realtime_price()
#     [INFO] get_kline_data() - 需要参数
# ...
```

### 3. 生成升级建议
```python
# 获取升级建议
recommendations = system.optimization.generate_upgrade_recommendations()

# 输出:
# 【紧急】0 项
# 【重要】1 项
#   * 补充缺失组件：capital_flow_tencent.py
# 【可选】4 项
#   - 添加更多技术指标
#   - 优化用户界面
#   ...
# 【学习参考】4 项
#   > 关注 akshare 最新版本，及时更新数据接口
#   > 学习 Qlib 最新策略，优化量化模型
#   ...
```

### 4. 清理过期文件
```python
# 预览模式（不实际删除）
cleanup = system.optimization.cleanup_old_files(dry_run=True)

# 实际删除
# cleanup = system.optimization.cleanup_old_files(dry_run=False)

# 输出:
# ============================================================
# 清理过期文件 (预览模式)
# ============================================================
# [1/3] 检查过期报告...
# [2/3] 检查过期缓存...
# [3/3] 检查临时文件...
#   [DEL] optimization_fixed.log
#   [DEL] __pycache__
# ...
# 扫描文件：42 个
# 待删除：3 个
# 可释放空间：1.5MB
```

### 5. 生成完整报告
```python
# 生成并保存完整报告
report_file = system.optimization.generate_report()

# 报告包含:
# - 系统完整性评分
# - 问题列表
# - 升级建议
# - 清理建议
# - 学习参考资料
```

---

## 📊 检查项目详解

### 系统完整性检查

| 检查项 | 权重 | 说明 |
|--------|------|------|
| 核心文件 | 20 分/个 | stock_v13_system.py 等 |
| 小助手模块 | 10 分/个 | 核心小助手 12 个 |
| 必要目录 | 自动创建 | reports/, data/, live_trading/ |
| 磁盘空间 | 10 分 | 最小 1GB |

**评分标准**:
- 90-100: 优秀
- 80-89: 良好
- 70-79: 一般
- <70: 需要立即修复

### 小助手 BUG 检查

| 检查项 | 说明 |
|--------|------|
| 语法检查 | Python 语法是否正确 |
| 导入检查 | 模块是否可正常导入 |
| 实例化检查 | 类是否可正常实例化 |
| 方法测试 | 关键方法是否可执行 |

### 清理策略

| 类型 | 保留期限 | 示例 |
|------|----------|------|
| 报告文件 | 30 天 | reports/*.json |
| 缓存文件 | 3 天 | data/cache/* |
| 日志文件 | 7 天 | *.log |
| 临时文件 | 立即 | *.tmp, *.bak |
| Python 缓存 | 立即 | __pycache__/ |

---

## 📋 使用场景

### 场景 1: 每日系统检查
```python
# 每天开盘前执行
system = StockV13System()
result = system.optimization.check_system_integrity()

if result['score'] < 80:
    print("⚠️ 系统需要维护！")
    # 查看详细问题
    for issue in result['issues']:
        print(f"  - {issue}")
```

### 场景 2: 发现异常时
```python
# 某个小助手工作不正常
system.optimization.check_assistant_bugs('trading_assistant')

# 查看具体哪个方法有问题
```

### 场景 3: 系统升级前
```python
# 获取升级建议
recommendations = system.optimization.generate_upgrade_recommendations()

# 根据建议制定升级计划
for item in recommendations['critical']:
    print(f"紧急：{item}")
```

### 场景 4: 磁盘空间不足
```python
# 查看可以清理什么
cleanup = system.optimization.cleanup_old_files(dry_run=True)
print(f"可释放空间：{cleanup['space_to_free']/1024/1024:.2f}MB")

# 执行清理
# cleanup = system.optimization.cleanup_old_files(dry_run=False)
```

---

## 📄 报告格式

生成的报告为 JSON 格式，包含：

```json
{
  "timestamp": "2026-03-14T23:29:00",
  "integrity": {
    "score": 95,
    "core_files": [...],
    "assistants": [...],
    "issues": [...]
  },
  "recommendations": {
    "critical": [],
    "important": [],
    "optional": [],
    "learning": []
  },
  "cleanup": {
    "files_scanned": 42,
    "files_to_delete": 3,
    "space_to_free": 1532
  },
  "summary": {
    "score": 95,
    "critical_issues": 0,
    "important_issues": 1,
    "files_to_cleanup": 3,
    "space_to_free_mb": 1.46
  }
}
```

---

## 🔧 配置选项

在 `optimization_assistant.py` 中可调整：

```python
self.config = {
    'max_report_age_days': 30,      # 报告保留天数
    'max_log_age_days': 7,          # 日志保留天数
    'max_cache_age_days': 3,        # 缓存保留天数
    'min_disk_space_mb': 1000,      # 最小磁盘空间 (MB)
}
```

---

## 📈 与其他小助手的关系

```
StockV13System
├── data / ta / momentum / ...  ← 业务小助手
├── trading / tail_pick          ← 交易功能
└── optimization                 ← 系统守护者 ⭐
    ├── 检查业务小助手状态
    ├── 评估系统完整性
    ├── 提供升级建议
    └── 清理过期文件
```

---

## 🎯 使用建议

### 每日必做
- [ ] 开盘前执行一次完整性检查

### 每周必做
- [ ] 执行一次完整报告生成
- [ ] 清理过期文件（预览模式）

### 每月必做
- [ ] 执行一次实际清理
- [ ] 审查升级建议
- [ ] 学习参考资料

### 按需执行
- [ ] 发现异常时检查对应小助手
- [ ] 系统升级前生成建议报告

---

**状态**: ✅ 系统优化提升小助手已就位

**职责**: 守护系统完整性，持续优化提升

**口号**: 让系统始终保持最佳状态！
