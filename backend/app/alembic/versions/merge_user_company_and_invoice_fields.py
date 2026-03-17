"""merge user company m2m and invoice fields heads

Revision ID: merge_heads_20260313
Revises: ('add_invoice_file_fields_safe_001', 'add_inv_tpl_ver_id_002', 'add_user_company_m2m_001')
Create Date: 2026-03-13 10:00:00.000000

说明：
- 合并三个head revisions：
  1. add_invoice_file_fields_safe_001 (invoice_file表的model_name等字段)
  2. add_inv_tpl_ver_id_002 (invoice表的template_version_id字段)
  3. add_user_company_m2m_001 (user_company多对多关系表)
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "merge_heads_20260313"
down_revision = ("add_invoice_file_fields_safe_001", "add_inv_tpl_ver_id_002", "add_user_company_m2m_001")
branch_labels = None
depends_on = None


def upgrade():
    # 这是一个合并迁移，所有实际的更改已经在各自的迁移文件中完成
    # 这里不需要做任何操作，只是合并迁移链
    pass


def downgrade():
    # 合并迁移的回滚也不需要操作
    pass
