# 网络能力工具选择矩阵

> 最后更新：2026-10-17
> 维护者：可悦

---

## 📊 工具总览

| 工具 | 类型 | 安装状态 | 最佳用途 | 限制 |
|------|------|---------|---------|------|
| **Playwright** | Python库 | ✅ 已安装 | JS渲染页面、复杂交互、登录态 | 需手动管理context |
| **agent-browser** | CLI工具 | ✅ 已安装 | 快速自动化、多会话、状态持久化 | npm工具，需命令行调用 |
| **web_fetch** | 内置工具 | ✅ 可用 | 静态页面、API调用、快速获取 | 不支持JS渲染 |
| **browserforge** | Python库 | ✅ 已安装 | 反指纹、绕过检测 | 需配合其他工具使用 |
| **crawlee** | Python库 | ✅ 已安装 | 大规模爬虫、队列管理 | 学习成本高 |

---

## 🎯 任务→工具映射表

### L0 - 静态内容（最快）
```
任务类型：文档获取、API响应、静态网页
推荐工具：web_fetch
示例：
- 获取新闻文章全文
- 抓取JSON API数据
- 读取静态HTML页面
```

### L1 - 搜索与查询
```
任务类型：关键词搜索、资讯获取
推荐工具：web_fetch + Bing搜索
示例：
- 搜索最新行业资讯
- 查询天气/汇率
- 获取公开数据
```

### L2 - JS渲染页面（中等复杂度）
```
任务类型：动态内容、SPA应用、需要执行JS
推荐工具：Playwright
示例：
- B站视频信息获取
- 头条文章全文
- 知乎问题回答
- 需要登录的页面（提供Cookie）
```

### L3 - 反爬对抗（高复杂度）
```
任务类型：强反爬网站、需绕过检测
推荐工具：agent-browser + browserforge
示例：
- 抖音/视频号数据采集
- 公众号文章获取
- 需要规避检测的网站
```

### L4 - 大规模采集（工程级）
```
任务类型：海量数据、定时抓取、队列管理
推荐工具：crawlee
示例：
- 全站数据采集
- 定时监控任务
- 分布式爬虫
```

---

## 🔧 工具使用规范

### Playwright（推荐主力）
```python
from playwright.sync_api import sync_playwright

# 基础用法
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://example.com')
    content = page.content()
    
# 登录态管理
context = browser.new_context(storage_state='cookies.json')
page = context.new_page()

# 反检测
browser = p.chromium.launch(
    headless=True,
    args=['--disable-blink-features=AutomationControlled']
)
```

### agent-browser（快速自动化）
```bash
# 基础导航
agent-browser open https://example.com
agent-browser snapshot -i --json

# 多会话
agent-browser --session admin open site.com
agent-browser --session admin state load auth.json

# 截图/PDF
agent-browser screenshot page.png
agent-browser pdf report.pdf
```

### web_fetch（轻量级）
```python
# 内置工具，直接调用
# 适合：静态页面、API、无需JS执行
```

---

## ⚠️ 常见陷阱

1. **不要用web_fetch抓取JS渲染页面** → 返回空内容
2. **不要忽略登录态** → 提前准备好cookies.json
3. **不要高频访问同一站点** → 添加延迟，避免封IP
4. **不要硬编码API Key** → 使用环境变量或配置文件
5. **不要混用工具** → 同一任务选择一种工具贯穿始终

---

## 📋 任务选择决策树

```
开始
  │
  ├─ 需要JS执行？ ──YES──→ Playwright / agent-browser
  │                          │
  │                          ├─ 需要多会话？ ──YES──→ agent-browser
  │                          │
  │                          └─ 需要反检测？ ──YES──→ agent-browser + browserforge
  │
  └─ 静态内容？ ──YES──→ web_fetch
         │
         └─ 需要搜索？ ──YES──→ web_fetch + Bing API
```

---

## 🔄 工具迁移记录

| 日期 | 变更内容 | 原因 |
|------|---------|------|
| 2026-10-17 | 建立本矩阵 | 统一工具选择标准 |
| 2026-10-17 | 移除微信推送配置 | 彻底清理 |
| 2026-10-17 | 修正sensenova模型配置 | API响应model_id不匹配 |

---

## ✅ 验证清单

每次任务前检查：
- [ ] 明确任务类型（L0-L4）
- [ ] 选择对应工具
- [ ] 确认工具已安装
- [ ] 准备必要配置（cookies/API Key）
- [ ] 设置超时和重试策略

---

_本文件由系统维护，随工具链更新而修订_
