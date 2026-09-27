# -*- coding: utf-8 -*-
"""Run PVPipeline silently (stdout may be closed in cron)."""
import sys, os
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-pv\scripts')
os.chdir(r'C:\Users\Administrator\.openclaw\workspace\workspace-pv')

from core.pipeline import PVPipeline
pipeline = PVPipeline()
result = pipeline.run_full(verbose=False)

import json
out = {
    "status": result["summary"]["status"],
    "topics_collected": result["summary"]["topics_collected"],
    "pv_related": result["summary"]["pv_related"],
    "elapsed": result["summary"]["elapsed"],
}
print(json.dumps(out, ensure_ascii=False))
