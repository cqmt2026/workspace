#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proxy for agnes-video generation
Usage: python agnes_video_proxy.py "prompt" [duration] [output_dir]
"""
import json, urllib.request, urllib.error, ssl, sys, os, time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ctx = ssl.create_default_context()

BASE = "https://apihub.agnes-ai.com/v1"
KEY = "sk-Q8CQhUsRI2CqYT16qEIi8wK603Vup1YarFCdcjghTHiHbkJf"

model = "agnes-video-v2.0"
duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5
output_dir = sys.argv[3] if len(sys.argv) > 3 else "."
prompt = sys.argv[1]

url = "%s/videos" % BASE
payload = json.dumps({
    "model": model,
    "prompt": prompt,
    "duration": duration
}).encode("utf-8")
req = urllib.request.Request(url, data=payload, headers={
    "Content-Type": "application/json",
    "Authorization": "Bearer " + KEY
}, method="POST")

try:
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        body = resp.read().decode("utf-8")
        data = json.loads(body)
        print("OK: %s" % body)
        print("task_id: %s" % data.get("task_id", ""))
        print("video_id: %s" % data.get("video_id", ""))
        print("status: %s" % data.get("status", ""))
except urllib.error.HTTPError as e:
    print("HTTP %d: %s" % (e.code, e.read().decode("utf-8", errors="replace")[:200]))
except Exception as e:
    print("ERROR: %s: %s" % (type(e).__name__, str(e)))
