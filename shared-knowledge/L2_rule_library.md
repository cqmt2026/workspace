# L2 异常定位规则库
# 每发现一种新错误模式，追加一条规则

## 规则格式
```
- 模式: <错误摘要或错误消息关键词>
  类型: timeout | script_error | db_error | network_error | model_error
  根因: <分析结论>
  修复: <修复方案>
  验证: <验证方法>
```

## 规则列表

### R001: 模型调用超时 (timeout)
- 模式: `last phase: model-call-started`
- 类型: model_error
- 根因: isolated session 启动后调用模型时卡住，通常是模型排队或超时设置不足
- 修复: 增加 timeoutSeconds + 添加更多 fallback 模型
- 验证: 下次触发正常即修复

### R002: 脚本执行超时 (timeout)
- 模式: `last phase: exec-started` 或 `last phase: tool-call-started`
- 类型: timeout
- 根因: 脚本本身执行时间超过 timeoutSeconds
- 修复: 检查脚本是否有死循环或慢操作，适当增加 timeout
- 验证: 手动运行脚本确认

### R003: Python 语法错误
- 模式: `SyntaxError` 或 `ModuleNotFoundError`
- 类型: script_error
- 根因: 脚本修改后未验证语法或依赖缺失
- 修复: 运行 `python -c "import py_compile; py_compile.compile('script.py', doraise=True)"` 检查
- 验证: 语法检查通过

### R004: 数据库连接失败
- 模式: `database` 或 `sqlite3` 或 `OperationalError`
- 类型: db_error
- 根因: 数据库文件被占用、损坏或路径变更
- 修复: 检查文件存在性、权限、完整性
- 验证: 手动连接查询

### R005: 网络请求超时 (network)
- 模式: `timeout` 且包含 `url` 或 `http` 或 `request`
- 类型: network_error
- 根因: 外部API不可达或响应慢
- 修复: 增加重试机制，或检查网络连通性
- 验证: 手动 curl 测试

### R006: 文件不存在
- 模式: `FileNotFoundError` 或 `No such file`
- 类型: script_error
- 根因: 脚本引用的文件被移动或删除
- 修复: 更新路径或恢复文件
- 验证: 文件存在性检查

### R007: 磁盘空间不足
- 模式: `No space left` 或 `disk full`
- 类型: system_error
- 根因: 临时文件或日志过多
- 修复: 运行 auto_cleanup.py 清理
- 验证: 磁盘空间检查

### R008: Gateway重启导致任务中断
- 模式: `job interrupted by gateway restart`
- 类型: system_error
- 根因: Gateway重启时正在运行的任务被中断，不影响下次执行
- 修复: 无需修复，下次自动恢复
- 验证: 下次触发正常即修复

### R009: 投资系统模型调用超时 (agnes-2.0-flash)
- 模式: `last phase: model-call-started` 且模型为 `agnes-2.0-flash`
- 类型: model_error
- 根因: agnes-2.0-flash 模型在投资系统isolated session中调用超时
- 修复: timeout→900s + 添加 deepseek-v4-flash 作为主要fallback
- 验证: 下次触发正常即修复

### R010: 投资系统收盘任务链超时
- 模式: `last phase: model-call-started` 且任务名包含 `INV-`
- 类型: model_error
- 根因: 收盘时段（14:30-17:05）模型调用并发高，孤立session超时
- 修复: timeout→900s + 错开 staggerMs + 添加更多fallback
- 验证: 下次触发正常即修复
- 模式: `last phase: model-call-started` 且模型为 `agnes-2.0-flash`
- 类型: model_error
- 根因: agnes-2.0-flash 模型在投资系统isolated session中调用超时
- 修复: timeout→900s + 添加 deepseek-v4-flash 作为主要fallback
- 验证: 下次触发正常即修复

### R010: 投资系统收盘任务链超时
- 模式: `last phase: model-call-started` 且任务名包含 `INV-`
- 类型: model_error
- 根因: 收盘时段（14:30-17:05）模型调用并发高，孤立session超时
- 修复: timeout→900s + 错开 staggerMs + 添加更多fallback
- 验证: 下次触发正常即修复
- 模式: `last phase: model-call-started` 且模型为 `agnes-2.0-flash`
- 类型: model_error
- 根因: agnes-2.0-flash 模型在投资系统isolated session中调用超时
- 修复: timeout→900s + 添加 deepseek-v4-flash 作为主要fallback
- 验证: 下次触发正常即修复
- 模式: `No space left` 或 `disk full`
- 类型: system_error
- 根因: 临时文件或日志过多
- 修复: 运行 auto_cleanup.py 清理
- 验证: 磁盘空间检查