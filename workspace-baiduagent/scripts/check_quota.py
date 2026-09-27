# -*- coding: utf-8 -*-
import sys, requests
sys.stdout.reconfigure(encoding='utf-8')

print("=== 高德配额实测 ===")
GD_KEY = '3f85cf…bd51'
try:
    r = requests.get('https://restapi.amap.com/v3/place/text',
        params={'keywords':'口腔','city':'重庆','offset':1,'page':1,'key':GD_KEY}, timeout=10)
    d = r.json()
    print(f"  状态: status={d.get('status')}, info={d.get('info')}")
except Exception as e:
    print(f"  错误: {e}")

print("\n=== 百度配额实测 ===")
BD_KEY = 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0'
# 测试地点检索2.0
for api in ['https://api.map.baidu.com/place/v2/search', 'https://api.map.baidu.com/place/v3/region']:
    try:
        params = {'query':'机械设备','region':'重庆','output':'json','ak':BD_KEY,'page_size':1,'page_num':0,'scope':2}
        if 'region' in api:
            params = {'query':'机械设备','region':'重庆','ak':BD_KEY,'scope':2}
        r = requests.get(api, params=params, timeout=10)
        d = r.json()
        print(f"  {api.split('/place/')[-1]}: status={d.get('status')}, msg={d.get('message','')}, total={d.get('total')}")
    except Exception as e:
        print(f"  {api}: 错误 {e}")