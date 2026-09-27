# 橙子分类器项目

> AI挑战赛：构建橙子识别分类器

## 📁 项目结构

```
橙子分类器/
├── train_orange_classifier.py  # 主训练脚本
├── grader.py                   # 自动评分器
├── prepare_dataset.py          # 数据集准备
├── README.md                   # 本文件
├── dataset/                    # 数据集目录（运行后生成）
│   ├── train/
│   │   ├── orange/
│   │   └── non_orange/
│   ├── test/
│   │   ├── orange/
│   │   └── non_orange/
│   └── labels.json
└── output/                     # 模型输出目录
    ├── model.pt
    ├── labels.json
    └── config.json
```

## 🚀 快速开始

### 1. 准备数据集

```bash
# 将图片按类别放入 source_images/ 目录
source_images/
├── orange/      # 橙子图片
└── non_orange/  # 非橙子图片（苹果、香蕉等）

# 运行准备脚本
python prepare_dataset.py
```

### 2. 训练模型

```bash
python train_orange_classifier.py
```

### 3. 评估（教师端）

```bash
python grader.py output/model.pt dataset/test/ dataset/labels.json
```

## 📊 预期结果

- 训练集准确率：≥90%
- 测试集准确率：≥85%
- 模型文件大小：<10MB

## ⚠️ 常见问题

### Q1: CUDA out of memory
```bash
# 解决方法：减小batch_size
# 修改 train_orange_classifier.py 中的 CONFIG
CONFIG['batch_size'] = 4
```

### Q2: 准确率上不去
```bash
# 检查数据质量：
# 1. 图片是否清晰？
# 2. 正负样本是否平衡？
# 3. 是否有异常标签？
```

### Q3: 训练太慢
```bash
# 使用GPU加速（如果有）
# 代码中已默认使用GPU（如果有）
```

## 🎯 扩展挑战

1. **五分类任务**：橙子、苹果、香蕉、柠檬、葡萄
2. **目标检测**：用YOLO定位橙子位置
3. **模型压缩**：量化感知训练，减小模型体积
4. **边缘部署**：部署到树莓派/手机

## 📝 提交清单

学生需提交：
- [x] 训练脚本运行截图
- [x] 训练Loss曲线截图
- [x] 测试集混淆矩阵
- [x] 模型文件（model.pt）
- [x] 反思回答（≥3条改进措施）

## 🔗 相关资源

- PyTorch官方文档：https://pytorch.org/docs/
- torchvision模型库：https://pytorch.org/vision/stable/models.html
- 竞赛数据集：[待补充]

---

_创建时间：2026-09-19_
