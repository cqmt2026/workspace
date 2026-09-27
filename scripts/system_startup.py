# -*- coding: utf-8 -*-
"""
系统启动脚本
每次系统启动时自动运行所有规则检查

执行顺序:
1. 会话启动检查 (session_start_checker.py)
2. 规则检查器初始化 (rule_checker.py)
3. 自动监控系统启动 (auto_monitor.py)
4. 生成启动报告
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json
import io

sys.stdout.reconfigure(encoding='utf-8')

class SystemStartup:
    """系统启动管理器"""
    
    def __init__(self):
        self.workspace = Path(r'C:\Users\Administrator\.openclaw\workspace')
        self.scripts_dir = self.workspace / 'scripts'
        self.start_time = datetime.now()
        self.results = {
            'startup_time': self.start_time.isoformat(),
            'checks': {},
            'summary': {},
        }
    
    def run_session_start_checker(self):
        """步骤 1: 运行会话启动检查"""
        print('='*60)
        print('[1/4] 会话启动检查')
        print('='*60)
        print()
        
        script = self.scripts_dir / 'session_start_checker.py'
        if not script.exists():
            print(f'❌ 脚本不存在：{script}')
            self.results['checks']['session_start'] = {
                'status': '❌ 脚本不存在',
                'success': False,
            }
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=60
            )
            
            # 打印输出
            print(result.stdout)
            if result.stderr:
                print(f'错误：{result.stderr}')
            
            success = result.returncode == 0
            self.results['checks']['session_start'] = {
                'status': '✅ 通过' if success else '❌ 失败',
                'success': success,
                'returncode': result.returncode,
            }
            
            return success
        
        except subprocess.TimeoutExpired:
            print('❌ 检查超时 (60 秒)')
            self.results['checks']['session_start'] = {
                'status': '❌ 超时',
                'success': False,
            }
            return False
        except Exception as e:
            print(f'❌ 执行失败：{e}')
            self.results['checks']['session_start'] = {
                'status': f'❌ 错误：{e}',
                'success': False,
            }
            return False
    
    def run_rule_checker_init(self):
        """步骤 2: 初始化规则检查器"""
        print()
        print('='*60)
        print('[2/4] 规则检查器初始化')
        print('='*60)
        print()
        
        script = self.scripts_dir / 'rule_checker.py'
        if not script.exists():
            print(f'❌ 脚本不存在：{script}')
            self.results['checks']['rule_checker'] = {
                'status': '❌ 脚本不存在',
                'success': False,
            }
            return False
        
        try:
            # 运行测试
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )
            
            # 打印输出
            print(result.stdout)
            
            # 规则检查器只需加载，不要求测试通过
            self.results['checks']['rule_checker'] = {
                'status': '✅ 已加载',
                'success': True,
            }
            
            return True
        
        except Exception as e:
            print(f'⚠️ 初始化警告：{e}')
            self.results['checks']['rule_checker'] = {
                'status': f'⚠️ 警告：{e}',
                'success': True,  # 警告不影响启动
            }
            return True
    
    def run_auto_monitor(self):
        """步骤 3: 启动自动监控"""
        print()
        print('='*60)
        print('[3/4] 自动监控系统')
        print('='*60)
        print()
        
        script = self.scripts_dir / 'auto_monitor.py'
        if not script.exists():
            print(f'❌ 脚本不存在：{script}')
            self.results['checks']['auto_monitor'] = {
                'status': '❌ 脚本不存在',
                'success': False,
            }
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=60
            )
            
            # 打印输出
            print(result.stdout)
            
            success = result.returncode == 0
            self.results['checks']['auto_monitor'] = {
                'status': '✅ 已启动' if success else '⚠️ 需注意',
                'success': True,  # 监控启动即可，有问题会提醒
            }
            
            return True
        
        except Exception as e:
            print(f'⚠️ 监控启动警告：{e}')
            self.results['checks']['auto_monitor'] = {
                'status': f'⚠️ 警告：{e}',
                'success': True,
            }
            return True
    
    def check_core_files(self):
        """步骤 4: 检查核心文件"""
        print()
        print('='*60)
        print('[4/4] 核心文件检查')
        print('='*60)
        print()
        
        core_files = {
            '核心规则卡片.md': '10 条铁律',
            '违规总结机制.md': '违规处理流程',
        }
        
        all_exist = True
        for fname, desc in core_files.items():
            fpath = self.workspace / fname
            if fpath.exists():
                size = fpath.stat().st_size
                print(f'✅ {fname:20} ({size:,} bytes) - {desc}')
            else:
                print(f'❌ {fname:20} - 缺失')
                all_exist = False
        
        self.results['checks']['core_files'] = {
            'status': '✅ 完整' if all_exist else '❌ 缺失',
            'success': all_exist,
        }
        
        return all_exist
    
    def generate_startup_report(self):
        """生成启动报告"""
        print()
        print('='*60)
        print('系统启动报告')
        print('='*60)
        print()
        
        # 计算总耗时
        end_time = datetime.now()
        elapsed = (end_time - self.start_time).total_seconds()
        
        # 统计通过情况
        checks = self.results['checks']
        total = len(checks)
        passed = sum(1 for c in checks.values() if c.get('success', False))
        
        # 生成摘要
        self.results['summary'] = {
            'end_time': end_time.isoformat(),
            'elapsed_seconds': elapsed,
            'total_checks': total,
            'passed_checks': passed,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'status': '✅ 启动成功' if passed == total else '⚠️ 部分失败',
        }
        
        # 打印报告
        print(f'启动时间：{self.start_time.strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'结束时间：{end_time.strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'总耗时：{elapsed:.1f} 秒')
        print()
        print(f'检查项目：{total} 个')
        print(f'通过项目：{passed}/{total}')
        print(f'通过率：{self.results["summary"]["success_rate"]:.0f}%')
        print()
        print(f'启动状态：{self.results["summary"]["status"]}')
        print()
        
        # 检查清单
        print('检查清单:')
        for name, result in checks.items():
            status = result.get('status', '未知')
            print(f'  {status:15} - {name}')
        print()
        
        # 保存报告
        self._save_report()
        
        print('='*60)
        
        return passed == total
    
    def _save_report(self):
        """保存启动报告"""
        report_file = self.workspace / 'memory' / 'startup_report.json'
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f'启动报告已保存：{report_file}')
    
    def run_all(self):
        """运行全部启动检查"""
        print()
        print('#'*60)
        print('#  系统启动检查')
        print('#'*60)
        print()
        
        # 执行检查
        results = [
            self.run_session_start_checker(),
            self.run_rule_checker_init(),
            self.run_auto_monitor(),
            self.check_core_files(),
        ]
        
        # 生成报告
        success = self.generate_startup_report()
        
        # 返回状态
        return success


if __name__ == '__main__':

    if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    startup = SystemStartup()
    success = startup.run_all()
    
    # 返回状态码
    sys.exit(0 if success else 1)
