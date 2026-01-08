"""
统一数据库配置文件 - 包含主数据库和跨数据库配置
"""

from typing import Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, computed_field

class DatabaseConfig(BaseSettings):
    """统一数据库配置类"""
    
    model_config = SettingsConfigDict(
        env_file="../.env",  # 使用项目根目录的 .env 文件
        env_ignore_empty=True,
        extra="ignore",
    )
    
    # ==================== 主数据库配置 ====================
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "changethis"
    POSTGRES_DB: str = "app"
    
    # ==================== sys数据库配置 ====================
    SYS_DB_HOST: str = "localhost"
    SYS_DB_PORT: int = 5432
    SYS_DB_NAME: str = "sys"
    SYS_DB_USER: str = "postgres"
    SYS_DB_PASSWORD: str = "changethis"
    
    # ==================== 其他数据库配置 ====================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    # ==================== 计算字段和方法 ====================
    
    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        """生成主数据库的 SQLAlchemy 连接字符串"""
        # 使用字符串构建，避免 MultiHostUrl 兼容性问题
        return PostgresDsn(f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}")
    
    def get_main_db_connection_string(self) -> str:
        """生成主数据库的连接字符串"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    def get_sys_db_dblink_string(self) -> str:
        """生成sys数据库的dblink连接字符串"""
        return f"host={self.SYS_DB_HOST} port={self.SYS_DB_PORT} dbname={self.SYS_DB_NAME} user={self.SYS_DB_USER} password={self.SYS_DB_PASSWORD}"
    
    def get_redis_connection_string(self) -> str:
        """生成Redis连接字符串"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        else:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取所有数据库配置信息"""
        return {
            "main_database": {
                "host": self.POSTGRES_SERVER,
                "port": self.POSTGRES_PORT,
                "database": self.POSTGRES_DB,
                "user": self.POSTGRES_USER,
                "connection_string": self.get_main_db_connection_string()
            },
            "sys_database": {
                "host": self.SYS_DB_HOST,
                "port": self.SYS_DB_PORT,
                "database": self.SYS_DB_NAME,
                "user": self.SYS_DB_USER,
                "dblink_string": self.get_sys_db_dblink_string()
            },
            "redis": {
                "host": self.REDIS_HOST,
                "port": self.REDIS_PORT,
                "database": self.REDIS_DB,
                "connection_string": self.get_redis_connection_string()
            }
        }

# 全局配置实例
db_config = DatabaseConfig() 