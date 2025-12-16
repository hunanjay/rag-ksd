"""create document and document_chunk tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 document 表
    op.create_table(
        'document',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=True, comment='内容哈希值，用于判断页面内容是否有变化'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    
    # 为 content_hash 创建索引以便快速查找
    op.create_index(
        'idx_document_content_hash',
        'document',
        ['content_hash'],
        schema='public'
    )
    
    # 创建 document_chunk 表（先不包含 embedding 列）
    op.create_table(
        'document_chunk',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('document_id', sa.BigInteger(), nullable=True),
        sa.Column('chunk_index', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['public.document.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='public'
    )
    
    # 使用原生 SQL 添加 vector 类型列（因为 SQLAlchemy 不直接支持 pgvector）
    op.execute("""
        ALTER TABLE public.document_chunk 
        ADD COLUMN embedding vector(1536);
    """)
    
    # 创建 ivfflat 索引用于向量相似度搜索
    op.execute("""
        CREATE INDEX idx_document_chunk_embedding 
        ON public.document_chunk 
        USING ivfflat (embedding vector_cosine_ops) 
        WITH (lists = 100);
    """)


def downgrade() -> None:
    # 删除索引
    op.execute("DROP INDEX IF EXISTS public.idx_document_chunk_embedding")
    op.drop_index('idx_document_content_hash', table_name='document', schema='public')
    
    # 删除表（自动处理外键约束）
    op.drop_table('document_chunk', schema='public')
    op.drop_table('document', schema='public')
