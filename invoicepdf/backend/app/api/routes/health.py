"""
健康检查API
用于检查数据库连接状态
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlmodel import Session

from app.api.deps import SessionDep
from app.core.db import engine, reconnect_database

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/db")
def check_database_health(
    *,
    session: SessionDep
) -> Any:
    """
    检查数据库连接健康状态
    """
    try:
        # 测试基本连接
        result = session.exec(text("SELECT 1 as test")).one()
        
        # 获取数据库版本
        version_result = session.exec(text("SELECT version()")).first()
        db_version = version_result if version_result else "Unknown"
        
        # 获取连接池状态
        pool = engine.pool
        pool_status = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid()
        }
        
        return {
            "status": "healthy",
            "database": {
                "connected": True,
                "version": db_version[:100] if db_version else "Unknown",  # 限制长度
                "test_query": result
            },
            "connection_pool": pool_status
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": {
                "connected": False,
                "error": str(e)
            },
            "connection_pool": {
                "size": engine.pool.size() if hasattr(engine, 'pool') else None,
                "error": "无法获取连接池状态"
            }
        }


@router.get("")
def health_check() -> Any:
    """
    基本健康检查（不依赖数据库）
    """
    return {
        "status": "ok",
        "service": "invoice-pdf-api"
    }


@router.post("/db/reconnect")
def reconnect_database_endpoint() -> Any:
    """
    手动触发数据库重连
    用于在连接断开后手动恢复连接
    """
    try:
        success = reconnect_database()
        if success:
            return {
                "status": "success",
                "message": "数据库重连成功"
            }
        else:
            raise HTTPException(
                status_code=503,
                detail="数据库重连失败，请检查数据库服务器状态"
            )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"数据库重连失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"数据库重连失败: {str(e)}"
        )

