"""add model_name, template_name, template_version to invoice_file

Revision ID: add_model_template_fields_001
Revises: add_invoice_item_001
Create Date: 2025-01-20 16:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_model_template_fields_001"
down_revision = "add_invoice_item_001"
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
    op.drop_column('invoice_file', 'template_version')
    op.drop_column('invoice_file', 'template_name')
    op.drop_column('invoice_file', 'model_name')

