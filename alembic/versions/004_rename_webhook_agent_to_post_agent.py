"""rename webhook agent to post agent

Revision ID: 004
Revises: 003
Create Date: 2024-03-14 13:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('channels', 'huginn_webhook_agent_id',
                    new_column_name='huginn_post_agent_id',
                    existing_type=sa.Integer)


def downgrade():
    op.alter_column('channels', 'huginn_post_agent_id',
                    new_column_name='huginn_webhook_agent_id',
                    existing_type=sa.Integer)