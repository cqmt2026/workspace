# 头条号 Cookie 获取指南

**更新时间**: 2026-04-08 10:10  
**适用**: 头条号后台登录

---

## 📱 获取步骤

### 步骤 1: 打开头条号后台

**网址**: https://mp.toutiao.com

在浏览器中打开（推荐 Chrome/Edge）

---

### 步骤 2: 登录账号

**方式**:
- 扫码登录（推荐）
- 密码登录
- 手机验证码登录

确保成功进入头条号后台主页

---

### 步骤 3: 打开开发者工具

**快捷键**: `F12` (Windows) / `Cmd+Option+I` (Mac)

**或者**:
- 点击浏览器右上角"..."
- 选择"更多工具"
- 点击"开发者工具"

---

### 步骤 4: 切换到 Network 标签

```
开发者工具 → 顶部标签 → Network（网络）
```

---

### 步骤 5: 刷新页面

**快捷键**: `F5` 或 `Ctrl+R`

确保看到 Network 标签中有新的请求列表

---

### 步骤 6: 查找 Cookie

1. **点击第一个请求**（通常是 `index` 或 `home`）
2. **切换到 Headers 标签**
3. **向下滚动到 Request Headers 区域**
4. **找到 `Cookie` 字段**
5. **复制完整 Cookie 字符串**

---

## 🔍 Cookie 示例

```
Cookie: tt_webid=7123456789012345678; tt_webid_v2=7123456789012345678; 
passport_auth_status=sid%3A...; sid_guard=...; uid_guard=...; 
sid_tt=...; sessionid=...; __tasessionId=...
```

**注意**: 
- Cookie 是很长的字符串
- 包含多个 `key=value` 对，用 `; ` 分隔
- 复制完整的整行内容

---

## 📝 粘贴到配置文件

### 配置文件路径

```
workspace-social/config/toutiao_accounts.json
```

### 粘贴位置

```json
{
  "accounts": [
    {
      "name": "主账号",
      "credentials": {
        "cookie": "在此粘贴 Cookie 字符串"
      }
    }
  ]
}
```

---

## ✅ 验证 Cookie

### 方法 1: 测试脚本

```bash
cd workspace-social
python bank/房产专业/scripts/auto_publish_toutiao.py --test-login
```

如果显示"登录成功"，说明 Cookie 有效

### 方法 2: 手动验证

1. 打开新的无痕浏览器窗口
2. 访问 https://mp.toutiao.com
3. 如果自动登录成功，说明 Cookie 有效

---

## ⚠️ 注意事项

### Cookie 有效期

- **有效期**: 约 7 天
- **建议**: 每周更新一次
- **提醒**: 失效后需重新登录获取

### 安全提示

- ⚠️ **不要分享 Cookie**：包含账号登录凭证
- ⚠️ **不要上传到公开仓库**：此文件应加入 `.gitignore`
- ⚠️ **定期更新**：避免失效影响发布

### 常见问题

**Q: Cookie 复制后无法使用？**

A: 检查是否完整复制，确保包含所有 `key=value` 对

**Q: 提示 Cookie 失效？**

A: 重新登录头条号后台，获取新的 Cookie

**Q: 多账号如何配置？**

A: 在 `accounts` 数组中添加多个账号对象

---

## 📋 配置完成后的工作流

```
09:00 晨间采集（百家号 + 头条号）
   ↓
10:00 内容创作
   ↓
12:00 质量检查
   ↓
14:00 发布（百家号 + 头条号）← 头条号已启用
   ↓
20:00 数据复盘
```

---

**配置完成后即可启用头条号发布功能！** 🌸
