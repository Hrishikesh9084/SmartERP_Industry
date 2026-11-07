"""Add creation timestamps to email OTP records."""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_email_otp_created_at"
down_revision = "0002_add_email_otps"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "email_otps",
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("email_otps", "created_at")
