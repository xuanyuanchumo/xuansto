"""
缓存服务测试

测试缓存相关功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.cache import CacheService, CacheKeys, cached, invalidate_cache


@pytest.mark.unit
class TestCacheService:
    """测试 CacheService 类"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        instance1 = CacheService()
        instance2 = CacheService()
        
        assert instance1 is instance2

    def test_serialize_dict(self):
        """测试序列化字典"""
        service = CacheService()
        result = service._serialize({"key": "value"})
        
        assert result == '{"key": "value"}'

    def test_serialize_list(self):
        """测试序列化列表"""
        service = CacheService()
        result = service._serialize([{"id": 1}, {"id": 2}])
        
        assert '"id": 1' in result
        assert '"id": 2' in result

    def test_serialize_pydantic_model(self):
        """测试序列化 Pydantic 模型"""
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str
            value: int
        
        service = CacheService()
        model = TestModel(name="test", value=123)
        result = service._serialize(model)
        
        assert '"name": "test"' in result
        assert '"value": 123' in result

    def test_deserialize_dict(self):
        """测试反序列化字典"""
        service = CacheService()
        result = service._deserialize('{"key": "value"}')
        
        assert result == {"key": "value"}

    def test_deserialize_with_model_class(self):
        """测试使用模型类反序列化"""
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str
            value: int
        
        service = CacheService()
        result = service._deserialize('{"name": "test", "value": 123}', TestModel)
        
        assert isinstance(result, TestModel)
        assert result.name == "test"
        assert result.value == 123

    def test_deserialize_none(self):
        """测试反序列化 None"""
        service = CacheService()
        result = service._deserialize(None)
        
        assert result is None

    def test_get_when_disconnected(self):
        """测试未连接时获取缓存"""
        service = CacheService()
        service._connected = False
        service._redis_client = None
        
        result = service.get("test_key")
        
        assert result is None

    def test_set_when_disconnected(self):
        """测试未连接时设置缓存"""
        service = CacheService()
        service._connected = False
        service._redis_client = None
        
        result = service.set("test_key", "test_value")
        
        assert result is False

    def test_delete_when_disconnected(self):
        """测试未连接时删除缓存"""
        service = CacheService()
        service._connected = False
        service._redis_client = None
        
        result = service.delete("test_key")
        
        assert result is False

    def test_delete_pattern_when_disconnected(self):
        """测试未连接时删除模式匹配缓存"""
        service = CacheService()
        service._connected = False
        service._redis_client = None
        
        result = service.delete_pattern("test:*")
        
        assert result == 0

    def test_get_stats_when_disconnected(self):
        """测试未连接时获取统计"""
        service = CacheService()
        service._connected = False
        service._redis_client = None
        
        result = service.get_stats()
        
        assert result["connected"] is False

    def test_incr_when_disconnected(self):
        """测试未连接时递增"""
        service = CacheService()
        service._connected = False
        service._redis_client = None
        
        result = service.incr("test_counter")
        
        assert result == 0


@pytest.mark.unit
class TestCacheKeys:
    """测试 CacheKeys 类"""

    def test_generate_key_project_list(self):
        """测试生成项目列表缓存键"""
        key = CacheKeys.generate_key(
            CacheKeys.PROJECT_LIST,
            status="active",
            page=1,
            page_size=10
        )
        
        assert "active" in key
        assert "1" in key
        assert "10" in key

    def test_generate_key_project_detail(self):
        """测试生成项目详情缓存键"""
        key = CacheKeys.generate_key(CacheKeys.PROJECT_DETAIL, project_id=123)
        
        assert "123" in key

    def test_generate_key_task_list(self):
        """测试生成任务列表缓存键"""
        key = CacheKeys.generate_key(CacheKeys.TASK_LIST, project_id=456)
        
        assert "456" in key

    def test_generate_key_skill_call_list(self):
        """测试生成技能调用列表缓存键"""
        key = CacheKeys.generate_key(
            CacheKeys.SKILL_CALL_LIST,
            skill_name="test_skill",
            status="completed",
            skip=0,
            limit=10
        )
        
        assert "test_skill" in key
        assert "completed" in key


@pytest.mark.unit
class TestCachedDecorator:
    """测试 cached 装饰器"""

    def test_cached_decorator_calls_function(self):
        """测试装饰器调用原函数"""
        mock_redis = MagicMock()
        mock_redis.get_json.return_value = None
        
        with patch('app.services.cache.cache_service') as mock_service:
            mock_service.get_json.return_value = None
            mock_service.set_json.return_value = True
            
            @cached(key_template="test:{param}", ttl=60)
            def test_func(param: str, db=None):
                return {"result": param}
            
            result = test_func(param="value")
            
            assert result == {"result": "value"}

    def test_cached_decorator_returns_cached_value(self):
        """测试装饰器返回缓存值"""
        cached_value = {"result": "cached"}
        
        with patch('app.services.cache.cache_service') as mock_service:
            mock_service.get_json.return_value = cached_value
            
            call_count = 0
            
            @cached(key_template="test:{param}", ttl=60)
            def test_func(param: str, db=None):
                nonlocal call_count
                call_count += 1
                return {"result": param}
            
            result = test_func(param="value")
            
            assert result == cached_value
            assert call_count == 0


@pytest.mark.unit
class TestInvalidateCache:
    """测试缓存失效函数"""

    def test_invalidate_cache_calls_delete_pattern(self):
        """测试缓存失效调用删除模式"""
        with patch('app.services.cache.cache_service') as mock_service:
            mock_service.delete_pattern.return_value = 5
            
            invalidate_cache("projects:*")
            
            mock_service.delete_pattern.assert_called_once_with("projects:*")


@pytest.mark.unit
class TestCacheServiceIntegration:
    """测试缓存服务集成"""

    @patch('app.services.cache.redis.from_url')
    def test_connection_success(self, mock_from_url):
        """测试成功连接"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_from_url.return_value = mock_client
        
        service = CacheService.__new__(CacheService)
        service._redis_client = None
        service.__init__()
        
        assert service._connected is True

    @patch('app.services.cache.redis.from_url')
    def test_connection_failure(self, mock_from_url):
        """测试连接失败"""
        mock_from_url.side_effect = Exception("Connection failed")
        
        service = CacheService.__new__(CacheService)
        service._redis_client = None
        service.__init__()
        
        assert service._connected is False
        assert service._redis_client is None

    def test_is_connected_property(self):
        """测试 is_connected 属性"""
        service = CacheService()
        service._connected = True
        
        assert service.is_connected is True
        
        service._connected = False
        
        assert service.is_connected is False
