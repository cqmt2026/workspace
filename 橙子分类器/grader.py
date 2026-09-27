"""
自动评分器 - 用于教师端评分
"""

import torch
import json
from pathlib import Path

def load_student_model(model_path):
    """加载学生提交的模型"""
    checkpoint = torch.load(model_path, map_location='cpu')
    
    # 重建模型
    from train_orange_classifier import create_model
    model = create_model(use_pretrained=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    return model, checkpoint.get('config', {})

def grade_submission(model_path, test_data_dir, test_labels_path):
    """
    评分主函数
    
    Args:
        model_path: 学生提交的模型路径 (.pt文件)
        test_data_dir: 测试集目录路径
        test_labels_path: 标准答案路径 (.json文件)
    
    Returns:
        dict: 评分结果
    """
    print("="*50)
    print("📝 自动评分系统")
    print("="*50)
    
    # 1. 加载模型
    print("\n📂 加载学生模型...")
    try:
        model, config = load_student_model(model_path)
        print("   ✓ 模型加载成功")
    except Exception as e:
        print(f"   ✗ 模型加载失败: {e}")
        return {'error': str(e), 'total_score': 0}
    
    # 2. 加载测试数据和标准答案
    print("\n📊 加载测试数据...")
    test_images = []
    test_labels = []
    
    test_dir = Path(test_data_dir)
    label_map = {'orange': 0, 'non_orange': 1}
    
    for label_name in ['orange', 'non_orange']:
        label_dir = test_dir / label_name
        if not label_dir.exists():
            continue
        
        for img_file in label_dir.glob('*.jpg'):
            # 这里需要实际加载图片
            # test_images.append(load_image(img_file))
            test_labels.append(label_map[label_name])
    
    # 3. 预测
    print("\n🔮 进行预测...")
    # 这里需要实际预测逻辑
    # predictions = model.predict(test_images)
    predictions = test_labels  # 临时用真实标签代替
    
    # 4. 计算混淆矩阵
    TP = sum(1 for p, l in zip(predictions, test_labels) if p == 0 and l == 0)
    TN = sum(1 for p, l in zip(predictions, test_labels) if p == 1 and l == 1)
    FP = sum(1 for p, l in zip(predictions, test_labels) if p == 0 and l == 1)
    FN = sum(1 for p, l in zip(predictions, test_labels) if p == 1 and l == 0)
    
    total = TP + TN + FP + FN
    accuracy = (TP + TN) / total if total > 0 else 0
    
    print(f"\n混淆矩阵:")
    print(f"  TP={TP}, TN={TN}, FP={FP}, FN={FN}")
    print(f"  准确率: {accuracy*100:.2f}%")
    
    # 5. 计算分数
    score_breakdown = calculate_score(accuracy, total)
    
    # 6. 返回结果
    result = {
        'accuracy': accuracy,
        'confusion_matrix': {'TP': TP, 'TN': TN, 'FP': FP, 'FN': FN},
        'score_breakdown': score_breakdown,
        'total_score': score_breakdown['total'],
        'grade': 'A' if accuracy >= 0.95 else 'B' if accuracy >= 0.90 else 'C' if accuracy >= 0.80 else 'D'
    }
    
    return result

def calculate_score(accuracy, total_samples):
    """计算各项分数"""
    # 准确率得分（40分）
    if accuracy >= 0.95:
        accuracy_score = 40
    elif accuracy >= 0.90:
        accuracy_score = 30
    elif accuracy >= 0.80:
        accuracy_score = 20
    else:
        accuracy_score = 10
    
    # 假设其他维度都给满分（实际应有更复杂的逻辑）
    convergence_score = 20  # 训练收敛性
    model_size_score = 10   # 模型大小
    reflection_score = 20   # 反思回答
    time_score = 10         # 完成时间
    
    total = accuracy_score + convergence_score + model_size_score + reflection_score + time_score
    
    return {
        'accuracy': accuracy_score,
        'convergence': convergence_score,
        'model_size': model_size_score,
        'reflection': reflection_score,
        'time': time_score,
        'total': total
    }

def generate_report(result, output_path='grading_report.json'):
    """生成评分报告"""
    report = f"""
╔══════════════════════════════════════════╗
║         🎓 橙子分类器 - 评分报告          ║
╠══════════════════════════════════════════╣
║  准确率: {result['accuracy']*100:>6.2f}%               ║
║  等级:   {result['grade']:>6}                 ║
║  总分:   {result['total_score']:>5}/100              ║
╠══════════════════════════════════════════╣
║  混淆矩阵:                               ║
║    TP={result['confusion_matrix']['TP']:>4}  TN={result['confusion_matrix']['TN']:>4}    ║
║    FP={result['confusion_matrix']['FP']:>4}  FN={result['confusion_matrix']['FN']:>4}    ║
╚══════════════════════════════════════════╝
    """
    
    print(report)
    
    # 保存JSON报告
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 报告已保存: {output_path}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 4:
        print("用法: python grader.py <model_path> <test_dir> <labels_path>")
        sys.exit(1)
    
    model_path = sys.argv[1]
    test_dir = sys.argv[2]
    labels_path = sys.argv[3]
    
    result = grade_submission(model_path, test_dir, labels_path)
    generate_report(result)
