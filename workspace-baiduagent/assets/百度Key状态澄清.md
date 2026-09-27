# 百度Key状态澄清（2026-08-29）

## 问题回顾
用户质疑：为什么之前说百度Key无效？

## 真相
**百度Key根本没问题！** `KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0` 完全有效。

## 验证结果
```
place/v2/search: status=302 "天配额超限"  →  Key有效，配额用完
geocoding/v3:    status=0 成功            →  Key完全有效
suggestion:      status=302 配额超限      →  Key有效，配额用完
```

## 我的错误
之前测试时出现了误判，可能原因：
1. 用了截断的Key（错误示范）
2. 测试脚本写错参数
3. 混淆了不同API的响应状态

## 正确认知
| 平台 | Key状态 | 今日配额 | 可用接口 |
|------|---------|---------|---------|
| 高德 | ✅有效 | ❌30万耗尽 | geocoding可用 |
| 百度 | ✅有效 | ❌5万耗尽 | **geocoding可用** |
| 腾讯 | ✅有效 | ❌5千耗尽 | geocoding可用 |

## 百度geocoding可立即使用
- 接口：`https://api.map.baidu.com/geocoding/v3/`
- 功能：地址→坐标转换
- 配额：独立计算，不受place限制
- 用途：补充CRM中缺失坐标的客户

---
_小度 | 2026-08-29 20:10_
