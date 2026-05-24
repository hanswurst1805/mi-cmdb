"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "machines",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("fqdn", sa.String(255), nullable=False, unique=True),
        sa.Column("hostname", sa.String(255), nullable=False),
        sa.Column("os", sa.String(255)),
        sa.Column("ram_gb", sa.Integer()),
        sa.Column("cpu_cores", sa.Integer()),
        sa.Column("status", sa.Enum("active", "inactive", "decommissioned", name="machinestatus"), nullable=False, server_default="active"),
        sa.Column("description", sa.Text()),
        sa.Column("owner", sa.String(255)),
        sa.Column("embedding", Vector(1024)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime()),
    )
    op.create_index("ix_machines_fqdn", "machines", ["fqdn"])
    op.create_index("ix_machines_deleted_at", "machines", ["deleted_at"])

    op.create_table(
        "networks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("cidr", sa.String(50), nullable=False, unique=True),
        sa.Column("gateway", sa.String(50)),
        sa.Column("description", sa.Text()),
        sa.Column("location", sa.String(255)),
        sa.Column("embedding", Vector(1024)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "nics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("machine_id", UUID(as_uuid=True), sa.ForeignKey("machines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("mac_address", sa.String(17)),
    )

    op.create_table(
        "ip_addresses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("nic_id", UUID(as_uuid=True), sa.ForeignKey("nics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("network_id", UUID(as_uuid=True), sa.ForeignKey("networks.id", ondelete="SET NULL")),
        sa.Column("address", sa.String(45), nullable=False),
        sa.Column("type", sa.Enum("ipv4", "ipv6", name="iptype"), nullable=False, server_default="ipv4"),
        sa.Column("deleted_at", sa.DateTime()),
    )
    op.create_index("ix_ip_addresses_address", "ip_addresses", ["address"])

    op.create_table(
        "api_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("permissions", sa.Enum("read", "write", name="tokenpermission"), nullable=False, server_default="read"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime()),
    )


def downgrade() -> None:
    op.drop_table("api_tokens")
    op.drop_table("ip_addresses")
    op.drop_table("nics")
    op.drop_table("networks")
    op.drop_table("machines")
    op.execute("DROP TYPE IF EXISTS machinestatus")
    op.execute("DROP TYPE IF EXISTS iptype")
    op.execute("DROP TYPE IF EXISTS tokenpermission")
