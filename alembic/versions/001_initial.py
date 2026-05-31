"""Initial migration - create tables

Revision ID: 001
Revises: 
Create Date: 2026-05-31

"""
from alembic import op
import sqlalchemy as sa


revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('products',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('price', sa.Float(), nullable=True),
    sa.Column('link', sa.String(length=2000), nullable=False),
    sa.Column('image_url', sa.String(length=2000), nullable=True),
    sa.Column('source', sa.String(length=50), nullable=False),
    sa.Column('affiliate_tag', sa.String(length=200), nullable=True),
    sa.Column('state', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
    sa.Column('first_published_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('link')
    )
    op.create_index('ix_products_state', 'products', ['state'])

    op.create_table('post_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('platform', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('published_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_post_log_product_id', 'post_log', ['product_id'])

    op.create_table('platform_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('platform', sa.String(length=50), nullable=False),
    sa.Column('token', sa.String(length=2000), nullable=False),
    sa.Column('refresh_token', sa.String(length=2000), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('platform')
    )


def downgrade() -> None:
    op.drop_table('platform_tokens')
    op.drop_index('ix_post_log_product_id', table_name='post_log')
    op.drop_table('post_log')
    op.drop_index('ix_products_state', table_name='products')
    op.drop_table('products')
