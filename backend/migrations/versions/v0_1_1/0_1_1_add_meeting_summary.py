"""Add summary column to meetings table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b_add_meeting_summary'
down_revision = 'a_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('meetings', sa.Column('summary', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('meetings', 'summary')
