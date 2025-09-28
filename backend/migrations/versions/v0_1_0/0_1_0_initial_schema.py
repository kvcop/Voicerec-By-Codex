"""Initial database schema for core models."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from app.models._types import GUID
from app.models.meeting import MeetingStatus

# revision identifiers, used by Alembic.
revision = '0.1.0_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id', name='pk_users'),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=False)

    op.create_table(
        'meetings',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('filename', sa.String(length=512), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            'status',
            sa.Enum(MeetingStatus, name='meeting_status', native_enum=False),
            nullable=False,
            server_default=sa.text(f"'{MeetingStatus.PENDING.value}'"),
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_meetings_user_id_users', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_meetings'),
    )
    op.create_index('ix_meetings_user_created_at', 'meetings', ['user_id', 'created_at'], unique=False)

    op.create_table(
        'transcripts',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('meeting_id', GUID(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('speaker_id', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ['meeting_id'], ['meetings.id'], name='fk_transcripts_meeting_id_meetings', ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id', name='pk_transcripts'),
    )
    op.create_index(
        'ix_transcripts_meeting_timestamp',
        'transcripts',
        ['meeting_id', 'timestamp'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_transcripts_meeting_timestamp', table_name='transcripts')
    op.drop_table('transcripts')

    op.drop_index('ix_meetings_user_created_at', table_name='meetings')
    op.drop_table('meetings')

    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')

    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute(sa.text('DROP TYPE IF EXISTS meeting_status'))
