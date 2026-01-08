"""merge template branches

Revision ID: merge_template_branches_001
Revises: ('fix_template_type_001', 'template_version_001')
Create Date: 2024-12-28 13:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "merge_template_branches_001"
down_revision = ("fix_template_type_001", "template_version_001")
branch_labels = None
depends_on = None


def upgrade():
    # 这是一个合并迁移，不需要执行任何操作
    # 两个分支的迁移已经各自完成了表的创建和修改
    pass


def downgrade():
    # 回滚时也不需要操作
    pass

