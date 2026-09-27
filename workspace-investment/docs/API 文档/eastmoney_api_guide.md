# 东方财富 API 使用指南

**更新时间**: 2026-04-07  
**状态**: 已验证可用

---

## 🔐 认证配置

### 【Cookie 获取】

1. 登录东方财富网：https://www.eastmoney.com/
2. F12 打开开发者工具
3. Network 标签 → 刷新页面
4. 复制请求头中的 Cookie
5. 保存到 `config/eastmoney_cookie.json`

### 【Cookie 配置】

```json
{
  "cookie": "EM_UserID=xxx; EM_LoginToken=xxx; ...",
  "update_time": "2026-04-07 12:22:00",
  "status": "active"
}
```

**有效期**: 7-30 天  
**更新**: Cookie 过期后重新获取

---

## 📊 API 接口汇总

### 【1. 大盘指数】

**接口**:
```
GET http://push2.eastmoney.com/api/qt/stock/get
```

**参数**:
```python
params = {
    'secid': '1.000001',  # 上证指数
    'fields': 'f43,f168,f169,f170,f171'  # 当前价/开盘/最高/最低/成交量
}
```

**代码示例**:
```python
from pathlib import Path
import requests
import json

# 加载 Cookie
cookie_file = Path('config/eastmoney_cookie.json')
with open(cookie_file) as f:
    cookie = json.load(f)['cookie']

session = requests.Session()
session.headers.update({'Cookie': cookie})

# 获取上证指数
url = 'http://push2.eastmoney.com/api/qt/stock/get'
params = {'secid': '1.000001', 'fields': 'f43'}
resp = session.get(url, params=params)
data = resp.json()

price = data['data']['f43'] / 100  # 转换为元
print(f'上证指数：{price}点')
```

---

### 【2. 个股行情】

**接口**:
```
GET http://push2.eastmoney.com/api/qt/stock/get
```

**参数**:
```python
params = {
    'secid': '1.600519',  # 贵州茅台
    'fields': 'f43,f44,f45,f46,f47,f168'  # 当前价/涨跌/成交量等
}
```

**secid 格式**:
- `1.600519` - 沪市股票
- `0.000001` - 深市股票

**返回字段**:
- `f43`: 当前价 (分)
- `f44`: 涨跌额 (分)
- `f45`: 涨跌幅 (%)
- `f46`: 最高价 (分)
- `f47`: 最低价 (分)
- `f168`: 成交量 (手)

---

### 【3. 板块数据】

**接口**:
```
GET http://push2.eastmoney.com/api/qt/clist/get
```

**参数**:
```python
params = {
    'pn': '1',  # 页码
    'pz': '50',  # 每页数量
    'fs': 'm:90 t:3',  # m:90 t:3=概念板块
    'fields': 'f12,f14,f3,f104,f105'  # 代码/名称/涨幅/涨跌家数
}
```

**板块类型**:
- `m:90 t:3` - 概念板块
- `m:90 t:2` - 行业板块
- `m:90 t:1` - 地域板块

---

### 【4. 资金流向】

**接口**:
```
GET http://push2.eastmoney.com/api/qt/stock/get
```

**参数**:
```python
params = {
    'secid': '1.600519',
    'fields': 'f113,f114,f115'  # 主力净流入/超大单/大单
}
```

**返回字段**:
- `f113`: 主力净流入 (分)
- `f114`: 超大单净流入 (分)
- `f115`: 大单净流入 (分)

---

## 📁 已实现脚本

| 脚本 | 功能 | 位置 |
|------|------|------|
| `tencent_realtime.py` | 腾讯实时数据 | `src/data_fetchers/` |
| `eastmoney_capabilities.py` | 能力测试 | `src/data_fetchers/` |
| `fetch_kline_v2.py` | K 线数据 (腾讯) | `src/data_fetchers/` |
| `fetch_north_flow_v2.py` | 北向资金 | `src/data_fetchers/` |
| `fetch_top_list.py` | 龙虎榜 | `src/data_fetchers/` |

---

## ⚠️ 注意事项

### 【1. 频率限制】
- 单个 IP 每秒不超过 5 次请求
- 建议添加延时：`time.sleep(0.5)`

### 【2. 数据单位】
- 价格：分 (需要 /100 转换)
- 金额：分 (需要 /10000 转换为亿)
- 数量：手

### 【3. 错误处理】
```python
try:
    resp = session.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get('data'):
        # 处理数据
        pass
except requests.exceptions.Timeout:
    print('请求超时')
except requests.exceptions.RequestException as e:
    print(f'请求失败：{e}')
```

---

## 🔍 调试技巧

### 【1. 查看原始响应】
```python
resp = session.get(url, params=params)
print(resp.text)  # 查看原始 JSON
```

### 【2. 格式化输出】
```python
import json
print(json.dumps(data, indent=2, ensure_ascii=False))
```

### 【3. 保存测试数据】
```python
with open('test_response.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

---

## 📊 数据源对比

| 数据源 | 优势 | 劣势 | 推荐用途 |
|--------|------|------|---------|
| **东财 (Cookie)** | 数据全面 | 需要 Cookie | 主力数据源 |
| **腾讯财经** | 稳定简单 | 字段较少 | 备用数据源 |
| **新浪财经** | - | HTTP 403 | 不推荐 |
| **AkShare** | - | 网络问题 | 不推荐 |

---

## 🎯 最佳实践

### 【1. 双数据源】
```python
# 优先使用东财
try:
    data = fetch_from_eastmoney(code)
except:
    # 降级到腾讯
    data = fetch_from_tencent(code)
```

### 【2. 缓存数据】
```python
# 避免重复请求
if cache.exists() and cache.is_valid():
    data = cache.load()
else:
    data = fetch_from_api()
    cache.save(data)
```

### 【3. 批量获取】
```python
# 一次获取多只股票
codes = ['600519', '000001', '300750']
for code in codes:
    fetch_stock(code)
    time.sleep(0.5)  # 避免限流
```

---

_API 指南版本：V1.0 (2026-04-07)_
