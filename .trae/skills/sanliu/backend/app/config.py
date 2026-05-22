from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any
from functools import lru_cache
import os
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    APP_NAME: str = "Sanliu Skill Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "postgres"
    DATABASE_NAME: str = "sanliu"
    
    @property
    def DATABASE_URL(self) -> str:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return db_url
        
        if not self.DATABASE_PASSWORD:
            logger.warning(
                "DATABASE_PASSWORD is empty. "
                "Please set DATABASE_PASSWORD in .env file or environment variables. "
                "Using default password 'postgres' for development."
            )
        
        password = self.DATABASE_PASSWORD or "postgres"
        return f"postgresql://{self.DATABASE_USER}:{password}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    def validate_database_config(self) -> dict:
        """验证数据库配置完整性"""
        issues = []
        warnings = []
        
        if not self.DATABASE_PASSWORD:
            warnings.append("DATABASE_PASSWORD is not set (using default 'postgres')")
        
        if self.DATABASE_HOST == "localhost" and not os.getenv("DATABASE_URL"):
            warnings.append("Using localhost for DATABASE_HOST (development mode)")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "config": {
                "host": self.DATABASE_HOST,
                "port": self.DATABASE_PORT,
                "user": self.DATABASE_USER,
                "database": self.DATABASE_NAME,
                "password_set": bool(self.DATABASE_PASSWORD)
            }
        }
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            return redis_url
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # === PathConfigCenter 集成配置 ===
    SKILL_ROOT: Optional[str] = None
    DOCS_DIR: Optional[str] = None
    SCRIPTS_DIR: Optional[str] = None
    REPORTS_DIR: Optional[str] = None
    CACHE_DIR: Optional[str] = None
    LOGS_DIR: Optional[str] = None
    CURRENT_VERSION: str = "v3.2.0"
    PATH_CONFIG_ENABLED: bool = True

    def get_path_config_center(self):
        """获取 PathConfigCenter 实例（懒初始化）"""
        if not self.PATH_CONFIG_ENABLED:
            return None
        from skillscripts.core.path_config_center import get_path_config
        return get_path_config()

    def get_path_status(self) -> Dict[str, Any]:
        """获取所有路径配置状态"""
        pcc = self.get_path_config_center()
        if not pcc:
            return {"enabled": False, "paths": {}}
        return {
            "enabled": True,
            "skill_root": str(pcc.SKILL_ROOT),
            "docs_dir": str(pcc.DOCS_DIR),
            "scripts_dir": str(pcc.SCRIPTS_DIR),
            "reports_dir": str(pcc.REPORTS_DIR),
            "versions_dir": str(pcc.VERSIONS_DIR),
            "current_version": pcc.get_current_version(),
            "env_overrides": {
                k: v for k, v in os.environ.items() 
                if k.startswith("SANLIU_")
            }
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
