from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate

# 确保使用psycopg驱动（psycopg3）
# 如果连接字符串是postgresql://，需要转换为postgresql+psycopg://
database_url = str(settings.SQLALCHEMY_DATABASE_URI)

# 确保使用 psycopg3 驱动
# 处理各种可能的 URL 格式
if database_url.startswith("postgresql://"):
    # 如果只是 postgresql://，转换为 postgresql+psycopg://
    if "+psycopg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql+psycopg2://"):
    # 如果使用了 psycopg2，转换为 psycopg3
    database_url = database_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)

# 添加数据库连接超时配置和重试机制
import logging
logger = logging.getLogger(__name__)

# 验证 psycopg3 是否已安装
try:
    import psycopg
    logger.debug("psycopg3 (psycopg) is available")
except ImportError:
    logger.error("psycopg3 (psycopg) is not installed. Please install it with: pip install psycopg[binary]")
    raise ImportError(
        "psycopg3 is required but not installed. "
        "Please install it with: pip install psycopg[binary]"
    )

# 改进的连接参数，增强网络稳定性
# 针对远程数据库服务器的优化配置
connect_args = {
    "connect_timeout": 10,        # 连接超时（10秒）
    "options": "-c statement_timeout=300000 -c application_name=invoice_pdf_api",  # 5分钟语句超时和应用名称
    "keepalives": 1,             # 启用TCP保活
    "keepalives_idle": 30,       # 30秒后开始保活
    "keepalives_interval": 10,   # 保活间隔10秒
    "keepalives_count": 5,       # 最多5次保活尝试
    "tcp_user_timeout": 30000,   # TCP用户超时（30秒）
}

# 创建数据库引擎，配置连接池和自动重连机制
from sqlalchemy import event
from sqlalchemy.exc import DisconnectionError, OperationalError

def create_db_engine():
    """创建数据库引擎，配置自动重连"""
    engine = create_engine(
        database_url,
        pool_pre_ping=True,          # 连接前检查（自动重连断开的连接）
        pool_recycle=1800,           # 连接回收时间（30分钟）
        pool_timeout=60,             # 连接池超时（60秒，增加超时时间以应对高并发）
        pool_size=15,                # 连接池大小（增加到15）
        max_overflow=25,             # 最大溢出连接数（增加到25，总共最多40个连接）
        echo=False,                  # 关闭SQL日志
        connect_args=connect_args,
    )
    
    # 添加连接断开自动重连的事件监听器
    @event.listens_for(engine, "connect")
    def set_connection_settings(dbapi_conn, connection_record):
        """连接建立时的设置"""
        logger.debug("数据库连接已建立")
    
    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """从连接池获取连接时检查连接有效性"""
        try:
            # 使用 pool_pre_ping 时，这里会自动检查连接
            pool = engine.pool
            logger.debug(
                f"从连接池获取连接 - "
                f"池大小: {pool.size()}, "
                f"已检出: {pool.checkedout()}, "
                f"已归还: {pool.checkedin()}, "
                f"溢出: {pool.overflow()}"
            )
            # 如果连接池接近满载，记录警告
            if pool.checkedout() > pool.size() * 0.8:
                logger.warning(
                    f"连接池使用率较高: {pool.checkedout()}/{pool.size() + pool.overflow()} "
                    f"({pool.checkedout() * 100 / (pool.size() + pool.overflow()):.1f}%)"
                )
        except Exception as e:
            logger.warning(f"连接检查失败，将自动重连: {e}")
            raise DisconnectionError("连接已断开，需要重连")
    
    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """连接归还到连接池"""
        pool = engine.pool
        logger.debug(
            f"连接已归还到连接池 - "
            f"池大小: {pool.size()}, "
            f"已检出: {pool.checkedout()}, "
            f"已归还: {pool.checkedin()}"
        )
    
    @event.listens_for(engine, "invalidate")
    def receive_invalidate(dbapi_conn, connection_record, exception):
        """连接失效时的处理"""
        logger.warning(f"数据库连接失效: {exception}，将自动重新创建连接")
    
    return engine


# 创建数据库引擎
try:
    engine = create_db_engine()
    
    # 测试连接是否可用（不阻塞启动）
    def test_connection_async():
        """异步测试连接"""
        try:
            with engine.connect() as test_conn:
                test_conn.exec_driver_sql("SELECT 1")
            logger.info("数据库连接测试成功")
        except Exception as test_error:
            logger.warning(f"数据库连接测试失败: {test_error}")
            logger.info("引擎已创建，将在实际使用时自动重连")
    
    # 在后台测试连接（不阻塞）
    import threading
    test_thread = threading.Thread(target=test_connection_async, daemon=True)
    test_thread.start()
        
except Exception as e:
    logger.error(f"创建数据库引擎失败: {e}", exc_info=True)
    raise


def reconnect_database():
    """
    手动重连数据库
    关闭现有连接池并重新创建引擎
    """
    global engine
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("开始重连数据库...")
        
        # 关闭现有连接池
        if engine:
            try:
                engine.dispose()
                logger.info("已关闭现有数据库连接池")
            except Exception as e:
                logger.warning(f"关闭连接池时出错: {e}")
        
        # 重新创建引擎
        engine = create_db_engine()
        logger.info("数据库引擎已重新创建")
        
        # 测试新连接
        try:
            with engine.connect() as test_conn:
                test_conn.exec_driver_sql("SELECT 1")
            logger.info("数据库重连成功")
            return True
        except Exception as test_error:
            logger.error(f"数据库重连测试失败: {test_error}")
            return False
            
    except Exception as e:
        logger.error(f"数据库重连失败: {e}", exc_info=True)
        return False


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)
