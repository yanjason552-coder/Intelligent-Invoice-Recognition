"""add llm config table

Revision ID: add_llm_config_001
Revises: add_dify_fields_001
Create Date: 2024-12-20 15:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_llm_config_001"
down_revision = "add_dify_fields_001"
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建llm_config表
    op.create_table(
        'llm_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('endpoint', sa.String(length=500), nullable=False),
        sa.Column('api_key', sa.String(length=200), nullable=False),
        sa.Column('app_id', sa.String(length=100), nullable=True),
        sa.Column('workflow_id', sa.String(length=100), nullable=True),
        sa.Column('app_type', sa.String(length=20), nullable=False, server_default='workflow'),
        sa.Column('timeout', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.Column('update_time', sa.DateTime(), nullable=True),
        sa.Column('updater_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updater_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_llm_config_name'), 'llm_config', ['name'], unique=True)
    
    # 2. 为model_config表添加syntax相关字段（兼容旧dify字段）
    op.add_column('model_config', sa.Column('syntax_endpoint', sa.String(length=500), nullable=True))
    op.add_column('model_config', sa.Column('syntax_api_key', sa.String(length=200), nullable=True))
    op.add_column('model_config', sa.Column('syntax_app_id', sa.String(length=100), nullable=True))
    op.add_column('model_config', sa.Column('syntax_workflow_id', sa.String(length=100), nullable=True))
    
    # 3. 更新provider默认值为syntax
    op.execute("UPDATE model_config SET provider = 'syntax' WHERE provider = 'dify' OR provider IS NULL")


def downgrade():
    # 删除syntax字段
    op.drop_column('model_config', 'syntax_workflow_id')
    op.drop_column('model_config', 'syntax_app_id')
    op.drop_column('model_config', 'syntax_api_key')
    op.drop_column('model_config', 'syntax_endpoint')
    
    # 删除llm_config表
    op.drop_index(op.f('ix_llm_config_name'), table_name='llm_config')
    op.drop_table('llm_config')

