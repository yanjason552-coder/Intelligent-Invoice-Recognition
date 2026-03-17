"""add data_name to template_field

Revision ID: add_data_name_001
Revises: template_version_001
Create Date: 2025-02-04 16:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_data_name_001"
down_revision = "template_version_001"  # 需要根据实际情况调整
branch_labels = None
depends_on = None


def upgrade():
    # 添加 data_name 字段到 template_field 表
    op.add_column('template_field', sa.Column('data_name', sa.String(length=100), nullable=True))


def downgrade():
    # 删除 data_name 字段
    op.drop_column('template_field', 'data_name')

