"""add huginn fields

Revision ID: 003
Revises: 002
Create Date: 2024-03-14 12:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('channels', sa.Column('huginn_rss_agent_id', sa.Integer, nullable=True))
    op.add_column('channels', sa.Column('huginn_webhook_agent_id', sa.Integer, nullable=True))


def downgrade():
    op.drop_column('channels', 'huginn_webhook_agent_id')
    op.drop_column('channels', 'huginn_rss_agent_id') 