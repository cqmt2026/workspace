# -*- coding: utf-8 -*-
"""
方案B：用专精特新名单中的企业名称，分批次用小Key重试（绕过限额）
或者用企业查询API（如果有）
"""
import sys, os, time, re, csv, requests
sys.stdout.reconfigure(encoding='utf-8')

# 尝试用不同的API或策略
# 1. 高德API可能有多Key轮询（如果有多个Key）
# 2. 用企查查/天眼查（需主人提供）
# 3. 用百度地图POI API（备用）
# 4. 用行业名录网站爬取

print("当前高德API已超限，需要:")
print("1. 等待明天重置（免费Key每日5万次）")
print("2. 或者申请更多API Key")
print("3. 或者使用企查查/天眼查（需主人提供账号）")
