import os
import glob

os.chdir(r"C:\Users\Administrator\.openclaw\workspace\workspace-novel\项目一：鉴城师\L4-shared\正文")

# Find all chapter files
pattern = "*.md"
md_files = glob.glob(pattern)

# Get file info with mtime
file_info = []
for f in md_files:
    stat = os.stat(f)
    file_info.append((f, stat.st_mtime, stat.st_size))

# Sort by mtime descending
file_info.sort(key=lambda x: x[1], reverse=True)

latest = file_info[0][0]
print(f"Latest: {latest}")

# Read first 500 chars to verify
with open(latest, 'r', encoding='utf-8') as fp:
    content = fp.read()
    print(f"Size: {len(content)} chars")
    print("Preview:", content[:300])
