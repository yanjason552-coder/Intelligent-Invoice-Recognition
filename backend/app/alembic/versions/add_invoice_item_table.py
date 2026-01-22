"""add invoice_item table

Revision ID: add_invoice_item_001
Revises: add_external_file_id_001
Create Date: 2024-12-30 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_invoice_item_001"
down_revision = "add_external_file_id_001"
branch_labels = None
depends_on = None


def upgrade():
    # 创建发票行项目表
    op.create_table(
        "invoice_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_no", sa.String(length=100), nullable=False),
        sa.Column("line_no", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=True),
        sa.Column("part_no", sa.String(length=100), nullable=True),
        sa.Column("supplier_partno", sa.String(length=100), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("unit_price", sa.Float(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("tax_rate", sa.String(length=20), nullable=True),
        sa.Column("tax_amount", sa.Float(), nullable=True),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.Column("update_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["id"], ["invoice.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", "invoice_no", "line_no"),
    )
    # 创建索引以提高查询性能
    op.create_index(op.f("ix_invoice_item_id"), "invoice_item", ["id"])
    op.create_index(op.f("ix_invoice_item_invoice_no"), "invoice_item", ["invoice_no"])


def downgrade():
    # 删除索引
    op.drop_index(op.f("ix_invoice_item_invoice_no"), table_name="invoice_item")
    op.drop_index(op.f("ix_invoice_item_id"), table_name="invoice_item")
    # 删除表
    op.drop_table("invoice_item")

