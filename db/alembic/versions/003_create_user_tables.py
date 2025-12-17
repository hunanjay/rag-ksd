"""create user and session tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 users 表
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('username', sa.String(50), nullable=False, unique=True, comment='用户名，唯一'),
        sa.Column('email', sa.String(100), nullable=True, unique=True, comment='邮箱，可选，唯一'),
        sa.Column('password', sa.String(255), nullable=False, comment='密码（明文存储）'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'), comment='是否激活'),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('false'), comment='是否为管理员'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False, onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    
    # 创建索引
    op.create_index('idx_users_username', 'users', ['username'], schema='public')
    op.create_index('idx_users_email', 'users', ['email'], schema='public', unique=False)  # email 可能为空，所以不设 unique=True
    
    # 创建 sessions 表（用于存储登录会话）
    op.create_table(
        'sessions',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('session_id', sa.String(128), nullable=False, unique=True, comment='会话ID（UUID或随机字符串）'),
        sa.Column('user_id', sa.BigInteger(), nullable=False, comment='关联的用户ID'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='过期时间'),
        sa.Column('ip_address', sa.String(45), nullable=True, comment='登录IP地址（支持IPv6）'),
        sa.Column('user_agent', sa.String(500), nullable=True, comment='用户代理字符串'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='最后访问时间'),
        sa.ForeignKeyConstraint(['user_id'], ['public.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    
    # 创建索引
    op.create_index('idx_sessions_session_id', 'sessions', ['session_id'], schema='public', unique=True)
    op.create_index('idx_sessions_user_id', 'sessions', ['user_id'], schema='public')
    op.create_index('idx_sessions_expires_at', 'sessions', ['expires_at'], schema='public')
    
    # 创建触发器：自动更新 updated_at 字段（PostgreSQL 特有）
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON public.users
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # 删除触发器
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON public.users")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # 删除索引
    op.drop_index('idx_sessions_expires_at', table_name='sessions', schema='public')
    op.drop_index('idx_sessions_user_id', table_name='sessions', schema='public')
    op.drop_index('idx_sessions_session_id', table_name='sessions', schema='public')
    op.drop_index('idx_users_email', table_name='users', schema='public')
    op.drop_index('idx_users_username', table_name='users', schema='public')
    
    # 删除表
    op.drop_table('sessions', schema='public')
    op.drop_table('users', schema='public')
