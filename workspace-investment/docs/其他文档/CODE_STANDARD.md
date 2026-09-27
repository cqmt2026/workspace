# 股票 V13.2 系统 - 代码规范

**创建时间**: 2026-03-17

## 1. 文件结构

### 1.1 文件头
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小助手名称
功能描述
作者：股票 V13.2 系统
创建时间：YYYY-MM-DD
更新时间：YYYY-MM-DD
"""
```

## 2. 命名规范

- **文件名**: 小写 + 下划线（assistant_name.py）
- **类名**: 大驼峰（AssistantName）
- **函数名**: 小写 + 下划线（function_name）
- **变量名**: 小写 + 下划线（variable_name）

## 3. 文档规范

- 每个文件必须有文档字符串
- 每个类必须有文档字符串
- 每个公共方法必须有文档字符串

## 4. 导入规范

```python
# 标准库
import os
import sys

# 第三方库
import requests

# 本地模块
from data_assistant import DataAssistant
```

## 5. 错误处理

```python
try:
    # 代码
    pass
except Exception as e:
    print('错误：{}'.format(e))
```

## 6. 日志规范

```python
from logger import logger
logger.info('信息')
```
