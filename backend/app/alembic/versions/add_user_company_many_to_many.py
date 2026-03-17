"""add user company many to many relationship

Revision ID: add_user_company_m2m_001
Revises: add_company_table_and_user_company_id
Create Date: 2025-03-12 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_user_company_m2m_001"
down_revision = "add_company_001"  # 基于 add_company_table_and_user_company_id.py 的 revision (revision = "add_company_001")
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建用户公司关联表（多对多关系）
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
    
    # 创建唯一索引：确保一个用户不能重复关联同一个公司
    op.create_index(
        "ix_user_company_user_company",
        "user_company",
        ["user_id", "company_id"],
        unique=True
    )
    
    # 创建索引：便于查询用户的所有公司
    op.create_index(
        "ix_user_company_user_id",
        "user_company",
        ["user_id"]
    )
    
    # 创建索引：便于查询公司的所有用户
    op.create_index(
        "ix_user_company_company_id",
        "user_company",
        ["company_id"]
    )
    
    # 2. 迁移现有数据：将 user.company_id 迁移到 user_company 表
    # 首先检查是否有 company_id 字段
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('user')]
    
    if 'company_id' in columns:
        # 迁移现有数据
        op.execute("""
            INSERT INTO user_company (id, user_id, company_id, is_primary, create_time)
            SELECT 
                gen_random_uuid(),
                id,
                company_id,
                true,
                create_time
            FROM "user"
            WHERE company_id IS NOT NULL
        """)
        
        # 3. 删除 user 表的 company_id 字段（可选，保留字段以便兼容）
        # 注意：为了向后兼容，我们先不删除 company_id 字段
        # 如果确定不需要，可以在后续迁移中删除
        # op.drop_column('user', 'company_id')


def downgrade():
    # 删除索引
    op.drop_index("ix_user_company_company_id", table_name="user_company")
    op.drop_index("ix_user_company_user_id", table_name="user_company")
    op.drop_index("ix_user_company_user_company", table_name="user_company")
    
    # 删除表
    op.drop_table("user_company")
