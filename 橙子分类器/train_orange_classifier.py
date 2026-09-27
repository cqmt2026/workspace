"""
橙子分类器 - 完整实现代码
适用于：AI入门课程、开发者挑战赛
"""

import torch
import torch.nn as nn
from torchvision import models, transforms
from torch.utils.data import DataLoader, Dataset
import os
from PIL import Image
import json
from pathlib import Path

# ==================== 配置 ====================
CONFIG = {
    'input_size': 224,
    'num_classes': 2,
    'epochs': 15,
    'batch_size': 8,
    'learning_rate': 0.001,
    'label_map': {
        'orange': 0,
        'non_orange': 1
    }
}

# ==================== 数据集类 ====================
class OrangeDataset(Dataset):
    """橙子分类数据集"""
    
    def __init__(self, root_dir, transform=None, is_test=False):
        self.root_dir = root_dir
        self.transform = transform
        self.samples = []
        self.is_test = is_test
        
        # 遍历所有子目录
        for label_name in ['orange', 'non_orange']:
            label_dir = os.path.join(root_dir, label_name)
            if not os.path.exists(label_dir):
                continue
            
            for img_name in os.listdir(label_dir):
                if img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    img_path = os.path.join(label_dir, img_name)
                    label = CONFIG['label_map'][label_name]
                    self.samples.append((img_path, label))
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        
        # 读取图片
        image = Image.open(img_path).convert('RGB')
        
        # 数据变换
        if self.transform:
            image = self.transform(image)
        
        return image, label, img_path.split('/')[-1]

