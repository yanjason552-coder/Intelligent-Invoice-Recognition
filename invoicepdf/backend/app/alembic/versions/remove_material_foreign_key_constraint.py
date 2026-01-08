"""remove foreign key constraint from material_d

Revision ID: remove_material_fk
Revises: e2412789c190
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_material_fk'
down_revision = '1a31ce608336'  # 修改为指向主分支的最新迁移
branch_labels = None
depends_on = None


def upgrade() -> None:
    """移除 material_d 表的外键约束"""
    # 检查是否存在外键约束
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # 获取 material_d 表的外键约束
    foreign_keys = inspector.get_foreign_keys('material_d')
    
    for fk in foreign_keys:
        if 'material_id' in fk['constrained_columns']:
            # 删除外键约束
            op.drop_constraint(
                fk['name'], 
                'material_d', 
                type_='foreignkey'
            )
            print(f"已删除外键约束: {fk['name']}")


def downgrade() -> None:
    """重新添加外键约束（如果需要回滚）"""
    # 重新添加外键约束
    op.create_foreign_key(
        'fk_material_d_material_id',
        'material_d',
        'material',
        ['material_id'],
        ['material_id']
    ) 