# -*- coding: utf-8 -*-
"""填充行业数据卡 (industry_cards)"""
import sqlite3, sys, json
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/baidu_crm.db')
c = conn.cursor()

# 数据来源说明：
# - search_volume: 基于行业常识的重庆本地月度搜索量级估算（标注"估算"）
# - competitor_count: 来自CRM客户池实际数量（可信数据）
# - avg_cpc: 行业平均点击价格估算（标注"估算"）
# - key_words: 高价值关键词（来自知识库）
# - tip: 拨打切入提示（来自知识库话术）

cards = [
    {
        "industry": "口腔诊所",
        "search_volume": "重庆'整牙/补牙/XX区口腔'月搜约5-8万次(估算)",
        "competitor_count": "1,953家(本地实际)",
        "avg_cpc": "区域词约5-15元(估算)",
        "key_words": "XX区整牙,XX区补牙,XX区口腔,牙齿矫正,种植牙",
        "tip": "高客单(矫正上万)。破冰:患者搜'XX区整牙'先看到谁?区域词蓝海,大词被连锁占。医疗广告需资质,不承诺效果。"
    },
    {
        "industry": "医美机构",
        "search_volume": "重庆'医美/XX区双眼皮/整形'月搜约4-7万次(估算)",
        "competitor_count": "467家(本地实际)",
        "avg_cpc": "区域词约8-20元(估算)",
        "key_words": "XX区双眼皮,医美,整形,皮肤管理,光子嫩肤",
        "tip": "高客单(几千到几万)。求美者决策前深度搜索比价。破冰:'XX区XX'能搜到你吗?医疗广告审核严,合规话术。"
    },
    {
        "industry": "教培机构",
        "search_volume": "重庆'XX区XX培训/辅导'月搜约6-10万次(估算)",
        "competitor_count": "1,165家(本地实际)",
        "avg_cpc": "区域词约4-12元(估算)",
        "key_words": "XX区数学辅导,XX区英语培训,XX区艺术班,奥数,留学",
        "tip": "招生驱动,决策人校长/创始人。旺季(开学/寒暑假)搜索暴涨。破冰:'家长搜XX区XX培训,你在吗?'区域词蓝海。"
    },
    {
        "industry": "装修装饰",
        "search_volume": "重庆'XX区装修公司/装修'月搜约6-9万次(估算)",
        "competitor_count": "1,417家(本地实际)",
        "avg_cpc": "区域词约6-18元(估算)",
        "key_words": "XX区装修公司,装修报价,全屋定制,半包,整装",
        "tip": "高客单(几万到几十万)。业主搜'XX区装修公司'比价。破冰:'你想装修的业主搜'XX区装修'看到你吗?'可配爱采购做B2B。"
    },
    {
        "industry": "宠物医院",
        "search_volume": "重庆'宠物医院/XX区宠物'月搜约2-4万次(估算)",
        "competitor_count": "636家(本地实际)",
        "avg_cpc": "区域词约4-10元(估算)",
        "key_words": "XX区宠物医院,宠物看病,宠物洗澡,宠物疫苗,宠物美容",
        "tip": "宠物主找附近兽医,决策快。破冰:'附近宠物主搜'XX区宠物医院'能预约到你吗?'可配地图推广。"
    },
    {
        "industry": "母婴亲子",
        "search_volume": "重庆'XX区母婴/儿童摄影/早教'月搜约3-5万次(估算)",
        "competitor_count": "928家(本地实际)",
        "avg_cpc": "区域词约3-8元(估算)",
        "key_words": "XX区母婴,儿童摄影,早教,亲子游乐,宝宝游泳",
        "tip": "到店消费,妈妈决策。破冰:'宝妈搜'XX区儿童X'能找到你吗?'可配信息流+地图。"
    },
]

# 清空重填
c.execute("DELETE FROM industry_cards")

for card in cards:
    c.execute('''INSERT INTO industry_cards 
                (industry, search_volume, competitor_count, avg_cpc, key_words, tip)
                VALUES (?, ?, ?, ?, ?, ?)''',
             (card["industry"], card["search_volume"], card["competitor_count"],
              card["avg_cpc"], card["key_words"], card["tip"]))

conn.commit()

# 验证
c.execute("SELECT industry, search_volume, competitor_count, avg_cpc FROM industry_cards")
print("✅ 行业数据卡已填充:")
for r in c.fetchall():
    print(f"\n  【{r[0]}】")
    print(f"    搜索量: {r[1]}")
    print(f"    竞品数: {r[2]}")
    print(f"    平均CPC: {r[3]}")

conn.close()