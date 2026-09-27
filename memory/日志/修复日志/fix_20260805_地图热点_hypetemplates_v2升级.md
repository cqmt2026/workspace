# 修复日志 - 2026-08-05 地图热点子系统 HyperFrames模板v2升级

## 任务：升级HyperFrames模板，实现AE级地图动画效果

### 问题
萨拉视频（地理科普）用了AE做地图动画（水流路径动画、地图缩放、数据对比图），我们当前用matplotlib静态图+HyperFrames GSAP动画，精细度差一档。AE装不了（RAM/GPU/C盘不足）。

### 解决方案
创建 `hyperframes_template_v2.py`，在HyperFrames框架内实现AE级动画能力：
1. **SVG路径动画** — GSAP MotionPathPlugin 让箭头/粒子沿河流路径流动
2. **数据对比图** — SVG circle面积对比动画（洞庭湖4350→2625km²）
3. **场景转场** — push slide + blur + scale 三效合一转场
4. **梅雨带效果** — 雨滴CSS动画 + 半透明叠加层

### 新增文件
- `core/hyperframes_template_v2.py` (46KB) — 升级版模板生成器
- `my-video/index.html` (37KB) — 长江流域四重考验HTML输出

### 6场景编排
1. **钩子** — 长江全景SVG + 水流箭头沿干流流动 + 鄂湘赣省界高亮
2. **第一重考验** — 金沙江/岷江/嘉陵江/乌江支流汇入三峡动画
3. **第二重考验** — 汉江+赣江汇入，洞庭湖+鄱阳湖弹出
4. **第三重考验** — 洞庭湖面积对比（大圆缩到小圆）+ 鄱阳湖对比
5. **第四重考验** — 梅雨带半透明层 + 雨滴落下动画
6. **升华结尾** — 温暖光晕扩散 + 文字淡入

### 验证结果
- ✅ GSAP 3.14.2 CDN + MotionPathPlugin
- ✅ 6场景全部存在且无ID冲突
- ✅ 14个motionPath动画
- ✅ 123个HTML元素ID，263个GSAP选择器引用
- ✅ 5个场景转场定义
- ✅ 10/10动画功能检查通过
- ✅ 输出 1080x1920 竖屏

### 关键代码片段
- 河流路径SVG：`lonlat_to_svg(lon, lat)` 坐标映射函数
- 水流箭头：`motionPath: { path: riverPath, align: riverPath, autoRotate: true }`
- 湖泊对比：GSAP `r: 45→28` 圆半径缩放动画
- 雨滴效果：`repeat: -1` 无限循环 + `y: +=40` 下落

### 后续步骤
1. 可在浏览器中打开 `my-video/index.html` 预览动画效果
2. 如需渲染为视频，运行：`python hyperframes_template_v2.py 长江流域 --render --quality draft`
3. 可基于此模板为其他流域（黄河、珠江等）快速生成类似演示
