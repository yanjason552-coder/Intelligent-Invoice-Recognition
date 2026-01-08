from fastapi import APIRouter, Depends
from pydantic.networks import EmailStr

from app.api.deps import get_current_active_superuser
from app.models import Message
from app.utils import (
    generate_test_email, 
    send_email,
    get_server_datetime,
    get_server_datetime_utc,
    get_server_datetime_iso,
    get_server_datetime_utc_iso,
    get_server_date_string,
    get_server_time_string,
    get_server_datetime_string,
    get_server_timezone_info,
    get_timestamp_milliseconds,
    get_timestamp_seconds
)

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True


@router.get("/server-time/")
async def get_server_time() -> dict:
    """
    获取服务器当前时间信息
    """
    return {
        "success": True,
        "data": {
            "datetime": get_server_datetime_string(),
            "date": get_server_date_string(),
            "time": get_server_time_string(),
            "iso": get_server_datetime_iso(),
            "utc_iso": get_server_datetime_utc_iso(),
            "timestamp_seconds": get_timestamp_seconds(),
            "timestamp_milliseconds": get_timestamp_milliseconds(),
            "timezone_info": get_server_timezone_info()
        },
        "message": "服务器时间获取成功"
    }


@router.get("/server-time/{timezone_name}")
async def get_server_time_with_timezone(timezone_name: str) -> dict:
    """
    获取指定时区的服务器时间信息
    
    Args:
        timezone_name: 时区名称，如"Asia/Shanghai", "America/New_York", "Europe/London"
    """
    try:
        datetime_obj = get_server_datetime(timezone_name)
        return {
            "success": True,
            "data": {
                "timezone": timezone_name,
                "datetime": datetime_obj.strftime("%Y-%m-%d %H:%M:%S"),
                "date": datetime_obj.strftime("%Y-%m-%d"),
                "time": datetime_obj.strftime("%H:%M:%S"),
                "iso": datetime_obj.isoformat(),
                "timestamp_seconds": int(datetime_obj.timestamp()),
                "timestamp_milliseconds": int(datetime_obj.timestamp() * 1000)
            },
            "message": f"时区 {timezone_name} 的时间获取成功"
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"获取时区 {timezone_name} 的时间失败: {str(e)}"
        }
