"""Enable RLS

Revision ID: 082640853378
Revises: d3a07b348ca6
Create Date: 2026-03-20 12:45:18.664583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '082640853378'
down_revision: Union[str, Sequence[str], None] = 'd3a07b348ca6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable Row-Level Security on all tenant-scoped tables."""
    # Enable RLS
    op.execute('ALTER TABLE patients ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE telemetry_readings ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE document_embeddings ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE chat_histories ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE users ENABLE ROW LEVEL SECURITY')

    # Create tenant isolation policies for each table
    tables = ['patients', 'telemetry_readings', 'document_embeddings', 'chat_histories', 'users']
    
    for table in tables:
        policy_sql = f"""
        CREATE POLICY tenant_isolation_policy ON {table}
        USING (clinic_id = current_setting('app.current_tenant', true)::uuid)
        WITH CHECK (clinic_id = current_setting('app.current_tenant', true)::uuid)
        """
        op.execute(policy_sql)


def downgrade() -> None:
    """Disable Row-Level Security and remove policies."""
    tables = ['patients', 'telemetry_readings', 'document_embeddings', 'chat_histories', 'users']
    
    for table in tables:
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation_policy ON {table}')
        op.execute(f'ALTER TABLE {table} DISABLE ROW LEVEL SECURITY')
