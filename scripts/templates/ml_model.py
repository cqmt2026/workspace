#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
机器学习模型模板 - 训练/预测/评估流水线

用法：
    python ml_model.py --train training_data.csv
    python ml_model.py --predict test_data.csv --model model.pkl
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import joblib


class MLModel:
    """机器学习模型"""
    
    def __init__(self, model_type: str = 'classifier'):
        """初始化
        
        Args:
            model_type: 模型类型 (classifier/regressor)
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.history = {}
    
    def load_data(self, filepath: str) -> Dict:
        """加载数据
        
        Args:
            filepath: 数据文件路径
            
        Returns:
            dict: 包含X和y的字典
        """
        df = pd.read_csv(filepath)
        
        # 自动识别特征和标签
        # 假设最后一列为标签
        X = df.iloc[:, :-1].values
        y = df.iloc[:, -1].values
        
        return {'X': X, 'y': y}
    
    def train(self, X: np.ndarray, y: np.ndarray, 
              test_size: float = 0.2, random_state: int = 42) -> Dict:
        """训练模型
        
        Args:
            X: 特征数据
            y: 标签数据
            test_size: 测试集比例
            random_state: 随机种子
            
        Returns:
            dict: 训练结果
        """
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # 标准化
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 根据模型类型创建模型
        if self.model_type == 'classifier':
            from sklearn.ensemble import RandomForestClassifier
            self.model = RandomForestClassifier(n_estimators=100, random_state=random_state)
        elif self.model_type == 'regressor':
            from sklearn.ensemble import RandomForestRegressor
            self.model = RandomForestRegressor(n_estimators=100, random_state=random_state)
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
        
        # 训练
        self.model.fit(X_train_scaled, y_train)
        
        # 预测
        y_pred = self.model.predict(X_test_scaled)
        
        # 评估
        if self.model_type == 'classifier':
            accuracy = accuracy_score(y_test, y_pred)
            report = classification_report(y_test, y_pred, output_dict=True)
        else:
            from sklearn.metrics import mean_squared_error, r2_score
            accuracy = r2_score(y_test, y_pred)
            report = {'mse': mean_squared_error(y_test, y_pred), 'r2': accuracy}
        
        result = {
            'accuracy': accuracy,
            'report': report,
            'test_size': len(y_test)
        }
        
        self.history['train_result'] = result
        
        return result
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测
        
        Args:
            X: 特征数据
            
        Returns:
            np.ndarray: 预测结果
        """
        if self.model is None:
            raise RuntimeError("请先训练模型")
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def save(self, filepath: str):
        """保存模型
        
        Args:
            filepath: 保存路径
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # 保存模型和scaler
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'model_type': self.model_type,
            'history': self.history
        }
        
        joblib.dump(model_data, filepath)
        print(f"模型已保存到: {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'MLModel':
        """加载模型
        
        Args:
            filepath: 模型文件路径
            
        Returns:
            MLModel: 加载的模型
        """
        model_data = joblib.load(filepath)
        
        model = cls(model_type=model_data['model_type'])
        model.model = model_data['model']
        model.scaler = model_data['scaler']
        model.history = model_data.get('history', {})
        
        return model


def main():
    parser = argparse.ArgumentParser(
        description="机器学习模型训练/预测流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python ml_model.py --train data.csv --output model.pkl
  python ml_model.py --predict test.csv --model model.pkl --output predictions.csv
        """
    )
    
    parser.add_argument('--train', '-t', help='训练数据文件')
    parser.add_argument('--predict', '-p', help='预测数据文件')
    parser.add_argument('--model', '-m', help='模型文件路径')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--type', choices=['classifier', 'regressor'], default='classifier',
                        help='模型类型')
    
    args = parser.parse_args()
    
    try:
        # 训练模式
        if args.train:
            print("=== 训练模式 ===")
            model = MLModel(model_type=args.type)
            
            # 加载数据
            print(f"加载训练数据: {args.train}")
            data = model.load_data(args.train)
            
            # 训练
            print("训练模型...")
            result = model.train(data['X'], data['y'])
            
            print(f"\n训练完成:")
            print(f"  准确率: {result['accuracy']:.4f}")
            print(f"  测试集大小: {result['test_size']}")
            
            # 保存模型
            if args.output:
                model.save(args.output)
            else:
                output_path = Path(args.train).parent / 'model.pkl'
                model.save(str(output_path))
                print(f"\n模型已保存到: {output_path}")
        
        # 预测模式
        elif args.predict:
            print("=== 预测模式 ===")
            
            # 加载模型
            if not args.model:
                raise ValueError("预测模式需要指定--model参数")
            
            model = MLModel.load(args.model)
            
            # 加载数据
            print(f"加载预测数据: {args.predict}")
            df = pd.read_csv(args.predict)
            X = df.values
            
            # 预测
            print("执行预测...")
            predictions = model.predict(X)
            
            # 保存结果
            if args.output:
                result_df = df.copy()
                result_df['prediction'] = predictions
                result_df.to_csv(args.output, index=False)
                print(f"预测结果已保存到: {args.output}")
            else:
                # 输出到控制台
                for i, pred in enumerate(predictions[:10]):
                    print(f"  样本{i+1}: {pred}")
                if len(predictions) > 10:
                    print(f"  ... 共{len(predictions)}个预测结果")
        
        else:
            parser.print_help()
        
    except Exception as e:
        print(f"执行失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
