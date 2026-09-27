#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多账号管理模块
管理多个百家号/头条号账号，支持账号切换、状态监控

作者：房地产自媒体团队
版本：V1.0
创建时间：2026-03-15
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 导入日志系统
import sys
sys.path.append(str(Path(__file__).parent))
from logger import logger


class AccountManager:
    """多账号管理器"""
    
    def __init__(self):
        self.config_dir = Path('config')
        self.config_dir.mkdir(exist_ok=True)
        
        self.accounts_file = self.config_dir / 'accounts.json'
        
        # 账号存储
        self.accounts = self.load_accounts()
        
        # 当前账号
        self.current_account = None
        
        logger.info("多账号管理器初始化完成")
    
    def load_accounts(self) -> Dict[str, Any]:
        """
        加载账号配置
        
        返回:
            dict: 账号配置
        """
        if self.accounts_file.exists():
            with open(self.accounts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 初始化空配置
            config = {
                'accounts': [],
                'current': None
            }
            self.save_accounts(config)
            return config
    
    def save_accounts(self, config: Dict):
        """
        保存账号配置
        
        参数:
            config (dict): 账号配置
        """
        with open(self.accounts_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"账号配置已保存：{self.accounts_file}")
    
    def add_account(self, name: str, platform: str, credentials: Dict) -> bool:
        """
        添加账号
        
        参数:
            name (str): 账号名称
            platform (str): 平台（baijiahao/toutiao）
            credentials (dict): 账号凭证
        
        返回:
            bool: 是否添加成功
        """
        account = {
            'id': f"{platform}_{len(self.accounts['accounts']) + 1}",
            'name': name,
            'platform': platform,
            'credentials': credentials,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'last_used': None
        }
        
        self.accounts['accounts'].append(account)
        self.save_accounts(self.accounts)
        
        logger.success(f"账号已添加：{name} ({platform})")
        
        return True
    
    def remove_account(self, account_id: str) -> bool:
        """
        删除账号
        
        参数:
            account_id (str): 账号 ID
        
        返回:
            bool: 是否删除成功
        """
        for i, account in enumerate(self.accounts['accounts']):
            if account['id'] == account_id:
                self.accounts['accounts'].pop(i)
                self.save_accounts(self.accounts)
                logger.success(f"账号已删除：{account_id}")
                return True
        
        logger.warning(f"账号不存在：{account_id}")
        return False
    
    def switch_account(self, account_id: str) -> bool:
        """
        切换账号
        
        参数:
            account_id (str): 账号 ID
        
        返回:
            bool: 是否切换成功
        """
        for account in self.accounts['accounts']:
            if account['id'] == account_id:
                self.accounts['current'] = account_id
                account['last_used'] = datetime.now().isoformat()
                self.save_accounts(self.accounts)
                
                self.current_account = account
                logger.success(f"账号已切换：{account['name']}")
                
                return True
        
        logger.warning(f"账号不存在：{account_id}")
        return False
    
    def get_current_account(self) -> Optional[Dict]:
        """
        获取当前账号
        
        返回:
            dict: 当前账号信息
        """
        if self.accounts['current']:
            for account in self.accounts['accounts']:
                if account['id'] == self.accounts['current']:
                    return account
        return None
    
    def list_accounts(self, platform: Optional[str] = None) -> List[Dict]:
        """
        列出账号
        
        参数:
            platform (str, optional): 平台过滤
        
        返回:
            list: 账号列表
        """
        accounts = self.accounts['accounts']
        
        if platform:
            accounts = [a for a in accounts if a['platform'] == platform]
        
        return accounts
    
    def get_account_status(self, account_id: str) -> Dict[str, Any]:
        """
        获取账号状态
        
        参数:
            account_id (str): 账号 ID
        
        返回:
            dict: 账号状态
        """
        for account in self.accounts['accounts']:
            if account['id'] == account_id:
                return {
                    'id': account['id'],
                    'name': account['name'],
                    'platform': account['platform'],
                    'status': account['status'],
                    'created_at': account['created_at'],
                    'last_used': account['last_used']
                }
        
        return {'error': '账号不存在'}
    
    def get_all_status(self) -> Dict[str, Any]:
        """
        获取所有账号状态
        
        返回:
            dict: 所有账号状态
        """
        status = {
            'total': len(self.accounts['accounts']),
            'active': len([a for a in self.accounts['accounts'] if a['status'] == 'active']),
            'current': self.accounts['current'],
            'accounts': []
        }
        
        for account in self.accounts['accounts']:
            status['accounts'].append({
                'id': account['id'],
                'name': account['name'],
                'platform': account['platform'],
                'status': account['status'],
                'last_used': account['last_used']
            })
        
        return status


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("多账号管理模块")
    logger.info("=" * 60)
    
    manager = AccountManager()
    
    # 获取所有账号状态
    status = manager.get_all_status()
    
    print("\n" + "=" * 60)
    print("账号状态")
    print("=" * 60)
    print(f"总账号数：{status['total']}")
    print(f"活跃账号：{status['active']}")
    print(f"当前账号：{status['current'] or '无'}")
    print("\n账号列表:")
    
    for account in status['accounts']:
        current_icon = "👉" if account['id'] == status['current'] else "  "
        status_icon = "✅" if account['status'] == 'active' else "❌"
        print(f"{current_icon} {status_icon} {account['name']} ({account['platform']}) - {account['last_used'] or '从未使用'}")
    
    print("=" * 60)
    
    logger.success("多账号管理模块执行完成")


if __name__ == '__main__':
    main()
