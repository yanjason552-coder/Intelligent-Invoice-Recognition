"""add template version snapshot fields to recognition tables

Revision ID: add_template_snapshot_001
Revises: add_dify_fields_001
Create Date: 2024-12-25 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_template_snapshot_001"
down_revision = "add_dify_fields_001"  # 基于最新的迁移
branch_labels = None
depends_on = None


def upgrade():
    # 1. 修改recognition_task表
    # 添加template_version_id字段（识别时使用的模板版本ID）
    op.add_column(
        'recognition_task',
        sa.Column('template_version_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    # 添加外键约束
    op.create_foreign_key(
        'fk_recognition_task_template_version_id',
        'recognition_task',
        'template_version',
        ['template_version_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # 2. 修改recognition_result表
    # 添加模板版本快照字段（用于审核页按版本展示字段）
    
    # 添加template_version_id字段（识别时使用的模板版本ID）
    op.add_column(
        'recognition_result',
        sa.Column('template_version_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    # 添加外键约束
    op.create_foreign_key(
        'fk_recognition_result_template_version_id',
        'recognition_result',
        'template_version',
        ['template_version_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # 添加prompt_snapshot字段（识别时使用的提示词快照）
    op.add_column(
        'recognition_result',
        sa.Column('prompt_snapshot', sa.Text(), nullable=True)
    )
    
    # 添加schema_snapshot字段（识别时使用的Schema快照）
    op.add_column(
        'recognition_result',
        sa.Column('schema_snapshot', postgresql.JSONB(), nullable=True)
    )
    
    # 添加field_defs_snapshot字段（识别时的字段定义快照，用于审核页展示）
    op.add_column(
        'recognition_result',
        sa.Column('field_defs_snapshot', postgresql.JSONB(), nullable=True)
    )


def downgrade():
    # 删除recognition_result表的字段
    op.drop_column('recognition_result', 'field_defs_snapshot')
    op.drop_column('recognition_result', 'schema_snapshot')
    op.drop_column('recognition_result', 'prompt_snapshot')
    op.drop_constraint('fk_recognition_result_template_version_id', 'recognition_result', type_='foreignkey')
    op.drop_column('recognition_result', 'template_version_id')
    
    # 删除recognition_task表的字段
    op.drop_constraint('fk_recognition_task_template_version_id', 'recognition_task', type_='foreignkey')
    op.drop_column('recognition_task', 'template_version_id')

