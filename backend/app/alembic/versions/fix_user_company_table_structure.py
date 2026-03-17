"""fix user_company table structure

Revision ID: fix_user_company_structure_001
Revises: merge_heads_20260313
Create Date: 2026-03-13 11:00:00.000000

说明：
- 修复 user_company 表结构，添加缺失的 id, is_primary, create_time 列
- 如果表已存在但结构不完整，则添加缺失的列
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "fix_user_company_structure_001"
down_revision = "merge_heads_20260313"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # 检查表是否存在
    tables = inspector.get_table_names()
    if 'user_company' not in tables:
        # 如果表不存在，创建完整的表结构
        op.create_table(
            "user_company",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("create_time", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["company_id"], ["company.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        
        # 创建索引
        op.create_index(
            "ix_user_company_user_company",
            "user_company",
            ["user_id", "company_id"],
            unique=True
        )
        op.create_index("ix_user_company_user_id", "user_company", ["user_id"])
        op.create_index("ix_user_company_company_id", "user_company", ["company_id"])
    else:
        # 表已存在，检查并添加缺失的列
        columns = [col['name'] for col in inspector.get_columns('user_company')]
        
        # 添加 id 列（如果不存在）
        if 'id' not in columns:
            # 首先检查是否有主键约束
            pk_constraint = None
            for constraint in inspector.get_pk_constraint('user_company')['constrained_columns']:
                pk_constraint = constraint
                break
            
            # 如果存在复合主键或其他主键，先删除
            if pk_constraint:
                op.execute("ALTER TABLE user_company DROP CONSTRAINT IF EXISTS user_company_pkey")
            
            # 添加 id 列
            op.execute("""
                ALTER TABLE user_company 
                ADD COLUMN id UUID DEFAULT gen_random_uuid()
            """)
            
            # 更新现有记录的 id
            op.execute("""
                UPDATE user_company 
                SET id = gen_random_uuid() 
                WHERE id IS NULL
            """)
            
            # 设置 id 为 NOT NULL
            op.execute("ALTER TABLE user_company ALTER COLUMN id SET NOT NULL")
            
            # 设置 id 为主键
            op.execute("ALTER TABLE user_company ADD PRIMARY KEY (id)")
        
        # 添加 is_primary 列（如果不存在）
        if 'is_primary' not in columns:
            op.execute("""
                ALTER TABLE user_company 
                ADD COLUMN is_primary BOOLEAN NOT NULL DEFAULT false
            """)
        
        # 添加 create_time 列（如果不存在）
        if 'create_time' not in columns:
            # 如果有 created_at 列，重命名它
            if 'created_at' in columns:
                op.execute("ALTER TABLE user_company RENAME COLUMN created_at TO create_time")
            else:
                op.execute("""
                    ALTER TABLE user_company 
                    ADD COLUMN create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                """)
        
        # 创建唯一索引（如果不存在）
        indexes = [idx['name'] for idx in inspector.get_indexes('user_company')]
        if 'ix_user_company_user_company' not in indexes:
            op.create_index(
                "ix_user_company_user_company",
                "user_company",
                ["user_id", "company_id"],
                unique=True
            )
        
        # 创建其他索引（如果不存在）
        if 'ix_user_company_user_id' not in indexes:
            op.create_index("ix_user_company_user_id", "user_company", ["user_id"])
        if 'ix_user_company_company_id' not in indexes:
            op.create_index("ix_user_company_company_id", "user_company", ["company_id"])


def downgrade():
    # 回滚：删除添加的列（保留原有结构）
    op.execute("ALTER TABLE user_company DROP COLUMN IF EXISTS id")
    op.execute("ALTER TABLE user_company DROP COLUMN IF EXISTS is_primary")
    # 如果 create_time 是从 created_at 重命名来的，恢复原名
    op.execute("ALTER TABLE user_company DROP COLUMN IF EXISTS create_time")
    
    # 删除索引
    op.drop_index("ix_user_company_company_id", table_name="user_company", if_exists=True)
    op.drop_index("ix_user_company_user_id", table_name="user_company", if_exists=True)
    op.drop_index("ix_user_company_user_company", table_name="user_company", if_exists=True)
