# -*- coding: utf-8 -*-
"""Run content_generator.py — stdout may be closed in cron, so write results to file."""
import sys, os, json
sys.path.insert(0, r'C:\Users\Administrator\.openclaw\workspace\workspace-pv\scripts')
os.chdir(r'C:\Users\Administrator\.openclaw\workspace\workspace-pv')

from core.content_generator import ContentGenerator

gen = ContentGenerator(use_llm=False, auto_record=True)
contents = gen.generate_daily_content(limit_topics=6, limit_policies=4)
report = gen.generate_report(contents)
report_path = gen.save_report(report)
scripts_dir = gen.save_single_scripts(contents)
gen.db.close()

result = {
    "status": "ok",
    "count": len(contents),
    "report_path": str(report_path),
    "scripts_dir": str(scripts_dir),
    "tracking_ids": [c["tracking_id"] for c in contents],
    "directions": [c["direction_name"] for c in contents],
}

# Write result to a status file so we can verify
status_path = os.path.join(os.path.dirname(__file__), '_cg_status.json')
with open(status_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"CG done: {len(contents)} items, report={report_path.name}, scripts_dir={scripts_dir.name}")
