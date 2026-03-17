"""add prompt fields to template_version table

Revision ID: add_prompt_fields_to_template_version_001
Revises: add_sample_file_to_template_001
Create Date: 2026-01-28 14:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_prompt_fields_to_template_version_001"
down_revision = "add_sample_file_to_template_001"
branch_labels = None
depends_on = None


def upgrade():
    # 添加提示词管理相关字段到 template_version 表
    op.add_column('template_version', sa.Column('prompt', sa.Text(), nullable=True))
    op.add_column('template_version', sa.Column('prompt_status', sa.String(length=20), nullable=True))
    op.add_column('template_version', sa.Column('prompt_updated_at', sa.DateTime(), nullable=True))
    op.add_column('template_version', sa.Column('prompt_hash', sa.String(length=64), nullable=True))
    op.add_column('template_version', sa.Column('prompt_previous_version', sa.Text(), nullable=True))


def downgrade():
    # 删除提示词管理相关字段
    op.drop_column('template_version', 'prompt_previous_version')
    op.drop_column('template_version', 'prompt_hash')
    op.drop_column('template_version', 'prompt_updated_at')
    op.drop_column('template_version', 'prompt_status')
    op.drop_column('template_version', 'prompt')

