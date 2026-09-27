# -*- coding: utf-8 -*-
"""重新注入15条政策数据"""
import sys, os
from pathlib import Path
BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

from core.database import init_db, PVDatabase
init_db()
db = PVDatabase()

news = [
    ('国家能源局发布2026年上半年光伏发电建设情况', None, 'national', 'plan'),
    ('江苏河南云南居前三！2026上半年各省光伏新增装机出炉', None, 'national', 'data'),
    ('光伏遭遇内外夹击！八大巨头同签行业倡议书', None, 'national', 'other'),
    ('重大利好！一光伏电池产线全面复产', None, 'national', 'other'),
    ('业绩暴涨股价翻倍，立新能源半年报出炉', None, 'national', 'other'),
    ('比亚迪光伏天窗量产，光伏新机遇？', None, 'national', 'other'),
    ('隆基绿能以BC技术领跑欧洲高效光伏市场', None, 'international', 'other'),
    ('山东的今天是很多省的明天：136号文后分布式光伏', None, 'province', 'policy'),
    ('分布式光伏四可改造要求，AGC/AVC下沉到10kV', None, 'national', 'grid'),
    ('2026年户用光伏补贴0.03元/度，并网审批7个工作日', None, 'national', 'subsidy'),
    ('浙江分布式光伏省补0.02元/kWh，绍兴叠加市级补贴', '浙江', 'province', 'subsidy'),
    ('深圳分布式光伏补贴政策有效期至2026年底', '广东', 'province', 'subsidy'),
    ('河南部分区域红色预警暂停分布式光伏备案', '河南', 'province', 'grid'),
    ('储能是不是光伏人的出路？人才缺口50万', None, 'national', 'other'),
    ('天合光能Q2盈利扭亏为盈', None, 'national', 'other'),
]

for title, prov, level, ptype in news:
    db.add_policy(title, prov, level, ptype)
    print(f'  Added: {title[:40]}')

db.close()
print(f'\nInjected {len(news)} policies')
