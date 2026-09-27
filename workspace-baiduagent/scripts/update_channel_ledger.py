# -*- coding: utf-8 -*-
"""更新多渠道台账 - 纳入所有行业的主管部门+行业协会"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

LEDGER_FILE = r'C:\Users\Administrator\.openclaw\workspace\workspace-baiduagent\data\multi_channel_ledger.json'

# 加载现有台账
with open(LEDGER_FILE, encoding='utf-8') as f:
    ledger = json.load(f)

# 补充所有行业的主管部门+行业协会
ledger['channels']['市场监管局'] = {
    "status": "❌未抓取",
    "description": "市市场监管局 - 检验检测/食品/广告/商贸/餐饮/药品许可",
    "coverage": {
        "covered_industries": ["检验检测","食品加工","广告传媒","商贸批发","酒店餐饮"],
        "row_count": 0,
        "note": "资质认定名单含电话，覆盖率高"
    }
}
ledger['channels']['经信委'] = {
    "status": "❌未抓取",
    "description": "市经信委 - 软件/智能制造/机械/新材料/电子/新能源 高新企业",
    "coverage": {
        "covered_industries": ["软件信息","智能制造","机械装备汽配","新材料化工","电子科技","新能源充电电力"],
        "row_count": 0,
        "note": "高新技术企业名单权威"
    }
}
ledger['channels']['药监局'] = {
    "status": "❌未抓取",
    "description": "市药监局 - 医疗器械生产/经营许可证",
    "coverage": {
        "covered_industries": ["医疗器械"],
        "row_count": 0,
        "note": "医疗器械电话仅50%，需补充"
    }
}
ledger['channels']['交通局'] = {
    "status": "❌未抓取",
    "description": "市交通局 - 道路运输经营许可/汽车维修备案",
    "coverage": {
        "covered_industries": ["物流货运","汽车服务"],
        "row_count": 0
    }
}
ledger['channels']['民政局'] = {
    "status": "❌未抓取",
    "description": "市民政局 - 托育机构备案",
    "coverage": {
        "covered_industries": ["母婴亲子"],
        "row_count": 0
    }
}
ledger['channels']['人社局'] = {
    "status": "❌未抓取",
    "description": "市人社局 - 人力资源服务许可",
    "coverage": {
        "covered_industries": ["人力资源"],
        "row_count": 0,
        "note": "覆盖率仅25%，需补充"
    }
}
ledger['channels']['生态环境局'] = {
    "status": "❌未抓取",
    "description": "市生态环境局 - 环保检测机构/排污许可",
    "coverage": {
        "covered_industries": ["环保检测","能源环保补充"],
        "row_count": 0
    }
}
ledger['channels']['发改委'] = {
    "status": "❌未抓取",
    "description": "市发改委 - 新能源/循环经济/节能项目",
    "coverage": {
        "covered_industries": ["新能源充电电力","能源环保补充"],
        "row_count": 0
    }
}
ledger['channels']['应急管理局'] = {
    "status": "❌未抓取",
    "description": "市应急局 - 化工安全许可",
    "coverage": {
        "covered_industries": ["新材料化工"],
        "row_count": 0
    }
}
ledger['channels']['统计局'] = {
    "status": "❌未抓取",
    "description": "市统计局 - 规模以上工业企业名录",
    "coverage": {
        "covered_industries": ["机械装备汽配","新材料化工","智能制造","电子科技"],
        "row_count": 0
    }
}
ledger['channels']['农业农村委'] = {
    "status": "⏳评估中",
    "description": "市农业农村委 - 动物诊疗许可证",
    "coverage": {
        "covered_industries": ["宠物医院"],
        "row_count": 0,
        "note": "各区格式碎片化，性价比低，待评估"
    }
}

# 补充行业协会渠道
ledger['channels']['重庆市口腔医学会'] = {
    "status": "❌未接入",
    "description": "行业协会 - 口腔医疗会员名单",
    "coverage": {"covered_industries": ["口腔诊所"], "row_count": 0}
}
ledger['channels']['重庆市建筑装饰协会'] = {
    "status": "❌未接入",
    "description": "行业协会 - 建筑装饰会员名单",
    "coverage": {"covered_industries": ["装修装饰","建筑建材"], "row_count": 0}
}
ledger['channels']['重庆软件行业协会'] = {
    "status": "❌未接入",
    "description": "行业协会 - 软件企业会员名单",
    "coverage": {"covered_industries": ["软件信息"], "row_count": 0}
}
ledger['channels']['重庆机械工业联合会'] = {
    "status": "❌未接入",
    "description": "行业协会 - 机械制造会员名单",
    "coverage": {"covered_industries": ["机械装备汽配"], "row_count": 0}
}
ledger['channels']['重庆医疗器械行业协会'] = {
    "status": "❌未接入",
    "description": "行业协会 - 医疗器械会员名单",
    "coverage": {"covered_industries": ["医疗器械"], "row_count": 0}
}
ledger['channels']['重庆环保产业协会'] = {
    "status": "❌未接入",
    "description": "行业协会 - 环保检测会员名单",
    "coverage": {"covered_industries": ["环保检测"], "row_count": 0}
}
ledger['channels']['重庆市口腔医学会'] = {
    "status": "❌未接入",
    "description": "行业协会 - 口腔医疗会员名单",
    "coverage": {"covered_industries": ["口腔诊所"], "row_count": 0}
}
ledger['channels']['重庆整形美容协会'] = {
    "status": "❌未接入",
    "description": "行业协会 - 医美会员名单",
    "coverage": {"covered_industries": ["医美机构"], "row_count": 0}
}
ledger['channels']['重庆市律师协会'] = {
    "status": "❌未接入",
    "description": "行业协会 - 律所会员名单",
    "coverage": {"covered_industries": ["法律服务"], "row_count": 0}
}
ledger['channels']['重庆市医院协会'] = {
    "status": "❌未接入",
    "description": "行业协会 - 医院会员名单",
    "coverage": {"covered_industries": ["医疗健康"], "row_count": 0}
}

with open(LEDGER_FILE, 'w', encoding='utf-8') as f:
    json.dump(ledger, f, ensure_ascii=False, indent=2)

print("✅ 台账已更新，新增11个主管部门+10个行业协会渠道")
print(f"当前渠道总数: {len(ledger['channels'])}个")
