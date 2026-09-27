# 修复日志 - 2026-08-17 光伏获客系统迭代

## 完成内容

### ① 数据持久化修复（P0）
- **问题**: DB_PATH指向workspace/data/pv.db而非workspace-pv/data/pv.db，每次init_db()重建表导致数据丢失
- **修复**: database.py改用绝对路径 `BASE / "data" / "pv.db"`，不再依赖import config
- **验证**: 集成测试全通过，数据跨次运行保留

### ② 去重优化
- **问题**: solarbe/bjx/nea可能采集到同名不同来源的重复话题
- **修复**: save_results()改为UPSERT逻辑——已存在则比较pv_score，高者覆盖
- **效果**: 避免重复标题占据数据库

### ③ 内容生成模块完善
- 6条每日脚本已可用（5个方向模板）
- 输出到 data/content/ 和 data/output/
- 集成到cron定时任务

### ④ 竞品分析框架
- CompetitorContentAnalyzer: 热点→方向分类→钩子/正文/CTA建议
- 13家头部竞品已录入数据库

## 当前数据状态
| 表 | 记录数 |
|----|--------|
| hot_topics (PV相关) | 24 |
| policies | 16 |
| competitors | 13 |
| system_logs | - |

## 已知问题
1. 竞品内容采集需Playwright接入抖音/头条API（预留接口）
2. 政策自动采集目前返回0条（百度搜索被安全验证拦截）
3. 内容脚本模板偏固定，需A/B测试验证点击率
