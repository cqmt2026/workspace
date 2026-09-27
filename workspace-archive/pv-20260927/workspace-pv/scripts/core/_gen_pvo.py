"""生成测试用脚本JSON"""
import json
from datetime import datetime

data = {
    "title": "屋顶装光伏到底划不划算？",
    "body": "以常见的5kW-10kW屋顶光伏为例，结合当前组件价格和上网电价，真实算一笔账：前期投入约1.5万，每年发电约5000度，回本周期3-4年，25年寿命期总收益可达8万+。光伏发电不只有一次收益，还有碳排放指标和绿证收益，综合下来更划算。",
    "cta": "点关注私信我，免费帮你测算当地政策",
    "full_script": "屋顶装光伏到底划不划算？以常见的5kW-10kW屋顶光伏为例，结合当前组件价格和上网电价，真实算一笔账：前期投入约1.5万，每年发电约5000度，回本周期3-4年，25年寿命期总收益可达8万+。光伏发电不只有一次收益，还有碳排放指标和绿证收益，综合下来更划算。关注九箭新能源，获取最新光伏政策解读。",
    "tracking_id": "PV_HYPER_V1_TEST",
    "direction": "benefit",
    "direction_name": "收益",
    "target_audience": "有屋顶的家庭",
    "geo_primary_province": "重庆",
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
}

output_path = "workspace-pv/data/content/test_pv_script.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"Saved test script to {output_path}")