"""add title and photo_url to subscriptions

Revision ID: 007
Revises: 006
Create Date: 2024-03-14 16:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Add title and photo_url columns to subscriptions table
    op.add_column(
        'subscriptions',
        sa.Column('title', sa.String(255), nullable=True)
    )
    op.add_column(
        'subscriptions',
        sa.Column('photo_url', sa.String(1024), nullable=True)
    )


def downgrade():
    # Drop the new columns
    op.drop_column('subscriptions', 'photo_url')
    op.drop_column('subscriptions', 'title') 