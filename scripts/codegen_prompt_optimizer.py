#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码生成Prompt优化器

功能：
1. 分析失败案例，提取失败模式
2. 自动优化prompt模板
3. 生成改进后的prompt示例
4. 对比优化前后效果

用法：
    python codegen_prompt_optimizer.py --analyze      # 分析失败案例
    python codegen_prompt_optimizer.py --optimize     # 生成优化建议
    python codegen_prompt_optimizer.py --test "需求"  # 测试新prompt
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).parent.parent
FAILURE_LOG = BASE_DIR / "memory" / "代码生成失败案例" / "failures.json"
STATS_FILE = BASE_DIR / "memory" / "代码生成失败案例" / "stats.json"


class PromptOptimizer:
    """Prompt优化器"""
    
    # 失败模式到优化建议的映射
    OPTIMIZATION_RULES = {
        "语法错误": {
            "pattern": r"SyntaxError|invalid syntax|unterminated|string",
            "suggestions": [
                "在prompt中添加：'确保所有字符串使用正确的引号配对'",
                "添加示例：'输出格式为纯代码，不要包含markdown代码块标记'",
                "强调：'每行代码必须正确缩进'"
            ],
            "weight": 1.0
        },
        "编码错误": {
            "pattern": r"UnicodeEncodeError|UnicodeDecodeError|GBK|utf-8",
            "suggestions": [
                "在prompt中添加：'所有字符串使用ASCII字符，避免emoji'",
                "强调：'输出编码为utf-8'",
                "添加：'使用print('[OK]')而非print('✅')'"
            ],
            "weight": 0.9
        },
        "导入错误": {
            "pattern": r"ImportError|ModuleNotFoundError|no module named",
            "suggestions": [
                "在prompt中添加：'只使用标准库，不引入第三方依赖'",
                "强调：'如需要第三方库，请在代码开头添加import语句'",
                "添加：'避免使用pandas/numpy等重型库'"
            ],
            "weight": 0.8
        },
        "类型错误": {
            "pattern": r"TypeError|NoneType|not subscriptable",
            "suggestions": [
                "在prompt中添加：'对所有输入进行类型检查'",
                "强调：'函数必须有返回值，不能返回None'",
                "添加：'处理空值情况，返回默认值而非抛出异常'"
            ],
            "weight": 0.85
        },
        "文件错误": {
            "pattern": r"FileNotFoundError|File is read only|PermissionError",
            "suggestions": [
                "在prompt中添加：'先检查文件是否存在再操作'",
                "强调：'使用Path对象处理路径，避免硬编码'",
                "添加：'所有文件操作必须包含try-except'"
            ],
            "weight": 0.7
        }
    }
    
    def __init__(self):
        self.failures = self._load_failures()
        self.stats = self._load_stats()
    
    def _load_failures(self) -> List[Dict]:
        """加载失败案例"""
        if FAILURE_LOG.exists():
            try:
                return json.loads(FAILURE_LOG.read_text(encoding='utf-8'))
            except:
                return []
        return []
    
    def _load_stats(self) -> Dict:
        """加载统计信息"""
        if STATS_FILE.exists():
            try:
                return json.loads(STATS_FILE.read_text(encoding='utf-8'))
            except:
                return {}
        return {}
    
    def analyze(self) -> Dict:
        """分析失败案例"""
        if not self.failures:
            return {"message": "暂无失败案例"}
        
        analysis = {
            "total_failures": len(self.failures),
            "failure_patterns": {},
            "top_failures": []
        }
        
        # 统计失败模式
        for f in self.failures:
            cause = f.get('root_cause', 'unknown')
            if cause not in analysis['failure_patterns']:
                analysis['failure_patterns'][cause] = 0
            analysis['failure_patterns'][cause] += 1
        
        # 找出最严重的失败（得分最低）
        scored = [f for f in self.failures if f.get('review_score')]
        if scored:
            scored.sort(key=lambda x: x['review_score'])
            analysis['top_failures'] = scored[:5]
        
        return analysis
    
    def optimize(self) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 基于失败模式生成建议
        for cause, count in self.stats.get('by_cause', {}).items():
            if count >= 2:  # 只有重复出现的错误才建议优化
                for rule_name, rule in self.OPTIMIZATION_RULES.items():
                    if cause in rule_name or rule_name in cause:
                        for suggestion in rule['suggestions']:
                            if suggestion not in suggestions:
                                suggestions.append(f"[{cause}] {suggestion}")
        
        # 基于平均得分生成建议
        avg_score = self.stats.get('avg_score')
        if avg_score and avg_score < 80:
            suggestions.append("【代码质量】优化prompt模板，增加更多约束条件")
        
        if not suggestions:
            suggestions.append("当前prompt质量良好，无需优化")
        
        return suggestions
    
    def generate_improved_prompt(self, template_type: str = "script") -> str:
        """生成优化后的prompt模板"""
        
        base_prompt = """你是一位专业的Python工程师，擅长编写高质量、可维护的代码。

## 编码规范（必须遵守）
1. **边界全覆盖**：所有函数必须处理空输入、None、空字符串、0值、负数
2. **错误处理分层**：使用具体异常类型，不要裸except
3. **命名规范**：函数用动词开头（process_/validate_/load_），常量UPPER_SNAKE_CASE
4. **文档字符串**：每个函数必须有docstring，说明参数和返回值
5. **类型提示**：函数签名必须包含类型标注
6. **编码安全**：所有字符串使用ASCII，避免emoji和特殊字符

## 输出要求
1. 只输出Python代码，不要任何解释文字
2. 代码必须是完整可运行的，不要省略部分
3. 使用标准库，避免第三方依赖（除非必要）
4. 代码风格遵循PEP 8规范
"""
        
        # 根据模板类型添加特定建议
        if template_type == "api_client":
            base_prompt += """
## API客户端特别要求
1. 必须包含重试机制（最多3次）
2. 必须设置超时时间（默认30秒）
3. 必须处理HTTP错误（4xx/5xx）
4. 必须使用Session复用连接
"""
        elif template_type == "data_pipeline":
            base_prompt += """
## 数据处理特别要求
1. 必须处理文件不存在的情况
2. 必须处理JSON解析错误
3. 必须验证数据格式
4. 必须提供清晰的进度输出
"""
        elif template_type == "scheduler":
            base_prompt += """
## 定时任务特别要求
1. 必须处理KeyboardInterrupt
2. 必须记录执行日志
3. 必须支持--once和--daemon模式
4. 必须处理异常避免任务中断
"""
        
        return base_prompt
    
    def test_prompt(self, description: str, improved_prompt: str) -> str:
        """测试优化后的prompt效果（模拟）"""
        # 这里可以调用LLM进行测试
        # 暂时返回模拟结果
        
        return f"""
## 测试 prompt
{improved_prompt[:500]}...

## 测试需求
{description}

## 预期改进
- 语法错误率预计降低50%
- 编码错误率预计降低80%
- 代码质量评分预计提升至85+分
"""


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="代码生成Prompt优化器")
    parser.add_argument("--analyze", "-a", action="store_true", help="分析失败案例")
    parser.add_argument("--optimize", "-o", action="store_true", help="生成优化建议")
    parser.add_argument("--generate", "-g", help="生成优化后的prompt")
    parser.add_argument("--test", "-t", help="测试prompt效果")
    
    args = parser.parse_args()
    
    optimizer = PromptOptimizer()
    
    if args.analyze:
        analysis = optimizer.analyze()
        print("=== 失败案例分忻 ===")
        print(f"总失败次数: {analysis['total_failures']}")
        print("\n失败模式分布:")
        for pattern, count in sorted(analysis['failure_patterns'].items(), key=lambda x: -x[1]):
            print(f"  - {pattern}: {count}次")
    
    elif args.optimize:
        suggestions = optimizer.optimize()
        print("=== 优化建议 ===")
        for s in suggestions:
            print(s)
    
    elif args.generate:
        prompt = optimizer.generate_improved_prompt(args.generate)
        print("=== 优化后Prompt ===")
        print(prompt)
    
    elif args.test:
        prompt = optimizer.generate_improved_prompt("script")
        result = optimizer.test_prompt(args.test, prompt)
        print(result)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
