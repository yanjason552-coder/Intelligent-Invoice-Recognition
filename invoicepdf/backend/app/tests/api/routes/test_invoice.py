"""
票据识别API测试
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlmodel import Session, select, delete

from app.models import User
from app.models.models_invoice import Invoice, InvoiceFile, RecognitionTask, RecognitionResult


@pytest.fixture
def test_invoice_file(db: Session, superuser_token_headers: dict) -> InvoiceFile:
    """创建测试文件"""
    # 获取当前用户
    from app.tests.utils.utils import get_superuser_token_headers
    from app.core.security import get_password_hash
    
    # 查找或创建测试用户
    user = db.exec(select(User).where(User.email == "admin@example.com")).first()
    if not user:
        user = User(
            email="admin@example.com",
            hashed_password=get_password_hash("changethis"),
            full_name="Admin User",
            is_active=True,
            is_superuser=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    invoice_file = InvoiceFile(
        file_name="test_invoice.pdf",
        file_path="/tmp/test_invoice.pdf",
        file_size=1024,
        file_type="pdf",
        mime_type="application/pdf",
        uploader_id=user.id,
        status="uploaded"
    )
    db.add(invoice_file)
    db.commit()
    db.refresh(invoice_file)
    yield invoice_file
    
    # 清理
    db.delete(invoice_file)
    db.commit()


@pytest.fixture
def test_invoice(db: Session, test_invoice_file: InvoiceFile) -> Invoice:
    """创建测试票据"""
    user = db.exec(select(User).where(User.email == "admin@example.com")).first()
    
    invoice = Invoice(
        invoice_no="TEST-INV-001",
        invoice_type="增值税专用发票",
        file_id=test_invoice_file.id,
        creator_id=user.id,
        recognition_status="pending",
        review_status="pending"
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    yield invoice
    
    # 清理
    db.delete(invoice)
    db.commit()


def test_query_invoices(client: TestClient, test_invoice: Invoice, superuser_token_headers: dict):
    """测试查询票据"""
    response = client.get(
        "/api/v1/invoices/query",
        headers=superuser_token_headers,
        params={"skip": 0, "limit": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert isinstance(data["data"], list)


def test_get_invoice(client: TestClient, test_invoice: Invoice, superuser_token_headers: dict):
    """测试获取票据详情"""
    response = client.get(
        f"/api/v1/invoices/{test_invoice.id}",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["invoice_no"] == test_invoice.invoice_no
    assert data["id"] == str(test_invoice.id)


def test_get_pending_reviews(client: TestClient, test_invoice: Invoice, superuser_token_headers: dict):
    """测试获取待审核票据"""
    response = client.get(
        "/api/v1/invoices/review/pending",
        headers=superuser_token_headers,
        params={"skip": 0, "limit": 10}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data


def test_get_ocr_config(client: TestClient, superuser_token_headers: dict):
    """测试获取OCR配置"""
    response = client.get(
        "/api/v1/config/ocr",
        headers=superuser_token_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert "language" in data
    assert "confidence_threshold" in data


