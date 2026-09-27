"""配置管理器 - 所有模块的统一配置入口

支持多级覆盖、热更新、配置验证。

配置优先级（高→低）:
  1. 命令行参数
  2. 环境变量
  3. 用户配置 (custom.yaml)
  4. 默认配置 (default.yaml)
"""

import os
import copy
import yaml
from typing import Any, Dict, List, Optional, Callable
from .exceptions import ConfigError


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._default_config: Dict[str, Any] = {}
        self._watchers: Dict[str, List[Callable]] = {}
        self._loaded = False

    def load(self, path: Optional[str] = None) -> 'ConfigManager':
        """加载配置

        Args:
            path: 用户配置文件路径。不传则只加载默认配置。
        """
        # 加载默认配置
        default_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'default.yaml')
        if os.path.exists(default_path):
            with open(default_path, 'r', encoding='utf-8') as f:
                self._default_config = yaml.safe_load(f) or {}
        else:
            self._default_config = {}

        # 从默认配置开始
        self._config = copy.deepcopy(self._default_config)

        # 加载用户配置
        if path and os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f) or {}
            self._deep_merge(self._config, user_config)

        # 环境变量覆盖
        self._apply_env_overrides()

        self._loaded = True
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键，支持点号分隔 (如 'data.db_path')
            default: 键不存在时的默认值
        """
        if not self._loaded:
            raise ConfigError("配置未加载，请先调用 load()")

        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> 'ConfigManager':
        """设置配置值

        Args:
            key: 配置键，支持点号分隔
            value: 配置值
        """
        keys = key.split('.')
        target = self._config
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value

        # 触发监听
        self._notify_watchers(key, value)
        return self

    def save(self, path: Optional[str] = None) -> 'ConfigManager':
        """保存配置到文件

        Args:
            path: 保存路径。不传则保存到用户配置路径。
        """
        if path is None:
            path = os.path.join(os.path.dirname(__file__), '..', 'config', 'custom.yaml')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
        return self

    def reload(self) -> 'ConfigManager':
        """重新加载配置"""
        self._config = copy.deepcopy(self._default_config)
        user_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'custom.yaml')
        if os.path.exists(user_path):
            with open(user_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f) or {}
            self._deep_merge(self._config, user_config)
        self._apply_env_overrides()
        return self

    def watch(self, key: str, callback: Callable[[str, Any], None]) -> 'ConfigManager':
        """监听配置变化

        Args:
            key: 要监听的配置键
            callback: 回调函数，接收 (key, new_value)
        """
        if key not in self._watchers:
            self._watchers[key] = []
        self._watchers[key].append(callback)
        return self

    def get_all(self) -> Dict[str, Any]:
        """获取全部配置"""
        return copy.deepcopy(self._config)

    def validate(self, required_keys: List[str]) -> List[str]:
        """验证必要配置是否存在

        Args:
            required_keys: 必要配置键列表

        Returns:
            缺失的配置键列表
        """
        missing = []
        for key in required_keys:
            if self.get(key) is None:
                missing.append(key)
        return missing

    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """深度合并字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖

        环境变量格式: AQ_DATA_DB_PATH -> data.db_path
        """
        prefix = 'AQ_'
        for env_key, env_value in os.environ.items():
            if env_key.startswith(prefix):
                config_key = env_key[len(prefix):].lower().replace('_', '.')
                # 尝试转换类型
                try:
                    if '.' in env_value:
                        env_value = float(env_value)
                    else:
                        env_value = int(env_value)
                except (ValueError, TypeError):
                    pass
                self.set(config_key, env_value)

    def _notify_watchers(self, key: str, value: Any) -> None:
        """通知配置监听器"""
        for watch_key, callbacks in self._watchers.items():
            if key.startswith(watch_key) or watch_key.startswith(key):
                for callback in callbacks:
                    try:
                        callback(key, value)
                    except Exception as e:
                        import logging
                        logging.warning(f"配置监听回调异常: {e}")