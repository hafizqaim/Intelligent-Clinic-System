"""RAG (Retrieval-Augmented Generation) router."""

from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Header, HTTPException
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_tenant_db
from app.core.config import settings
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


def _resolve_api_key(x_gemini_key: Optional[str]) -> str:
    """Prefer a caller-supplied key (bring-your-own-key for public deployments)
    and fall back to the server's own configured key (for local/private use)."""
    key = x_gemini_key or settings.gemini_api_key
    if not key:
        raise HTTPException(
            status_code=400,
            detail="No Gemini API key available — enter one in the RAG assistant.",
        )
    return key


def _check_llm_error(e: Exception):
    if isinstance(e, httpx.ConnectError):
        raise HTTPException(
            status_code=503,
            detail="Cannot reach the Gemini API. Check your network connection.",
        )
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code in (401, 403):
            raise HTTPException(
                status_code=502,
                detail="Gemini rejected the request — check that your API key is correct.",
            )
        if e.response.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="Gemini API rate limit or quota exceeded. Try again shortly.",
            )
        raise HTTPException(
            status_code=502, detail=f"Gemini API error: {e.response.status_code}"
        )
    raise


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    x_gemini_key: Optional[str] = Header(default=None),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Upload a document (PDF or TXT), chunk it, embed it, and store in pgvector."""
    api_key = _resolve_api_key(x_gemini_key)

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
        total_chunks = await ingest_document(
            db, current_user.clinic_id, file.filename, content, api_key
        )
    except Exception as e:
        _check_llm_error(e)

    return DocumentUploadResponse(
        filename=file.filename,
        total_chunks=total_chunks,
        message=f"Document processed into {total_chunks} chunks",
    )


@router.post("/query", response_model=RAGQueryResponse)
async def query_documents(
    body: RAGQueryRequest,
    x_gemini_key: Optional[str] = Header(default=None),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Semantic search over uploaded documents + LLM-generated answer."""
    api_key = _resolve_api_key(x_gemini_key)

    try:
        chunks = await retrieve_relevant_chunks(
            db,
            current_user.clinic_id,
            body.query,
            api_key,
            body.top_k,
        )

        answer = await generate_answer(body.query, chunks, api_key)
    except Exception as e:
        _check_llm_error(e)

    sources = list({c["source_filename"] for c in chunks})

    # Persist conversation
    await save_chat_message(
        db, current_user.clinic_id, current_user.user_id, "user", body.query
    )
    await save_chat_message(
        db, current_user.clinic_id, current_user.user_id, "assistant", answer
    )

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
