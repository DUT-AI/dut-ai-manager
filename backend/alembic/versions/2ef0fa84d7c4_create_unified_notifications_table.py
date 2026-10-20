"""create_unified_notifications_table

Revision ID: 2ef0fa84d7c4
Revises: 4b96820839eb
Create Date: 2026-10-21 02:16:23.337983

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2ef0fa84d7c4'
down_revision: Union[str, Sequence[str], None] = '4b96820839eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tạo bảng notifications thống nhất
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='SYSTEM'),
        sa.Column('level', sa.String(length=50), nullable=False, server_default='INFO'),
        sa.Column('action_url', sa.String(length=500), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('task_type', sa.String(length=50), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('reminder_stage', sa.String(length=50), nullable=True),
        sa.Column('discord_status', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_notif_dedup', 'notifications', ['task_type', 'task_id', 'user_id', 'reminder_stage'], unique=False)
    op.create_index('idx_notif_user_created', 'notifications', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_notif_user_unread', 'notifications', ['user_id', 'is_read', 'created_at'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)

    # 2. Xóa 2 bảng cũ in_app_notifications và task_reminder_logs
    op.drop_table('in_app_notifications')
    op.drop_table('task_reminder_logs')


def downgrade() -> None:
    # Tái tạo 2 bảng cũ nếu rollback
    op.create_table(
        'task_reminder_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('task_title', sa.String(255), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reminder_stage', sa.String(50), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False, server_default='DISCORD_DM'),
        sa.Column('status', sa.String(50), nullable=False, server_default='SENT'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), server_default='false'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )
    op.create_table(
        'in_app_notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False, server_default='SYSTEM'),
        sa.Column('level', sa.String(50), nullable=False, server_default='INFO'),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), server_default='false'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
    )
    op.drop_table('notifications')
