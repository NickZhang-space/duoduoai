"""
代理池管理模块（MVP 阶段简化版）
"""
import requests
from typing import Optional
from .config import USE_PROXY, PROXY_API_URL


class ProxyPool:
    def __init__(self):
        self.use_proxy = USE_PROXY
        self.proxy_api_url = PROXY_API_URL
    
    def get_proxy(self) -> Optional[Dict]:
        """
        获取代理
        MVP 阶段直接返回 None（不使用代理）
        """
        if not self.use_proxy:
            return None
        
        # 预留：从芝麻代理 API 获取
        # try:
        #     response = requests.get(self.proxy_api_url, timeout=5)
        #     if response.status_code == 200:
        #         proxy_data = response.json()
        #         return {
        #             'http': f"http://{proxy_data['ip']}:{proxy_data['port']}",
        #             'https': f"http://{proxy_data['ip']}:{proxy_data['port']}"
        #         }
        # except Exception as e:
        #     print(f"获取代理失败: {e}")
        
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
