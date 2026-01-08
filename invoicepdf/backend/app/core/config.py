from typing import Any, Literal, Optional
from pydantic import AnyUrl, BeforeValidator, EmailStr, HttpUrl, computed_field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore"
    )
    
    # 应用基础配置
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    PROJECT_NAME: str
    
    # 跨域配置
    BACKEND_CORS_ORIGINS: list[AnyUrl] | str = []
    SENTRY_DSN: Optional[HttpUrl] = None
    
    # 数据库连接（支持两种方式：DATABASE_URL 或单独的 POSTGRES_* 配置）
    # 方式1: 直接使用 DATABASE_URL
    DATABASE_URL: Optional[PostgresDsn] = None  # 业务数据库(bsz)
    SYS_DATABASE_URL: Optional[PostgresDsn] = None  # 系统数据库(sys)
    
    # 方式2: 使用单独的 POSTGRES_* 配置（兼容旧配置）
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    
    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """生成业务数据库的SQLAlchemy连接字符串"""
        # 优先使用 DATABASE_URL
        if self.DATABASE_URL:
            return str(self.DATABASE_URL)
        
        # 如果 DATABASE_URL 不存在，使用 POSTGRES_* 配置构建
        if self.POSTGRES_SERVER and self.POSTGRES_USER and self.POSTGRES_DB:
            password = self.POSTGRES_PASSWORD or ""
            return f"postgresql+psycopg://{self.POSTGRES_USER}:{password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
        raise ValueError("DATABASE_URL or (POSTGRES_SERVER, POSTGRES_USER, POSTGRES_DB) must be set in .env file")
        
    def get_sys_db_dblink_string(self) -> str:
        """生成系统数据库连接字符串"""
        if not self.SYS_DATABASE_URL:
            raise ValueError("SYS_DATABASE_URL must be set in .env file")
        return str(self.SYS_DATABASE_URL)
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    # 邮件配置
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # 超级用户配置
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    # 调试开关：允许超级用户重复上传同一文件（跳过去重）
    # 默认关闭；建议仅在 ENVIRONMENT=local 时开启
    INVOICE_DEBUG_ALLOW_DUPLICATE_UPLOADS: bool = False

   
settings = Settings()
