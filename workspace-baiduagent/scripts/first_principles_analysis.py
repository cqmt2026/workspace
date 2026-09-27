# 第一性原理分析：配额限制的真实原因

## 第一步：砸碎表象

**现象**：
- 高德 text: "USER_DAILY_QUERY_OVER_LIMIT"
- 高德 around: "INVALID_USER_KEY"
- 百度: "天配额超限，限制访问"
- 腾讯 place: "此key每日调用量已达到上限"
- 腾讯 geocoder: ✅ 可用

**真正的问题是什么？**
不是"配额不够用"，而是：
1. 为什么三个平台同时超限？
2. 为什么腾讯 geocoder 可用但 place 不可用？
3. 为什么高德 around 报 INVALID_USER_KEY（之前测试通过）？

## 第二步：倒空烂苹果

**物理定律（不可跨越）：**
- API配额是按Key计算的，不是按接口计算的
- 个人开发者有固定日配额上限
- 超限后所有使用该Key的接口都会被限制

**人为规定（可以打破的）：**
- "腾讯每天5,000次" — 这是我从FAQ推断的，需要验证
- "高德30万次" — 同样需要验证实际额度
- "腾讯 geocoder 不受限制" — 需要验证

## 第三步：重拼乐高 — 从原点推导

**真正能回答问题的数据：**
1. 控制台实际显示的配额数字是多少？
2. 今天到底调用了多少次？
3. 腾讯 geocoder 真的不受限制吗？
4. 高德 around 为什么从"可用"变成"INVALID_USER_KEY"？

**最可能的真实原因：**
- 多个Key可能共用同一个账户配额
- 或者腾讯 geocoder 是独立配额
- 或者高德 around 接口的Key配置有问题（INVALID_USER_KEY = Key无效，不是配额问题）

## 第四步：找裂缝

**行业现实 vs 理论最优：**
- 理论：三个平台总配额 = 30万+5万+0.5万 = 35.5万次/天
- 现实：今天大量调用后全部超限
- 裂缝：我们实际用了多少？是否真的用完了配额？

**待验证假设：**
1. 腾讯 geocoder 是否有独立配额？
2. 高德 around 的 INVALID_USER_KEY 是Key问题还是配额问题？
3. 百度是否真的超限还是Key配置问题？
4. 三个平台的配额是否是独立计算还是共享？
"""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

GD_KEY = '3f85cf…bd51'
TX_KEY = 'JGGBZ-D5I6Q-66H5K-22SMU-I5VXO-NDFLJ'
BD_KEY = 'KKcT6s…i2C0'

print("=" * 60)
print("【假设验证】重新测试所有API")
print("=" * 60)

# 测试1: 腾讯geocoder是否真的可用
print("\n1. 腾讯 geocoder (连续10次测试)")
for i in range(10):
    r = requests.get('https://apis.map.qq.com/ws/geocoder/v1',
        params={'key': TX_KEY, 'address': f'重庆市测试{i}号'}, timeout=5)
    d = r.json()
    if d.get('status') != 0:
        print(f"   第{i+1}次: ❌ {d.get('message')}")
        break
    if i == 9:
        print("   10次全部成功 ✅ geocoder配额充足")

# 测试2: 腾讯place是否真的超限
print("\n2. 腾讯 place/search (测试1次)")
r = requests.get('https://apis.map.qq.com/ws/place/v1/search',
    params={'key': TX_KEY, 'boundary': 'region(重庆,0)', 'keyword': '口腔', 'max_per_page': 3}, timeout=5)
d = r.json()
print(f"   status={d.get('status')}, msg={d.get('message','')}")

# 测试3: 高德around为什么报INVALID_USER_KEY
print("\n3. 高德 around (测试1次)")
r = requests.get('https://restapi.amap.com/v3/place/around',
    params={'keywords': '口腔', 'location': '106.55,29.56', 'radius': 5000, 'offset': 5, 'page': 1, 'key': GD_KEY}, timeout=5)
d = r.json()
print(f"   status={d.get('status')}, info={d.get('info')}")
print(f"   → 如果是INVALID_USER_KEY，说明Key本身有问题，不是配额问题")

# 测试4: 高德text的配额状态
print("\n4. 高德 text (测试1次)")
r = requests.get('https://restapi.amap.com/v3/place/text',
    params={'keywords': '口腔', 'city': '重庆', 'offset': 5, 'page': 1, 'key': GD_KEY}, timeout=5)
d = r.json()
print(f"   status={d.get('status')}, info={d.get('info')}")
print(f"   → 区分'配额超限'和'Key无效'")

# 测试5: 百度配额
print("\n5. 百度 place/v2/search (测试1次)")
r = requests.get('https://api.map.baidu.com/place/v2/search',
    params={'query': '口腔', 'region': '重庆', 'output': 'json', 'ak': BD_KEY, 'page_size': 3, 'scope': 2}, timeout=5)
d = r.json()
print(f"   status={d.get('status')}, msg={d.get('message','')}")

print("\n" + "=" * 60)
print("【关键问题】")
print("=" * 60)
print("1. 腾讯 geocoder 是否真的无限制？")
print("2. 高德 around 的 INVALID_USER_KEY 是Key问题还是配额问题？")
print("3. 三个平台的配额是否是独立计算？")
print("4. 今天实际调用了多少次？")
