"""create hole position record tables

Revision ID: create_hole_position_001
Revises: add_model_template_fields_001
Create Date: 2025-01-21 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "create_hole_position_001"
down_revision = "add_model_template_fields_001"
branch_labels = None
depends_on = None


def upgrade():
    # 创建孔位类记录表
    op.create_table(
        "hole_position_record",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("record_no", sa.String(length=100), nullable=False),
        sa.Column("doc_type", sa.String(length=100), nullable=True),
        sa.Column("form_title", sa.String(length=200), nullable=True),
        sa.Column("drawing_no", sa.String(length=100), nullable=True),
        sa.Column("part_name", sa.String(length=200), nullable=True),
        sa.Column("part_no", sa.String(length=100), nullable=True),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.Column("inspector_name", sa.String(length=100), nullable=True),
        sa.Column("overall_result", sa.String(length=20), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_name", sa.String(length=200), nullable=True),
        sa.Column("template_version", sa.String(length=50), nullable=True),
        sa.Column("model_name", sa.String(length=200), nullable=True),
        sa.Column("recognition_accuracy", sa.Float(), nullable=True),
        sa.Column("recognition_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("review_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("review_time", sa.DateTime(), nullable=True),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.Column("update_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["file_id"], ["invoice_file.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["creator_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["company.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_hole_position_record_record_no"), "hole_position_record", ["record_no"])

    # 创建孔位类行项目表
    op.create_table(
        "hole_position_item",
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_no", sa.Integer(), nullable=True),
        sa.Column("inspection_item", sa.String(length=500), nullable=True),
        sa.Column("spec_requirement", sa.String(length=500), nullable=True),
        sa.Column("actual_value", sa.String(length=500), nullable=True),
        sa.Column("actual", postgresql.JSON(), nullable=True),
        sa.Column("range_min", sa.Float(), nullable=True),
        sa.Column("range_max", sa.Float(), nullable=True),
        sa.Column("range_value", sa.String(length=200), nullable=True),
        sa.Column("judgement", sa.String(length=20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.Column("update_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["record_id"], ["hole_position_record.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("record_id", "item_no"),
    )


def downgrade():
    # 删除表（按依赖关系逆序）
    op.drop_table("hole_position_item")
    op.drop_table("hole_position_record")

