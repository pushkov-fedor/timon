"""rename username to channel_name

Revision ID: 002
Revises: 001
Create Date: 2024-03-14 11:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.alter_column('channels', 'username',
                    new_column_name='channel_name',
                    existing_type=sa.String())

def downgrade() -> None:
    op.alter_column('channels', 'channel_name',
                    new_column_name='username',
                    existing_type=sa.String())
