"""add company table and user company_id

Revision ID: add_company_001
Revises: ('add_invoice_item_001', 'merge_template_branches_001')
Create Date: 2024-12-31 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_company_001"
down_revision = ("add_invoice_item_001", "merge_template_branches_001")
branch_labels = None
depends_on = None


def upgrade():
    # 创建 company 表
    op.create_table(
        "company",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("contact_person", sa.String(length=100), nullable=True),
        sa.Column("contact_phone", sa.String(length=50), nullable=True),
        sa.Column("contact_email", sa.String(length=100), nullable=True),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )
    # 创建索引
    op.create_index(op.f("ix_company_code"), "company", ["code"], unique=True)
    op.create_index(op.f("ix_company_name"), "company", ["name"])
    
    # 在 user 表中添加 company_id 列
    op.add_column("user", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
    # 创建外键约束
    op.create_foreign_key(
        "fk_user_company_id",
        "user",
        "company",
        ["company_id"],
        ["id"],
        ondelete="SET NULL"
    )
    # 创建索引
    op.create_index(op.f("ix_user_company_id"), "user", ["company_id"])


def downgrade():
    # 删除 user 表中的 company_id 相关约束和索引
    op.drop_index(op.f("ix_user_company_id"), table_name="user")
    op.drop_constraint("fk_user_company_id", "user", type_="foreignkey")
    op.drop_column("user", "company_id")
    
    # 删除 company 表的索引和表
    op.drop_index(op.f("ix_company_name"), table_name="company")
    op.drop_index(op.f("ix_company_code"), table_name="company")
    op.drop_table("company")

