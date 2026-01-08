"""compat shim for missing revision in existing DB

Revision ID: add_permission_menu_fields
Revises: add_company_001
Create Date: 2026-01-07 11:00:00.000000

说明：
- 你的数据库 alembic_version 指向 add_permission_menu_fields，但当前代码库缺少该迁移脚本，导致无法 upgrade。
- 该迁移作为“占位/兼容”迁移，不做任何结构变更，只用于让迁移链闭合、继续后续迁移。
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_permission_menu_fields"
down_revision = "add_company_001"
branch_labels = None
depends_on = None


def upgrade():
    # no-op (compatibility shim)
    pass


def downgrade():
    # no-op
    pass






