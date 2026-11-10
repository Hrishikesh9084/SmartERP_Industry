"""Add customer, sales, and expense tables used by the business APIs."""

from alembic import op
import sqlalchemy as sa

revision = "0007_dashboard_business_tables"
down_revision = "0006_organization_foundation"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("total_spend", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_customers_company_id", "customers", ["company_id"])
    op.create_index("ix_customers_name", "customers", ["name"])
    op.create_table(
        "sales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("amount_paid", sa.Float(), nullable=False, server_default="0"),
        sa.Column("description", sa.String(255), nullable=False, server_default="Sale"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sales_company_id", "sales", ["company_id"])
    op.create_index("ix_sales_created_at", "sales", ["created_at"])
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.String(255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_expenses_company_id", "expenses", ["company_id"])
    op.create_index("ix_expenses_created_at", "expenses", ["created_at"])


def downgrade():
    op.drop_index("ix_expenses_created_at", table_name="expenses")
    op.drop_index("ix_expenses_company_id", table_name="expenses")
    op.drop_table("expenses")
    op.drop_index("ix_sales_created_at", table_name="sales")
    op.drop_index("ix_sales_company_id", table_name="sales")
    op.drop_table("sales")
    op.drop_index("ix_customers_name", table_name="customers")
    op.drop_index("ix_customers_company_id", table_name="customers")
    op.drop_table("customers")
