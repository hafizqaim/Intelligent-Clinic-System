"""Guard the RLS policy's uuid cast against an empty current_tenant setting

app.current_tenant is a custom (extension-less) GUC. Once any session on a
pooled physical connection has SET it, a later RESET does not return it to
a true "never set" NULL state -- it leaves it as an empty string. Since
requests that intentionally run without tenant scoping (login, register,
clinic administration) use plain, non-tenant-scoped sessions and never set
this GUC themselves, they can inherit that leftover '' from a previous,
unrelated request that reused the same pooled connection. The old policy
expression, current_setting(...)::uuid, then raises a Postgres error
("invalid input syntax for type uuid") instead of safely matching no rows
-- surfacing as an unhandled 500 on totally unrelated requests, non-
deterministically, depending on which pooled connection got reused.

NULLIF(..., '') converts that empty-string leftover to a real NULL before
the cast, so it safely evaluates to "no tenant match" (as intended) instead
of crashing.

Revision ID: b8d4f2a6c1e3
Revises: a7c3e91f0b2d
Create Date: 2026-09-13 10:30:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8d4f2a6c1e3"
down_revision: Union[str, Sequence[str], None] = "a7c3e91f0b2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "patients",
    "telemetry_readings",
    "document_embeddings",
    "chat_histories",
    "users",
]

GUARDED_EXPR = (
    "clinic_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid"
)
UNGUARDED_EXPR = "clinic_id = current_setting('app.current_tenant', true)::uuid"


def upgrade() -> None:
    for table in TABLES:
        op.execute(
            f"ALTER POLICY tenant_isolation_policy ON {table} "
            f"USING ({GUARDED_EXPR}) WITH CHECK ({GUARDED_EXPR})"
        )


def downgrade() -> None:
    for table in TABLES:
        op.execute(
            f"ALTER POLICY tenant_isolation_policy ON {table} "
            f"USING ({UNGUARDED_EXPR}) WITH CHECK ({UNGUARDED_EXPR})"
        )
