"""enable row level security

Revision ID: 7cbb93ba889b
Revises: 
Create Date: 2026-03-09 22:10:23.301991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7cbb93ba889b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Enable RLS
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE patients ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE telemetry_readings ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE chat_histories ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE document_embeddings ENABLE ROW LEVEL SECURITY;")

    # Create policies
    op.execute("""
    CREATE POLICY clinic_isolation_users ON users
      USING (clinic_id::text = current_setting('app.current_clinic_id', true));
    """)
    op.execute("""
    CREATE POLICY clinic_isolation_patients ON patients
      USING (clinic_id::text = current_setting('app.current_clinic_id', true));
    """)
    op.execute("""
    CREATE POLICY clinic_isolation_telemetry ON telemetry_readings
      USING (clinic_id::text = current_setting('app.current_clinic_id', true));
    """)
    op.execute("""
    CREATE POLICY clinic_isolation_chats ON chat_histories
      USING (clinic_id::text = current_setting('app.current_clinic_id', true));
    """)
    op.execute("""
    CREATE POLICY clinic_isolation_docs ON document_embeddings
      USING (clinic_id::text = current_setting('app.current_clinic_id', true));
    """)

    # Force RLS even for table owner
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE patients FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE telemetry_readings FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE chat_histories FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE document_embeddings FORCE ROW LEVEL SECURITY;")

def downgrade():
    # Drop policies and disable RLS
    op.execute("DROP POLICY clinic_isolation_users ON users;")
    op.execute("DROP POLICY clinic_isolation_patients ON patients;")
    op.execute("DROP POLICY clinic_isolation_telemetry ON telemetry_readings;")
    op.execute("DROP POLICY clinic_isolation_chats ON chat_histories;")
    op.execute("DROP POLICY clinic_isolation_docs ON document_embeddings;")

    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE patients DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE telemetry_readings DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE chat_histories DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE document_embeddings DISABLE ROW LEVEL SECURITY;")
