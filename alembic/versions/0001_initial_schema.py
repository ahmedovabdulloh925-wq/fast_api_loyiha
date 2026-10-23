"""Boshlang'ich sxema: users, products, stock_movements

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-23 14:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users jadvalini yaratish
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('user', 'staff', 'admin')", name="check_user_role"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # 2. products jadvalini yaratish
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("sku", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("low_stock_threshold", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("quantity >= 0", name="check_product_quantity_non_negative"),
        sa.CheckConstraint("low_stock_threshold >= 0", name="check_product_threshold_non_negative"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_products_id"), "products", ["id"], unique=False)
    op.create_index(op.f("ix_products_sku"), "products", ["sku"], unique=True)

    # 3. stock_movements jadvalini yaratish
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("performed_by_id", sa.Integer(), nullable=False),
        sa.Column("movement_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "movement_type IN ('incoming', 'outgoing')",
            name="check_movement_type",
        ),
        sa.CheckConstraint("amount > 0", name="check_movement_amount_positive"),
        sa.CheckConstraint("length(trim(reason)) > 0", name="check_movement_reason_not_empty"),
        sa.ForeignKeyConstraint(["performed_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_stock_movements_id"), "stock_movements", ["id"], unique=False)
    op.create_index(op.f("ix_stock_movements_product_id"), "stock_movements", ["product_id"], unique=False)
    op.create_index(
        op.f("ix_stock_movements_performed_by_id"),
        "stock_movements",
        ["performed_by_id"],
        unique=False,
    )
    op.create_index(op.f("ix_stock_movements_created_at"), "stock_movements", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_stock_movements_created_at"), table_name="stock_movements")
    op.drop_index(op.f("ix_stock_movements_performed_by_id"), table_name="stock_movements")
    op.drop_index(op.f("ix_stock_movements_product_id"), table_name="stock_movements")
    op.drop_index(op.f("ix_stock_movements_id"), table_name="stock_movements")
    op.drop_table("stock_movements")

    op.drop_index(op.f("ix_products_sku"), table_name="products")
    op.drop_index(op.f("ix_products_id"), table_name="products")
    op.drop_table("products")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
