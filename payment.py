# payment.py - 支付集成模块

import os
import hmac
import hashlib
from datetime import datetime
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class PaymentService:
    """支付服务基类"""
    
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY", "")
    
    def generate_signature(self, data: Dict) -> str:
        """生成签名"""
        # 按key排序
        sorted_items = sorted(data.items())
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_items])
        
        signature = hmac.new(
            self.secret_key.encode(),
            sign_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_signature(self, data: Dict, signature: str) -> bool:
        """验证签名"""
        expected = self.generate_signature(data)
        return hmac.compare_digest(expected, signature)


class AlipayService(PaymentService):
    """支付宝支付服务"""
    
    def __init__(self):
        super().__init__()
        self.app_id = os.getenv("ALIPAY_APP_ID", "")
        self.private_key = os.getenv("ALIPAY_PRIVATE_KEY", "")
        self.alipay_public_key = os.getenv("ALIPAY_PUBLIC_KEY", "")
        self.notify_url = os.getenv("ALIPAY_NOTIFY_URL", "")
        self.return_url = os.getenv("ALIPAY_RETURN_URL", "")
        
    def create_order(self, order_id: int, amount: float, subject: str) -> Dict:
        """创建支付宝订单"""
        try:
            # 这里需要真实的支付宝SDK集成
            # 当前返回模拟数据
            logger.info(f"创建支付宝订单: order_id={order_id}, amount={amount}")
            
            return {
                "success": True,
                "payment_url": f"https://openapi.alipay.com/gateway.do?order_id={order_id}",
                "order_id": order_id,
                "qr_code": f"alipay://pay?order_id={order_id}",
                "message": "请使用支付宝扫码支付"
            }
        except Exception as e:
            logger.error(f"创建支付宝订单失败: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def verify_callback(self, params: Dict) -> bool:
        """验证支付宝回调"""
        try:
            # 这里需要真实的支付宝签名验证
            # 当前返回模拟验证
            signature = params.get("sign", "")
            return self.verify_signature(params, signature)
        except Exception as e:
            logger.error(f"验证支付宝回调失败: {e}")
            return False


class WechatPayService(PaymentService):
    """微信支付服务"""
    
    def __init__(self):
        super().__init__()
        self.app_id = os.getenv("WECHAT_APP_ID", "")
        self.mch_id = os.getenv("WECHAT_MCH_ID", "")
        self.api_key = os.getenv("WECHAT_API_KEY", "")
        self.notify_url = os.getenv("WECHAT_NOTIFY_URL", "")
        
    def create_order(self, order_id: int, amount: float, subject: str) -> Dict:
        """创建微信支付订单"""
        try:
            # 这里需要真实的微信支付SDK集成
            # 当前返回模拟数据
            logger.info(f"创建微信支付订单: order_id={order_id}, amount={amount}")
            
            return {
                "success": True,
                "payment_url": f"weixin://wxpay/bizpayurl?order_id={order_id}",
                "order_id": order_id,
                "qr_code": f"weixin://pay?order_id={order_id}",
                "message": "请使用微信扫码支付"
            }
        except Exception as e:
            logger.error(f"创建微信支付订单失败: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def verify_callback(self, params: Dict) -> bool:
        """验证微信支付回调"""
        try:
            # 这里需要真实的微信支付签名验证
            # 当前返回模拟验证
            signature = params.get("sign", "")
            return self.verify_signature(params, signature)
        except Exception as e:
            logger.error(f"验证微信支付回调失败: {e}")
            return False


class PaymentManager:
    """支付管理器"""
    
    def __init__(self):
        self.alipay = AlipayService()
        self.wechat = WechatPayService()
    
    def create_payment(self, payment_method: str, order_id: int, amount: float, subject: str) -> Dict:
        """创建支付订单"""
        if payment_method == "alipay":
            return self.alipay.create_order(order_id, amount, subject)
        elif payment_method == "wechat":
            return self.wechat.create_order(order_id, amount, subject)
        else:
            return {
                "success": False,
                "message": "不支持的支付方式"
            }
    
    def verify_payment_callback(self, payment_method: str, params: Dict) -> bool:
        """验证支付回调"""
        if payment_method == "alipay":
            return self.alipay.verify_callback(params)
        elif payment_method == "wechat":
            return self.wechat.verify_callback(params)
        else:
            return False


# 全局支付管理器实例
payment_manager = PaymentManager()
