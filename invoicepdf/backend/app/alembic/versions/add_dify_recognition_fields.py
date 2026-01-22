"""add dify recognition fields

Revision ID: add_dify_fields_001
Revises: create_invoice_tables_001
Create Date: 2024-12-20 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_dify_fields_001"
down_revision = "11367c892248"  # 基于最新的迁移
branch_labels = None
depends_on = None


def upgrade():
    # 1. 修改recognition_task表
    # 添加params字段
    op.add_column('recognition_task', sa.Column('params', postgresql.JSON(), nullable=True))
    
    # 修改template_id为可空
    op.alter_column('recognition_task', 'template_id', nullable=True)
    
    # 添加Dify相关字段
    op.add_column('recognition_task', sa.Column('provider', sa.String(length=50), nullable=False, server_default='dify'))
    op.add_column('recognition_task', sa.Column('request_id', sa.String(length=100), nullable=True))
    op.add_column('recognition_task', sa.Column('trace_id', sa.String(length=100), nullable=True))
    op.add_column('recognition_task', sa.Column('error_code', sa.String(length=50), nullable=True))
    
    # 添加request_id索引
    op.create_index(op.f('ix_recognition_task_request_id'), 'recognition_task', ['request_id'], unique=False)
    
    # 2. 修改recognition_result表
    # 添加Dify相关字段
    op.add_column('recognition_result', sa.Column('raw_payload', sa.Text(), nullable=True))
    op.add_column('recognition_result', sa.Column('raw_response_uri', sa.String(length=500), nullable=True))
    op.add_column('recognition_result', sa.Column('normalized_fields', postgresql.JSON(), nullable=True))
    op.add_column('recognition_result', sa.Column('model_usage', postgresql.JSON(), nullable=True))
    
    # 3. 创建output_schema表（必须在model_config之前，因为model_config有外键引用）
    op.create_table(
        'output_schema',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False, server_default='1.0.0'),
        sa.Column('schema_definition', postgresql.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.Column('update_time', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_output_schema_name'), 'output_schema', ['name'], unique=False)
    
    # 4. 创建model_config表
    op.create_table(
        'model_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='dify'),
        sa.Column('dify_endpoint', sa.String(length=500), nullable=True),
        sa.Column('dify_api_key', sa.String(length=200), nullable=True),
        sa.Column('dify_app_id', sa.String(length=100), nullable=True),
        sa.Column('dify_workflow_id', sa.String(length=100), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('cost_level', sa.String(length=20), nullable=False, server_default='standard'),
        sa.Column('default_mode', sa.String(length=50), nullable=False, server_default='llm_extract'),
        sa.Column('allowed_modes', postgresql.JSON(), nullable=True),
        sa.Column('default_schema_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('allowed_user_ids', postgresql.JSON(), nullable=True),
        sa.Column('allowed_role_ids', postgresql.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.Column('update_time', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['default_schema_id'], ['output_schema.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_model_config_name'), 'model_config', ['name'], unique=False)


def downgrade():
    # 删除表
    op.drop_index(op.f('ix_output_schema_name'), table_name='output_schema')
    op.drop_table('output_schema')
    op.drop_index(op.f('ix_model_config_name'), table_name='model_config')
    op.drop_table('model_config')
    
    # 删除recognition_result字段
    op.drop_column('recognition_result', 'model_usage')
    op.drop_column('recognition_result', 'normalized_fields')
    op.drop_column('recognition_result', 'raw_response_uri')
    op.drop_column('recognition_result', 'raw_payload')
    
    # 删除recognition_task字段
    op.drop_index(op.f('ix_recognition_task_request_id'), table_name='recognition_task')
    op.drop_column('recognition_task', 'error_code')
    op.drop_column('recognition_task', 'trace_id')
    op.drop_column('recognition_task', 'request_id')
    op.drop_column('recognition_task', 'provider')
    op.drop_column('recognition_task', 'params')
    
    # 恢复template_id为不可空（注意：这可能导致数据问题，实际使用时需要先清理数据）
    # op.alter_column('recognition_task', 'template_id', nullable=False)

