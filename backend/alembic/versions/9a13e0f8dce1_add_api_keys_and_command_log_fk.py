"""add api keys and command log auth

Revision ID: 9a13e0f8dce1
Revises: 7c1c8b9e3a2a
Create Date: 2026-02-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a13e0f8dce1"
down_revision: Union[str, Sequence[str], None] = "7c1c8b9e3a2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("key_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)

    op.add_column("command_logs", sa.Column("api_key_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(
        "fk_command_logs_api_key_id",
        "command_logs",
        "api_keys",
        ["api_key_id"],
        ["id"],
    )
    op.create_index("ix_command_logs_api_key_id", "command_logs", ["api_key_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_command_logs_api_key_id", table_name="command_logs")
    op.drop_constraint("fk_command_logs_api_key_id", "command_logs", type_="foreignkey")
    op.drop_column("command_logs", "api_key_id")
    op.drop_index("ix_api_keys_key_hash", table_name="api_keys")
    op.drop_table("api_keys")
