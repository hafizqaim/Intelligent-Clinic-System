import glob

files = glob.glob('alembic/versions/*_enable_rls.py')
file = files[0]

with open(file, 'r') as f:
    content = f.read()

up_replace = """def upgrade() -> None:
    # Enable RLS on tables
    op.execute('ALTER TABLE patients ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE telemetry_readings ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE document_embeddings ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE chat_histories ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE users ENABLE ROW LEVEL SECURITY')

    # Create policies
    policy_sql = '''
    CREATE POLICY tenant_isolation_policy ON {table}
    USING (clinic_id = current_setting('app.current_tenant', true)::uuid);
    '''
    for table in ['patients', 'telemetry_readings', 'document_embeddings', 'chat_histories', 'users']:
        op.execute(policy_sql.format(table=table))
"""

down_replace = """def downgrade() -> None:
    for table in ['patients', 'telemetry_readings', 'document_embeddings', 'chat_histories', 'users']:
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation_policy ON {table}')
        op.execute(f'ALTER TABLE {table} DISABLE ROW LEVEL SECURITY')
"""

content = content.replace("def upgrade() -> None:\n    pass", up_replace)
content = content.replace("def downgrade() -> None:\n    pass", down_replace)

with open(file, 'w') as f:
    f.write(content)
