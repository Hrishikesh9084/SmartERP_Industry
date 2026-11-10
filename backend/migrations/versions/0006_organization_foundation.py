"""Add tenant-scoped branches, departments, and warehouses."""

from alembic import op
import sqlalchemy as sa

revision = "0006_organization_foundation"
down_revision = "0005_auth_profile_fields"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "branches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "code", name="uq_branch_code_company"),
    )
    op.create_index("ix_branches_company_id", "branches", ["company_id"])
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "code", name="uq_department_code_company"),
    )
    op.create_index("ix_departments_company_id", "departments", ["company_id"])
    op.create_table(
        "warehouses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("branch_id", sa.Integer(), sa.ForeignKey("branches.id"), nullable=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("company_id", "code", name="uq_warehouse_code_company"),
    )
    op.create_index("ix_warehouses_company_id", "warehouses", ["company_id"])
    op.create_index("ix_warehouses_branch_id", "warehouses", ["branch_id"])


def downgrade():
    op.drop_index("ix_warehouses_branch_id", table_name="warehouses")
    op.drop_index("ix_warehouses_company_id", table_name="warehouses")
    op.drop_table("warehouses")
    op.drop_index("ix_departments_company_id", table_name="departments")
    op.drop_table("departments")
    op.drop_index("ix_branches_company_id", table_name="branches")
    op.drop_table("branches")
