#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字资产管理系统 v1.0
功能：资产注册、查询、迁移、索引
"""

import sys
import os
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(r'C:\Users\Administrator\.openclaw')
ASSET_DB = BASE_DIR / 'workspace' / 'data' / 'assets.json'
LOG_FILE = BASE_DIR / 'workspace' / 'logs' / 'asset_manager.log'

# 资产分类定义
CATEGORIES = {
    'math_ep': {
        'name': '数学动画-EP系列',
        'prefix': 'EP',
        'base_path': BASE_DIR / 'workspace' / 'math' / 'ep',
        'pattern': r'EP\d{6}_\d{3}',
    },
    'math_scene': {
        'name': '数学动画-场景库',
        'prefix': 'SC',
        'base_path': BASE_DIR / 'workspace' / 'math' / 'scenes',
        'pattern': r'SC_[A-Z]\w+',
    },
    'investment': {
        'name': '投资数据',
        'prefix': 'INV',
        'base_path': BASE_DIR / 'workspace' / 'investment' / 'data',
        'pattern': r'INV_\w+',
    },
    'baidu': {
        'name': '百都客户',
        'prefix': 'BD',
        'base_path': BASE_DIR / 'workspace' / 'baidu' / 'clients',
        'pattern': r'BD_\w+',
    },
    'shared': {
        'name': '共享资源',
        'prefix': 'SHARED',
        'base_path': BASE_DIR / 'workspace' / 'shared',
        'pattern': r'SHARED_\w+',
    },
}

class AssetManager:
    def __init__(self):
        self.db_path = ASSET_DB
        self.log_path = LOG_FILE
        self._ensure_dirs()
        self._init_db()
    
    def _ensure_dirs(self):
        """确保必要目录存在"""
        for cat in CATEGORIES.values():
            cat['base_path'].mkdir(parents=True, exist_ok=True)
        (BASE_DIR / 'workspace' / 'data').mkdir(parents=True, exist_ok=True)
        (BASE_DIR / 'workspace' / 'logs').mkdir(parents=True, exist_ok=True)
    
    def _init_db(self):
        """初始化资产数据库"""
        if not self.db_path.exists():
            self.db = {'assets': {}, 'index': {}, 'metadata': {
                'created': datetime.now().isoformat(),
                'version': '1.0',
                'total_assets': 0,
            }}
            self._save_db()
        else:
            self.db = json.loads(self.db_path.read_text(encoding='utf-8'))
    
    def _save_db(self):
        """保存数据库"""
        self.db['metadata']['last_updated'] = datetime.now().isoformat()
        self.db_path.write_text(json.dumps(self.db, ensure_ascii=False, indent=2), encoding='utf-8')
    
    def _log(self, msg):
        """记录日志"""
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    
    def _compute_hash(self, filepath):
        """计算文件哈希"""
        h = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    
    def register(self, filepath, category, custom_id=None):
        """注册新资产"""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"文件不存在: {filepath}")
        
        cat_config = CATEGORIES.get(category)
        if not cat_config:
            raise ValueError(f"未知分类: {category}")
        
        # 生成资产ID
        if custom_id:
            asset_id = custom_id
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            asset_id = f"{cat_config['prefix']}_{timestamp}_{filepath.stem}"
        
        # 计算哈希
        file_hash = self._compute_hash(filepath)
        
        # 创建目标路径
        target_dir = cat_config['base_path'] / datetime.now().strftime('%Y%m%d')
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{asset_id}{filepath.suffix}"
        
        # 复制文件
        shutil.copy2(filepath, target_path)
        
        # 记录资产信息
        asset_info = {
            'id': asset_id,
            'original_path': str(filepath),
            'stored_path': str(target_path),
            'category': category,
            'hash': file_hash,
            'size': filepath.stat().st_size,
            'registered_at': datetime.now().isoformat(),
            'metadata': {
                'extension': filepath.suffix,
                'mime_type': self._guess_mime(filepath.suffix),
            }
        }
        
        self.db['assets'][asset_id] = asset_info
        
        # 更新索引
        if category not in self.db['index']:
            self.db['index'][category] = {}
        if asset_id not in self.db['index'][category]:
            self.db['index'][category][asset_id] = str(target_path)
        
        # 更新日期索引
        date_key = datetime.now().strftime('%Y-%m-%d')
        if date_key not in self.db['index']:
            self.db['index'][date_key] = {}
        if asset_id not in self.db['index'][date_key]:
            self.db['index'][date_key][asset_id] = category
        
        self.db['metadata']['total_assets'] = len(self.db['assets'])
        self._save_db()
        self._log(f"注册资产: {asset_id} -> {target_path}")
        
        return asset_id
    
    def query(self, asset_id=None, category=None, date=None, keyword=None):
        """查询资产"""
        results = []
        
        if asset_id:
            # 按ID查询
            if asset_id in self.db['assets']:
                results.append(self.db['assets'][asset_id])
        elif category:
            # 按分类查询
            if category in self.db['index']:
                for aid in self.db['index'][category].keys():
                    results.append(self.db['assets'].get(aid))
        elif date:
            # 按日期查询
            if date in self.db['index']:
                for aid in self.db['index'][date].keys():
                    results.append(self.db['assets'].get(aid))
        elif keyword:
            # 关键词搜索
            kw_lower = keyword.lower()
            for aid, info in self.db['assets'].items():
                if kw_lower in aid.lower() or kw_lower in info.get('original_path', '').lower():
                    results.append(info)
        else:
            # 返回全部
            results = list(self.db['assets'].values())
        
        return [r for r in results if r is not None]
    
    def migrate_old_assets(self):
        """迁移旧资产到新结构"""
        migrated = 0
        # 扫描workspace/EP*目录
        ws_path = BASE_DIR / 'workspace'
        for item in ws_path.iterdir():
            if item.name.startswith('EP') and item.name[2:].isdigit():
                # EP系列目录
                for mp4 in item.glob('*.mp4'):
                    # 提取EP编号
                    ep_num = item.name[2:]
                    asset_id = f"EP_{datetime.now().strftime('%Y%m%d')}_{ep_num}_{mp4.stem}"
                    try:
                        self.register(mp4, 'math_ep', custom_id=asset_id)
                        migrated += 1
                    except Exception as e:
                        self._log(f"迁移失败 {mp4}: {e}")
        
        self._log(f"迁移完成: {migrated}个资产")
        return migrated
    
    def generate_report(self):
        """生成资产报告"""
        report = []
        report.append("=" * 70)
        report.append("数字资产管理系统报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("=" * 70)
        
        report.append(f"\n总资产数: {self.db['metadata']['total_assets']}")
        
        # 按分类统计
        report.append("\n【按分类统计】")
        cat_counts = {}
        for asset in self.db['assets'].values():
            cat = asset['category']
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
            cat_name = CATEGORIES.get(cat, {}).get('name', cat)
            report.append(f"  {cat_name}: {count}个")
        
        # 按日期统计（最近7天）
        report.append("\n【最近7天新增】")
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            if date in self.db['index']:
                count = len(self.db['index'][date])
                report.append(f"  {date}: {count}个")
        
        # 存储位置
        report.append("\n【存储位置】")
        for cat, config in CATEGORIES.items():
            path = config['base_path']
            if path.exists():
                count = len(list(path.rglob('*')))
                size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                report.append(f"  {config['name']}: {path} ({count}文件, {size/1024/1024:.1f}MB)")
        
        return "\n".join(report)
    
    def _guess_mime(self, ext):
        """猜测MIME类型"""
        mime_map = {
            '.mp4': 'video/mp4',
            '.py': 'text/x-python',
            '.md': 'text/markdown',
            '.json': 'application/json',
            '.db': 'application/x-sqlite3',
        }
        return mime_map.get(ext.lower(), 'application/octet-stream')


from datetime import timedelta

if __name__ == '__main__':
    import sys
    
    manager = AssetManager()
    
    if len(sys.argv) < 2:
        print("用法: python asset_manager.py <命令> [参数]")
        print("命令:")
        print("  register <文件路径> <分类> [自定义ID]  - 注册资产")
        print("  query [--id <ID>] [--category <分类>] [--date <日期>] [--keyword <关键词>] - 查询")
        print("  migrate  - 迁移旧资产")
        print("  report  - 生成报告")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'register':
        if len(sys.argv) < 4:
            print("错误: 需要文件和分类参数")
            sys.exit(1)
        filepath = sys.argv[2]
        category = sys.argv[3]
        custom_id = sys.argv[4] if len(sys.argv) > 4 else None
        asset_id = manager.register(filepath, category, custom_id)
        print(f"已注册: {asset_id}")
    
    elif cmd == 'query':
        args = sys.argv[2:]
        kwargs = {}
        i = 0
        while i < len(args):
            if args[i] == '--id' and i + 1 < len(args):
                kwargs['asset_id'] = args[i + 1]
                i += 2
            elif args[i] == '--category' and i + 1 < len(args):
                kwargs['category'] = args[i + 1]
                i += 2
            elif args[i] == '--date' and i + 1 < len(args):
                kwargs['date'] = args[i + 1]
                i += 2
            elif args[i] == '--keyword' and i + 1 < len(args):
                kwargs['keyword'] = args[i + 1]
                i += 2
            else:
                i += 1
        results = manager.query(**kwargs)
        print(f"查询结果: {len(results)}条")
        for r in results[:20]:
            print(f"  {r['id']}: {r['category']} - {r['stored_path']}")
    
    elif cmd == 'migrate':
        count = manager.migrate_old_assets()
        print(f"迁移完成: {count}个资产")
    
    elif cmd == 'report':
        print(manager.generate_report())
    
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)
