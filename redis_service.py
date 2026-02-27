# redis_service.py - Redis 服务模块

import os
import redis
import json
import time
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class RedisService:
    """Redis 服务"""
    
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self.client.ping()
            self.enabled = True
            logger.info("Redis 连接成功")
        except Exception as e:
            logger.warning(f"Redis 连接失败，使用内存存储: {e}")
            self.enabled = False
            self.memory_storage = {}
    
    def get(self, key: str) -> Optional[str]:
        """获取值"""
        try:
            if self.enabled:
                return self.client.get(key)
            else:
                return self.memory_storage.get(key)
        except Exception as e:
            logger.error(f"Redis GET 失败: {e}")
            return None
    
    def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """设置值"""
        try:
            if self.enabled:
                if expire:
                    return self.client.setex(key, expire, value)
                else:
                    return self.client.set(key, value)
            else:
                self.memory_storage[key] = value
                return True
        except Exception as e:
            logger.error(f"Redis SET 失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除键"""
        try:
            if self.enabled:
                return self.client.delete(key) > 0
            else:
                if key in self.memory_storage:
                    del self.memory_storage[key]
                    return True
                return False
        except Exception as e:
            logger.error(f"Redis DELETE 失败: {e}")
            return False
    
    def incr(self, key: str) -> int:
        """递增"""
        try:
            if self.enabled:
                return self.client.incr(key)
            else:
                current = int(self.memory_storage.get(key, 0))
                current += 1
                self.memory_storage[key] = str(current)
                return current
        except Exception as e:
            logger.error(f"Redis INCR 失败: {e}")
            return 0
    
    def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        try:
            if self.enabled:
                return self.client.expire(key, seconds)
            else:
                # 内存存储不支持过期，忽略
                return True
        except Exception as e:
            logger.error(f"Redis EXPIRE 失败: {e}")
            return False
    
    def get_json(self, key: str) -> Optional[Any]:
        """获取JSON值"""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return None
        return None
    
    def set_json(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置JSON值"""
        try:
            json_str = json.dumps(value)
            return self.set(key, json_str, expire)
        except:
            return False


class RateLimiter:
    """速率限制器（基于Redis）"""
    
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service
    
    def check_limit(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """检查是否超过速率限制"""
        try:
            current_key = f"rate_limit:{key}:{int(time.time() / window_seconds)}"
            
            count = self.redis.incr(current_key)
            
            if count == 1:
                self.redis.expire(current_key, window_seconds)
            
            return count <= max_requests
            
        except Exception as e:
            logger.error(f"速率限制检查失败: {e}")
            # 出错时允许请求通过
            return True
    
    def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        """获取剩余请求次数"""
        try:
            current_key = f"rate_limit:{key}:{int(time.time() / window_seconds)}"
            count = int(self.redis.get(current_key) or 0)
            return max(0, max_requests - count)
        except:
            return max_requests


class CacheService:
    """缓存服务"""
    
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service
    
    def get_cached(self, key: str) -> Optional[Any]:
        """获取缓存"""
        return self.redis.get_json(f"cache:{key}")
    
    def set_cached(self, key: str, value: Any, expire: int = 3600) -> bool:
        """设置缓存"""
        return self.redis.set_json(f"cache:{key}", value, expire)
    
    def delete_cached(self, key: str) -> bool:
        """删除缓存"""
        return self.redis.delete(f"cache:{key}")
    
    def clear_pattern(self, pattern: str) -> int:
        """清除匹配的缓存"""
        try:
            if self.redis.enabled:
                keys = self.redis.client.keys(f"cache:{pattern}")
                if keys:
                    return self.redis.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
            return 0


# 全局实例
redis_service = RedisService()
rate_limiter = RateLimiter(redis_service)
cache_service = CacheService(redis_service)
