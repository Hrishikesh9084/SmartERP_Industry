"""Add soft deletion fields for workspaces."""

from alembic import op
import sqlalchemy as sa

revision = "0008_soft_delete_workspaces"
down_revision = "0007_dashboard_business_tables"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("companies", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column("companies", sa.Column("deleted_by", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_companies_deleted_by_users",
        "companies",
        "users",
        ["deleted_by"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("fk_companies_deleted_by_users", "companies", type_="foreignkey")
    op.drop_column("companies", "deleted_by")
    op.drop_column("companies", "deleted_at")
