"""add github account and repository tables

Revision ID: c1c8f15247d4
Revises: 89c0e446ddab
Create Date: 2026-07-09 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1c8f15247d4'
down_revision: Union[str, Sequence[str], None] = '89c0e446ddab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'github_accounts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('github_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('access_token', sa.String(length=500), nullable=False),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('profile_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'repositories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('github_repo_id', sa.Integer(), nullable=False),
        sa.Column('repo_name', sa.String(length=255), nullable=False),
        sa.Column('branch', sa.String(length=255), nullable=False),
        sa.Column('language', sa.String(length=100), nullable=True),
        sa.Column('private', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('clone_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('repositories')
    op.drop_table('github_accounts')
