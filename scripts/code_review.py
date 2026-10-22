#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码审查工具 - 方案B配套

用法：
    python code_review.py path/to/script.py
    python code_review.py path/to/script.py --json
"""

import os
import sys
import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 检查规则
CHECK_RULES = {
    "语法检查": "syntax",
    "边界处理": "boundary",
    "错误处理": "error_handling",
    "命名规范": "naming",
    "函数长度": "function_length",
    "注释密度": "comment_density",
    "导入检查": "imports",
    "类型提示": "type_hints",
}

class CodeReviewer:
    """代码审查器"""
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.code = self.filepath.read_text(encoding='utf-8')
        self.tree = None
        self.issues = []
        
        # 解析AST
        try:
            self.tree = ast.parse(self.code)
        except SyntaxError as e:
            self.issues.append({
                "check": "语法检查",
                "severity": "ERROR",
                "message": f"语法错误: {e}"
            })
    
    def review(self) -> Dict:
        """执行所有检查
        
        Returns:
            dict: 审查结果
        """
        results = {}
        
        for check_name, check_func_name in CHECK_RULES.items():
            check_func = getattr(self, f'check_{check_func_name}', None)
            if check_func:
                result = check_func()
                results[check_name] = result
                if result['status'] in ['ERROR', 'WARN']:
                    self.issues.append({
                        "check": check_name,
                        **result
                    })
        
        # 计算总分
        total_checks = len(results)
        passed_checks = sum(1 for r in results.values() if r['status'] == 'PASS')
        self.overall_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "filepath": str(self.filepath),
            "score": self.overall_score,
            "checks": results,
            "issues": self.issues,
            "summary": self._generate_summary()
        }
    
    def check_syntax(self) -> Dict:
        """语法检查"""
        if self.tree is None:
            return {"status": "ERROR", "message": "语法错误，无法继续审查"}
        return {"status": "PASS", "message": "语法正确"}
    
    def check_boundary(self) -> Dict:
        """边界处理检查"""
        issues = []
        
        # 检查是否有空值处理
        has_none_check = bool(re.search(r'if\s+.*is\s+None|if\s+not\s+\w+|if\s+len\(', self.code))
        
        # 检查是否有空列表处理
        has_empty_list = bool(re.search(r'if\s+not\s+\w+\s*\[|\[\s*\]', self.code))
        
        # 检查函数参数是否有默认值
        has_default_params = bool(re.search(r'def\s+\w+\([^)]*=\s*[^)]+', self.code))
        
        if not has_none_check and not has_empty_list:
            issues.append("建议添加空值检查（None/空列表）")
        
        if not has_default_params:
            issues.append("建议为函数参数添加默认值")
        
        return {
            "status": "WARN" if issues else "PASS",
            "message": "; ".join(issues) if issues else "边界处理良好"
        }
    
    def check_error_handling(self) -> Dict:
        """错误处理检查"""
        has_try_except = 'try:' in self.code and 'except' in self.code
        has_specific_except = bool(re.search(r'except\s+\w+', self.code))
        has_generic_except = 'except:' in self.code or 'except Exception' in self.code
        
        issues = []
        
        if not has_try_except:
            issues.append("建议添加异常处理（try-except）")
        elif has_generic_except and not has_specific_except:
            issues.append("建议使用具体异常类型，避免裸except")
        
        return {
            "status": "WARN" if issues else "PASS",
            "message": "; ".join(issues) if issues else "错误处理良好"
        }
    
    def check_naming(self) -> Dict:
        """命名规范检查"""
        issues = []
        
        # 检查函数命名（应该是snake_case）
        func_names = [node.name for node in ast.walk(self.tree) if isinstance(node, ast.FunctionDef)]
        camelcase_funcs = [name for name in func_names if re.search(r'[A-Z]', name) and name != name.upper()]
        
        if camelcase_funcs:
            issues.append(f"发现驼峰命名函数: {camelcase_funcs[:5]}")
        
        # 检查常量命名（应该是UPPER_SNAKE）
        const_names = [node.targets[0].id for node in ast.walk(self.tree) 
                       if isinstance(node, ast.Assign) 
                       and isinstance(node.targets[0], ast.Name)
                       and node.targets[0].id.isupper()]
        
        return {
            "status": "WARN" if issues else "PASS",
            "message": "; ".join(issues) if issues else "命名规范良好"
        }
    
    def check_function_length(self) -> Dict:
        """函数长度检查"""
        long_functions = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                length = len(node.body)
                if length > 50:
                    long_functions.append((node.name, length))
        
        if long_functions:
            return {
                "status": "WARN",
                "message": f"发现过长函数（>50行）: {long_functions[:5]}"
            }
        
        return {"status": "PASS", "message": "函数长度合理"}
    
    def check_comment_density(self) -> Dict:
        """注释密度检查"""
        lines = self.code.split('\n')
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        total_lines = len([l for l in lines if l.strip()])
        
        density = comment_lines / total_lines * 100 if total_lines > 0 else 0
        
        if density < 5:
            return {
                "status": "WARN",
                "message": f"注释密度较低（{density:.1f}%），建议增加到10%以上"
            }
        
        return {"status": "PASS", "message": f"注释密度良好（{density:.1f}%）"}
    
    def check_imports(self) -> Dict:
        """导入检查"""
        issues = []
        
        # 检查是否有未使用的导入
        imports = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.append(alias.asname or alias.name)
        
        # 检查导入的模块是否在代码中使用
        for import_name in imports:
            # 简单检查：看导入名是否在代码其他地方出现
            pattern = r'\b' + re.escape(import_name) + r'\b'
            if not re.search(pattern, self.code):
                issues.append(f"可能未使用的导入: {import_name}")
        
        return {
            "status": "WARN" if issues else "PASS",
            "message": "; ".join(issues) if issues else "导入良好"
        }
    
    def check_type_hints(self) -> Dict:
        """类型提示检查"""
        has_type_hints = bool(re.search(r'def\s+\w+\([^)]*\)\s*:\s*[^:]*->', self.code))
        has_param_types = bool(re.search(r'def\s+\w+\([^)]*:\s*\w+', self.code))
        
        if not has_type_hints and not has_param_types:
            return {
                "status": "WARN",
                "message": "建议添加类型提示"
            }
        
        return {"status": "PASS", "message": "类型提示良好"}
    
    def _generate_summary(self) -> str:
        """生成审查摘要"""
        errors = sum(1 for i in self.issues if i.get('severity') == 'ERROR')
        warnings = sum(1 for i in self.issues if i.get('severity') == 'WARN')
        
        if errors > 0:
            return f"FAIL: {errors} errors, {warnings} warnings"
        elif warnings > 0:
            return f"WARN: {warnings} warnings"
        else:
            return f"PASS: score={self.overall_score:.1f}"


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="代码审查工具")
    parser.add_argument("filepath", help="要审查的Python文件路径")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    parser.add_argument("--min-score", type=float, default=70.0, 
                        help="最低通过分数（默认70）")
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    filepath = Path(args.filepath)
    if not filepath.exists():
        print(f"错误：文件不存在: {filepath}", file=sys.stderr)
        sys.exit(1)
    
    # 执行审查
    reviewer = CodeReviewer(str(filepath))
    result = reviewer.review()
    
    # 输出结果
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"\n=== 代码审查报告 ===")
        print(f"文件: {filepath}")
        print(f"得分: {result['score']:.1f}/100")
        print(f"\n检查项:")
        for check_name, check_result in result['checks'].items():
            icon = "[OK]" if check_result['status'] == 'PASS' else "[WARN]"
            print(f"  {icon} {check_name}: {check_result['message']}")
        
        if result['issues']:
            print(f"\n问题列表:")
            for issue in result['issues']:
                severity = "错误" if issue.get('severity') == 'ERROR' else "警告"
                print(f"  [{severity}] {issue['check']}: {issue['message']}")
        
        print(f"\n{result['summary']}")
    
    # 根据分数决定是否通过
    if result['score'] < args.min_score:
        print(f"\nFAIL: below {args.min_score} points")
        sys.exit(1)
    else:
        print(f"\nPASSED")
        sys.exit(0)


if __name__ == '__main__':
    main()
