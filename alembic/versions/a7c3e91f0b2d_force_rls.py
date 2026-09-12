"""Force row-level security on tenant-scoped tables

ENABLE ROW LEVEL SECURITY (from the earlier enable_rls migration) does
NOT apply to the table owner by default -- only to other roles. Since
the application always connects as the same role that owns the tables
(the role the migrations themselves ran as), every query was silently
bypassing RLS entirely and returning cross-tenant data, regardless of
the app.current_tenant session variable set per-request.

FORCE ROW LEVEL SECURITY makes the policy apply to the owner too. It
still has no effect on a genuine Postgres superuser (RLS can never be
forced for those), but fixes the common case of an elevated-but-not-
superuser owner role, which is how most managed Postgres providers
provision the database owner.

Revision ID: a7c3e91f0b2d
Revises: c9d1e2f3a4b5
Create Date: 2026-09-13 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7c3e91f0b2d"
down_revision: Union[str, Sequence[str], None] = "c9d1e2f3a4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "patients",
    "telemetry_readings",
    "document_embeddings",
    "chat_histories",
    "users",
]


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
