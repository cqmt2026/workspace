# -*- coding: utf-8 -*-
"""下载并解析沙坪坝教培白名单PDF"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
import requests

pdf_url = 'https://www.cqspb.gov.cn/bm/qjw/jczwgk/ywjy/jygk/XWPXJG/202509/W020250918614436313373.pdf'
save_path = 'data/source/weijkw/jp_list_chongqing_weijkw_20260829_shapingba.pdf'
os.makedirs(os.path.dirname(save_path), exist_ok=True)

r = requests.get(pdf_url, timeout=30, headers={'User-Agent':'Mozilla/5.0'})
print('status:', r.status_code)
print('content-type:', r.headers.get('Content-Type'))
print('size:', len(r.content))
if r.status_code == 200 and len(r.content) > 1000:
    with open(save_path, 'wb') as f:
        f.write(r.content)
    print('已保存:', save_path, '大小:', len(r.content))
else:
    print('下载失败')