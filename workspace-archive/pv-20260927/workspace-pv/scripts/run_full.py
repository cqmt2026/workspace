# -*- coding: utf-8 -*-
"""运行完整流水线"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pipeline import PVPipeline
from core.database import PVDatabase

pipeline = PVPipeline()
result = pipeline.run_full(verbose=True)
print("\n" + "="*60)
print("流水线完成")
print("="*60)
print(f"耗时: {result['summary'].get('elapsed', 'N/A')}s")
print(f"汇总: {result['summary']}")