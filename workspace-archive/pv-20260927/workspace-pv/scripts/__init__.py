# -*- coding: utf-8 -*-
"""
光伏获客系统 - 初始化
"""
import os
import sys
from pathlib import Path

# 确保workspace-pv在path中
BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "scripts"))

from core.config import *
from core.database import *
from core.hot_topic_collector import HotTopicCollector
from core.policy_monitor import PolicyMonitor
from core.pv_analyzer import PVAnalyzer

__version__ = "0.1.0"
__all__ = ["HotTopicCollector", "PolicyMonitor", "PVAnalyzer"]