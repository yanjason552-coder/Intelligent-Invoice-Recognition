"""
票据识别系统数据验证工具
"""

from typing import Any
from uuid import UUID
from datetime import datetime
from pydantic import field_validator, ValidationError


def validate_invoice_no(invoice_no: str) -> str:
    """验证票据编号格式"""
    if not invoice_no or len(invoice_no.strip()) == 0:
        raise ValueError("票据编号不能为空")
    if len(invoice_no) > 100:
        raise ValueError("票据编号长度不能超过100个字符")
    return invoice_no.strip()


def validate_amount(amount: float | None) -> float | None:
    """验证金额"""
    if amount is not None:
        if amount < 0:
            raise ValueError("金额不能为负数")
        if amount > 999999999.99:
            raise ValueError("金额超出允许范围")
    return amount


def validate_tax_no(tax_no: str | None) -> str | None:
    """验证税号格式"""
    if tax_no:
        # 中国税号通常是15、18或20位
        if len(tax_no) not in [15, 18, 20]:
            raise ValueError("税号格式不正确，应为15、18或20位")
        if not tax_no.isalnum():
            raise ValueError("税号只能包含字母和数字")
    return tax_no


def validate_invoice_type(invoice_type: str) -> str:
    """验证票据类型"""
    allowed_types = [
        "增值税专用发票",
        "增值税普通发票",
        "增值税电子普通发票",
        "增值税电子专用发票",
        "其他"
    ]
    if invoice_type not in allowed_types:
        raise ValueError(f"票据类型必须是以下之一: {', '.join(allowed_types)}")
    return invoice_type


def validate_status(status: str, allowed_statuses: list[str]) -> str:
    """验证状态值"""
    if status not in allowed_statuses:
        raise ValueError(f"状态必须是以下之一: {', '.join(allowed_statuses)}")
    return status


def validate_recognition_accuracy(accuracy: float | None) -> float | None:
    """验证识别准确率"""
    if accuracy is not None:
        if accuracy < 0 or accuracy > 100:
            raise ValueError("识别准确率必须在0-100之间")
    return accuracy


def validate_file_type(file_type: str) -> str:
    """验证文件类型"""
    allowed_types = ["pdf", "jpg", "jpeg", "png"]
    file_type_lower = file_type.lower()
    if file_type_lower not in allowed_types:
        raise ValueError(f"文件类型必须是以下之一: {', '.join(allowed_types)}")
    return file_type_lower


def validate_template_version(version: str) -> str:
    """验证模板版本号格式"""
    import re
    # 版本号格式：x.y.z 或 x.y
    pattern = r'^\d+\.\d+(\.\d+)?$'
    if not re.match(pattern, version):
        raise ValueError("版本号格式不正确，应为 x.y.z 或 x.y 格式")
    return version


def validate_priority(priority: int) -> int:
    """验证优先级"""
    if priority < 0 or priority > 100:
        raise ValueError("优先级必须在0-100之间")
    return priority


def validate_confidence(confidence: float) -> float:
    """验证置信度"""
    if confidence < 0 or confidence > 1:
        raise ValueError("置信度必须在0-1之间")
    return confidence


def validate_json_field(field_value: dict | None, field_name: str = "字段") -> dict | None:
    """验证JSON字段"""
    if field_value is not None:
        if not isinstance(field_value, dict):
            raise ValueError(f"{field_name}必须是字典类型")
    return field_value


