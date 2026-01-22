"""add invoice.template_version_id column (hotfix)

Revision ID: add_inv_tpl_ver_id_002
Revises: fix_invoice_item_pk_001
Create Date: 2026-01-07

说明：
- 代码侧已开始读取 invoice.template_version_id，但部分数据库迁移链的 head 停在 fix_invoice_item_pk_001，
  导致 invoice 表缺少该列，从而 /api/v1/invoices/query 直接 500。
- 本迁移从当前 head 接上去，补齐 invoice.template_version_id，并添加外键到 template_version.id。
- 使用 Postgres 的 IF NOT EXISTS/异常捕获，保证可重复执行，避免某些环境已存在该列/约束时报错。
"""

from alembic import op


# revision identifiers, used by Alembic.
# 注意：部分环境的 alembic_version.version_num 是 VARCHAR(32)，revision 字符串不能超过 32 字符。
revision = "add_inv_tpl_ver_id_002"
down_revision = "fix_invoice_item_pk_001"
branch_labels = None
depends_on = None


def upgrade():
    # 1) 加列（若不存在）
    op.execute(
        """
        ALTER TABLE invoice
        ADD COLUMN IF NOT EXISTS template_version_id UUID NULL;
        """
    )

    # 2) 加外键（若不存在）
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_invoice_template_version_id'
            ) THEN
                ALTER TABLE invoice
                ADD CONSTRAINT fk_invoice_template_version_id
                FOREIGN KEY (template_version_id)
                REFERENCES template_version (id)
                ON DELETE SET NULL;
            END IF;
        END $$;
        """
    )


def downgrade():
    # 回滚：先删外键再删列
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_invoice_template_version_id'
            ) THEN
                ALTER TABLE invoice DROP CONSTRAINT fk_invoice_template_version_id;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        ALTER TABLE invoice
        DROP COLUMN IF EXISTS template_version_id;
        """
    )


