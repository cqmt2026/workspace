"""模型注册中心 - 模型生命周期管理"""
import os
import json
from typing import Optional, Dict, List, Any
from datetime import datetime


class ModelRegistry:
    """模型注册中心

    管理模型生命周期：开发→验证→上线→下线。
    """

    def __init__(self, config=None):
        self._config = config
        self._registry_dir = self._get_registry_dir()
        os.makedirs(self._registry_dir, exist_ok=True)
        self._models: Dict[str, dict] = {}

    def register(self, name: str, model_type: str, params: dict = None) -> str:
        """注册模型

        Args:
            name: 模型名称
            model_type: 模型类型 (lightgbm/xgboost/mstnn)
            params: 训练参数

        Returns:
            模型版本号
        """
        version = self._next_version(name)
        record = {
            'name': name,
            'version': version,
            'model_type': model_type,
            'params': params or {},
            'status': 'developing',  # developing → validating → online → offline
            'created_at': datetime.now().isoformat(),
            'metrics': {},
            'deployments': [],
        }
        self._save_record(name, version, record)
        self._models[f"{name}_{version}"] = record
        return version

    def update_status(self, name: str, version: str, status: str):
        """更新模型状态

        Args:
            name: 模型名称
            version: 版本号
            status: developing/validating/online/offline
        """
        key = f"{name}_{version}"
        if key in self._models:
            self._models[key]['status'] = status
            self._save_record(name, version, self._models[key])

    def update_metrics(self, name: str, version: str, metrics: dict):
        """更新评估指标"""
        key = f"{name}_{version}"
        if key in self._models:
            self._models[key]['metrics'] = metrics
            self._save_record(name, version, self._models[key])

    def get_online_model(self, name: str) -> Optional[dict]:
        """获取当前在线的模型"""
        for key, record in self._models.items():
            if record['name'] == name and record['status'] == 'online':
                return record
        # 从文件查找
        records = self.list_models(name)
        for r in records:
            if r['status'] == 'online':
                return r
        return None

    def list_models(self, name: Optional[str] = None,
                    status: Optional[str] = None) -> List[dict]:
        """列出模型

        Args:
            name: 模型名称过滤
            status: 状态过滤

        Returns:
            模型记录列表
        """
        results = []
        if not os.path.exists(self._registry_dir):
            return results

        for fname in os.listdir(self._registry_dir):
            if not fname.endswith('.json'):
                continue
            with open(os.path.join(self._registry_dir, fname), 'r', encoding='utf-8') as f:
                record = json.load(f)

            if name and record['name'] != name:
                continue
            if status and record['status'] != status:
                continue
            results.append(record)

        return sorted(results, key=lambda x: x['created_at'], reverse=True)

    def get_model_info(self, name: str, version: str) -> Optional[dict]:
        """获取模型信息"""
        key = f"{name}_{version}"
        if key in self._models:
            return self._models[key]

        path = os.path.join(self._registry_dir, f"{name}_{version}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                record = json.load(f)
            self._models[key] = record
            return record
        return None

    def _next_version(self, name: str) -> str:
        """生成下一个版本号"""
        existing = self.list_models(name)
        if not existing:
            return 'v1.0.0'

        versions = []
        for r in existing:
            try:
                v = r['version'].lstrip('v')
                versions.append([int(x) for x in v.split('.')])
            except (ValueError, AttributeError):
                pass

        if not versions:
            return 'v1.0.0'

        latest = max(versions)
        latest[-1] += 1
        return 'v' + '.'.join(str(x) for x in latest)

    def _save_record(self, name: str, version: str, record: dict):
        """保存模型记录到文件"""
        path = os.path.join(self._registry_dir, f"{name}_{version}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

    def _get_registry_dir(self) -> str:
        """获取注册目录"""
        if self._config:
            model_dir = self._config.get('models.model_dir', '')
            if model_dir:
                return os.path.join(model_dir, 'registry')
        return os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'data', 'models', 'registry')