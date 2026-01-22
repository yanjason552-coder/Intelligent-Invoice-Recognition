"""create invoice recognition tables

Revision ID: create_invoice_tables_001
Revises: 1a31ce608336
Create Date: 2024-01-15 12:00:00.000000

"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "create_invoice_tables_001"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    # 创建票据文件表
    op.create_table(
        "invoice_file",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("upload_time", sa.DateTime(), nullable=False),
        sa.Column("uploader_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="uploaded"),
        sa.ForeignKeyConstraint(["uploader_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_invoice_file_file_name"), "invoice_file", ["file_name"])

    # 创建模板表
    op.create_table(
        "template",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("template_file_path", sa.String(length=500), nullable=True),
        sa.Column("sample_image_path", sa.String(length=500), nullable=True),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("training_samples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_training_time", sa.DateTime(), nullable=True),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.Column("update_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["creator_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_template_name"), "template", ["name"])

    # 创建模板字段表
    op.create_table(
        "template_field",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("field_code", sa.String(length=50), nullable=False),
        sa.Column("field_type", sa.String(length=20), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("position", postgresql.JSON(), nullable=True),
        sa.Column("validation_rules", postgresql.JSON(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("remark", sa.String(length=200), nullable=True),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["template.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建模板训练任务表
    op.create_table(
        "template_training_task",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_no", sa.String(length=100), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("training_samples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("training_data_path", sa.String(length=500), nullable=True),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("model_path", sa.String(length=500), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["template.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["operator_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_no"),
    )
    op.create_index(op.f("ix_template_training_task_task_no"), "template_training_task", ["task_no"], unique=True)

    # 创建票据表
    op.create_table(
        "invoice",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_no", sa.String(length=100), nullable=False),
        sa.Column("invoice_type", sa.String(length=50), nullable=False),
        sa.Column("invoice_date", sa.DateTime(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("tax_amount", sa.Float(), nullable=True),
        sa.Column("total_amount", sa.Float(), nullable=True),
        sa.Column("supplier_name", sa.String(length=200), nullable=True),
        sa.Column("supplier_tax_no", sa.String(length=50), nullable=True),
        sa.Column("buyer_name", sa.String(length=200), nullable=True),
        sa.Column("buyer_tax_no", sa.String(length=50), nullable=True),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recognition_accuracy", sa.Float(), nullable=True),
        sa.Column("recognition_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("review_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("review_time", sa.DateTime(), nullable=True),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("remark", sa.String(length=500), nullable=True),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.Column("update_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["file_id"], ["invoice_file.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["template.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["creator_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_invoice_invoice_no"), "invoice", ["invoice_no"])

    # 创建识别任务表
    op.create_table(
        "recognition_task",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_no", sa.String(length=100), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoice.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["template.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["operator_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_no"),
    )
    op.create_index(op.f("ix_recognition_task_task_no"), "recognition_task", ["task_no"], unique=True)

    # 创建识别结果表
    op.create_table(
        "recognition_result",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_fields", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recognized_fields", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accuracy", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="success"),
        sa.Column("raw_data", postgresql.JSON(), nullable=True),
        sa.Column("recognition_time", sa.DateTime(), nullable=False),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoice.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["recognition_task.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )

    # 创建识别字段表
    op.create_table(
        "recognition_field",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_field_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=False),
        sa.Column("field_value", sa.Text(), nullable=True),
        sa.Column("original_value", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=False),
        sa.Column("position", postgresql.JSON(), nullable=True),
        sa.Column("is_manual_corrected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("corrected_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("corrected_time", sa.DateTime(), nullable=True),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoice.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["result_id"], ["recognition_result.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_field_id"], ["template_field.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["corrected_by"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建审核记录表
    op.create_table(
        "review_record",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_status", sa.String(length=20), nullable=False),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_time", sa.DateTime(), nullable=False),
        sa.Column("review_details", postgresql.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoice.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建OCR配置表
    op.create_table(
        "ocr_config",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("config_key", sa.String(length=100), nullable=False),
        sa.Column("config_value", sa.Text(), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("update_time", sa.DateTime(), nullable=False),
        sa.Column("updater_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["updater_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("config_key"),
    )
    op.create_index(op.f("ix_ocr_config_config_key"), "ocr_config", ["config_key"], unique=True)

    # 创建识别规则表
    op.create_table(
        "recognition_rule",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_name", sa.String(length=100), nullable=False),
        sa.Column("rule_type", sa.String(length=50), nullable=False),
        sa.Column("rule_definition", postgresql.JSON(), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("field_name", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("remark", sa.String(length=200), nullable=True),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.Column("update_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["template_id"], ["template.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creator_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    # 删除所有表（按依赖关系逆序）
    op.drop_table("recognition_rule")
    op.drop_table("ocr_config")
    op.drop_table("review_record")
    op.drop_table("recognition_field")
    op.drop_table("recognition_result")
    op.drop_table("recognition_task")
    op.drop_table("invoice")
    op.drop_table("template_training_task")
    op.drop_table("template_field")
    op.drop_table("template")
    op.drop_table("invoice_file")


