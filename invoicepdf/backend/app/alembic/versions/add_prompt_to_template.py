"""add prompt to template

Revision ID: add_prompt_to_template
Revises: 
Create Date: 2026-01-27 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_prompt_to_template'
down_revision = 'add_default_schema_id_to_template_001'  # 基于最新的模板相关迁移
branch_labels = None
depends_on = None


def upgrade():
    # 添加 prompt 字段到 template 表
    op.add_column('template', sa.Column('prompt', sa.Text(), nullable=True))


def downgrade():
    # 删除 prompt 字段
    op.drop_column('template', 'prompt')

