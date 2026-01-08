"""add_file_hash_to_invoice_file

Revision ID: 11367c892248
Revises: merge_001
Create Date: 2025-12-27 11:47:28.913854

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '11367c892248'
down_revision = 'merge_001'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 file_hash 字段到 invoice_file 表
    op.add_column(
        'invoice_file',
        sa.Column('file_hash', sa.String(length=64), nullable=True)
    )
    
    # 创建索引以提高查询性能
    op.create_index(
        op.f('ix_invoice_file_file_hash'),
        'invoice_file',
        ['file_hash']
    )


def downgrade():
    # 删除索引
    op.drop_index(op.f('ix_invoice_file_file_hash'), table_name='invoice_file')
    
    # 删除 file_hash 字段
    op.drop_column('invoice_file', 'file_hash')
