from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import Dict
from app.rag.embeddings import get_embedding_model

async def retrive_relevant_chunks(db: AsyncSession, clinic_id: UUID, query: str, top_k: int = 5) -> list[Dict]:
    sql = """SELECT chunk_text, source_filename, chunk_index,
                1 - (embedding <=> :query_vector) AS similarity
            FROM document_embeddings
            WHERE clinic_id = :clinic_id
            ORDER BY embedding <=> :query_vector
            LIMIT :top_k;"""
    
    embedding_model = get_embedding_model("all-MiniLM-L6-v2")

    document_embeddings = embedding_model.embed_query([query])

    result = db.execute(sql, {
        "clinic_id": clinic_id,
        "query_vector": document_embeddings[0],
        "top_k": top_k
    })

    rows = result.mappings().all()

    chunks = [
        {
            "chunk_text": row["chunk_text"],
            "source_filename": row["source_filename"],
            "chunk_index": row["chunk_index"],
            "similarity": float(row["similarity"]),
        }
        for row in rows
        if row["similarity"] >= 0.3 
    ]

    return chunks
