"""
代理池管理模块（MVP 阶段简化版）
"""
import requests
from typing import Optional, Dict


class ProxyPool:
    def __init__(self):
        self.use_proxy = False  # MVP 阶段不使用代理
        self.proxy_api_url = None
    
    def get_proxy(self) -> Optional[Dict]:
        """
        获取代理
        MVP 阶段直接返回 None（不使用代理）
        """
        if not self.use_proxy:
            return None
        
        return None
    
    def validate_proxy(self, proxy: Dict) -> bool:
        """
        验证代理是否可用
        """
        try:
            response = requests.get(
                'https://www.baidu.com',
                proxies=proxy,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
