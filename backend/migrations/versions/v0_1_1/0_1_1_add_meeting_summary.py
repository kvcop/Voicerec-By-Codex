"""Add summary column to meetings table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'v0_1_1_add_meeting_summary'
down_revision = '0.1.0_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('meetings', sa.Column('summary', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('meetings', 'summary')
