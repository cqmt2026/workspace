# TOOLS.md - 本地工具笔记（百都系统）

**最后更新**: 2026-09-06

---

## 销售流程

```
客户数据 → 话术生成 → 拨打 → 记录 → 分析 → 优化
```

## 核心数据

- **客户名单**: workspace-baiduagent/data/master/ (61+个CSV)
- **源数据**: workspace-baiduagent/data/source/ (amap/gxq/weijkw)
- **电话脚本**: assets/电话沟通脚本_v4.md（SPIN+BANT双轮+分级授权）
- **行业完成度盘点**: scripts/core/industry_completion.py（v4：贝叶斯线索评分预留）
- **AI话术生成器**: scripts/modules/ai_script_generator.py（借鉴Prospex AI Content Engine）
- **行业彻底补抓**: scripts/modules/fetch_industry_complete.py（v2：Fast/Detailed双模式+分区域+多源融合）

## 核心脚本

| 脚本 | 功能 |
|------|------|
| client_manager.py | 客户管理 |
| script_generator.py | 话术生成 |
| call_logger.py | 拨打记录 |
| analytics.py | 数据分析 |
| industry_completion.py | 行业完成度盘点（v4） |
| fetch_industry_complete.py | 行业彻底补抓（v2） |
| ai_script_generator.py | AI话术生成器（新） |

## 抖音内容获取管线

| 脚本 | 功能 |
|------|------|
| `scripts/tools/douyin_pipeline.py` | 抖音视频内容获取完整管线 |
| `scripts/tools/correct_asr.py` | ASR修正器（规则修正+预留LLM接口） |

**用法**：
```bash
python scripts/tools/douyin_pipeline.py "https://v.douyin.com/xxx/"
```

**输出目录**：`assets/reports/`（子系统内）

**依赖**：
- 抖音Cookies：`workspace/workspace-math/L3-音频/douyin_cookies.json`
- Whisper：`openai-whisper`（自动加载tiny→base降级）
- Playwright：浏览器降级方案（API失败时使用）

**降级策略**：
1. API元数据 → 视频下载 → Whisper转写 → ASR修正 → 海报生成
2. 若API/下载失败 → 自动启用浏览器兜底（读取页面文案）

**ASR修正能力**：
- 50+条行业术语修正规则（GEO、DeepSeek、平台名称等）
- 可扩展词典，支持后续接入LLM润色

---

## 高德API

- **Key**: 已配置于.env
- **能力**: POI搜索、周边搜索
- **限制**: 5万次/天

---
_由小度维护，2026-09-06更新：融合Prospex设计理念，新增AI话术生成器_

---

## 外部工具（2026-09-16更新）

| 工具 | 用途 | 状态 |
|------|------|------|
| **企查查专业版** | 批量筛选+获取电话，每日30-50条线索（**待主人授权**） | ⏳待授权 |
| 企查查/天眼查 | 补充低电话覆盖率行业（人力资源/软件信息等） | ⏳待授权 |
| **360搜索** | **替代web_search**（2026-09-16验证可用） | ✅已验证 |
| Bing搜索 | 验证企业信息/百度现状 | ✅可用 |
| 百度推广后台 | 查看竞品投放情况 | ✅可用 |
| Excel/CSV | 名单整理+导出 | ✅可用 |

**⚠️ 重要更新（2026-09-16）**：
- web_search工具暂时不可用（provider disabled）
- 已验证替代方案：web_fetch + 360搜索（so.com）
- 其他备用方案：搜狗搜索（sogou.com）、神马搜索（sm.cn）
- 详见：memory/corrections/2026-09-16_web_search故障排查.md
