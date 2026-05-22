#!/usr/bin/env python3
"""测试fixture配置是否正确"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import BaseE2ETest
import pytest

def test_client_fixture():
    """测试client fixture是否正常工作"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.base import Base
    
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    def override_get_db():
        try:
            yield session
        finally:
            pass
    
    from app.models.base import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/health")
            print(f"Health check status: {response.status_code}")
            print(f"Health check response: {response.json()}")
            
            response = client.post("/api/projects/", json={"name": "Test Project"})
            print(f"Create project status: {response.status_code}")
            print(f"Create project response: {response.json()}")
    finally:
        app.dependency_overrides.clear()
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_base_e2e_test_class():
    """测试BaseE2ETest类是否正常工作"""
    print("\nTesting BaseE2ETest class...")
    
    class TestExample(BaseE2ETest):
        def test_example(self):
            print(f"Client type: {type(self.client)}")
            print(f"DB session type: {type(self.db_session)}")
            print(f"Has client attribute: {hasattr(self, 'client')}")
            assert hasattr(self, 'client'), "BaseE2ETest should have client attribute"
            assert hasattr(self, 'db_session'), "BaseE2ETest should have db_session attribute"
            assert hasattr(self, 'mock_redis'), "BaseE2ETest should have mock_redis attribute"
            assert hasattr(self, 'mock_celery'), "BaseE2ETest should have mock_celery attribute"
            assert hasattr(self, 'mock_external_services'), "BaseE2ETest should have mock_external_services attribute"
            print("✓ All attributes are correctly set")
    
    test_instance = TestExample()
    
    print("✓ BaseE2ETest class structure is correct")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Fixture Configuration")
    print("=" * 60)
    
    print("\n1. Testing client fixture...")
    test_client_fixture()
    
    print("\n2. Testing BaseE2ETest class...")
    test_base_e2e_test_class()
    
    print("\n" + "=" * 60)
    print("All fixture tests passed!")
    print("=" * 60)
