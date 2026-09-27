# 配置文件

> 百都系统环境配置
> 创建: 2026-08-26

---

## 数据库配置

```python
DB_PATH = "scripts/data/baidu_crm.db"
```

## 路径配置

```python
ASSETS_DIR = "assets"
KNOWLEDGE_DIR = "knowledge"
MEMORY_LOGS_DIR = "memory/logs"
MEMORY_CORRECTIONS_DIR = "memory/corrections"
```

## 外部API

| 服务 | 用途 | 状态 |
|------|------|------|
| 企查查专业版 | 批量获客+电话 | 待开通 |
| Bing搜索 | 企业信息验证 | 已可用 |
| 百度指数 | 行业搜索量 | 免费可用 |

## 业务配置

| 项目 | 配置值 |
|------|--------|
| 日拨打目标 | 15-20通 |
| 周成交目标 | 2-3家 |
| 月成交目标 | 10家 |
| 客户分层标准 | A级≥5000月耗, B级1000-5000, C级<1000 |

---

_由小度维护_