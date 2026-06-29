"""change warehouse string to warehouse_id foreign key

Revision ID: 326385_change_warehouse_to_foreign_key
Revises: 44e1506dbe10
Create Date: 2026-06-29 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '326385_change_warehouse_to_foreign_key'
down_revision: Union[str, None] = '44e1506dbe10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change warehouse string fields to foreign key references."""
    op.add_column(
        'inventory_items',
        sa.Column('warehouse_id', sa.Integer(), nullable=True)
    )
    op.create_index(
        op.f('ix_inventory_items_warehouse_id'),
        'inventory_items',
        ['warehouse_id'],
        unique=False
    )

    op.add_column(
        'inventory_transactions',
        sa.Column('source_warehouse_id', sa.Integer(), nullable=True)
    )
    op.add_column(
        'inventory_transactions',
        sa.Column('target_warehouse_id', sa.Integer(), nullable=True)
    )
    op.create_index(
        op.f('ix_inventory_transactions_source_warehouse_id'),
        'inventory_transactions',
        ['source_warehouse_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_inventory_transactions_target_warehouse_id'),
        'inventory_transactions',
        ['target_warehouse_id'],
        unique=False
    )

    conn = op.get_bind()
    warehouses = conn.execute(sa.text("SELECT id, name FROM warehouses")).fetchall()
    wh_name_to_id = {row[1]: row[0] for row in warehouses}

    for name, wid in wh_name_to_id.items():
        conn.execute(
            sa.text("UPDATE inventory_items SET warehouse_id = :wid WHERE warehouse = :name"),
            {"wid": wid, "name": name}
        )
        conn.execute(
            sa.text("UPDATE inventory_transactions SET source_warehouse_id = :wid WHERE source_warehouse = :name"),
            {"wid": wid, "name": name}
        )
        conn.execute(
            sa.text("UPDATE inventory_transactions SET target_warehouse_id = :wid WHERE target_warehouse = :name"),
            {"wid": wid, "name": name}
        )

    op.alter_column('inventory_items', 'warehouse_id', nullable=False)

    op.create_foreign_key(
        op.f('fk_inventory_items_warehouse_id_warehouses'),
        'inventory_items',
        'warehouses',
        ['warehouse_id'],
        ['id']
    )
    op.create_foreign_key(
        op.f('fk_inventory_transactions_source_warehouse_id_warehouses'),
        'inventory_transactions',
        'warehouses',
        ['source_warehouse_id'],
        ['id']
    )
    op.create_foreign_key(
        op.f('fk_inventory_transactions_target_warehouse_id_warehouses'),
        'inventory_transactions',
        'warehouses',
        ['target_warehouse_id'],
        ['id']
    )

    op.drop_index('ix_inventory_items_warehouse', table_name='inventory_items')
    op.drop_column('inventory_items', 'warehouse')
    op.drop_column('inventory_transactions', 'source_warehouse')
    op.drop_column('inventory_transactions', 'target_warehouse')


def downgrade() -> None:
    """Revert to warehouse string fields."""
    op.add_column(
        'inventory_transactions',
        sa.Column('target_warehouse', sa.VARCHAR(length=100), nullable=True)
    )
    op.add_column(
        'inventory_transactions',
        sa.Column('source_warehouse', sa.VARCHAR(length=100), nullable=True)
    )
    op.add_column(
        'inventory_items',
        sa.Column('warehouse', sa.VARCHAR(length=100), nullable=True)
    )

    conn = op.get_bind()
    warehouses = conn.execute(sa.text("SELECT id, name FROM warehouses")).fetchall()
    wh_id_to_name = {row[0]: row[1] for row in warehouses}

    conn.execute(
        sa.text("""
            UPDATE inventory_items 
            SET warehouse = (SELECT name FROM warehouses WHERE id = inventory_items.warehouse_id)
        """)
    )
    conn.execute(
        sa.text("""
            UPDATE inventory_transactions 
            SET source_warehouse = (SELECT name FROM warehouses WHERE id = inventory_transactions.source_warehouse_id)
        """)
    )
    conn.execute(
        sa.text("""
            UPDATE inventory_transactions 
            SET target_warehouse = (SELECT name FROM warehouses WHERE id = inventory_transactions.target_warehouse_id)
        """)
    )

    op.alter_column('inventory_items', 'warehouse', nullable=False)

    op.create_index(
        'ix_inventory_items_warehouse',
        'inventory_items',
        ['warehouse'],
        unique=False
    )

    op.drop_constraint(
        op.f('fk_inventory_transactions_target_warehouse_id_warehouses'),
        'inventory_transactions',
        type_='foreignkey'
    )
    op.drop_constraint(
        op.f('fk_inventory_transactions_source_warehouse_id_warehouses'),
        'inventory_transactions',
        type_='foreignkey'
    )
    op.drop_constraint(
        op.f('fk_inventory_items_warehouse_id_warehouses'),
        'inventory_items',
        type_='foreignkey'
    )

    op.drop_index(
        op.f('ix_inventory_transactions_target_warehouse_id'),
        table_name='inventory_transactions'
    )
    op.drop_index(
        op.f('ix_inventory_transactions_source_warehouse_id'),
        table_name='inventory_transactions'
    )
    op.drop_index(
        op.f('ix_inventory_items_warehouse_id'),
        table_name='inventory_items'
    )

    op.drop_column('inventory_transactions', 'target_warehouse_id')
    op.drop_column('inventory_transactions', 'source_warehouse_id')
    op.drop_column('inventory_items', 'warehouse_id')