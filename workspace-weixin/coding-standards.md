# 编码规范与最佳实践 Checklist

**创建日期**: 2026-07-14
**适用范围**: 所有 Python/JS/Shell 脚本编写

---

## 1. 语法/基础 — 边界全覆盖

### 规则
- 每个函数必须考虑：空输入、None/null、空字符串、0值、负数、超大值
- 列表操作前检查长度 `if len(lst) == 0`
- 字典访问用 `.get()` 而非 `[]`，除非确定key存在
- 字符串操作注意 encoding（Windows中文路径必用utf-8）

### 自检问题
- [ ] 空输入会崩吗？
- [ ] 边界值（0, -1, 极大值）处理了吗？
- [ ] 类型不匹配会报错吗？

### 示例
```python
# ❌ 差
def process_list(items):
    return [x * 2 for x in items]

# ✅ 好
def process_list(items):
    if not items:
        return []
    return [x * 2 for x in items if isinstance(x, (int, float))]
```

---

## 2. 项目结构 — 全局视角

### 规则
- 动代码前先 read 相关模块，理解调用链
- 修改公共函数后，grep 所有调用点确认同步
- 保持现有命名约定和目录结构一致
- 新文件放正确位置，不随意新建目录

### 工作流
1. `read` 目标文件 → 理解当前逻辑
2. `exec grep` 搜索调用点 → 确认影响范围
3. 修改核心逻辑 → 同步修改所有调用方
4. `read` 改后的文件 → 二次确认

---

## 3. 调试能力 — 系统化

### 规则
- **先看错误栈**：文件→行号→具体错误信息
- **二分法定位**：注释一半代码，逐步缩小范围
- **日志优先**：关键变量打印出来看
- **最小复现**：剥离无关逻辑，只留bug核心

### 调试步骤
1. 读错误信息，确定文件和行号
2. read 该文件，看上下文
3. 加 print/log 输出关键变量
4. 运行验证，确认假设
5. 修复后删除临时日志

---

## 4. 重构嗅觉 — 主动优化

### 坏味道清单（出现就修）
- 重复代码块 → 提取函数
- 函数超过50行 → 拆分
- 嵌套超过3层 → 提前return/提取
- 魔法数字 → 命名常量
- 长参数列表 → 对象/配置类封装

### 原则
- 小步重构，改一行跑一次
- 不改功能的前提下优化结构
- 重构后必须验证原有功能正常

---

## 5. 测试意识 — 关键路径覆盖

### 规则
- 核心业务逻辑必须有验证
- 简单脚本用 assert + print 快速验证
- 复杂逻辑写独立测试函数
- 至少覆盖：正常路径 + 2个异常路径

### 快速测试模板
```python
def test_xxx():
    # 正常路径
    assert func(normal_input) == expected
    
    # 边界：空
    assert func([]) == expected_empty
    
    # 边界：None
    result = func(None)
    assert result is None or has_error_handling
    
    print("✅ 测试通过")
```

---

## 6. 性能意识 — 复杂度分析

### 规则
- 循环内避免 O(n²) 操作（如 list.index, list.remove）
- 大文件读取用逐行而非 read() 全读
- 频繁查找用 dict/set 而非 list
- 字符串拼接用 join 而非 +=

### 自检
- [ ] 时间复杂度是多少？
- [ ] 数据量翻倍会怎样？
- [ ] 有没有不必要的重复计算？

---

## 7. 安全意识 — 防御性编程

### 规则
- 用户输入永远不可信（即使是内部脚本）
- 文件路径拼接用 os.path 或 pathlib，不直接用 +
- SQL/命令注入：永远用参数化查询
- 敏感信息不硬编码

### 示例
```python
# ❌ 危险
os.system(f"rm {user_path}")

# ✅ 安全
import shlex
os.system(f"rm {shlex.quote(user_path)}")
```

---

## 8. 错误处理 — 分层异常

### 规则
- 外层捕获，内层抛出具体异常
- 不要裸 except: 要 except SpecificError:
- 关键操作有 fallback/重试机制
- 错误信息要有用（包含上下文）

### 模板
```python
try:
    result = risky_operation()
except FileNotFoundError as e:
    log.error(f"文件不存在: {e.filename}")
    return default_value
except ValueError as e:
    log.error(f"数据格式错误: {e}")
    raise
```

---

## 9. 代码可读性 — 清晰表达

### 规则
- 变量名见名知意（不用 a/b/c，用 count/status/data）
- 函数名动词开头（get_users, validate_input）
- 每段代码不超过15行无空行
- 复杂逻辑必有注释解释"为什么"而非"做什么"

### 命名约定
- 函数/变量：snake_case
- 常量：UPPER_SNAKE_CASE
- 类名：PascalCase
- 私有方法：_prefix

---

## 10. 版本管理 — Git 规范

### 规则
- 每次有意义的修改都 commit
- commit message 格式：`[模块] 简短描述`
- 大改动用多个小commit，不是一次性all
- 关键修改前 git diff 确认变更

### Windows 环境
```powershell
git status        # 先看状态
git diff          # 再看变更
git add <file>    # 选择性地加
git commit -m "[scripts] fix: 修复中文路径读写问题"
```

---

## 11. 依赖管理 — 最小锁定

### 规则
- 能用标准库就不用第三方
- 第三方库锁定版本（pip freeze > requirements.txt）
- 安装前查安全漏洞（pip audit）
- 不用的依赖及时移除

### Python 环境检查
```python
# 写代码前检查依赖是否可用
try:
    import pandas
except ImportError:
    # 回退到标准库
    import csv
```

---

## 12. 环境一致性 — 可复现

### 规则
- 脚本注明 Python 版本要求
- 路径使用绝对路径或相对于项目根目录
- 编码统一 utf-8（Windows特别注意）
- 运行环境差异在代码中处理（os.name, platform）

### 环境检测模板
```python
import sys
import os

# 版本检查
assert sys.version_info >= (3, 8), "需要 Python 3.8+"

# 路径处理
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

# 编码处理（Windows）
if sys.platform == 'win32':
    import io
    sys.stdout.reconfigure(encoding='utf-8')
```

---

## 执行流程（每次编码任务）

### 开始前
1. 读现有代码，理解上下文
2. 确认依赖可用
3. 确认环境（Python版本/路径/编码）

### 编写中
1. 遵循命名约定
2. 边界情况同步处理
3. 遇到重复代码 → 立即提取函数

### 完成后
1. 运行快速验证测试
2. grep 确认没有遗漏的调用点
3. git diff 确认变更范围
4. 错误信息完整可读

---

_由可悦🌸 创建，持续更新_
