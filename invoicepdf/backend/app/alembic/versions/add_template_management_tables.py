"""add template management tables

Revision ID: add_template_management_001
Revises: add_llm_config_001
Create Date: 2024-12-20 16:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_template_management_001"
down_revision = "add_llm_config_001"
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建template表（先不添加current_version_id外键，避免循环依赖）
    op.create_table(
        'template',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='enabled'),
        sa.Column('current_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.Column('update_time', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_template_name'), 'template', ['name'], unique=False)
    op.create_index(op.f('ix_template_template_type'), 'template', ['template_type'], unique=False)
    
    # 2. 创建template_version表
    op.create_table(
        'template_version',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('schema_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('etag', sa.String(length=100), nullable=True),
        sa.Column('locked_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('locked_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('deprecated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['template.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['locked_by'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_template_version_version'), 'template_version', ['version'], unique=False)
    op.create_index(op.f('ix_template_version_template_id'), 'template_version', ['template_id'], unique=False)
    
    # 3. 添加template表的current_version_id外键约束（现在template_version表已存在）
    op.create_foreign_key(
        'fk_template_current_version_id',
        'template', 'template_version',
        ['current_version_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # 4. 创建template_field表
    op.create_table(
        'template_field',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_key', sa.String(length=100), nullable=False),
        sa.Column('field_name', sa.String(length=200), nullable=False),
        sa.Column('data_type', sa.String(length=50), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('example', sa.Text(), nullable=True),
        sa.Column('validation', postgresql.JSON(), nullable=True),
        sa.Column('validation_rules', postgresql.JSON(), nullable=True),
        sa.Column('normalize', postgresql.JSON(), nullable=True),
        sa.Column('prompt_hint', sa.Text(), nullable=True),
        sa.Column('confidence_threshold', sa.Float(), nullable=True),
        sa.Column('canonical_field', sa.String(length=100), nullable=True),
        sa.Column('parent_field_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deprecated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deprecated_at', sa.DateTime(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['template.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_version_id'], ['template_version.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_field_id'], ['template_field.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_template_field_field_key'), 'template_field', ['field_key'], unique=False)
    op.create_index(op.f('ix_template_field_template_id'), 'template_field', ['template_id'], unique=False)
    op.create_index(op.f('ix_template_field_template_version_id'), 'template_field', ['template_version_id'], unique=False)
    
    # 5. 为invoice表添加template_version_id字段
    op.add_column('invoice', sa.Column('template_version_id', postgresql.UUID(as_uuid=True), nullable=True))


def downgrade():
    # 删除字段
    op.drop_column('invoice', 'template_version_id')
    
    # 删除外键约束
    op.drop_constraint('fk_template_current_version_id', 'template', type_='foreignkey')
    
    # 删除表
    op.drop_index(op.f('ix_template_field_template_version_id'), table_name='template_field')
    op.drop_index(op.f('ix_template_field_template_id'), table_name='template_field')
    op.drop_index(op.f('ix_template_field_field_key'), table_name='template_field')
    op.drop_table('template_field')
    
    op.drop_index(op.f('ix_template_version_template_id'), table_name='template_version')
    op.drop_index(op.f('ix_template_version_version'), table_name='template_version')
    op.drop_table('template_version')
    
    op.drop_index(op.f('ix_template_template_type'), table_name='template')
    op.drop_index(op.f('ix_template_name'), table_name='template')
    op.drop_table('template')

