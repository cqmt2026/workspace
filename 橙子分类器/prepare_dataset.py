"""
数据集准备脚本 - 用于创建训练/测试数据集
"""

import os
import random
from pathlib import Path
import shutil

def create_dataset_structure(base_dir='dataset'):
    """创建数据集目录结构"""
    dirs = [
        f'{base_dir}/train/orange',
        f'{base_dir}/train/non_orange',
        f'{base_dir}/test/orange',
        f'{base_dir}/test/non_orange'
    ]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f'✓ 创建目录: {d}')

def prepare_training_data(source_img_dir, count_per_class=40):
    """
    准备训练数据
    
    Args:
        source_img_dir: 原始图片目录
        count_per_class: 每个类别的数量
    """
    print(f"\n📂 准备训练数据...")
    
    # 这里应该从共享云盘下载图片
    # 示例：假设图片已经按类别存放在 source_img_dir 下
    # orange/*.jpg, non_orange/*.jpg
    
    train_dir = 'dataset/train'
    
    for label in ['orange', 'non_orange']:
        src_label_dir = os.path.join(source_img_dir, label)
        dst_label_dir = os.path.join(train_dir, label)
        
        if not os.path.exists(src_label_dir):
            print(f'  ⚠ 源目录不存在: {src_label_dir}')
            continue
        
        # 复制图片
        images = [f for f in os.listdir(src_label_dir) 
                  if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        # 随机选择count_per_class张
        selected = random.sample(images, min(count_per_class, len(images)))
        
        for img_name in selected:
            src = os.path.join(src_label_dir, img_name)
            dst = os.path.join(dst_label_dir, f'{label}_{img_name}')
            shutil.copy2(src, dst)
        
        print(f'  ✓ {label}: {len(selected)} 张图片')

def prepare_test_data(source_img_dir, count_per_class=10):
    """准备测试数据（含陷阱样本）"""
    print(f"\n📊 准备测试数据...")
    
    test_dir = 'dataset/test'
    
    for label in ['orange', 'non_orange']:
        src_label_dir = os.path.join(source_img_dir, label)
        dst_label_dir = os.path.join(test_dir, label)
        
        if not os.path.exists(src_label_dir):
            continue
        
        images = [f for f in os.listdir(src_label_dir) 
                  if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        # 测试集选取（可以是固定的，方便复现）
        selected = sorted(images)[:count_per_class]
        
        for img_name in selected:
            src = os.path.join(src_label_dir, img_name)
            dst = os.path.join(dst_label_dir, f'test_{img_name}')
            shutil.copy2(src, dst)
        
        print(f'  ✓ {label}: {len(selected)} 张图片')

def create_label_map(output_path='dataset/labels.json'):
    """创建标签映射文件"""
    label_map = {
        'orange': 0,
        'non_orange': 1
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(label_map, f, indent=2, ensure_ascii=False)
    
    print(f'\n🏷️  标签映射已保存: {output_path}')

if __name__ == '__main__':
    import json
    
    # 创建目录结构
    create_dataset_structure()
    
    # 准备数据（需要指定源目录）
    # prepare_training_data('source_images', count_per_class=40)
    # prepare_test_data('source_images', count_per_class=10)
    
    # 创建标签映射
    create_label_map()
    
    print("\n✅ 数据集准备完成!")
    print("\n下一步: 运行 train_orange_classifier.py 开始训练")
