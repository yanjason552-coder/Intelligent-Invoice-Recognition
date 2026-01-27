"""fix invoice company_id type from bigint to uuid

Revision ID: fix_invoice_company_id_type_001
Revises: add_company_id_to_invoice_001
Create Date: 2026-01-26 17:20:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "fix_invoice_company_id_type_001"
down_revision = "add_company_id_to_invoice_001"
branch_labels = None
depends_on = None


def upgrade():
    """
    修复 invoice.company_id 列类型：从 bigint 改为 UUID
    """
    # 检查列是否存在
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT data_type 
        FROM information_schema.columns 
        WHERE table_name = 'invoice' 
        AND column_name = 'company_id'
    """))
    
    row = result.fetchone()
    if row:
        current_type = row[0]
        
        # 如果当前类型是 bigint，需要修复
        if current_type == 'bigint':
            # 1. 删除外键约束（如果存在）
            try:
                op.drop_constraint("fk_invoice_company_id", "invoice", type_="foreignkey")
            except Exception:
                pass  # 约束可能不存在
            
            # 2. 删除索引（如果存在）
            try:
                op.drop_index("ix_invoice_company_id", table_name="invoice")
            except Exception:
                pass  # 索引可能不存在
            
            # 3. 删除旧列
            op.drop_column("invoice", "company_id")
            
            # 4. 重新创建 UUID 类型的列
            op.add_column("invoice", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
            
            # 5. 创建外键约束
            op.create_foreign_key(
                "fk_invoice_company_id",
                "invoice",
                "company",
                ["company_id"],
                ["id"],
                ondelete="SET NULL"
            )
            
            # 6. 创建索引
            op.create_index(op.f("ix_invoice_company_id"), "invoice", ["company_id"])
        elif current_type == 'uuid':
            # 已经是 UUID 类型，不需要修改
            pass
        else:
            # 其他类型，也需要修复
            try:
                op.drop_constraint("fk_invoice_company_id", "invoice", type_="foreignkey")
            except Exception:
                pass
            try:
                op.drop_index("ix_invoice_company_id", table_name="invoice")
            except Exception:
                pass
            op.drop_column("invoice", "company_id")
            op.add_column("invoice", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
            op.create_foreign_key(
                "fk_invoice_company_id",
                "invoice",
                "company",
                ["company_id"],
                ["id"],
                ondelete="SET NULL"
            )
            op.create_index(op.f("ix_invoice_company_id"), "invoice", ["company_id"])
    else:
        # 列不存在，直接创建
        op.add_column("invoice", sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            "fk_invoice_company_id",
            "invoice",
            "company",
            ["company_id"],
            ["id"],
            ondelete="SET NULL"
        )
        op.create_index(op.f("ix_invoice_company_id"), "invoice", ["company_id"])


def downgrade():
    """
    回滚：将 UUID 类型改回 bigint（不推荐，但提供回滚能力）
    """
    # 注意：回滚到 bigint 会导致数据丢失，因为 UUID 无法转换为 bigint
    # 这里只删除列，不转换数据
    try:
        op.drop_index("ix_invoice_company_id", table_name="invoice")
    except Exception:
        pass
    try:
        op.drop_constraint("fk_invoice_company_id", "invoice", type_="foreignkey")
    except Exception:
        pass
    op.drop_column("invoice", "company_id")

