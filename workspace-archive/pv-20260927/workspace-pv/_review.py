"""Review current template and identify issues"""
import os, sqlite3

print("=== TEMPLATE ISSUES ===")
html_path = 'workspace-pv/data/videos/html/PV_HYPER_V1_TEST.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()
print(f"HTML size: {len(html)} bytes")
print()

issues = [
    ("GSAP infinite repeat", "repeat: -1 causes errors, need finite count"),
    ("Scene visibility kill", "Missing visibility:hidden hard kill after scene transitions"),
    (".point opacity noop", "CSS opacity:0 + gsap.from opacity:0 = no animation"),
    ("Font declaration", "PingFang SC / Microsoft YaHei not declared, fallback to generic"),
    ("Audio missing", "Removed audio tag for testing, need edge-tts integration"),
    ("No subtitles", "Text-only video, no captions for mute viewing"),
    ("Background quality", "Only 4 generic background images, need real solar photos"),
    ("No data visualization", "Static numbers, no animated charts/graphs"),
    ("Content hardcoded", "Scene 3 has fixed points, not dynamic from script"),
]
for title, desc in issues:
    print(f"  [{title}] {desc}")

print()
print("=== DB DATA CHECK ===")
db = sqlite3.connect('workspace-pv/data/pv.db')
c = db.cursor()
c.execute('PRAGMA table_info(content_items)')
cols = [r[1] for r in c.fetchall()]
print(f"Columns: {cols}")
c.execute('SELECT * FROM content_items WHERE status="published" ORDER BY created_at DESC LIMIT 3')
for row in c.fetchall():
    for i, col in enumerate(cols):
        val = str(row[i])[:40] if row[i] else 'None'
        print(f"  {col}: {val}")
    print()
db.close()

print("=== ASSET CHECK ===")
base = 'workspace-pv/data/assets'
for d in ['photos', '']:
    p = os.path.join(base, d)
    if os.path.isdir(p):
        files = os.listdir(p)
        print(f"  {d or '(root)'}: {len(files)} items")
        for f in sorted(files):
            sz = os.path.getsize(os.path.join(p, f))
            print(f"    {f} ({sz//1024}KB)")
