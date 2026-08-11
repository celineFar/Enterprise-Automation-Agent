"""Establish the Release 0 migration baseline.

Revision ID: 0001_initial_schema_baseline
Revises: None
"""

from collections.abc import Sequence

revision: str = "0001_initial_schema_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Reserve the baseline; product tables begin in later phases."""


def downgrade() -> None:
    """Remove the empty baseline revision."""
