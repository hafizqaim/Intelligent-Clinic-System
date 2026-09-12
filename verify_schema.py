import psycopg2
conn = psycopg2.connect('postgresql://qaim:qaim123@localhost:5432/intelligent_clinic_db')
cur = conn.cursor()

cur.execute("SELECT extname FROM pg_extension WHERE extname='vector'")
print('pgvector extension:', cur.fetchone())

cur.execute("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_name='document_embeddings' AND column_name='embedding'")
print('embedding column:', cur.fetchone())

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='chat_histories' ORDER BY ordinal_position")
print('chat_histories cols:', cur.fetchall())

conn.close()
