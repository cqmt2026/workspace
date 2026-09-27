"""检查高德API配额状态"""
import urllib.parse, urllib.request, json, os, sys

sys.stdout.reconfigure(encoding='utf-8')

LEDGER_PATH = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\multi_channel_ledger.json'

def get_amap_key():
    key = os.environ.get('GD_MAP_KEY', '')
    if not key:
        try:
            with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            key = data.get('channels', {}).get('高德POI', {}).get('key_source', '').replace('完整32位Key: ', '')
        except:
            pass
    return key

key = get_amap_key()
print(f"Key: {key[:8]}...{key[-4:]} (len={len(key)})")

# 用简单搜索测试配额
kw = urllib.parse.quote("口腔诊所 重庆")
url = f"https://restapi.amap.com/v3/place/text?key={key}&keywords={kw}&city=500000&offset=1&pageSize=5&output=json"

try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    print(f"status={data.get('status')}, info={data.get('info')}")
    print(f"pois={len(data.get('pois', []))}")
    if data.get('pois'):
        for poi in data['pois'][:3]:
            print(f"  {poi.get('name')} | {poi.get('tel')}")
except Exception as e:
    print(f"Error: {e}")
