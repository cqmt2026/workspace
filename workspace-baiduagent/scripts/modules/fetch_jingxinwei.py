# -*- coding: utf-8 -*-
"""下载经信委2025创新型中小企业名单Excel"""
import requests, os, sys
sys.stdout.reconfigure(encoding='utf-8')

os.makedirs(r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source\jingxinwei', exist_ok=True)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# 2025创新型中小企业申报通过名单
urls = {
    '2025_创新型_申报通过.xlsx': 'https://jjxxw.cq.gov.cn/zwgk_213/zcwj/qtwj/202508/W020250821669427347685.xlsx',
    '2025_创新型_复核通过.xlsx': 'https://jjxxw.cq.gov.cn/zwgk_213/zcwj/qtwj/202508/W020250821669428014459.xlsx',
    '2025_创新型_通知.doc': 'https://jjxxw.cq.gov.cn/zwgk_213/zcwj/qtwj/202508/W020250821669428991471.doc',
}

base = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\source\jingxinwei'
for fname, url in urls.items():
    try:
        r = requests.get(url, timeout=60, headers=headers)
        print(f"{fname}: status={r.status_code}, size={len(r.content)}")
        if r.status_code == 200 and len(r.content) > 100:
            with open(os.path.join(base, fname), 'wb') as f:
                f.write(r.content)
            print(f"  ✅ 已保存: {os.path.join(base, fname)}")
        else:
            print(f"  ❌ 下载失败或为空")
    except Exception as e:
        print(f"{fname}: 错误 {e}")
