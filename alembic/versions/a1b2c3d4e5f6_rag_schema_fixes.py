"""RAG schema fixes: pgvector extension, vector column, chat_histories fields

Revision ID: a1b2c3d4e5f6
Revises: 082640853378
Create Date: 2026-03-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str]] = '082640853378'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Replace ARRAY(Float) embedding column with proper vector(1536)
    op.execute("ALTER TABLE document_embeddings DROP COLUMN embedding")
    op.execute("ALTER TABLE document_embeddings ADD COLUMN embedding vector(1536)")

    # Add role and created_at to chat_histories
    op.execute("ALTER TABLE chat_histories ADD COLUMN role VARCHAR(20) DEFAULT 'user'")
    op.execute("UPDATE chat_histories SET role = 'user' WHERE role IS NULL")
    op.execute("ALTER TABLE chat_histories ALTER COLUMN role SET NOT NULL")
    op.execute("ALTER TABLE chat_histories ADD COLUMN created_at TIMESTAMP DEFAULT now()")

    # Expand message column from VARCHAR(255) to TEXT
    op.execute("ALTER TABLE chat_histories ALTER COLUMN message TYPE TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE chat_histories ALTER COLUMN message TYPE VARCHAR(255)")
    op.execute("ALTER TABLE chat_histories DROP COLUMN IF EXISTS created_at")
    op.execute("ALTER TABLE chat_histories DROP COLUMN IF EXISTS role")
    op.execute("ALTER TABLE document_embeddings DROP COLUMN embedding")
    op.execute("ALTER TABLE document_embeddings ADD COLUMN embedding FLOAT[] NOT NULL DEFAULT '{}'")
    op.execute("DROP EXTENSION IF EXISTS vector")
