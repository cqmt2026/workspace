#!/usr/bin/env python3
"""检查scene2的img标签"""
import re

with open(r"C:\Users\Administrator\.openclaw\workspace\workspace-maphot\my-video\index.html", encoding="utf-8") as f:
    html = f.read()

# Find scene2 content
scene2_match = re.search(r'<div id="scene2"[^>]*>(.*?)</div>\s*<div id="scene3"', html, re.DOTALL)
if scene2_match:
    scene2 = scene2_match.group(1)
    # Find all img tags in scene2
    imgs = re.findall(r'<img[^>]+>', scene2)
    print(f"Scene2 img tags: {len(imgs)}")
    for img in imgs:
        print(f"  {img[:200]}")
    # Also check for CSS background images
    bg_imgs = re.findall(r'url\(["\']?([^"\')]+)\.png["\']?\)', scene2)
    print(f"\nCSS bg images in scene2: {bg_imgs}")
else:
    print("scene2 not found")

# Check the full HTML for all scene img references
all_img_refs = re.findall(r'src="assets/maps/([^"]+)"', html)
print(f"\nAll map refs in HTML: {len(all_img_refs)}")
for ref in all_img_refs:
    print(f"  {ref}")

# Check for inline style with background-image
bg_style_refs = re.findall(r'background-image:\s*url\([^)]+\)', html)
print(f"\nBackground image styles: {len(bg_style_refs)}")
for ref in bg_style_refs[:5]:
    print(f"  {ref}")
