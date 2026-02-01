"""add sample_file_path and sample_file_type to template table

Revision ID: add_sample_file_to_template_001
Revises: add_default_schema_id_to_template_001
Create Date: 2026-01-28 13:40:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_sample_file_to_template_001"
down_revision = "add_default_schema_id_to_template_001"
branch_labels = None
depends_on = None


def upgrade():
    # 在 template 表中添加 sample_file_path 和 sample_file_type 列
    op.add_column("template", sa.Column("sample_file_path", sa.String(length=500), nullable=True))
    op.add_column("template", sa.Column("sample_file_type", sa.String(length=50), nullable=True))


def downgrade():
    # 删除 sample_file_path 和 sample_file_type 列
    op.drop_column("template", "sample_file_type")
    op.drop_column("template", "sample_file_path")

