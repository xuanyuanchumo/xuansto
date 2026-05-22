import json
import hashlib
import time
from typing import Optional, Any, Callable, TypeVar, List
from functools import wraps
import redis
from ..config import settings

T = TypeVar('T')

class CacheService:
    _instance: Optional['CacheService'] = None
    _redis_client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                self._redis_client.ping()
                self._connected = True
            except Exception:
                self._connected = False
                self._redis_client = None
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    def _serialize(self, value: Any) -> str:
        if hasattr(value, 'model_dump'):
            return json.dumps(value.model_dump())
        elif isinstance(value, (list, tuple)):
            return json.dumps([
                item.model_dump() if hasattr(item, 'model_dump') else item
                for item in value
            ])
        return json.dumps(value)
    
    def _deserialize(self, value: str, model_class: Optional[type] = None) -> Any:
        if value is None:
            return None
        data = json.loads(value)
        if model_class and isinstance(data, dict):
            return model_class(**data)
        elif model_class and isinstance(data, list):
            return [model_class(**item) if isinstance(item, dict) else item for item in data]
        return data
    
    def get(self, key: str) -> Optional[str]:
        if not self._connected or not self._redis_client:
            return None
        try:
            return self._redis_client.get(key)
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        if not self._connected or not self._redis_client:
            return False
        try:
            serialized = self._serialize(value)
            return self._redis_client.setex(key, ttl, serialized)
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        if not self._connected or not self._redis_client:
            return False
        try:
            self._redis_client.delete(key)
            return True
        except Exception:
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        if not self._connected or not self._redis_client:
            return 0
        try:
            keys = self._redis_client.keys(pattern)
            if keys:
                return self._redis_client.delete(*keys)
            return 0
        except Exception:
            return 0
    
    def get_json(self, key: str, model_class: Optional[type] = None) -> Any:
        value = self.get(key)
        if value is None:
            return None
        return self._deserialize(value, model_class)
    
    def set_json(self, key: str, value: Any, ttl: int = 300) -> bool:
        return self.set(key, value, ttl)
    
    def incr(self, key: str) -> int:
        if not self._connected or not self._redis_client:
            return 0
        try:
            return self._redis_client.incr(key)
        except Exception:
            return 0
    
    def get_stats(self) -> dict:
        if not self._connected or not self._redis_client:
            return {"connected": False}
        try:
            info = self._redis_client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception:
            return {"connected": False}


cache_service = CacheService()


class CacheKeys:
    PROJECT_LIST = "projects:list:{status}:{page}:{page_size}"
    PROJECT_DETAIL = "projects:detail:{project_id}"
    PROJECT_STATS = "projects:stats:{project_id}"
    PROJECT_ALL_STATS = "projects:stats:all"
    
    TASK_LIST = "tasks:list:{project_id}"
    TASK_DETAIL = "tasks:detail:{task_id}"
    TASK_STATS = "tasks:stats:{project_id}"
    
    SKILL_CALL_LIST = "skill_calls:list:{skill_name}:{status}:{skip}:{limit}"
    SKILL_CALL_DETAIL = "skill_calls:detail:{call_id}"
    SKILL_CALL_STATS = "skill_calls:stats"
    SKILL_CALL_TREE = "skill_calls:tree:{root_id}"
    
    AGENT_LIST = "agents:list"
    AGENT_DETAIL = "agents:detail:{agent_id}"
    AGENT_STATS = "agents:stats"
    
    DASHBOARD_STATS = "dashboard:stats"
    
    @staticmethod
    def generate_key(template: str, **kwargs) -> str:
        return template.format(**kwargs)


def cached(
    key_template: str,
    ttl: int = 300,
    key_params: Optional[List[str]] = None
):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            params = dict(bound.arguments)
            
            if 'db' in params:
                del params['db']
            if 'self' in params:
                del params['self']
            
            cache_key = key_template
            if key_params:
                cache_key = cache_key.format(**{k: params.get(k, '') for k in key_params})
            else:
                cache_key = cache_key.format(**params)
            
            cached_value = cache_service.get_json(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            
            if result is not None:
                cache_service.set_json(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    cache_service.delete_pattern(pattern)


def cache_result(key: str, result: Any, ttl: int = 300) -> bool:
    return cache_service.set_json(key, result, ttl)


def get_cached_result(key: str) -> Any:
    return cache_service.get_json(key)
