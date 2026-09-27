# corrections.md - 踩坑记录

**更新时间**: 2026-05-23
**来源**: 错题本实战

---

## 【已记录】

### 1. 云函数跨环境传参丢坐标
| 字段 | 内容 |
|------|------|
| 问题 | 用户框选坐标传到云函数，变成 null，导致 fallback 全图 OCR |
| 根因 | 微信云函数跨环境传参时，JSON 对象参数序列化丢失 |
| 触发条件 | 前端传 cropBox 对象给云函数时 |
| 解法 | 前端 Canvas 裁剪，只传 fileID，云函数不收坐标 |
| 来源 | 错题本 add.js confirmSelection() |
| 日期 | 2026-05-22 |

### 2. 组件内 Canvas node() 返回 undefined
| 字段 | 内容 |
|------|------|
| 问题 | 组件中用 createSelectorQuery() 获取 canvas 节点失败 |
| 根因 | 未用 .in(this) 绑定组件实例 |
| 触发条件 | 在自定义组件内查询自身模板内 canvas |
| 解法 | createSelectorQuery().in(this) |
| 来源 | 错题本 add.js |
| 日期 | 2026-05-22 |

### 3. canvasToTempFilePath 报错 invalid canvas
| 字段 | 内容 |
|------|------|
| 问题 | canvasToTempFilePath 提示 invalid canvas |
| 根因 | 传的 canvas 字符串 id，而非 canvas 对象实例 |
| 触发条件 | 用 canvas-id 老写法时 |
| 解法 | 传 res.node（canvas实例对象），不是字符串 id |
| 来源 | 错题本 add.js cropWithCanvas |
| 日期 | 2026-05-22 |

### 4. token 无缓存重复申请
| 字段 | 内容 |
|------|------|
| 问题 | 每次 OCR 都重新申请 access_token，很慢 |
| 根因 | 没有缓存机制 |
| 触发条件 | 连续多次 OCR 时 |
| 解法 | 内存缓存 tokenCache，过期前5分钟重新申请 |
| 来源 | 错题本 cloudfunctions/ocr/index.js |
| 日期 | 2026-05-22 |

### 5. 裁剪结果模糊
| 字段 | 内容 |
|------|------|
| 问题 | 导出的裁剪图片模糊不清 |
| 根因 | destWidth/destHeight 设的太小 |
| 触发条件 | 使用 canvasToTempFilePath 导出时 |
| 解法 | destWidth/destHeight 保持与 canvas 物理尺寸一致 |
| 来源 | 错题本 add.js |
| 日期 | 2026-05-22 |

### 6. setData 异步导致读不到新值
| 字段 | 内容 |
|------|------|
| 问题 | setData 后立即读取 data，得到旧值 |
| 根因 | setData 是异步的 |
| 触发条件 | onLoad 中 setData 后立即读取 |
| 解法 | setData callback 或 wx.nextTick |
| 来源 | 小程序通用 |
| 日期 | 2026-05-23 |

### 7. setData 遇到 undefined 导致 SystemError
| 字段 | 内容 |
|------|------|
| 问题 | 小程序页面报错 Cannot read properties of undefined (reading 'setChanges') |
| 根因 | 旧数据字段为 undefined，新字段（如 practice/knowledge）旧数据没有，setData 遇到 undefined 报错 |
| 触发条件 | 页面展示有新增字段的旧数据 |
| 解法 | 构建全新的安全对象，不用 setData 合并；所有字段给默认值；用 JSON.parse(JSON.stringify()) 清除 undefined |
| 来源 | 错题本 detail.js loadDetail |
| 日期 | 2026-05-23 |

---

## 8. AI讲题解析失败率高（2026-05-24）
| 字段 | 内容 |
|------|------|
| 问题 | solveQuestion云函数正则解析失败时显示原始乱码 |
| 根因 | Prompt不够结构化+正则匹配脆弱+tokens太少(400)+兜底粗暴 |
| 触发条件 | AI返回格式稍有不同（多了空格/换了标点） |
| 解法 | v4.0升级：JSON格式Prompt+tokens扩到600+JSON解析兜底+步骤用\n分隔 |
| 来源 | solveQuestion v3.3→v4.0 |

## 9. detail页面不支持追问（2026-05-24）
| 字段 | 内容 |
|------|------|
| 问题 | 用户看完AI讲题无法追问 |
| 根因 | 原始设计只有单向展示 |
| 解法 | v4.0新增追问入口+输入框+调用solveQuestion追加步骤 |
| 来源 | detail.js/wxml/wxss v4.0 |

## 10. AI返回残缺JSON导致steps为空（2026-05-24）
| 字段 | 内容 |
|------|------|
| 问题 | AI输出"{\"steps\": ,...}"空数组，页面无法分步显示 |
| 根因 | MiniMax模型思考过程吞掉了steps字段，Prompt没给足够示例 |
| 触发条件 | AI思考过程干扰JSON格式 |
| 解法 | v5.0：Prompt加完整示例+四种字段独立提取+云函数端解析steps |
| 来源 | solveQuestion v3.3→v5.0 |

## 11. practice_questions集合不存在（2026-05-24）
| 字段 | 内容 |
|------|------|
| 问题 | generatePractice报错 collection not exists |
| 根因 | 数据库没有创建practice_questions集合 |
| 解法 | 云开发控制台 → 数据库 → 创建集合 → 填practice_questions |
| 来源 | generatePractice云函数 |

_由 可悦🌸 2026-05-24_

## 2026-06-13 [日志机制与记忆系统] 自动化必须绑定系统

### 问题
昨晚对话丢失，日志规则写在文档里但没有技术机制强制执行。

### 根因
自动化机制与系统核心是分离的，不是系统的一部分。

### 固化措施
- [x] 所有Cron任务必须通过run_with_log.py执行并记录日志
- [x] task_logger.py作为所有自动化的基础设施
- [x] Supermemory提取每30分钟自动运行
- [x] corrections.md由log_audit.py每日自动更新新踩坑
- [x] 系统迭代时，所有自动化必须同步迁移，不得丢失

_由可悦🌸 维护_
