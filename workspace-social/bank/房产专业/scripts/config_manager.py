#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理工具 V2.0
集中管理所有配置，支持配置验证、版本管理、备份、导入导出

优化内容 (V2.0):
- ✅ 配置验证功能
- ✅ 配置版本管理
- ✅ 配置备份功能
- ✅ 配置导入导出
- ✅ 接入日志系统
- ✅ 完善文档字符串

作者：房地产自媒体团队
版本：V2.0
最后更新：2026-03-15
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
import sys

# 导入日志系统
sys.path.append(str(Path(__file__).parent))
from logger import logger


class ConfigValidationError(Exception):
    """配置验证异常"""
    pass


class ConfigManager:
    """
    高级配置管理器
    
    功能:
        - 配置加载/保存
        - 配置验证
        - 配置版本管理
        - 配置备份
        - 配置导入导出
        - 配置更新
    
    属性:
        config_file (Path): 配置文件路径
        backup_dir (Path): 备份目录
        config (dict): 配置字典
    
    示例:
        >>> config = ConfigManager()
        >>> config.show_config()
        >>> config.update_config('output', 'word_enabled', False)
        >>> config.backup_config()
    """
    
    # 配置 schema（用于验证）
    CONFIG_SCHEMA = {
        'system': {
            'required': True,
            'fields': {
                'name': {'type': str, 'required': True},
                'version': {'type': str, 'required': True},
                'last_update': {'type': str, 'required': False}
            }
        },
        'output': {
            'required': True,
            'fields': {
                'word_enabled': {'type': bool, 'required': True},
                'excel_enabled': {'type': bool, 'required': True},
                'auto_export': {'type': bool, 'required': True},
                'output_dir': {'type': str, 'required': True}
            }
        },
        'quality': {
            'required': True,
            'fields': {
                'min_score': {'type': int, 'required': True, 'min': 0, 'max': 100},
                'check_ai': {'type': bool, 'required': True},
                'check_data': {'type': bool, 'required': True},
                'check_writing': {'type': bool, 'required': True}
            }
        },
        'publish': {
            'required': True,
            'fields': {
                'platforms': {'type': list, 'required': True},
                'auto_publish': {'type': bool, 'required': True},
                'peak_hours': {'type': list, 'required': True}
            }
        },
        'schedule': {
            'required': True,
            'fields': {
                'morning_monitor': {'type': str, 'required': True},
                'noon_reminder': {'type': str, 'required': True},
                'evening_review': {'type': str, 'required': True},
                'night_backup': {'type': str, 'required': True}
            }
        }
    }
    
    def __init__(self, config_file='config.json', auto_load=True):
        """
        初始化配置管理器
        
        参数:
            config_file (str): 配置文件路径
            auto_load (bool): 是否自动加载配置
        
        示例:
            >>> config = ConfigManager('config.json')
            >>> config = ConfigManager('config.json', auto_load=False)
        """
        self.config_file = Path(config_file)
        self.backup_dir = Path('config_backups')
        self.backup_dir.mkdir(exist_ok=True)
        self.config = {}
        
        if auto_load:
            self.load_config()
        
        logger.info("配置管理器初始化完成")
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        返回:
            dict: 配置字典
        
        异常:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: JSON 格式错误
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                
                # 验证配置
                self.validate_config()
                
                logger.success(f"配置已加载：{self.config_file}")
                logger.debug(f"配置内容：{json.dumps(self.config, ensure_ascii=False, indent=2)}")
            else:
                logger.warning(f"配置文件不存在，使用默认配置：{self.config_file}")
                self.config = self._get_default_config()
                self.save_config()
            
            return self.config
            
        except json.JSONDecodeError as e:
            logger.error(f"配置文件 JSON 格式错误：{e}")
            raise
        except Exception as e:
            logger.error(f"加载配置失败：{e}")
            raise
    
    def save_config(self, backup=True) -> bool:
        """
        保存配置文件
        
        参数:
            backup (bool): 保存前是否备份
        
        返回:
            bool: 是否保存成功
        """
        try:
            # 备份旧配置
            if backup and self.config_file.exists():
                self.backup_config()
            
            # 更新最后更新时间
            self.config.setdefault('system', {})
            self.config['system']['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.success(f"配置已保存：{self.config_file}")
            return True
            
        except (IOError, OSError) as e:
            logger.error(f"保存配置失败：{e}")
            return False
    
    def validate_config(self) -> bool:
        """
        验证配置有效性
        
        返回:
            bool: 配置是否有效
        
        异常:
            ConfigValidationError: 配置验证失败
        """
        try:
            for section, schema in self.CONFIG_SCHEMA.items():
                if schema['required'] and section not in self.config:
                    raise ConfigValidationError(f"缺少必需的配置项：{section}")
                
                if section in self.config:
                    for field, field_schema in schema['fields'].items():
                        if field_schema['required'] and field not in self.config[section]:
                            raise ConfigValidationError(f"缺少必需的字段：{section}.{field}")
                        
                        if field in self.config[section]:
                            value = self.config[section][field]
                            
                            # 类型检查
                            if 'type' in field_schema and not isinstance(value, field_schema['type']):
                                raise ConfigValidationError(
                                    f"字段类型错误：{section}.{field} 应为 {field_schema['type'].__name__}"
                                )
                            
                            # 范围检查
                            if 'min' in field_schema and value < field_schema['min']:
                                raise ConfigValidationError(
                                    f"字段值过小：{section}.{field} = {value} (最小值：{field_schema['min']})"
                                )
                            
                            if 'max' in field_schema and value > field_schema['max']:
                                raise ConfigValidationError(
                                    f"字段值过大：{section}.{field} = {value} (最大值：{field_schema['max']})"
                                )
            
            logger.success("配置验证通过")
            return True
            
        except ConfigValidationError as e:
            logger.error(f"配置验证失败：{e}")
            raise
        except Exception as e:
            logger.error(f"配置验证异常：{e}")
            raise
    
    def backup_config(self, backup_name=None) -> Path:
        """
        备份配置文件
        
        参数:
            backup_name (str): 备份文件名，默认使用时间戳
        
        返回:
            Path: 备份文件路径
        """
        try:
            if not self.config_file.exists():
                logger.warning("配置文件不存在，跳过备份")
                return None
            
            if backup_name is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f'config_backup_{timestamp}.json'
            
            backup_path = self.backup_dir / backup_name
            shutil.copy2(self.config_file, backup_path)
            
            logger.success(f"配置已备份：{backup_path}")
            return backup_path
            
        except (IOError, OSError) as e:
            logger.error(f"备份配置失败：{e}")
            return None
    
    def restore_config(self, backup_file) -> bool:
        """
        恢复配置文件
        
        参数:
            backup_file (str): 备份文件路径
        
        返回:
            bool: 是否恢复成功
        """
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                logger.error(f"备份文件不存在：{backup_path}")
                return False
            
            shutil.copy2(backup_path, self.config_file)
            self.load_config()
            
            logger.success(f"配置已恢复：{backup_path}")
            return True
            
        except (IOError, OSError) as e:
            logger.error(f"恢复配置失败：{e}")
            return False
    
    def export_config(self, export_file) -> bool:
        """
        导出配置文件
        
        参数:
            export_file (str): 导出文件路径
        
        返回:
            bool: 是否导出成功
        """
        try:
            export_path = Path(export_file)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.success(f"配置已导出：{export_path}")
            return True
            
        except (IOError, OSError) as e:
            logger.error(f"导出配置失败：{e}")
            return False
    
    def import_config(self, import_file) -> bool:
        """
        导入配置文件
        
        参数:
            import_file (str): 导入文件路径
        
        返回:
            bool: 是否导入成功
        """
        try:
            import_path = Path(import_file)
            if not import_path.exists():
                logger.error(f"导入文件不存在：{import_path}")
                return False
            
            # 备份当前配置
            self.backup_config()
            
            # 导入配置
            with open(import_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # 验证配置
            self.validate_config()
            
            # 保存配置
            self.save_config(backup=False)
            
            logger.success(f"配置已导入：{import_path}")
            return True
            
        except (IOError, OSError, json.JSONDecodeError) as e:
            logger.error(f"导入配置失败：{e}")
            return False
    
    def update_config(self, section: str, key: str, value: Any) -> bool:
        """
        更新配置项
        
        参数:
            section (str): 配置节
            key (str): 配置键
            value (Any): 配置值
        
        返回:
            bool: 是否更新成功
        """
        try:
            if section not in self.config:
                logger.error(f"配置项不存在：{section}")
                self.config[section] = {}
            
            old_value = self.config[section].get(key)
            self.config[section][key] = value
            
            # 保存配置
            if self.save_config():
                logger.success(f"配置已更新：{section}.{key} = {value} (原值：{old_value})")
                return True
            else:
                # 恢复旧值
                self.config[section][key] = old_value
                return False
            
        except Exception as e:
            logger.error(f"更新配置失败：{e}")
            return False
    
    def get_config(self, section: str, key: str = None, default: Any = None) -> Any:
        """
        获取配置项
        
        参数:
            section (str): 配置节
            key (str, optional): 配置键，None 返回整个节
            default (Any, optional): 默认值
        
        返回:
            Any: 配置值
        """
        try:
            if section not in self.config:
                logger.warning(f"配置节不存在：{section}")
                return default
            
            if key is None:
                return self.config[section]
            
            return self.config[section].get(key, default)
            
        except Exception as e:
            logger.error(f"获取配置失败：{e}")
            return default
    
    def show_config(self):
        """
        显示配置信息
        """
        print(f"\n{'='*60}")
        print(f"系统配置")
        print(f"{'='*60}")
        
        print(f"\n【系统信息】")
        print(f"  名称：{self.config.get('system', {}).get('name', 'N/A')}")
        print(f"  版本：{self.config.get('system', {}).get('version', 'N/A')}")
        print(f"  最后更新：{self.config.get('system', {}).get('last_update', 'N/A')}")
        
        print(f"\n【输出设置】")
        output = self.config.get('output', {})
        print(f"  Word 导出：{'✅' if output.get('word_enabled') else '❌'}")
        print(f"  Excel 导出：{'✅' if output.get('excel_enabled') else '❌'}")
        print(f"  自动导出：{'✅' if output.get('auto_export') else '❌'}")
        print(f"  输出目录：{output.get('output_dir', 'N/A')}")
        
        print(f"\n【质量检查】")
        quality = self.config.get('quality', {})
        print(f"  最低分数：{quality.get('min_score', 'N/A')}")
        print(f"  AI 检测：{'✅' if quality.get('check_ai') else '❌'}")
        print(f"  数据核实：{'✅' if quality.get('check_data') else '❌'}")
        print(f"  写作规范：{'✅' if quality.get('check_writing') else '❌'}")
        
        print(f"\n【发布设置】")
        publish = self.config.get('publish', {})
        print(f"  平台：{', '.join(publish.get('platforms', []))}")
        print(f"  自动发布：{'✅' if publish.get('auto_publish') else '❌'}")
        print(f"  流量高峰：{', '.join(publish.get('peak_hours', []))}")
        
        print(f"\n【定时任务】")
        schedule = self.config.get('schedule', {})
        task_names = {
            'morning_monitor': '早间监测',
            'noon_reminder': '午间提醒',
            'evening_review': '晚间复盘',
            'night_backup': '夜间备份'
        }
        for task, time in schedule.items():
            task_name = task_names.get(task, task)
            print(f"  {task_name}: {time}")
        
        print(f"\n{'='*60}")
    
    def get_backup_files(self) -> list:
        """
        获取所有备份文件列表
        
        返回:
            list: 备份文件列表
        """
        backups = []
        for file in self.backup_dir.glob('*.json'):
            backups.append({
                'path': str(file),
                'size': file.stat().st_size,
                'modified': datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
        return sorted(backups, key=lambda x: x['modified'], reverse=True)
    
    def cleanup_old_backups(self, keep_count=10) -> int:
        """
        清理旧备份文件
        
        参数:
            keep_count (int): 保留的备份数量
        
        返回:
            int: 清理的文件数量
        """
        backups = self.get_backup_files()
        cleaned_count = 0
        
        for backup in backups[keep_count:]:
            try:
                Path(backup['path']).unlink()
                logger.info(f"清理旧备份：{backup['path']}")
                cleaned_count += 1
            except OSError as e:
                logger.error(f"清理备份失败：{e}")
        
        logger.success(f"清理完成，共清理 {cleaned_count} 个备份文件")
        return cleaned_count
    
    def _get_default_config(self) -> dict:
        """
        获取默认配置
        
        返回:
            dict: 默认配置字典
        """
        return {
            'system': {
                'name': '房地产自媒体自动化系统',
                'version': 'V3.1',
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'output': {
                'word_enabled': True,
                'excel_enabled': True,
                'auto_export': True,
                'output_dir': 'articles'
            },
            'quality': {
                'min_score': 85,
                'check_ai': True,
                'check_data': True,
                'check_writing': True
            },
            'publish': {
                'platforms': ['百家号', '头条号'],
                'auto_publish': False,
                'peak_hours': ['12:00', '20:00']
            },
            'schedule': {
                'morning_monitor': '08:00',
                'noon_reminder': '12:00',
                'evening_review': '20:00',
                'night_backup': '22:00'
            }
        }


def main():
    """主函数"""
    try:
        print("=" * 60)
        print("配置管理工具 V2.0 测试")
        print("=" * 60)
        
        config = ConfigManager()
        
        # 显示配置
        config.show_config()
        
        # 测试配置更新
        print("\n测试配置更新:")
        config.update_config('output', 'word_enabled', False)
        
        # 测试备份
        print("\n创建配置备份:")
        backup_path = config.backup_config()
        print(f"备份文件：{backup_path}")
        
        # 测试获取备份列表
        print("\n备份文件列表:")
        backups = config.get_backup_files()
        for backup in backups[:5]:
            print(f"  {backup['path']} ({backup['size']} bytes, {backup['modified']})")
        
        # 测试配置验证
        print("\n配置验证:")
        try:
            config.validate_config()
            print("✅ 配置验证通过")
        except ConfigValidationError as e:
            print(f"❌ 配置验证失败：{e}")
        
        print("\n" + "=" * 60)
        print("配置管理工具测试完成")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"测试失败：{e}")
        print(f"\n[错误] 测试失败：{e}")


if __name__ == '__main__':
    main()
