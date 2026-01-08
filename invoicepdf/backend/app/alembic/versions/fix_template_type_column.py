"""fix template_type column

Revision ID: fix_template_type_001
Revises: add_template_management_001
Create Date: 2024-12-28 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "fix_template_type_001"
down_revision = "add_template_management_001"
branch_labels = None
depends_on = None

# 注意：此迁移与 template_version_001 形成分支，需要通过 merge_template_branches_001 合并


def upgrade():
    # 检查是否存在 type 列，如果存在则重命名为 template_type
    # 如果不存在 template_type 列，则添加它
    conn = op.get_bind()
    
    # 检查表是否存在
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'template'
        )
    """))
    table_exists = result.scalar()
    
    if not table_exists:
        # 表不存在，无需修复
        return
    
    # 检查列是否存在
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'template' 
        AND column_name IN ('type', 'template_type')
    """))
    
    existing_columns = [row[0] for row in result]
    
    if 'template_type' in existing_columns:
        # template_type 列已存在，确保索引存在
        try:
            op.create_index('ix_template_template_type', 'template', ['template_type'], unique=False, if_not_exists=True)
        except:
            # 索引可能已存在，忽略错误
            pass
    elif 'type' in existing_columns:
        # 存在 type 列，重命名为 template_type
        op.alter_column('template', 'type', new_column_name='template_type')
        # 确保索引存在
        try:
            op.create_index('ix_template_template_type', 'template', ['template_type'], unique=False, if_not_exists=True)
        except:
            # 索引可能已存在，忽略错误
            pass
    else:
        # 既没有 type 也没有 template_type，添加 template_type 列
        op.add_column('template', sa.Column('template_type', sa.String(length=50), nullable=False, server_default='其他'))
        try:
            op.create_index('ix_template_template_type', 'template', ['template_type'], unique=False, if_not_exists=True)
        except:
            pass


def downgrade():
    # 回滚操作：将 template_type 重命名为 type（如果需要）
    # 注意：这里不删除列，因为可能还有其他依赖
    pass

