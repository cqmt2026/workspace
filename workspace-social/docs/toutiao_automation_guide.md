# 头条号浏览器自动化 - 使用指南

**更新时间**: 2026-04-08 10:52  
**状态**: ✅ Cookie 有效，部分页面可用

---

## 📊 测试结果

### Cookie 状态
- **状态**: ✅ 有效
- **解析**: 29 个 Cookie 项
- **登录**: 成功
- **有效期**: 至 2026-06-07

### 页面可用性

| 页面 | URL | 状态 | 说明 |
|------|-----|------|------|
| **主页** | `/profile_v4/index` | ✅ 可用 | 可获取账号数据 |
| **文章管理** | `/article/manage` | ❌ 502 | 服务器故障 |
| **微头条** | `/wap/article/manage` | ⚠️ 待测试 | - |

---

## 🎯 已实现功能

### 1. 主页数据采集

**脚本**: `toutiao_collector.py`

**功能**:
- ✅ 访问主页
- ✅ 提取页面文本
- ✅ 截图保存
- ✅ JSON 格式输出

**数据示例**:
```
- 头条号已发布文章：2144 篇
- 粉丝数：30
- 累计阅读：8,168
- 文章标题列表
- 发布时间
- 阅读量
```

---

## 📄 已创建脚本

| 脚本 | 用途 | 状态 |
|------|------|------|
| `toutiao_automation.py` | 完整自动化 | ⚠️ 需优化选择器 |
| `toutiao_collector.py` | 数据采集 | ✅ 可用 |
| `toutiao_diagnose.py` | 页面诊断 | ✅ 可用 |
| `toutiao_browser_test.py` | Cookie 测试 | ✅ 可用 |

---

## 🚀 使用方法

### 快速测试

```bash
python C:\Users\Administrator\.openclaw\workspace\workspace-social\scripts\toutiao_collector.py
```

### 输出文件

**位置**: `workspace-social/data/`

**格式**:
- `toutiao_data_YYYYMMDD_HHMMSS.json` - 采集数据
- `collect_home_YYYYMMDD_HHMMSS.png` - 页面截图

---

## 📊 主页可采集数据

### 账号基本信息
- 已发布文章数
- 粉丝数
- 累计阅读量

### 文章列表
- 文章标题
- 发布时间
- 阅读量
- 评论数

### 收益数据
- 累计收益
- 单笔收益

---

## ⚠️ 限制说明

### 当前限制

1. **文章管理页面不可用**
   - URL: `/article/manage`
   - 状态：502 Bad Gateway
   - 原因：头条号服务器故障

2. **选择器需要优化**
   - 头条号页面使用动态类名
   - 需要通过文本内容提取数据

### 解决方案

**方案 A**: 使用文本分析
- 从页面文本中提取关键信息
- 不依赖 HTML 结构

**方案 B**: 等待服务器恢复
- 文章管理页面恢复后重试
- 使用完整的自动化流程

**方案 C**: 使用官方 API
- 需要申请开发者权限
- 稳定可靠但需要审批

---

## 💡 建议工作流

### 当前可用流程

```
1. 运行采集脚本
   ↓
2. 从主页获取账号数据
   ↓
3. 分析文章标题和阅读量
   ↓
4. 保存 JSON 数据
   ↓
5. 用于内容创作参考
```

### 完整流程（待服务器恢复）

```
1. 登录头条号
   ↓
2. 获取文章列表
   ↓
3. 采集文章详情
   ↓
4. 分析数据
   ↓
5. 发布新内容
```

---

## 📋 下一步

### 立即可做

1. **运行采集脚本**
   ```bash
   python scripts/toutiao_collector.py
   ```

2. **查看采集数据**
   - 位置：`workspace-social/data/`
   - 格式：JSON + PNG

3. **分析数据**
   - 文章标题
   - 阅读量分布
   - 发布时间规律

### 等待服务器恢复

1. **重试文章管理页面**
   ```bash
   python scripts/toutiao_automation.py
   ```

2. **获取完整文章列表**
   - 文章状态
   - 编辑/删除操作
   - 数据分析

---

## 🔒 安全提示

- ⚠️ **不要分享 Cookie**
- ⚠️ **定期更新**（每周一次）
- ⚠️ **不要上传到公开仓库**
- ⚠️ **本地使用**

---

## 📄 相关文件

| 文件 | 路径 |
|------|------|
| Cookie 配置 | `config/toutiao_accounts.json` |
| 操作指南 | `docs/toutiao_cookie_guide.md` |
| 状态报告 | `docs/toutiao_status_20260408.md` |
| 采集脚本 | `scripts/toutiao_collector.py` |
| 数据输出 | `data/toutiao_data_*.json` |

---

**结论**: Cookie 有效，主页可采集数据，文章管理页面等待服务器恢复！🌸
