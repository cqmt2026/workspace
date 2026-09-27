# corrections.md - 踩坑记录

## 2026-06-15 EP107竖式问题

### 问题
主人反馈EP107数学动画中的除法竖式布局完全不符合标准手工竖式。

### 根因（多层）

**第1层**：SESSION COMPACTION恢复旧文件
- 修改manim_templates.py后，文件被恢复成旧版本
- edit工具要求内容完全匹配，SESSION COMPACTION后匹配失败
- 反复修改模板无效，最终改写场景文件硬编码

**第2层**：numpy ndarray作为next_to的anchor
- `bar_x = LEFT * 0.5` 生成的是ndarray，Mobject的`next_to()`方法对这个ndarray无效
- 导致竖式所有元素静默失效（坐标变NaN），元素乱飞
- 修复：改用 `move_to(np.array([x, y, 0]))`

**第3层**：manim Text的width语义
- `Text.move_to(center)` 是按**中心点**定位
- 手工竖式要求**右端对齐**：所有数字右端对齐到同一基准x
- 错误做法：`D638.move_to(np.array([divd_x, 0, 0]))` → 右端偏右0.42个单位
- 正确做法：`D638.move_to(np.array([right_edge - D638.width, 0, 0]))`

**第4层**：坐标转换困惑
- Manim实际渲染分辨率为854×1920（不是1080×1920）
- 所有像素到manim坐标的转换需要基于实际渲染分辨率
- 导致像素分析结果与预期坐标不匹配

### 修复方案
1. **模板写入**：用Python脚本直接写入模板文件（`temp_fix_right_align.py`），不用edit工具
2. **右端对齐**：`right_edge - text.width` 替代 `move_to(center)`
3. **SESSION COMPACTION**：模板修改后立即渲染验证，不要依赖edit工具反复修改

### 遗留问题
- EP107竖式最终版本仍有问题，主人反馈"完全不对"
- 暂停此项，等主人后续指示
- 建议：考虑直接在场景文件里手写竖式，不用模板框架

### 避免方法
- 不依赖edit工具修改被SESSION COMPACTION影响的文件
- manim Text布局统一用 `move_to(np.array([x, y, 0]))`，不用链式next_to
- 手工竖式必须用右端对齐：`target_x - text.width`

_由可悦记录，2026-06-15 23:37_

---

## 2026-06-18 baostock日线数据更新时效

### 问题
INV-Daily-Market-Update 在 09:13 执行时报错：`baostock data for 2026-06-17 not yet available, latest is 2026-06-16, Data usually updates after 18:00`

### 根因
baostock 的 A 股日线数据在交易日 18:00 后才更新，当天早间执行任务时数据尚未同步。

### 固化措施
- [ ] 方案A：Cron 任务时间从 09:13 改为 18:30 后执行
- [ ] 方案B：脚本内增加容错，数据不可用时跳过而非报错退出
- [ ] 方案C：同时保留早间任务（抓取前一交易日数据用于分析），在脚本内判断数据时效

_由可悦记录，2026-06-18 09:13_