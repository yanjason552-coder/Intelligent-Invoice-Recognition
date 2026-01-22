"""add external_file_id to invoice_file

Revision ID: add_external_file_id_001
Revises: add_llm_config_001
Create Date: 2024-12-20 16:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_external_file_id_001"
down_revision = "add_llm_config_001"
branch_labels = None
depends_on = None


def upgrade():
    # 为 invoice_file 表添加 external_file_id 字段
    op.add_column('invoice_file', sa.Column('external_file_id', sa.String(length=100), nullable=True))


def downgrade():
    # 删除 external_file_id 字段
    op.drop_column('invoice_file', 'external_file_id')

