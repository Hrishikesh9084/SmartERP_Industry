"""Add profile fields required by the premium authentication flow."""

from alembic import op
import sqlalchemy as sa

revision = "0005_auth_profile_fields"
down_revision = "0004_reconcile_auth_indexes"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("companies") as batch:
        for column, default in (
            ("business_type", "General"),
            ("country", "India"),
            ("state", ""),
            ("city", ""),
        ):
            batch.add_column(
                sa.Column(column, sa.String(100), nullable=False, server_default=default)
            )
        batch.add_column(sa.Column("gstin", sa.String(32), nullable=True))
        batch.add_column(sa.Column("website", sa.String(255), nullable=True))

    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("first_name", sa.String(80), nullable=True))
        batch.add_column(sa.Column("last_name", sa.String(80), nullable=True))
        batch.add_column(
            sa.Column("auth_provider", sa.String(30), nullable=False, server_default="password")
        )
        batch.add_column(sa.Column("provider_user_id", sa.String(255), nullable=True))


def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.drop_column("provider_user_id")
        batch.drop_column("auth_provider")
        batch.drop_column("last_name")
        batch.drop_column("first_name")
    with op.batch_alter_table("companies") as batch:
        batch.drop_column("website")
        batch.drop_column("gstin")
        batch.drop_column("city")
        batch.drop_column("state")
        batch.drop_column("country")
        batch.drop_column("business_type")
