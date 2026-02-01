import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
import asyncio
import time

from app.api.main import api_router
from app.core.config import settings

# 静态文件目录
BACKEND_DIR = Path(__file__).parent.parent
UPLOADS_DIR = BACKEND_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


# 超时中间件
async def timeout_middleware(request: Request, call_next):
    start_time = time.time()
    timeout_seconds = 300  # 5分钟超时，与前端保持一致
    
    try:
        # 使用asyncio.wait_for设置超时
        response = await asyncio.wait_for(
            call_next(request), 
            timeout=timeout_seconds
        )
        return response
    except asyncio.TimeoutError:
        # 超时处理
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=408,
            content={
                "detail": f"请求超时，超过{timeout_seconds}秒",
                "error_code": "REQUEST_TIMEOUT"
            }
        )
    except Exception as e:
        # 记录错误但不阻止正常错误处理
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"请求处理异常: {e}")
        # 重新抛出异常，让FastAPI处理
        raise e


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
# 强制允许前端访问，解决CORS问题
# CORS 中间件必须在最前面，确保所有响应都包含 CORS 头
cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5174",  # Vite 可能使用其他端口
    "http://127.0.0.1:5174",
]

# 如果配置中有BACKEND_CORS_ORIGINS，合并使用
if settings.BACKEND_CORS_ORIGINS:
    if isinstance(settings.BACKEND_CORS_ORIGINS, str):
        cors_origins.extend([origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",")])
    elif isinstance(settings.BACKEND_CORS_ORIGINS, list):
        cors_origins.extend([str(origin) for origin in settings.BACKEND_CORS_ORIGINS])

# 去重
cors_origins = list(set(cors_origins))

# CORS 中间件必须在最前面（在其他中间件之前）
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],  # 如果列表为空，允许所有源（仅开发环境）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # 预检请求缓存时间（1小时）
)

# 添加超时中间件（在 CORS 之后）
app.middleware("http")(timeout_middleware)

# 添加异常处理中间件，确保即使出错也添加 CORS 头
async def cors_exception_handler(request: Request, call_next):
    """确保即使出错也添加 CORS 头"""
    try:
        response = await call_next(request)
        # 确保响应包含 CORS 头（即使 CORSMiddleware 没有添加）
        origin = request.headers.get("origin")
        if origin:
            if origin not in response.headers.get("Access-Control-Allow-Origin", ""):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    except Exception as e:
        from fastapi.responses import JSONResponse
        from fastapi import HTTPException
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"请求处理异常: {e}", exc_info=True)
        
        # 如果是 HTTPException，使用其状态码
        status_code = 500
        detail = f"服务器内部错误: {str(e)}"
        if isinstance(e, HTTPException):
            status_code = e.status_code
            detail = e.detail
        
        # 创建错误响应并添加 CORS 头
        error_response = JSONResponse(
            status_code=status_code,
            content={
                "detail": detail,
                "error_code": "INTERNAL_SERVER_ERROR" if status_code == 500 else "HTTP_ERROR"
            }
        )
        
        # 手动添加 CORS 头
        origin = request.headers.get("origin")
        if origin:
            error_response.headers["Access-Control-Allow-Origin"] = origin
            error_response.headers["Access-Control-Allow-Credentials"] = "true"
            error_response.headers["Access-Control-Allow-Methods"] = "*"
            error_response.headers["Access-Control-Allow-Headers"] = "*"
            error_response.headers["Access-Control-Expose-Headers"] = "*"
        
        return error_response

# 添加异常处理中间件（在 CORS 和超时之后）
app.middleware("http")(cors_exception_handler)

# 添加请求验证错误处理器
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """捕获请求验证错误，记录详细信息"""
    import json
    error_details = exc.errors()
    error_body = exc.body
    
    logger.error(f"请求验证失败 - URL: {request.url}")
    logger.error(f"请求验证失败 - 方法: {request.method}")
    logger.error(f"请求验证失败 - 错误详情: {json.dumps(error_details, indent=2, ensure_ascii=False)}")
    if error_body:
        try:
            body_str = error_body.decode('utf-8') if isinstance(error_body, bytes) else str(error_body)
            logger.error(f"请求验证失败 - 请求体: {body_str[:1000]}")  # 只记录前1000字符
        except:
            logger.error(f"请求验证失败 - 请求体: (无法解析)")
    
    # 返回详细的错误信息
    return JSONResponse(
        status_code=422,
        content={
            "detail": error_details,
            "body": error_body.decode('utf-8') if isinstance(error_body, bytes) else str(error_body) if error_body else None,
            "message": "请求验证失败，请检查请求参数"
        },
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        }
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

# 添加静态文件服务，用于访问上传的文件
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
