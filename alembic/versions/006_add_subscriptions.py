"""add subscriptions

Revision ID: 006
Revises: 005
Create Date: 2024-03-14 15:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.sql import column, table

from alembic import op

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=False),
        sa.Column('callback_url', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create temporary tables for data migration
    channels = table(
        'channels',
        column('id', sa.Integer),
        column('callback_url', sa.String)
    )
    
    subscriptions = table(
        'subscriptions',
        column('channel_id', sa.Integer),
        column('callback_url', sa.String),
        column('is_active', sa.Boolean)
    )

    # Migrate existing callback_urls to subscriptions
    connection = op.get_bind()
    for channel in connection.execute(channels.select()):
        if channel.callback_url and channel.callback_url != 'https://example.com/webhook':
            connection.execute(
                subscriptions.insert().values(
                    channel_id=channel.id,
                    callback_url=channel.callback_url,
                    is_active=True
                )
            )

    # Drop callback_url from channels
    op.drop_column('channels', 'callback_url')


def downgrade():
    # Add callback_url back to channels
    op.add_column(
        'channels',
        sa.Column('callback_url', sa.String(), nullable=True)
    )

    # Create temporary tables for data migration
    channels = table(
        'channels',
        column('id', sa.Integer),
        column('callback_url', sa.String)
    )
    
    subscriptions = table(
        'subscriptions',
        column('channel_id', sa.Integer),
        column('callback_url', sa.String),
        column('is_active', sa.Boolean)
    )

    # Migrate active subscriptions back to channels
    connection = op.get_bind()
    for subscription in connection.execute(
        subscriptions.select().where(subscriptions.c.is_active == True)
    ):
        connection.execute(
            channels.update()
            .where(channels.c.id == subscription.channel_id)
            .values(callback_url=subscription.callback_url)
        )

    # Drop subscriptions table
    op.drop_table('subscriptions') 