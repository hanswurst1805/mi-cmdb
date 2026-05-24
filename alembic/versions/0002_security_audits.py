"""add security_audits table

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-02 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "security_audits",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("machine_id", UUID(as_uuid=True),
                  sa.ForeignKey("machines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hardening_index", sa.Integer()),
        sa.Column("lynis_version", sa.String(50)),
        sa.Column("warnings", sa.JSON(), server_default="[]"),
        sa.Column("suggestions", sa.JSON(), server_default="[]"),
        sa.Column("test_results", sa.JSON(), server_default="{}"),
        sa.Column("audited_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_security_audits_machine_id", "security_audits", ["machine_id"])


def downgrade() -> None:
    op.drop_table("security_audits")
