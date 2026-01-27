"""add company_id to invoice table

Revision ID: add_company_id_to_invoice_001
Revises: add_company_001
Create Date: 2025-01-01 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_company_id_to_invoice_001"
down_revision = "add_company_001"
branch_labels = None
depends_on = None


def upgrade():
    # 在 invoice 表中添加 company_id 列
    op.add_column("invoice", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    
    # 创建外键约束
    op.create_foreign_key(
        "fk_invoice_company_id",
        "invoice",
        "company",
        ["company_id"],
        ["id"],
        ondelete="SET NULL"
    )
    
    # 创建索引
    op.create_index(op.f("ix_invoice_company_id"), "invoice", ["company_id"])


def downgrade():
    # 删除索引和外键约束
    op.drop_index(op.f("ix_invoice_company_id"), table_name="invoice")
    op.drop_constraint("fk_invoice_company_id", "invoice", type_="foreignkey")
    
    # 删除 company_id 列
    op.drop_column("invoice", "company_id")

