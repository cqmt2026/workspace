# -*- coding: utf-8 -*-
"""用yt-dlp提取抖音视频元数据和字幕"""
import subprocess, sys, json, os
sys.stdout.reconfigure(encoding='utf-8')

URL = "https://v.douyin.com/kRwdR8A70VA/"

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout, r.stderr

# 1) 获取所有元数据
print("="*70)
print("【获取视频元数据】")
print("="*70)
rc, out, err = run(['yt-dlp', '--skip-download', '--dump-json', '--no-warnings', URL])
if rc != 0:
    print("失败:", err[:3000])
else:
    try:
        data = json.loads(out)
        print("★ 标题:", data.get('title'))
        print("★ 作者:", data.get('uploader'), data.get('uploader_id'))
        print("★ 时长(秒):", data.get('duration'))
        print("★ 描述:")
        print(data.get('description', ''))
        print("\n★ 完整经度(可选字幕参数):")
        print("  upload_date:", data.get('upload_date'))
        print("  view_count:", data.get('view_count'))
    except Exception as e:
        print("JSON解析失败:", e)
        print("输出前3000:", out[:3000])

print("\n" + "="*70)
print("【尝试列出可用标题/字幕】")
print("="*70)
rc2, out2, err2 = run(['yt-dlp', '--skip-download', '--list-subs', '--no-warnings', URL])
print("rc:", rc2)
print("列出字幕输出:", (out2 or err2)[:3000])

# 3) 尝试直接输出字幕/标题
print("\n" + "="*70)
print("【尝试提取自动字幕/评论】")
print("="*70)
rc3, out3, err3 = run(['yt-dlp', '--skip-download', '--write-subs', '--sub-langs', 'all', '--sub-format', 'json3/srt/vtt', '--write-auto-subs', '--output', 'video_subs',  URL])
print("rc:", rc3)
print("stdout:", out3[:2000])
print("stderr:", err3[:2000])
for f in os.listdir('.'):
    if 'video_subs' in f:
        print("生成字幕文件:", f)
        try:
            print(open(f, encoding='utf-8').read()[:3000])
        except Exception as e:
            print("读取失败:", e)
