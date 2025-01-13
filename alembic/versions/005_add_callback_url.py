"""add callback url

Revision ID: 005
Revises: 004
Create Date: 2024-03-14 14:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Add callback_url column as non-nullable
    # We use server_default temporarily to handle existing rows
    op.add_column(
        'channels',
        sa.Column(
            'callback_url',
            sa.String(),
            server_default='https://example.com/webhook',
            nullable=False
        )
    )
    
    # Remove the server_default after adding the column
    op.alter_column(
        'channels',
        'callback_url',
        server_default=None
    )


def downgrade():
    op.drop_column('channels', 'callback_url') 