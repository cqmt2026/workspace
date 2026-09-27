# -*- coding: utf-8 -*-
with open(r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\scripts\gen_v3_video.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
out = []
for line in lines:
    if 'text_wrap' not in line:
        out.append(line)
with open(r'C:\Users\Administrator\.openclaw\workspace\workspace-maphot\scripts\gen_v3_video.py', 'w', encoding='utf-8') as f:
    f.writelines(out)
print(f"Removed text_wrap line. {len(out)} lines left.")