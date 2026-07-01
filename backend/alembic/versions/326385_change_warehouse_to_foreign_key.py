"""change warehouse string to warehouse_id foreign key

Revision ID: 326385_change_warehouse_to_foreign_key
Revises: 44e1506dbe10
Create Date: 2026-06-29 00:00:00.000000

SQLite 兼容版本：所有 ALTER TABLE 涉及约束变更的操作均通过 batch_alter_table
（copy-and-move 策略）执行，SQLite 不支持直接 ALTER COLUMN / ADD CONSTRAINT / DROP CONSTRAINT。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '326385_change_warehouse_to_foreign_key'
down_revision: Union[str, None] = '44e1506dbe10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    """检查表中是否已存在指定列（用于幂等操作）"""
    conn = op.get_bind()
    result = conn.execute(sa.text(f"PRAGMA table_info({table})")).fetchall()
    return any(row[1] == column for row in result)


def upgrade() -> None:
    """Change warehouse string fields to foreign key references.

    步骤：
    1. 新增 warehouse_id / source_warehouse_id / target_warehouse_id 列（nullable=True）
    2. 建索引
    3. 用 SQL UPDATE 从 warehouses 表回填 id
    4. batch_alter_table: 把 warehouse_id 改为 nullable=False，同时删掉旧 warehouse 列
    5. batch_alter_table: 删掉 inventory_transactions 的旧字符串列
    （SQLite 不支持 op.create_foreign_key / op.drop_constraint，外键仅用于 MySQL/PG）
    """
    conn = op.get_bind()

    # 1 & 2: 新增列 + 建索引（幂等：先检查是否已存在）
    if not _has_column('inventory_items', 'warehouse_id'):
        op.add_column(
            'inventory_items',
            sa.Column('warehouse_id', sa.Integer(), nullable=True)
        )
        op.create_index(
            'ix_inventory_items_warehouse_id',
            'inventory_items', ['warehouse_id'], unique=False
        )

    if not _has_column('inventory_transactions', 'source_warehouse_id'):
        op.add_column(
            'inventory_transactions',
            sa.Column('source_warehouse_id', sa.Integer(), nullable=True)
        )
        op.create_index(
            'ix_inventory_transactions_source_warehouse_id',
            'inventory_transactions', ['source_warehouse_id'], unique=False
        )

    if not _has_column('inventory_transactions', 'target_warehouse_id'):
        op.add_column(
            'inventory_transactions',
            sa.Column('target_warehouse_id', sa.Integer(), nullable=True)
        )
        op.create_index(
            'ix_inventory_transactions_target_warehouse_id',
            'inventory_transactions', ['target_warehouse_id'], unique=False
        )

    # 3. 用 warehouse 名称回填 id
    conn.execute(
        sa.text("""
            UPDATE inventory_items
            SET warehouse_id = (SELECT id FROM warehouses WHERE name = inventory_items.warehouse)
        """)
    )
    conn.execute(
        sa.text("""
            UPDATE inventory_transactions
            SET source_warehouse_id = (
                SELECT id FROM warehouses WHERE name = inventory_transactions.source_warehouse
            )
        """)
    )
    conn.execute(
        sa.text("""
            UPDATE inventory_transactions
            SET target_warehouse_id = (
                SELECT id FROM warehouses WHERE name = inventory_transactions.target_warehouse
            )
        """)
    )

    # 4. batch_alter_table: inventory_items
    #    - 删掉旧 warehouse 列（含其索引）
    #    - 把 warehouse_id 改为 nullable=False
    #    recreate='always' 让 SQLite 用 copy-and-move 策略，避免所有 ALTER 限制
    with op.batch_alter_table('inventory_items', recreate='always') as batch_op:
        if _has_column('inventory_items', 'warehouse'):
            # 删索引前先尝试（索引可能已不存在）
            try:
                batch_op.drop_index('ix_inventory_items_warehouse')
            except Exception:
                pass
            batch_op.drop_column('warehouse')
        batch_op.alter_column(
            'warehouse_id',
            existing_type=sa.Integer(),
            nullable=False
        )

    # 5. batch_alter_table: inventory_transactions
    #    - 删掉旧字符串列
    with op.batch_alter_table('inventory_transactions', recreate='always') as batch_op:
        if _has_column('inventory_transactions', 'source_warehouse'):
            batch_op.drop_column('source_warehouse')
        if _has_column('inventory_transactions', 'target_warehouse'):
            batch_op.drop_column('target_warehouse')


def downgrade() -> None:
    """Revert to warehouse string fields.

    步骤：
    1. 新增旧字符串列（幂等）
    2. 用 id 反查 warehouses 名称，回填字符串列
    3. batch_alter_table: inventory_items  —— 删掉 warehouse_id，warehouse 设为 nullable=False
    4. batch_alter_table: inventory_transactions —— 删掉 *_id 列
    """
    conn = op.get_bind()

    # 1. 恢复字符串列（幂等）
    if not _has_column('inventory_transactions', 'target_warehouse'):
        op.add_column(
            'inventory_transactions',
            sa.Column('target_warehouse', sa.VARCHAR(length=100), nullable=True)
        )
    if not _has_column('inventory_transactions', 'source_warehouse'):
        op.add_column(
            'inventory_transactions',
            sa.Column('source_warehouse', sa.VARCHAR(length=100), nullable=True)
        )
    if not _has_column('inventory_items', 'warehouse'):
        op.add_column(
            'inventory_items',
            sa.Column('warehouse', sa.VARCHAR(length=100), nullable=True)
        )

    # 2. 回填字符串列
    conn.execute(
        sa.text("""
            UPDATE inventory_items
            SET warehouse = (SELECT name FROM warehouses WHERE id = inventory_items.warehouse_id)
        """)
    )
    conn.execute(
        sa.text("""
            UPDATE inventory_transactions
            SET source_warehouse = (
                SELECT name FROM warehouses WHERE id = inventory_transactions.source_warehouse_id
            )
        """)
    )
    conn.execute(
        sa.text("""
            UPDATE inventory_transactions
            SET target_warehouse = (
                SELECT name FROM warehouses WHERE id = inventory_transactions.target_warehouse_id
            )
        """)
    )

    # 3. batch_alter_table: inventory_items
    with op.batch_alter_table('inventory_items', recreate='always') as batch_op:
        try:
            batch_op.drop_index('ix_inventory_items_warehouse_id')
        except Exception:
            pass
        if _has_column('inventory_items', 'warehouse_id'):
            batch_op.drop_column('warehouse_id')
        # warehouse 恢复为非空并重建索引
        batch_op.alter_column(
            'warehouse',
            existing_type=sa.VARCHAR(length=100),
            nullable=False
        )
        batch_op.create_index('ix_inventory_items_warehouse', ['warehouse'], unique=False)

    # 4. batch_alter_table: inventory_transactions
    with op.batch_alter_table('inventory_transactions', recreate='always') as batch_op:
        try:
            batch_op.drop_index('ix_inventory_transactions_target_warehouse_id')
        except Exception:
            pass
        try:
            batch_op.drop_index('ix_inventory_transactions_source_warehouse_id')
        except Exception:
            pass
        if _has_column('inventory_transactions', 'target_warehouse_id'):
            batch_op.drop_column('target_warehouse_id')
        if _has_column('inventory_transactions', 'source_warehouse_id'):
            batch_op.drop_column('source_warehouse_id')
