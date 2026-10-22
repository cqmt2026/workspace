#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码生成失败案例记录工具

功能：
1. 记录代码生成失败案例
2. 自动分析失败原因
3. 生成优化建议
4. 定期汇总统计

用法：
    python codegen_failure_logger.py "失败案例描述" --error "错误信息"
    python codegen_failure_logger.py --list              # 列出所有失败案例
    python codegen_failure_logger.py --stats             # 统计失败模式
    python codegen_failure_logger.py --analyze           # 分析并生成优化建议
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

# 配置
BASE_DIR = Path(__file__).parent.parent
FAILURE_LOG_DIR = BASE_DIR / "memory" / "代码生成失败案例"
FAILURE_LOG_FILE = FAILURE_LOG_DIR / "failures.json"
STATS_FILE = FAILURE_LOG_DIR / "stats.json"

# 确保目录存在
FAILURE_LOG_DIR.mkdir(parents=True, exist_ok=True)


class FailureLogger:
    """失败案例记录器"""
    
    def __init__(self):
        self.failures = self._load_failures()
    
    def _load_failures(self) -> List[Dict]:
        """加载失败案例"""
        if FAILURE_LOG_FILE.exists():
            try:
                return json.loads(FAILURE_LOG_FILE.read_text(encoding='utf-8'))
            except:
                return []
        return []
    
    def _save_failures(self):
        """保存失败案例"""
        FAILURE_LOG_FILE.write_text(
            json.dumps(self.failures, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
    
    def add_failure(
        self,
        description: str,
        error: str,
        template_type: str = "script",
        prompt: str = "",
        generated_code: str = "",
        syntax_error: str = "",
        review_score: Optional[float] = None
    ):
        """添加失败案例
        
        Args:
            description: 功能描述
            error: 错误信息
            template_type: 模板类型
            prompt: 生成的prompt
            generated_code: 生成的代码（前500字符）
            syntax_error: 语法错误详情
            review_score: 代码审查得分
        """
        # 截取关键信息
        code_snippet = generated_code[:500] if generated_code else ""
        
        failure = {
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "error": error,
            "template_type": template_type,
            "prompt": prompt[:500],
            "code_snippet": code_snippet,
            "syntax_error": syntax_error,
            "review_score": review_score,
            "root_cause": self._analyze_root_cause(error, syntax_error)
        }
        
        self.failures.append(failure)
        self._save_failures()
        
        print(f"✅ 失败案例已记录: {description[:30]}...")
        print(f"   根因分析: {failure['root_cause']}")
        
        return failure
    
    def _analyze_root_cause(self, error: str, syntax_error: str) -> str:
        """分析根因"""
        error_lower = (error + " " + syntax_error).lower()
        
        # 匹配常见错误模式
        patterns = [
            (r"syntaxerror.*invalid syntax", "语法错误"),
            (r"syntaxerror.*unterminated", "字符串未闭合"),
            (r"syntaxerror.*expected", "语法期望错误"),
            (r"keyerror", "键错误"),
            (r"typeerror", "类型错误"),
            (r"attributeerror", "属性错误"),
            (r"nameerror.*not defined", "未定义变量"),
            (r"importerror.*no module", "导入模块失败"),
            (r"filenotfounderror", "文件不存在"),
            (r"unicodeencodeerror|unicodedecodeerror", "编码错误"),
            (r"noneType.*not subscriptable", "None类型错误"),
        ]
        
        for pattern, cause in patterns:
            if re.search(pattern, error_lower):
                return cause
        
        return "未知错误"
    
    def list_failures(self, limit: int = 10):
        """列出失败案例"""
        if not self.failures:
            print("暂无失败案例")
            return
        
        print(f"\n=== 代码生成失败案例 ({len(self.failures)}条) ===\n")
        
        for i, f in enumerate(self.failures[-limit:], 1):
            print(f"[{i}] {f['timestamp'][:16]}")
            print(f"    描述: {f['description'][:50]}...")
            print(f"    错误: {f['error'][:60]}...")
            print(f"    根因: {f['root_cause']}")
            print()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        if not self.failures:
            return {"total": 0, "by_cause": {}, "by_type": {}}
        
        by_cause = {}
        by_type = {}
        by_template = {}
        scores = []
        
        for f in self.failures:
            cause = f.get('root_cause', 'unknown')
            by_cause[cause] = by_cause.get(cause, 0) + 1
            
            desc = f.get('description', '')
            if 'script' in desc.lower():
                by_type['通用脚本'] = by_type.get('通用脚本', 0) + 1
            elif 'api' in desc.lower():
                by_type['API客户端'] = by_type.get('API客户端', 0) + 1
            elif 'pipeline' in desc.lower():
                by_type['数据处理'] = by_type.get('数据处理', 0) + 1
            else:
                by_type['其他'] = by_type.get('其他', 0) + 1
            
            template = f.get('template_type', 'script')
            by_template[template] = by_template.get(template, 0) + 1
            
            if f.get('review_score'):
                scores.append(f['review_score'])
        
        return {
            "total": len(self.failures),
            "by_cause": by_cause,
            "by_type": by_type,
            "by_template": by_template,
            "avg_score": round(sum(scores)/len(scores), 1) if scores else None
        }
    
    def print_stats(self):
        """打印统计报告"""
        stats = self.get_stats()
        
        print("\n=== 代码生成失败案例统计 ===\n")
        print(f"总失败次数: {stats['total']}")
        
        if stats.get('avg_score'):
            print(f"平均审查得分: {stats['avg_score']}分")
        
        print("\n按错误类型分布:")
        for cause, count in sorted(stats.get('by_cause', {}).items(), key=lambda x: -x[1]):
            print(f"  {cause}: {count}次")
        
        print("\n按模板类型分布:")
        for template, count in sorted(stats.get('by_template', {}).items(), key=lambda x: -x[1]):
            print(f"  {template}: {count}次")
        
        print("\n按功能类型分布:")
        for ftype, count in sorted(stats.get('by_type', {}).items(), key=lambda x: -x[1]):
            print(f"  {ftype}: {count}次")
        
        # 保存统计
        STATS_FILE.write_text(
            json.dumps(stats, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
    
    def generate_optimization(self) -> str:
        """生成优化建议"""
        stats = self.get_stats()
        
        suggestions = []
        
        # 基于错误类型生成建议
        if stats['by_cause'].get('语法错误', 0) > 3:
            suggestions.append("【语法错误频发】检查模板中的引号匹配和缩进")
        
        if stats['by_cause'].get('编码错误', 0) > 2:
            suggestions.append("【编码错误频发】确保所有文件使用utf-8编码，避免emoji")
        
        if stats['by_cause'].get('导入模块失败', 0) > 2:
            suggestions.append("【导入错误频发】在模板中添加常见模块导入检查")
        
        if stats['by_cause'].get('None类型错误', 0) > 2:
            suggestions.append("【None错误频发】增强空值检查，添加边界处理")
        
        # 基于模板类型生成建议
        if stats.get('by_template', {}).get('script', 0) > stats.get('total', 1) * 0.5:
            suggestions.append("【通用脚本模板】增加更多参数验证和错误处理")
        
        # 基于审查得分生成建议
        avg_score = stats.get('avg_score')
        if avg_score and avg_score < 70:
            suggestions.append(f"【代码质量】平均审查得分{stats['avg_score']}分，建议优化prompt模板")
        
        if not suggestions:
            suggestions.append("当前代码生成质量良好，继续保持")
        
        return "\n".join(suggestions)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="代码生成失败案例记录工具")
    parser.add_argument("description", nargs="?", help="失败案例描述")
    parser.add_argument("--error", "-e", help="错误信息")
    parser.add_argument("--type", "-t", default="script", help="模板类型")
    parser.add_argument("--list", "-l", action="store_true", help="列出失败案例")
    parser.add_argument("--stats", "-s", action="store_true", help="查看统计")
    parser.add_argument("--optimize", "-o", action="store_true", help="生成优化建议")
    
    args = parser.parse_args()
    
    logger = FailureLogger()
    
    if args.list:
        logger.list_failures()
    elif args.stats:
        logger.print_stats()
    elif args.optimize:
        print(logger.generate_optimization())
    elif args.description and args.error:
        logger.add_failure(args.description, args.error, args.type)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
