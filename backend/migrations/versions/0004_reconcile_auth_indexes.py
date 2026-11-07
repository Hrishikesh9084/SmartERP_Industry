"""Reconcile authentication indexes and OTP nullability."""

from alembic import op
import sqlalchemy as sa


revision = "0004_reconcile_auth_indexes"
down_revision = "0003_add_email_otp_created_at"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    company_indexes = {index["name"] for index in inspector.get_indexes("companies")}
    if "ix_companies_name" in company_indexes:
        op.drop_index("ix_companies_name", table_name="companies")
    op.create_index("ix_companies_name", "companies", ["name"], unique=False)

    user_indexes = {index["name"] for index in inspector.get_indexes("users")}
    if "ix_users_phone" not in user_indexes:
        op.create_index("ix_users_phone", "users", ["phone"], unique=False)

    with op.batch_alter_table("email_otps") as batch:
        batch.alter_column(
            "created_at",
            existing_type=sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )


def downgrade():
    with op.batch_alter_table("email_otps") as batch:
        batch.alter_column(
            "created_at",
            existing_type=sa.DateTime(),
            nullable=True,
            server_default=None,
        )

    op.drop_index("ix_users_phone", table_name="users")
    op.drop_index("ix_companies_name", table_name="companies")
    op.create_index("ix_companies_name", "companies", ["name"], unique=False)
