"""RAG (Retrieval-Augmented Generation) router."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_tenant_db
from app.schemas.auth import TokenData
from app.schemas.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    DocumentUploadResponse,
    ChatHistoryResponse,
    ChatMessage,
)
from app.services.rag_service import (
    ingest_document,
    retrieve_relevant_chunks,
    generate_answer,
    save_chat_message,
    get_chat_history,
    extract_text_from_pdf,
)

router = APIRouter()

def _check_ollama_error(e: Exception):
    if isinstance(e, httpx.ConnectError):
        raise HTTPException(status_code=503, detail="Cannot connect to Ollama. Make sure it is running (ollama serve).")
    raise


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Upload a document (PDF or TXT), chunk it, embed it, and store in pgvector."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    raw = await file.read()

    if file.filename.lower().endswith(".pdf"):
        content = extract_text_from_pdf(raw)
    elif file.filename.lower().endswith((".txt", ".md")):
        content = raw.decode("utf-8", errors="replace")
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload .pdf, .txt, or .md files.",
        )

    if not content.strip():
        raise HTTPException(status_code=400, detail="Document is empty")

    try:
        total_chunks = await ingest_document(db, current_user.clinic_id, file.filename, content)
    except Exception as e:
        _check_ollama_error(e)

    return DocumentUploadResponse(
        filename=file.filename,
        total_chunks=total_chunks,
        message=f"Document processed into {total_chunks} chunks",
    )


@router.post("/query", response_model=RAGQueryResponse)
async def query_documents(
    body: RAGQueryRequest,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Semantic search over uploaded documents + LLM-generated answer."""
    try:
        chunks = await retrieve_relevant_chunks(
            db, current_user.clinic_id, body.query, body.top_k,
        )

        answer = await generate_answer(body.query, chunks)
    except Exception as e:
        _check_ollama_error(e)

    sources = list({c["source_filename"] for c in chunks})

    # Persist conversation
    await save_chat_message(db, current_user.clinic_id, current_user.user_id, "user", body.query)
    await save_chat_message(db, current_user.clinic_id, current_user.user_id, "assistant", answer)

    return RAGQueryResponse(query=body.query, answer=answer, sources=sources)


@router.get("/history", response_model=ChatHistoryResponse)
async def chat_history(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Retrieve chat history for the current user."""
    rows = await get_chat_history(db, current_user.clinic_id, current_user.user_id)
    messages = [
        ChatMessage(role=r["role"], message=r["message"], created_at=r["created_at"])
        for r in rows
    ]
    return ChatHistoryResponse(messages=messages)
