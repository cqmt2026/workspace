# 修复日志 - Playwright Chromium 浏览器安装

| 项目 | 内容 |
|------|------|
| **日期** | 2026-07-18 |
| **子系统** | Pixelle-Video |
| **问题** | Playwright Chromium 浏览器引擎未安装 |
| **错误信息** | `Executable doesn't exist at ...\chromium_headless_shell-1208\...` |
| **根因** | Playwright 包已升级到 v1.58.0，需要 chromium-1208，但只安装了旧版 chromium-1169 |
| **修复方案** | 运行 `playwright install chromium` 安装对应版本 |
| **验证结果** | ✅ `playwright.sync_api` 启动 Chromium headless 浏览器成功，输出 "OK" |
| **严重度** | 中 |
| **影响范围** | Pixelle-Video 的 HTML 渲染到图片功能 |
| **备注** | 旧版 chromium-1169 和 chromium_headless_shell-1169 被自动清理 |