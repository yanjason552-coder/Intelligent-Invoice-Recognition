"""fix invoice_item primary key to composite

Revision ID: fix_invoice_item_pk_001
Revises: add_company_001
Create Date: 2026-01-07 10:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fix_invoice_item_pk_001"
down_revision = "add_permission_menu_fields"
branch_labels = None
depends_on = None


def upgrade():
    # 运行时证据表明当前数据库里 invoice_item_pkey 仅约束了 id，导致同一发票无法保存多行项目。
    # 这里将主键修正为 (id, invoice_no, line_no) 的复合主键。
    op.drop_constraint("invoice_item_pkey", "invoice_item", type_="primary")
    op.create_primary_key("invoice_item_pkey", "invoice_item", ["id", "invoice_no", "line_no"])


def downgrade():
    # 回滚为单列主键（不推荐，仅用于兼容回滚）
    op.drop_constraint("invoice_item_pkey", "invoice_item", type_="primary")
    op.create_primary_key("invoice_item_pkey", "invoice_item", ["id"])


