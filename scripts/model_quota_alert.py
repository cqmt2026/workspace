#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""模型额度预警脚本"""
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(r"C:\Users\Administrator\.openclaw\workspace\memory\日志\模型额度监控")

def check_and_alert():
    now = datetime.now()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    alert = f"""## 模型额度检查

**时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}
**状态**: 请手动登录各provider控制台检查额度
- SenseNova: platform.sensenova.cn
- agnes-ai: apihub.agnes-ai.com
- Modal: modal.com/dashboard
"""
    
    alert_file = LOG_DIR / f"quota_alert_{now.strftime('%Y%m%d_%H%M%S')}.md"
    with open(alert_file, 'w', encoding='utf-8') as f:
        f.write(alert)
    
    return alert

if __name__ == "__main__":
    print(check_and_alert())
