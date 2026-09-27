#!/usr/bin/env python3
"""检查全景图引用和替代方案"""
import re, os, sys

root = r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video"
html = open(os.path.join(root, "index.html"), encoding="utf-8").read()

# Find all img src references
img_refs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', html)
map_refs = [r for r in img_refs if "maps" in r]
print("Images with maps/ path:")
for r in sorted(set(map_refs)):
    print(f"  {r}")

print()
print(f"Total image refs: {len(img_refs)}")
print(f"Total img tags: {html.count('<img')}")

# Check what 全景 references
idx = html.find("全景")
if idx >= 0:
    snippet = html[max(0, idx-300):idx+300]
    print(f"\nContext around 全景:")
    print(snippet)
else:
    print("\nNo '全景' found in HTML")

# Check for backup maps (original names)
maps_dir = os.path.join(root, "assets", "maps")
backup_dir = os.path.join(root, "assets", "maps_backup_original")
if os.path.exists(backup_dir):
    print(f"\nBackup files: {sorted(os.listdir(backup_dir))}")

# Check data/maps/20260825 for panorama
data_maps = os.path.join(root, "..", "data", "maps", "20260825")
if os.path.exists(data_maps):
    print(f"\nOriginal pipeline output: {sorted(os.listdir(data_maps))}")
