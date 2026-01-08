"""merge invoice and material migration branches

Revision ID: merge_001
Revises: create_invoice_tables_001, remove_material_fk
Create Date: 2024-01-15 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_001'
down_revision = ('create_invoice_tables_001', 'remove_material_fk')
branch_labels = None
depends_on = None


def upgrade():
    """
    合并迁移分支
    这个迁移不需要执行任何数据库操作，只是将两个分支合并在一起
    """
    pass


def downgrade():
    """
    回滚合并迁移
    """
    pass


