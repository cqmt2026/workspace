# 广州11区GDP视频工作流总结

## 任务目标
使用流水线生成"广州11区GDP排名"短视频

## 执行流程

### 1. 配置加载
- 配置文件: `config/city_广州.json`
- 注意: video_id 必须是 `city_广州`，不是 `guangzhou`

### 2. 脚本生成（步骤2）
- 输入: 11区GDP数据
- LLM生成: 372字，预计40秒
- 输出: `data/scripts/广州11区GDP排名_20260825_215837.json`

### 3. 地图绘制（步骤3）
- 使用 ProvinceMapDrawer
- 输出: 11张地图帧（每区一张）
- 位置: `data/maps/20260825/`

### 4. 配音生成（步骤4）
- 使用 Edge TTS
- 实际时长: 49.5秒
- 输出: `data/audio/city_广州_tts.mp3`

### 5. HF渲染（步骤5b）
- 自动匹配模板: `hyperframes_template`
- 音频时长: 49.5秒（自动同步）
- 输出: `my-video/city_广州_final.mp4`
- 大小: 394KB

### 6. 视频合成（手动）
- FFmpeg合并视频+配音
- 输出: `data/videos/广州11区GDP排名_流水线版.mp4`
- 大小: 969KB

## 关键发现

### 问题1: 配置ID不匹配
- 错误: `pipeline.py guangzhou` → 加载空配置
- 正确: `pipeline.py city_广州` → 加载完整配置
- 原因: 配置文件名为 `city_广州.json`

### 问题2: 脚本时长估算偏差
- 估算: 40秒
- 实际: 49.5秒
- 原因: TTS语速比预期慢

### 问题3: HF渲染超时
- 手动调试时多次超时
- 流水线自动处理内存阈值
- 建议: 优先使用流水线，避免手动调试

## 正确用法

```bash
# 完整流水线
python scripts/core/pipeline.py city_广州 --step 1-5 --quality draft

# 从某步骤开始
python scripts/core/pipeline.py city_广州 --step 3-5

# 跳过LLM（使用模板）
python scripts/core/pipeline.py city_广州 --skip-llm
```

## 后续优化

1. **字幕渲染**: drawtext滤镜语法问题待修复
2. **BGM混合**: 需添加背景音乐
3. **时长校准**: TTS语速需标准化

---

_记录时间: 2026-08-25 22:05_
