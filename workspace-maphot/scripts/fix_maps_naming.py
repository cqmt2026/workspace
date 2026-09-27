#!/usr/bin/env python3
"""
批量重命名 assets/maps 文件，使实际文件名匹配 index.html 的引用。
备份原文件到 backup_maps_original/，然后按引用列表重命名。
"""
import os, re, shutil
from pathlib import Path

ROOT = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video"
MAPS_DIR = os.path.join(ROOT, "assets", "maps")
BACKUP_DIR = os.path.join(ROOT, "assets", "maps_backup_original")
HTML_PATH = os.path.join(ROOT, "index.html")

# 读取 HTML 引用
html = open(HTML_PATH, encoding="utf-8").read()
refs = sorted(set(re.findall(r'assets/maps/([^\s"\'<>]+)', html)))
actual = set(os.listdir(MAPS_DIR))

# 找出缺失和多余
missing = [r for r in refs if r not in actual]
extra = [a for a in actual if a not in refs]

print(f"模板引用: {len(refs)} 个文件")
print(f"实际文件: {len(actual)} 个文件")
print(f"缺失: {len(missing)} 个 | 多余: {len(extra)} 个")

if not missing and not extra:
    print("✅ 已对齐，无需操作")
    exit(0)

# 创建备份
os.makedirs(BACKUP_DIR, exist_ok=True)
renamed = 0
for old_name in extra:
    src = os.path.join(MAPS_DIR, old_name)
    dst = os.path.join(BACKUP_DIR, old_name)
    shutil.copy2(src, dst)
    print(f"  备份: {old_name} → backup/")

# 按 refs 重建 assets/maps
# 策略：将 extra 中的文件重命名为 refs 中缺少的文件名
# 由于缺少的是带"广州_"前缀+_map_v3.png 后缀的，实际是 map_{区名}.png
# 建立映射规则
print()
print("执行重命名:")
for ref in refs:
    basename = ref  # e.g. "广州_天河区_map_v3.png"
    if basename not in actual:
        # 找实际文件中匹配的区名
        # 实际: map_天河区.png → 目标: 广州_天河区_map_v3.png
        match = re.search(r'map_(.+?)\.png', basename)
        if match:
            district = match.group(1)
            # 找实际文件
            candidates = [a for a in actual if f"map_{district}.png" in a]
            if candidates:
                src = os.path.join(MAPS_DIR, candidates[0])
                dst = os.path.join(MAPS_DIR, basename)
                shutil.move(src, dst)
                print(f"  ✅ {candidates[0]} → {basename}")
                renamed += 1
            else:
                print(f"  ❌ 找不到 map_{district}.png 的源文件")
        else:
            print(f"  ⚠️ 无法解析引用: {basename}")

print()
print(f"共重命名/对齐 {renamed} 个文件")
print("完成后请重新运行: hyperframes render --quality high --output city_广州_final.mp4")
