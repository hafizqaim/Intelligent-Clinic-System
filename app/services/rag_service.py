"""RAG service: chunking, embedding, retrieval, and LLM answer generation."""
import uuid
from typing import Optional
from datetime import datetime

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

OLLAMA_BASE = settings.ollama_base_url


# ── Text chunking ────────────────────────────────────────────────────────────

def chunk_text(content: str, chunk_size: int = 0, chunk_overlap: int = 0) -> list[str]:
    """Split text into overlapping chunks by character count."""
    size = chunk_size or settings.chunk_size
    overlap = chunk_overlap or settings.chunk_overlap
    chunks: list[str] = []
    start = 0
    while start < len(content):
        end = start + size
        chunks.append(content[start:end])
        start += size - overlap
    return [c.strip() for c in chunks if c.strip()]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    from PyPDF2 import PdfReader
    import io
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


# ── Embedding (Ollama) ───────────────────────────────────────────────────────

async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Call Ollama embeddings API for a list of texts."""
    embeddings = []
    async with httpx.AsyncClient(timeout=120.0) as client:
        for t in texts:
            resp = await client.post(
                f"{OLLAMA_BASE}/api/embed",
                json={"model": settings.ollama_embedding_model, "input": t},
            )
            resp.raise_for_status()
            data = resp.json()
            embeddings.append(data["embeddings"][0])
    return embeddings


# ── Document ingestion ───────────────────────────────────────────────────────

async def ingest_document(
    db: AsyncSession,
    clinic_id: str,
    filename: str,
    content: str,
) -> int:
    """Chunk the document, embed each chunk, and store in DB. Returns chunk count."""
    chunks = chunk_text(content)
    if not chunks:
        return 0

    embeddings = await generate_embeddings(chunks)

    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        emb_literal = "[" + ",".join(str(v) for v in emb) + "]"
        await db.execute(
            text(
                """
                INSERT INTO document_embeddings
                    (id, clinic_id, source_filename, chunk_index, chunk_text, embedding, created_at)
                VALUES
                    (CAST(:id AS uuid), CAST(:clinic_id AS uuid), :filename, :idx, :chunk, CAST(:emb AS vector), now())
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "clinic_id": clinic_id,
                "filename": filename,
                "idx": idx,
                "chunk": chunk,
                "emb": emb_literal,
            },
        )
    await db.commit()
    return len(chunks)


# ── Retrieval (semantic search) ──────────────────────────────────────────────

async def retrieve_relevant_chunks(
    db: AsyncSession,
    clinic_id: str,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """Return the top-K most similar chunks for the given query."""
    query_emb = (await generate_embeddings([query]))[0]
    emb_literal = "[" + ",".join(str(v) for v in query_emb) + "]"

    result = await db.execute(
        text(
            """
            SELECT source_filename, chunk_index, chunk_text,
                   1 - (embedding <=> CAST(:qemb AS vector)) AS similarity
            FROM document_embeddings
            WHERE clinic_id = CAST(:clinic_id AS uuid)
            ORDER BY embedding <=> CAST(:qemb AS vector)
            LIMIT :top_k
            """
        ),
        {"qemb": emb_literal, "clinic_id": clinic_id, "top_k": top_k},
    )
    rows = result.fetchall()
    return [
        {
            "source_filename": r.source_filename,
            "chunk_index": r.chunk_index,
            "chunk_text": r.chunk_text,
            "similarity": float(r.similarity),
        }
        for r in rows
    ]


# ── LLM answer generation ───────────────────────────────────────────────────

async def generate_answer(query: str, context_chunks: list[dict]) -> str:
    """Build a prompt from retrieved chunks and call Ollama chat model."""
    if not context_chunks:
        return "No relevant documents found. Please upload documents first."

    context = "\n\n---\n\n".join(
        f"[{c['source_filename']} chunk {c['chunk_index']}]\n{c['chunk_text']}"
        for c in context_chunks
    )

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{OLLAMA_BASE}/api/chat",
            json={
                "model": settings.ollama_chat_model,
                "stream": False,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful medical assistant for an intelligent clinic system. "
                            "Answer the user's question using ONLY the provided document context. "
                            "If the context does not contain enough information, say so clearly."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {query}",
                    },
                ],
            },
        )
        resp.raise_for_status()
        data = resp.json()
    return data["message"]["content"]


# ── Chat history ─────────────────────────────────────────────────────────────

async def save_chat_message(
    db: AsyncSession,
    clinic_id: str,
    user_id: str,
    role: str,
    message: str,
) -> None:
    await db.execute(
        text(
            """
            INSERT INTO chat_histories (id, clinic_id, user_id, role, message, created_at)
            VALUES (CAST(:id AS uuid), CAST(:clinic_id AS uuid), CAST(:user_id AS uuid), :role, :message, now())
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "clinic_id": clinic_id,
            "user_id": user_id,
            "role": role,
            "message": message,
        },
    )
    await db.commit()


async def get_chat_history(
    db: AsyncSession,
    clinic_id: str,
    user_id: str,
    limit: int = 50,
) -> list[dict]:
    result = await db.execute(
        text(
            """
            SELECT role, message, created_at
            FROM chat_histories
            WHERE clinic_id = CAST(:clinic_id AS uuid) AND user_id = CAST(:user_id AS uuid)
            ORDER BY created_at ASC
            LIMIT :lim
            """
        ),
        {"clinic_id": clinic_id, "user_id": user_id, "lim": limit},
    )
    return [
        {"role": r.role, "message": r.message, "created_at": r.created_at}
        for r in result.fetchall()
    ]
