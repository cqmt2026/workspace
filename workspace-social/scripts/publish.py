# -*- coding: utf-8 -*-
"""
通用发布脚本
支持：百家号、头条号、抖音
"""

import json
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

os.makedirs(OUTPUT_DIR, exist_ok=True)


def publish_to_baijiahao(article):
    """发布到百家号"""
    config_path = os.path.join(CONFIG_DIR, 'baijiahao_cookies.json')
    if not os.path.exists(config_path):
        logger.error("百家号cookie配置不存在")
        return False
    
    # 读取配置
    with open(config_path, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    
    logger.info(f"准备发布到百家号: {article.get('title', '未命名')}")
    
    # TODO: 实际发布逻辑（需浏览器自动化）
    # 这里先记录待发布状态
    pending_path = os.path.join(OUTPUT_DIR, 'pending_publish.json')
    pending = []
    if os.path.exists(pending_path):
        with open(pending_path, 'r', encoding='utf-8') as f:
            pending = json.load(f)
    
    pending.append({
        'title': article.get('title'),
        'content': article.get('content'),
        'platform': 'baijiahao',
        'created_at': datetime.now().isoformat(),
        'status': 'pending'
    })
    
    with open(pending_path, 'w', encoding='utf-8') as f:
        json.dump(pending, f, ensure_ascii=False, indent=2)
    
    logger.info(f"已加入发布队列: {article.get('title')}")
    return True


def publish_to_toutiao(article):
    """发布到头条号"""
    logger.info(f"准备发布到头条号: {article.get('title', '未命名')}")
    # TODO: 实际发布逻辑
    return True


def publish_to_douyin(video):
    """发布到抖音"""
    logger.info(f"准备发布到抖音: {video.get('title', '未命名')}")
    # TODO: 实际发布逻辑（需浏览器自动化）
    return True


def main():
    """主入口"""
    logger.info("=== 通用发布脚本 ===")
    
    # 检查待发布队列
    pending_path = os.path.join(OUTPUT_DIR, 'pending_publish.json')
    if not os.path.exists(pending_path):
        logger.info("无待发布内容")
        return
    
    with open(pending_path, 'r', encoding='utf-8') as f:
        pending = json.load(f)
    
    logger.info(f"待发布内容: {len(pending)}条")
    
    for item in pending:
        platform = item.get('platform')
        if platform == 'baijiahao':
            publish_to_baijiahao(item)
        elif platform == 'toutiao':
            publish_to_toutiao(item)
        elif platform == 'douyin':
            publish_to_douyin(item)
    
    logger.info("=== 发布完成 ===")


if __name__ == "__main__":
    main()
