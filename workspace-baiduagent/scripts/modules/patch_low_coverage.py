#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高德POI补抓脚本 - 针对低覆盖率行业
利用高德地图API获取含电话的POI数据
"""
import sys
import os
import time
import csv
import sqlite3
import requests

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 高德API Key - 从环境变量读取，如果未设置则使用备用Key
AMAP_KEY = os.environ.get('GD_MAP_KEY', 'KKcT6s4u9G9I7Mh6werQqypfiXiPi2C0')
BASE_URL = 'https://restapi.amap.com/v3/place/text'
DB_PATH = 'data/baidu_crm.db'
MASTER_DIR = 'data/master'
SOURCE_DIR = 'data/source'

# 重庆主城区9区adcode
DISTRICTS = {
    '渝中区': '500103',
    '江北区': '500105',
    '南岸区': '500108',
    '九龙坡区': '500107',
    '沙坪坝区': '500106',
    '北碚区': '500109',
    '大渡口区': '500104',
    '巴南区': '500113',
    '高新区': '500372',  # 重庆高新区临时adcode
}

# 低覆盖率行业补抓配置
PATCH_INDUSTRIES = [
    {
        'name': '人力资源',
        'keywords': ['人力资源公司', '劳务派遣', '猎头公司', '人才市场', '人事代理', '招聘服务'],
        'target_count': 300,
        'priority': 1,
    },
    {
        'name': '检验检测',
        'keywords': ['检测公司', '质检机构', '质量检测', '环境检测', '第三方检测', '食品检测'],
        'target_count': 200,
        'priority': 1,
    },
    {
        'name': '物流货运',
        'keywords': ['物流公司', '货运公司', '物流园', '仓储物流', '快递服务', '运输公司'],
        'target_count': 300,
        'priority': 1,
    },
    {
        'name': '软件信息',
        'keywords': ['软件公司', '软件开发', 'IT服务', '信息系统', '网络科技', '信息技术'],
        'target_count': 200,
        'priority': 1,
    },
    {
        'name': '智能制造',
        'keywords': ['智能装备', '工业机器人', '自动化设备', '智能科技', '智能制造'],
        'target_count': 150,
        'priority': 1,
    },
    {
        'name': '能源环保补充',
        'keywords': ['环保公司', '环保科技', '环境工程', '水处理', '废气处理', '节能科技'],
        'target_count': 150,
        'priority': 1,
    },
    {
        'name': '食品加工',
        'keywords': ['食品公司', '食品加工', '食品科技', '饮料制造', '糕点制造', '调味品'],
        'target_count': 150,
        'priority': 2,
    },
    {
        'name': '电子科技',
        'keywords': ['电子科技', '电子产品', '电子元器件', '电子器件', '电子设备'],
        'target_count': 100,
        'priority': 2,
    },
]


def check_amap_quota():
    """测试高德API配额状态"""
    try:
        params = {
            'key': AMAP_KEY,
            'keywords': '测试',
            'city': '重庆',
            'citylimit': 'true',
            'offset': 1,
            'page': 1,
            'output': 'JSON',
        }
        r = requests.get(BASE_URL, params=params, timeout=10)
        d = r.json()
        if d.get('status') == '1':
            return True, "可用"
        elif d.get('status') == '0':
            err = d.get('info', '')
            if 'quota' in err.lower() or 'limit' in err.lower() or ' exceed' in err:
                return False, f"配额限制: {err}"
            return False, f"错误: {err}"
        else:
            return False, f"未知状态: {d.get('info', 'unknown')}"
    except Exception as e:
        return False, f"请求异常: {e}"


def fetch_industry_amap(industry_cfg):
    """用高德POI抓取一个行业"""
    name = industry_cfg['name']
    keywords = industry_cfg['keywords']
    target = industry_cfg['target_count']
    
    print(f"\n{'='*60}")
    print(f"抓取行业: {name} (目标>={target}条)")
    print(f"{'='*60}")
    
    all_items = []
    seen_names = set()
    quota_limited = False
    
    # 遍历每个行政区
    for district, adcode in DISTRICTS.items():
        if quota_limited:
            break
            
        for kw in keywords:
            if quota_limited:
                break
            if len(all_items) >= target:
                break
                
            print(f"  [{district}] 关键词: {kw}")
            
            page = 1
            while True:
                params = {
                    'key': AMAP_KEY,
                    'keywords': kw,
                    'city': adcode,
                    'citylimit': 'true',
                    'offset': 20,
                    'page': page,
                    'output': 'JSON',
                }
                try:
                    r = requests.get(BASE_URL, params=params, timeout=15)
                    d = r.json()
                    
                    if d.get('status') != '1':
                        info = d.get('info', '')
                        print(f"    错误: {info}")
                        if 'quota' in info.lower() or 'limit' in info.lower() or 'exceed' in info:
                            quota_limited = True
                        break
                    
                    pois = d.get('pois', [])
                    if not pois:
                        break
                    
                    new_count = 0
                    for poi in pois:
                        # 解析地址
                        addr = poi.get('address', '')
                        # 提取区域名
                        area = district
                        for dname in DISTRICTS.keys():
                            if dname in addr:
                                area = dname
                                break
                        
                        title = poi.get('name', '').strip()
                        if not title or title in seen_names:
                            continue
                        
                        # 检查是否在主城区
                        in_main = any(d in area for d in DISTRICTS.keys())
                        if not in_main:
                            continue
                        
                        seen_names.add(title)
                        
                        tel = poi.get('tel', '')
                        # 清理电话号码
                        if tel:
                            tel = ''.join(c for c in tel if c.isdigit())
                            if len(tel) < 7:
                                tel = ''
                        
                        all_items.append({
                            '区域': area,
                            '机构名称': title,
                            '地址': addr,
                            '电话': tel,
                            '机构类别': name,
                            '经度': poi.get('location', '').split(',')[0] if poi.get('location') else '',
                            '纬度': poi.get('location', '').split(',')[1] if poi.get('location') else '',
                            '数据来源': '高德POI',
                            '抓取时间': time.strftime('%Y-%m-%d %H:%M'),
                        })
                        new_count += 1
                    
                    print(f"    第{page}页: +{new_count}条 (累计{len(all_items)}条)")
                    time.sleep(0.1)
                    page += 1
                    
                    if new_count == 0:
                        break
                        
                except Exception as e:
                    print(f"    异常: {e}")
                    time.sleep(1)
                    break
    
    print(f"\n[{name}] 抓取完成: 总计{len(all_items)}条, 有电话{sum(1 for i in all_items if i['电话'])}条")
    return all_items, quota_limited


def import_to_crm(items, source_tag):
    """导入到CRM"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    inserted = 0
    skipped = 0
    for row in items:
        name = row['机构名称'].strip()
        cur.execute("SELECT id FROM customers WHERE name = ?", (name,))
        if cur.fetchone():
            skipped += 1
            continue
        cur.execute("""
            INSERT INTO customers (name, industry, phone, address, district, lat, lng, source, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
        """, (
            row['机构名称'], row['机构类别'], row['电话'], row['地址'], row['区域'],
            row['纬度'], row['经度'], source_tag, '待联系'
        ))
        inserted += cur.rowcount
    
    conn.commit()
    conn.close()
    return inserted, skipped


