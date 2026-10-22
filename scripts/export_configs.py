#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
export_configs.py - 配置导出工具

功能：
1. 导出所有配置文件到时间戳目录
2. 生成配置清单
3. 可选压缩打包

用法：
    python export_configs.py              # 导出到默认目录
    python export_configs.py --output .   # 导出到当前目录
    python export_configs.py --zip        # 同时生成ZIP包
"""

import os
import sys
import json
import shutil
import zipfile
import datetime
from pathlib import Path

BASE = Path(r"C:\Users\Administrator\.openclaw")
EXPORT_BASE = BASE / "exports" / "configs"

# 需要导出的配置文件
CONFIG_FILES = [
    "openclaw.json",
    "backup_config.json",
    "circuit_breaker.json",
    "config_center.json",
    "monitoring_config.json",
    "gateway_ha.json",
    "gateway_watchdog_config.json",
    "requirements.txt",
    ".env",
]

# 需要导出的目录
CONFIG_DIRS = [
    "workspace/scripts",
    "workspace/memory/lancedb",
]

def export_configs(output_dir=None, create_zip=False):
    """导出配置文件"""
    if output_dir is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = EXPORT_BASE / timestamp
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    exported = {
        "timestamp": datetime.datetime.now().isoformat(),
        "path": str(output_dir),
        "files": [],
        "dirs": []
    }
    
    # 导出配置文件
    print(f"导出配置文件到: {output_dir}")
    for config_file in CONFIG_FILES:
        src = BASE / config_file
        if src.exists():
            dst = output_dir / config_file
            shutil.copy2(src, dst)
            exported["files"].append(config_file)
            print('  [OK] ' + config_file + ' (' + str(src.stat().st_size) + ' bytes)')
        else:
            print('  [X] ' + config_file + ' (不存在)')
    
    # 导出目录
    for config_dir in CONFIG_DIRS:
        src = BASE / config_dir
        if src.exists():
            dst = output_dir / config_dir.replace("\\", "_").replace("/", "_")
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            exported["dirs"].append(config_dir)
            print(f"  ✓ {config_dir}")
    
    # 保存导出清单
    manifest = output_dir / "manifest.json"
    with open(manifest, 'w', encoding='utf-8') as f:
        json.dump(exported, f, indent=2, ensure_ascii=False)
    
    print(f"\n导出清单已保存: {manifest}")
    
    # 生成ZIP包
    if create_zip:
        zip_path = output_dir.parent / f"configs_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(output_dir)
                    zf.write(file_path, arcname)
        print(f"ZIP包已生成: {zip_path} ({zip_path.stat().st_size / 1024:.1f} KB)")
    
    return exported

def main():
    import argparse
    parser = argparse.ArgumentParser(description="配置导出工具")
    parser.add_argument("--output", type=str, help="输出目录")
    parser.add_argument("--zip", action="store_true", help="生成ZIP包")
    args = parser.parse_args()
    
    result = export_configs(args.output, args.zip)
    
    print("\n导出完成:")
    print(f"  文件数: {len(result['files'])}")
    print(f"  目录数: {len(result['dirs'])}")
    print(f"  路径: {result['path']}")

if __name__ == "__main__":
    main()
