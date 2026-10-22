#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API客户端模板 - 通用API调用

用法：
    python api_client.py get /users --param id=123
    python api_client.py post /data --data '{"key": "value"}'
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import HTTPError, Timeout, RequestException


class APIClient:
    """API客户端类"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, 
                 timeout: int = 30, max_retries: int = 3):
        """初始化API客户端
        
        Args:
            base_url: API基础URL
            api_key: API密钥（可选）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        
        # 创建会话
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置默认 headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # 设置API密钥
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
    
    def _build_url(self, endpoint: str) -> str:
        """构建完整URL
        
        Args:
            endpoint: API端点
            
        Returns:
            str: 完整URL
        """
        return f"{self.base_url}/{endpoint.lstrip('/')}"
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """发送GET请求
        
        Args:
            endpoint: API端点
            params: 查询参数
            
        Returns:
            dict: API响应数据
        """
        url = self._build_url(endpoint)
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            self._handle_error(e, 'GET', endpoint)
        except Timeout:
            raise Timeout(f"请求超时: GET {url}")
        except RequestException as e:
            raise RequestException(f"请求失败: {e}")
    
    def post(self, endpoint: str, data: Optional[Dict] = None, 
             json_data: Optional[Dict] = None) -> Dict:
        """发送POST请求
        
        Args:
            endpoint: API端点
            data: 表单数据
            json_data: JSON数据
            
        Returns:
            dict: API响应数据
        """
        url = self._build_url(endpoint)
        
        try:
            response = self.session.post(
                url, 
                data=data, 
                json=json_data, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # 如果响应为空，返回空字典
            if response.status_code == 204:
                return {}
            
            return response.json()
        except HTTPError as e:
            self._handle_error(e, 'POST', endpoint)
        except Timeout:
            raise Timeout(f"请求超时: POST {url}")
        except RequestException as e:
            raise RequestException(f"请求失败: {e}")
    
    def put(self, endpoint: str, data: Optional[Dict] = None, 
            json_data: Optional[Dict] = None) -> Dict:
        """发送PUT请求
        
        Args:
            endpoint: API端点
            data: 表单数据
            json_data: JSON数据
            
        Returns:
            dict: API响应数据
        """
        url = self._build_url(endpoint)
        
        try:
            response = self.session.put(
                url,
                data=data,
                json=json_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            if response.status_code == 204:
                return {}
            
            return response.json()
        except HTTPError as e:
            self._handle_error(e, 'PUT', endpoint)
        except Timeout:
            raise Timeout(f"请求超时: PUT {url}")
        except RequestException as e:
            raise RequestException(f"请求失败: {e}")
    
    def delete(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """发送DELETE请求
        
        Args:
            endpoint: API端点
            params: 查询参数
            
        Returns:
            dict: API响应数据
        """
        url = self._build_url(endpoint)
        
        try:
            response = self.session.delete(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            if response.status_code == 204:
                return {}
            
            return response.json()
        except HTTPError as e:
            self._handle_error(e, 'DELETE', endpoint)
        except Timeout:
            raise Timeout(f"请求超时: DELETE {url}")
        except RequestException as e:
            raise RequestException(f"请求失败: {e}")
    
    def _handle_error(self, error: HTTPError, method: str, endpoint: str):
        """处理HTTP错误
        
        Args:
            error: HTTP错误对象
            method: HTTP方法
            endpoint: API端点
        """
        status_code = error.response.status_code if error.response else 'unknown'
        error_body = error.response.text if error.response else ''
        
        error_msg = f"HTTP {status_code}: {method} {endpoint}"
        if error_body:
            error_msg += f"\n响应: {error_body[:500]}"
        
        raise HTTPError(error_msg, response=error.response)
    
    def batch_get(self, endpoints: List[str], 
                  params_list: Optional[List[Dict]] = None) -> List[Dict]:
        """批量发送GET请求
        
        Args:
            endpoints: API端点列表
            params_list: 对应的查询参数列表
            
        Returns:
            List[Dict]: 响应列表
        """
        results = []
        
        for i, endpoint in enumerate(endpoints):
            params = params_list[i] if params_list and i < len(params_list) else None
            
            try:
                result = self.get(endpoint, params=params)
                results.append(result)
            except Exception as e:
                results.append({'error': str(e), 'endpoint': endpoint})
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="API客户端工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python api_client.py get /users --param id=123
  python api_client.py post /data --json '{"name": "test"}'
  python api_client.py get /search --param q=keyword --param page=1
        """
    )
    
    parser.add_argument('method', choices=['get', 'post', 'put', 'delete'],
                        help='HTTP方法')
    parser.add_argument('endpoint', help='API端点')
    parser.add_argument('--base-url', '-b', default=os.getenv('API_BASE_URL', ''),
                        help='API基础URL（可通过环境变量API_BASE_URL设置）')
    parser.add_argument('--api-key', '-k', default=os.getenv('API_KEY', ''),
                        help='API密钥（可通过环境变量API_KEY设置）')
    parser.add_argument('--param', '-p', action='append', 
                        help='查询参数 (key=value)，可多次使用')
    parser.add_argument('--data', '-d', help='表单数据')
    parser.add_argument('--json', '-j', help='JSON数据（字符串或文件路径）')
    parser.add_argument('--timeout', '-t', type=int, default=30,
                        help='请求超时时间（秒）')
    parser.add_argument('--output', '-o', help='输出文件路径')
    
    args = parser.parse_args()
    
    try:
        # 创建客户端
        client = APIClient(
            base_url=args.base_url,
            api_key=args.api_key,
            timeout=args.timeout
        )
        
        # 解析参数
        params = {}
        if args.param:
            for p in args.param:
                if '=' in p:
                    key, value = p.split('=', 1)
                    params[key] = value
        
        # 解析JSON数据
        json_data = None
        if args.json:
            if args.json.startswith('{'):
                json_data = json.loads(args.json)
            else:
                with open(args.json, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
        
        # 执行请求
        if args.method == 'get':
            result = client.get(args.endpoint, params=params if params else None)
        elif args.method == 'post':
            result = client.post(args.endpoint, json_data=json_data)
        elif args.method == 'put':
            result = client.put(args.endpoint, json_data=json_data)
        elif args.method == 'delete':
            result = client.delete(args.endpoint, params=params if params else None)
        else:
            raise ValueError(f"不支持的方法: {args.method}")
        
        # 输出结果
        output = json.dumps(result, ensure_ascii=False, indent=2)
        
        if args.output:
            Path(args.output).write_text(output, encoding='utf-8')
            print(f"结果已保存到: {args.output}")
        else:
            print(output)
        
    except FileNotFoundError as e:
        print(f"❌ 文件错误: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 请求失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
