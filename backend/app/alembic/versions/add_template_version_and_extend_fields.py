"""add template version and extend fields

Revision ID: template_version_001
Revises: add_dify_fields_001
Create Date: 2024-12-20 15:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "template_version_001"
down_revision = "add_dify_fields_001"
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建template_version表
    op.create_table(
        'template_version',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('deprecated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['template.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['user.id']),
        sa.UniqueConstraint('template_id', 'version', name='uq_template_version')
    )
    op.create_index('ix_template_version_template_id', 'template_version', ['template_id'])
    op.create_index('ix_template_version_version', 'template_version', ['version'])
    
    # 2. 修改template表，添加current_version_id字段
    op.add_column('template', sa.Column('current_version_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_template_current_version_id',
        'template', 'template_version',
        ['current_version_id'], ['id']
    )
    
    # 3. 扩展template_field表
    # 添加template_version_id字段
    op.add_column('template_field', sa.Column('template_version_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_template_field_version_id',
        'template_field', 'template_version',
        ['template_version_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 添加新字段属性
    op.add_column('template_field', sa.Column('field_key', sa.String(length=100), nullable=True))
    op.add_column('template_field', sa.Column('data_type', sa.String(length=50), nullable=True))
    op.add_column('template_field', sa.Column('required', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('template_field', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('template_field', sa.Column('example', sa.String(length=200), nullable=True))
    op.add_column('template_field', sa.Column('default_value', sa.Text(), nullable=True))
    op.add_column('template_field', sa.Column('validation', postgresql.JSON(), nullable=True))
    op.add_column('template_field', sa.Column('normalize', postgresql.JSON(), nullable=True))
    op.add_column('template_field', sa.Column('prompt_hint', sa.Text(), nullable=True))
    op.add_column('template_field', sa.Column('confidence_threshold', sa.Float(), nullable=True))
    op.add_column('template_field', sa.Column('canonical_field', sa.String(length=100), nullable=True))
    # 注意：不使用sub_fields JSON字段，改用parent_field_id关系建模嵌套字段
    op.add_column('template_field', sa.Column('parent_field_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('template_field', sa.Column('deprecated', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('template_field', sa.Column('deprecated_at', sa.DateTime(), nullable=True))
    op.add_column('template_field', sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'))
    
    # 添加外键约束
    op.create_foreign_key(
        'fk_template_field_parent_id',
        'template_field', 'template_field',
        ['parent_field_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 迁移旧数据：将field_code复制到field_key，field_type复制到data_type
    op.execute("""
        UPDATE template_field 
        SET field_key = field_code,
            data_type = field_type,
            required = is_required,
            sort_order = display_order
        WHERE field_key IS NULL
    """)
    
    # 为template_version表添加新字段
    # schema_snapshot 使用 JSONB 类型，支持结构化、嵌套数据，且不需要频繁 JOIN
    op.add_column('template_version', sa.Column('schema_snapshot', postgresql.JSONB(), nullable=True))
    op.add_column('template_version', sa.Column('etag', sa.String(length=50), nullable=True))
    op.add_column('template_version', sa.Column('locked_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('template_version', sa.Column('locked_at', sa.DateTime(), nullable=True))
    
    # 添加外键约束
    op.create_foreign_key(
        'fk_template_version_locked_by',
        'template_version', 'user',
        ['locked_by'], ['id']
    )


def downgrade():
    # 删除template_version表的新字段
    op.drop_constraint('fk_template_version_locked_by', 'template_version', type_='foreignkey')
    op.drop_column('template_version', 'locked_at')
    op.drop_column('template_version', 'locked_by')
    op.drop_column('template_version', 'etag')
    op.drop_column('template_version', 'schema_snapshot')
    
    # 删除template_field的新字段
    op.drop_constraint('fk_template_field_parent_id', 'template_field', type_='foreignkey')
    op.drop_column('template_field', 'deprecated_at')
    op.drop_column('template_field', 'deprecated')
    op.drop_column('template_field', 'parent_field_id')
    op.drop_column('template_field', 'sort_order')
    op.drop_column('template_field', 'canonical_field')
    op.drop_column('template_field', 'confidence_threshold')
    op.drop_column('template_field', 'prompt_hint')
    op.drop_column('template_field', 'normalize')
    op.drop_column('template_field', 'validation')
    op.drop_column('template_field', 'default_value')
    op.drop_column('template_field', 'example')
    op.drop_column('template_field', 'description')
    op.drop_column('template_field', 'required')
    op.drop_column('template_field', 'data_type')
    op.drop_column('template_field', 'field_key')
    
    # 删除外键和字段
    op.drop_constraint('fk_template_field_version_id', 'template_field', type_='foreignkey')
    op.drop_column('template_field', 'template_version_id')
    
    # 删除template表的current_version_id
    op.drop_constraint('fk_template_current_version_id', 'template', type_='foreignkey')
    op.drop_column('template', 'current_version_id')
    
    # 删除template_version表
    op.drop_index('ix_template_version_version', table_name='template_version')
    op.drop_index('ix_template_version_template_id', table_name='template_version')
    op.drop_table('template_version')

