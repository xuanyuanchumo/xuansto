"""
E2E测试配置和Fixtures

提供E2E测试所需的配置和fixtures
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from app.main import app


class BaseE2ETest:
    """E2E测试基类"""
    
    @pytest.fixture(autouse=True)
    def setup_e2e(self):
        """E2E测试前准备"""
        self.client = TestClient(app)
        yield
        self.client = None
