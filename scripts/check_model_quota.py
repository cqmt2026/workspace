#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""模型额度监控脚本"""
import json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(r"C:\Users\Administrator\.openclaw\workspace")
DATA_DIR = WORKSPACE / "DATA"
QUOTA_FILE = DATA_DIR / "model_quota_status.json"
LOG_DIR = WORKSPACE / "memory" / "日志" / "模型额度监控"

def generate_report():
    now = datetime.now()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    status = {
        "last_check": now.isoformat(),
        "providers": {
            "sensenova": {"status": "unknown", "remaining": None, "note": "需登录 platform.sensenova.cn"},
            "agnes_ai": {"status": "unknown", "remaining": None, "note": "需登录 apihub.agnes-ai.com"},
            "modal": {"status": "normal", "remaining": "pay_per_use", "note": "按量计费"}
        }
    }
    
    with open(QUOTA_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False)
    
    report = f"""## 模型额度监控报告

**时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}

### Provider状态

| Provider | 状态 | 剩余 | 备注 |
|----------|------|------|------|
| Sensenova | 待检查 | - | 需登录 platform.sensenova.cn |
| agnes-ai | 待检查 | - | 需登录 apihub.agnes-ai.com |
| Modal | 正常 | 按量计费 | 自动计费 |

**建议**: 登录各provider控制台确认实际额度。
"""
    
    report_file = LOG_DIR / f"quota_report_{now.strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return report

if __name__ == "__main__":
    print(generate_report())
