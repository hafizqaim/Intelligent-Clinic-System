"""Switch embedding dimension from 1536 to 768 for Ollama

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-28

"""

from typing import Sequence, Union

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str]] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Clear existing embeddings (dimension change makes old ones invalid)
    op.execute("DELETE FROM document_embeddings")
    op.execute("ALTER TABLE document_embeddings DROP COLUMN embedding")
    op.execute("ALTER TABLE document_embeddings ADD COLUMN embedding vector(768)")


def downgrade() -> None:
    op.execute("DELETE FROM document_embeddings")
    op.execute("ALTER TABLE document_embeddings DROP COLUMN embedding")
    op.execute("ALTER TABLE document_embeddings ADD COLUMN embedding vector(1536)")
