"""add invoice_file model_name, template_name, template_version columns (safe)

Revision ID: add_invoice_file_fields_safe_001
Revises: b08db22e3948
Create Date: 2026-02-06 12:00:00.000000

说明：
- 为 invoice_file 表添加 model_name, template_name, template_version 字段
- 使用 IF NOT EXISTS 保证可重复执行，避免字段已存在时报错
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "add_invoice_file_fields_safe_001"
down_revision = "b08db22e3948"
branch_labels = None
depends_on = None


def upgrade():
    # 为 invoice_file 表添加模型和模板相关字段（使用 IF NOT EXISTS 保证可重复执行）
    op.execute(
        """
        ALTER TABLE invoice_file
        ADD COLUMN IF NOT EXISTS model_name VARCHAR(200) NULL;
        """
    )
    op.execute(
        """
        ALTER TABLE invoice_file
        ADD COLUMN IF NOT EXISTS template_name VARCHAR(200) NULL;
        """
    )
    op.execute(
        """
        ALTER TABLE invoice_file
        ADD COLUMN IF NOT EXISTS template_version VARCHAR(50) NULL;
        """
    )


def downgrade():
    # 删除添加的字段
    op.execute(
        """
        ALTER TABLE invoice_file
        DROP COLUMN IF EXISTS template_version;
        """
    )
    op.execute(
        """
        ALTER TABLE invoice_file
        DROP COLUMN IF EXISTS template_name;
        """
    )
    op.execute(
        """
        ALTER TABLE invoice_file
        DROP COLUMN IF EXISTS model_name;
        """
    )
