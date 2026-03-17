"""merge_all_heads

Revision ID: b08db22e3948
Revises: add_data_name_001, add_prompt_fields_to_template_version_001, add_template_snapshot_001, create_hole_position_001, fix_invoice_company_id_type_001
Create Date: 2026-02-06 10:34:06.327158

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'b08db22e3948'
down_revision = ('add_data_name_001', 'add_prompt_fields_to_template_version_001', 'add_template_snapshot_001', 'create_hole_position_001', 'fix_invoice_company_id_type_001')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