def main():
    print("="*60)
    print("【高德POI补抓低覆盖率行业】")
    print("="*60)
    
    # 检查配额
    print("\n检查高德API配额状态...")
    ok, msg = check_amap_quota()
    if not ok:
        print(f"❌ 配额检查失败: {msg}")
        print("请等待配额恢复后重试")
        return
    print(f"✅ 配额状态: {msg}")
    
    all_inserted = 0
    all_skipped = 0
    quota_limited = False
    
    for idx, ind_cfg in enumerate(PATCH_INDUSTRIES, 1):
        if quota_limited:
            print(f"\n⚠️ 配额受限，停止后续抓取")
            break
        
        print(f"\n▶ 第{idx}/{len(PATCH_INDUSTRIES)}个: {ind_cfg['name']} (优先级{ind_cfg['priority']})")
        
        items, quota_limited = fetch_industry_amap(ind_cfg)
        
        if not items:
            print(f"  ⚠️ 无新数据")
            continue
        
        # 保存到master
        out_path = os.path.join(MASTER_DIR, f"{ind_cfg['name']}_amap_patch.csv")
        fieldnames = ['区域','机构名称','地址','电话','机构类别','经度','纬度','数据来源','抓取时间']
        with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)
        print(f"  已保存: {out_path}")
        
        # 导入CRM
        inserted, skipped = import_to_crm(items, f"高德POI补抓-{ind_cfg['name']}")
        all_inserted += inserted
        all_skipped += skipped
        
        phones = sum(1 for i in items if i['电话'])
        print(f"  导入CRM: +{inserted}条(有电话{phones}条), 跳过{skipped}条")
        
        time.sleep(0.5)
    
    # 验证结果
    print(f"\n{'='*60}")
    print(f"【补抓完成汇总】")
    print(f"{'='*60}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM customers')
    total = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM customers WHERE phone IS NOT NULL AND phone != ""')
    has_phone = cur.fetchone()[0]
    conn.close()
    
    print(f"CRM总客户: {total:,}")
    print(f"有电话: {has_phone:,} ({round(has_phone/total*100,1)}%)")
    print(f"本次新增: +{all_inserted}条, 跳过{all_skipped}条")


if __name__ == '__main__':
    main()