# ==================== 数据变换 ====================
train_transform = transforms.Compose([
    transforms.Resize((CONFIG['input_size'], CONFIG['input_size'])),
    transforms.RandomHorizontalFlip(),  # 水平翻转
    transforms.RandomRotation(15),      # 随机旋转±15度
    transforms.ColorJitter(            # 颜色抖动
        brightness=0.2,
        contrast=0.2,
        saturation=0.2
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

test_transform = transforms.Compose([
    transforms.Resize((CONFIG['input_size'], CONFIG['input_size'])),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ==================== 模型定义 ====================
def create_model(use_pretrained=True):
    """创建ResNet18模型"""
    model = models.resnet18(pretrained=use_pretrained)
    
    # 修改最后一层为2分类
    model.fc = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(model.fc.in_features, CONFIG['num_classes'])
    )
    
    return model

# ==================== 训练函数 ====================
def train_model(model, train_loader, optimizer, criterion, epoch):
    """单轮训练"""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for i, (images, labels, _) in enumerate(train_loader):
        # 前向传播
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # 统计
        running_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
        # 打印进度
        if (i + 1) % 10 == 0:
            print(f'  Epoch [{epoch+1}/{CONFIG["epochs"]}], '
                  f'Batch [{i+1}/{len(train_loader)}], '
                  f'Loss: {running_loss/(i+1):.4f}, '
                  f'Acc: {100*correct/total:.2f}%')
    
    avg_loss = running_loss / len(train_loader)
    accuracy = 100 * correct / total
    
    return avg_loss, accuracy

# ==================== 验证函数 ====================
def evaluate_model(model, data_loader):
    """模型评估"""
    model.eval()
    all_preds = []
    all_labels = []
    all_paths = []
    
    with torch.no_grad():
        for images, labels, paths in data_loader:
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            
            all_preds.extend(predicted.tolist())
            all_labels.extend(labels.tolist())
            all_paths.extend(paths)
    
    return all_preds, all_labels, all_paths

# ==================== 混淆矩阵 ====================
def compute_confusion_matrix(preds, labels):
    """计算混淆矩阵"""
    TP = sum(1 for p, l in zip(preds, labels) if p == 0 and l == 0)
    TN = sum(1 for p, l in zip(preds, labels) if p == 1 and l == 1)
    FP = sum(1 for p, l in zip(preds, labels) if p == 0 and l == 1)
    FN = sum(1 for p, l in zip(preds, labels) if p == 1 and l == 0)
    
    return {
        'TP': TP,
        'TN': TN,
        'FP': FP,
        'FN': FN
    }

def print_confusion_matrix(cm):
    """打印混淆矩阵"""
    print("\n" + "="*40)
    print("混淆矩阵")
    print("="*40)
    print(f"              预测橙子  预测非橙子")
    print(f"真实橙子      {cm['TP']:>6}      {cm['FN']:>6}")
    print(f"真实非橙子    {cm['FP']:>6}      {cm['TN']:>6}")
    print("="*40)
    
    accuracy = (cm['TP'] + cm['TN']) / sum(cm.values())
    recall = cm['TP'] / (cm['TP'] + cm['FN']) if (cm['TP'] + cm['FN']) > 0 else 0
    precision = cm['TP'] / (cm['TP'] + cm['FP']) if (cm['TP'] + cm['FP']) > 0 else 0
    
    print(f"\n准确率: {accuracy*100:.2f}%")
    print(f"召回率: {recall*100:.2f}%")
    print(f"精确率: {precision*100:.2f}%")

# ==================== 导出模型 ====================
def export_model(model, output_dir='output'):
    """导出模型文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 导出模型权重
    model_path = os.path.join(output_dir, 'model.pt')
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': CONFIG,
        'architecture': 'ResNet18'
    }, model_path)
    
    # 导出标签映射
    labels_path = os.path.join(output_dir, 'labels.json')
    with open(labels_path, 'w', encoding='utf-8') as f:
        json.dump(CONFIG['label_map'], f, indent=2, ensure_ascii=False)
    
    # 导出配置
    config_path = os.path.join(output_dir, 'config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump({
            'input_size': CONFIG['input_size'],
            'normalize': {
                'mean': [0.485, 0.456, 0.406],
                'std': [0.229, 0.224, 0.225]
            }
        }, f, indent=2, ensure_ascii=False)
    
    file_size = os.path.getsize(model_path) / 1024 / 1024  # MB
    print(f"\n✅ 模型已导出:")
    print(f"   - 权重: {model_path} ({file_size:.2f}MB)")
    print(f"   - 标签: {labels_path}")
    print(f"   - 配置: {config_path}")
    
    return model_path

# ==================== 主流程 ====================
def main():
    """主训练流程"""
    print("="*50)
    print("🍊 橙子分类器 - 训练启动")
    print("="*50)
    
    # 1. 加载数据
    print("\n📂 加载数据集...")
    train_dataset = OrangeDataset('train/', train_transform)
    test_dataset = OrangeDataset('test/', test_transform, is_test=True)
    
    train_loader = DataLoader(train_dataset, batch_size=CONFIG['batch_size'], 
                              shuffle=True, num_workers=2)
    test_loader = DataLoader(test_dataset, batch_size=CONFIG['batch_size'], 
                             shuffle=False, num_workers=2)
    
    print(f"   训练集: {len(train_dataset)} 张图片")
    print(f"   测试集: {len(test_dataset)} 张图片")
    
    # 2. 创建模型
    print("\n🏗️  创建模型...")
    model = create_model(use_pretrained=True)
    print(f"   模型架构: ResNet18 (预训练)")
    print(f"   参数量: {sum(p.numel() for p in model.parameters()):,}")
    
    # 3. 配置训练
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=CONFIG['learning_rate'])
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)
    
    # 4. 开始训练
    print("\n🚀 开始训练...")
    print("-"*50)
    
    training_logs = []
    
    for epoch in range(CONFIG['epochs']):
        print(f"\nEpoch {epoch+1}/{CONFIG['epochs']}")
        
        # 训练
        train_loss, train_acc = train_model(
            model, train_loader, optimizer, criterion, epoch
        )
        
        # 验证
        scheduler.step()
        
        log = {
            'epoch': epoch + 1,
            'train_loss': train_loss,
            'train_acc': train_acc
        }
        training_logs.append(log)
    
    print("\n" + "="*50)
    print("✅ 训练完成!")
    print("="*50)
    
    # 5. 测试集评估
    print("\n📊 测试集评估...")
    preds, labels, paths = evaluate_model(model, test_loader)
    cm = compute_confusion_matrix(preds, labels)
    print_confusion_matrix(cm)
    
    # 6. 导出模型
    print("\n💾 导出模型...")
    model_path = export_model(model)
    
    # 7. 保存训练日志
    log_path = 'training_log.json'
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump({
            'training_logs': training_logs,
            'confusion_matrix': cm,
            'model_path': model_path
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📝 训练日志已保存: {log_path}")
    print("\n" + "="*50)
    print("🎉 全部流程完成!")
    print("="*50)
    
    return model, cm

if __name__ == '__main__':
    model, cm = main()
