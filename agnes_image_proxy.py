#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proxy for agnes-image generation
Usage: python agnes_image_proxy.py "prompt" [model] [output_dir]
"""
import json, urllib.request, urllib.error, ssl, sys, os, time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ctx = ssl.create_default_context()

BASE = "https://apihub.agnes-ai.com/v1"
KEY = "sk-Q8CQhUsRI2CqYT16qEIi8wK603Vup1YarFCdcjghTHiHbkJf"

model = sys.argv[2] if len(sys.argv) > 2 else "agnes-image-2.1-flash"
output_dir = sys.argv[3] if len(sys.argv) > 3 else "."
prompt = sys.argv[1]

url = "%s/images/generations" % BASE
payload = json.dumps({
    "model": model,
    "prompt": prompt,
    "n": 1,
    "size": "1024x1024"
}).encode("utf-8")
req = urllib.request.Request(url, data=payload, headers={
    "Content-Type": "application/json",
    "Authorization": "Bearer " + KEY
}, method="POST")

try:
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        body = resp.read().decode("utf-8")
        data = json.loads(body)
        if "data" in data and len(data["data"]) > 0:
            img_url = data["data"][0].get("url", "")
            # Download the image
            img_req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(img_req, timeout=30, context=ctx) as img_resp:
                img_data = img_resp.read()
                ext = "png" if "png" in img_url else "jpg"
                fname = "%s/img_%d.%s" % (output_dir, int(time.time()), ext)
                with open(fname, "wb") as f:
                    f.write(img_data)
                print("OK: %s" % fname)
                print("URL: %s" % img_url)
        else:
            print("ERROR: no image data: %s" % body[:200])
except urllib.error.HTTPError as e:
    print("HTTP %d: %s" % (e.code, e.read().decode("utf-8", errors="replace")[:200]))
except Exception as e:
    print("ERROR: %s: %s" % (type(e).__name__, str(e)))
