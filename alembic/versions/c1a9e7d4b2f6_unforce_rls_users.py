"""Un-force RLS on users -- register/login structurally cannot be tenant-scoped

Every real access to the users table in this app (register, login, /me) is
deliberately a plain, non-tenant-scoped session: you don't know a user's
clinic until you've looked them up (login) or you're the one creating the
row in the first place (register). No code path ever queries users through
a tenant-scoped session.

Forcing RLS there therefore has no actual protective effect -- nothing it
would protect against exists -- while blocking those routes entirely: the
WITH CHECK clause rejects every registration insert (no tenant context to
satisfy it), and the USING clause hides every row from login's lookup.
ENABLE ROW LEVEL SECURITY (not forced) is left in place on this table for
any future non-owner role.

Revision ID: c1a9e7d4b2f6
Revises: b8d4f2a6c1e3
Create Date: 2026-09-13 11:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1a9e7d4b2f6"
down_revision: Union[str, Sequence[str], None] = "b8d4f2a6c1e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users NO FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY")
