#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据处理流水线模板 - 批量数据清洗/转换/导出

用法：
    python data_pipeline.py --input input.csv --output output.json
    python data_pipeline.py --input input.csv --clean --filter col eq 100
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import pandas as pd
import numpy as np


class DataPipeline:
    """数据处理流水线"""
    
    def __init__(self, input_path: str, output_path: Optional[str] = None):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path) if output_path else None
        self.data = None
        self.stats = {}
    
    def load(self, file_type: str = 'auto') -> pd.DataFrame:
        """加载数据
        
        Args:
            file_type: 文件格式 (csv/json/excel/auto)
            
        Returns:
            pd.DataFrame: 加载的数据
        """
        if not self.input_path.exists():
            raise FileNotFoundError(f"输入文件不存在: {self.input_path}")
        
        # 自动检测文件格式
        if file_type == 'auto':
            suffix = self.input_path.suffix.lower()
            if suffix == '.csv':
                file_type = 'csv'
            elif suffix == '.json':
                file_type = 'json'
            elif suffix in ['.xlsx', '.xls']:
                file_type = 'excel'
            else:
                raise ValueError(f"不支持的文件格式: {suffix}")
        
        # 根据格式加载
        if file_type == 'csv':
            self.data = pd.read_csv(self.input_path, encoding='utf-8')
        elif file_type == 'json':
            self.data = pd.read_json(self.input_path)
        elif file_type == 'excel':
            self.data = pd.read_excel(self.input_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
        
        self.stats['rows'] = len(self.data)
        self.stats['columns'] = list(self.data.columns)
        
        return self.data
    
    def clean(self, remove_null: bool = True, remove_duplicates: bool = True) -> pd.DataFrame:
        """数据清洗
        
        Args:
            remove_null: 是否删除空值
            remove_duplicates: 是否删除重复值
            
        Returns:
            pd.DataFrame: 清洗后的数据
        """
        if self.data is None:
            raise RuntimeError("请先调用load()方法加载数据")
        
        initial_rows = len(self.data)
        
        if remove_null:
            self.data = self.data.dropna()
        
        if remove_duplicates:
            self.data = self.data.drop_duplicates()
        
        cleaned_rows = initial_rows - len(self.data)
        self.stats['cleaned_rows'] = cleaned_rows
        
        return self.data
    
    def filter(self, column: str, condition: str, value: Any) -> pd.DataFrame:
        """过滤数据
        
        Args:
            column: 列名
            condition: 条件运算符 (eq/ne/lt/le/gt/ge)
            value: 比较值
            
        Returns:
            pd.DataFrame: 过滤后的数据
        """
        if self.data is None:
            raise RuntimeError("请先调用load()方法")
        
        operators = {
            'eq': lambda x, y: x == y,
            'ne': lambda x, y: x != y,
            'lt': lambda x, y: x < y,
            'le': lambda x, y: x <= y,
            'gt': lambda x, y: x > y,
            'ge': lambda x, y: x >= y,
        }
        
        if condition not in operators:
            raise ValueError(f"不支持的条件运算符: {condition}")
        
        self.data = self.data[operators[condition](self.data[column], value)]
        
        return self.data
    
    def transform(self, func) -> pd.DataFrame:
        """应用转换函数
        
        Args:
            func: 转换函数，接收DataFrame返回DataFrame
            
        Returns:
            pd.DataFrame: 转换后的数据
        """
        if self.data is None:
            raise RuntimeError("请先调用load()方法")
        
        self.data = func(self.data)
        return self.data
    
    def export(self, output_path: Optional[str] = None, file_type: str = 'csv') -> Path:
        """导出数据
        
        Args:
            output_path: 输出文件路径
            file_type: 文件格式 (csv/json/excel)
            
        Returns:
            Path: 输出文件路径
        """
        if self.data is None:
            raise RuntimeError("没有数据可导出")
        
        if output_path is None:
            output_path = self.output_path
        
        if output_path is None:
            output_path = self.input_path.with_suffix(f'.cleaned.{file_type}')
        else:
            output_path = Path(output_path)
        
        # 根据格式导出
        if file_type == 'csv':
            self.data.to_csv(output_path, index=False, encoding='utf-8')
        elif file_type == 'json':
            self.data.to_json(output_path, orient='records', force_ascii=False, indent=2)
        elif file_type == 'excel':
            self.data.to_excel(output_path, index=False)
        else:
            raise ValueError(f"不支持的文件格式: {file_type}")
        
        self.stats['output_path'] = str(output_path)
        
        return output_path
    
    def get_stats(self) -> Dict:
        """获取处理统计
        
        Returns:
            dict: 处理统计信息
        """
        return self.stats.copy()


def main():
    parser = argparse.ArgumentParser(
        description="数据处理流水线 - 清洗、转换、导出",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python data_pipeline.py --input data.csv --output result.json
  python data_pipeline.py --input data.csv --clean --normalize
  python data_pipeline.py --input data.csv --filter age gt 18
        """
    )
    
    parser.add_argument('--input', '-i', required=True, help='输入文件路径')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--type', '-t', choices=['csv', 'json', 'excel'], default='auto',
                        help='文件格式（默认自动检测）')
    parser.add_argument('--clean', action='store_true', help='执行数据清洗')
    parser.add_argument('--filter', '-f', nargs=3, metavar=('COLUMN', 'CONDITION', 'VALUE'),
                        help='过滤数据（列名 条件 值）')
    parser.add_argument('--stats', action='store_true', help='显示处理统计')
    
    args = parser.parse_args()
    
    try:
        # 创建流水线
        pipeline = DataPipeline(args.input, args.output)
        
        # 加载数据
        print(f"加载数据: {args.input}")
        pipeline.load(args.type)
        print(f"  行数: {pipeline.stats['rows']}, 列数: {len(pipeline.stats['columns'])}")
        
        # 执行清洗
        if args.clean:
            print("执行数据清洗...")
            pipeline.clean()
            print(f"  清理行数: {pipeline.stats.get('cleaned_rows', 0)}")
        
        # 执行过滤
        if args.filter:
            column, condition, value = args.filter
            print(f"执行过滤: {column} {condition} {value}")
            pipeline.filter(column, condition, value)
            print(f"  过滤后行数: {pipeline.stats['rows']}")
        
        # 导出数据
        if args.clean or args.filter:
            output_path = pipeline.export()
            print(f"导出结果: {output_path}")
        
        # 显示统计
        if args.stats:
            print("\n处理统计:")
            for key, value in pipeline.get_stats().items():
                print(f"  {key}: {value}")
        
        print("\n处理完成")
        
    except FileNotFoundError as e:
        print(f"文件错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"处理失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
