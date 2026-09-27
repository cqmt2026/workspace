# -*- coding: utf-8 -*-
"""
光伏获客系统 - 运行入口
用法: python -m scripts.core  或  python scripts/run.py
"""
import sys
import os
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "scripts"))
os.chdir(str(BASE))

from core.pipeline import main

if __name__ == "__main__":
    main()