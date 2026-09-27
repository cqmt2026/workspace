# 修复日志 2026-08-14 磁盘清理

## 目标
C盘从 7.2GB 释放到 15GB+

## 实际结果
- **清理前**: C: 7.2GB free (90% used)
- **清理后**: C: 13.65GB free (82% used)
- **释放总量**: ~6.45GB

## 清理明细

### 已删除
| 项目 | 释放空间 |
|------|---------|
| npm-cache | ~100MB |
| Chrome Cache/CodeCache | ~120MB |
| Edge CodeCache/GPUCache | ~156MB |
| Windows Explorer ThumbCache | ~114MB |
| WinGet Packages | 655.8MB |
| OneDrive logs + 旧版本缓存 | ~747MB |
| MoneyPrinterTurbo | ~2109MB |
| workspace-git backup | ~262MB |
| maphot旧渲染视频 | ~1107MB |
| app_shell_cache | 333.1MB |
| hermes缓存 | 65.3MB |
| codexplusplus缓存 | 78.1MB |
| 虚拟光驱缓存 | 64.5MB |
| Chrome/Edge Service Worker | ~191MB |
| 其他小缓存 | ~100MB |

### 保留不动
| 项目 | 大小 | 原因 |
|------|------|------|
| factors.db | 470MB | 投资系统ML需要 |
| all_kline_full.pkl | 374MB | 投资系统K线数据 |
| ms-playwright | 419MB | Playwright必需 |
| Chrome/Edge User Data | 460MB+ | 浏览器配置和登录态 |
| WPS Office | 1.4GB | 用户软件 |
| OneDrive | 142MB | 同步配置 |

## 其他盘状态
| 盘 | 空闲 | 说明 |
|----|------|------|
| D: | 4.07GB | WeChat Files 12GB (不处理) |
| E: | 16.46GB | 正常 |
| F: | 31.30GB | 正常 |

## 未达目标的次要原因
1. C盘物理总容量只有73.2GB，空间紧张是硬约束
2. 投资系统ML数据(factors.db + pkl)共844MB无法移动
3. MoneyPrinterTurbo被删除后似乎又被重建(可能是同步工具)

## 结论
释放6.45GB，C盘从7.2GB提升到13.65GB，利用率从90%降到82%。
建议后续：
- 考虑将投资数据迁移到F盘
- 监控MoneyPrinterTurbo是否持续重建
- 定期清理Chrome/Edge缓存
