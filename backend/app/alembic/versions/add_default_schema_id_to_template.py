"""add default_schema_id to template table

Revision ID: add_default_schema_id_to_template_001
Revises: add_template_management_001
Create Date: 2024-12-31 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_default_schema_id_to_template_001"
down_revision = "add_template_management_001"
branch_labels = None
depends_on = None


def upgrade():
    # 在 template 表中添加 default_schema_id 列
    op.add_column("template", sa.Column("default_schema_id", postgresql.UUID(as_uuid=True), nullable=True))
    
    # 创建外键约束
    op.create_foreign_key(
        "fk_template_default_schema_id",
        "template",
        "output_schema",
        ["default_schema_id"],
        ["id"],
        ondelete="SET NULL"
    )
    
    # 创建索引
    op.create_index(op.f("ix_template_default_schema_id"), "template", ["default_schema_id"])


def downgrade():
    # 删除索引
    op.drop_index(op.f("ix_template_default_schema_id"), table_name="template")
    
    # 删除外键约束
    op.drop_constraint("fk_template_default_schema_id", "template", type_="foreignkey")
    
    # 删除 default_schema_id 列
    op.drop_column("template", "default_schema_id")

