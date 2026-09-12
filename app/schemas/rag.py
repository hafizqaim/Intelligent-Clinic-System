"""RAG pipeline schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    filename: str
    total_chunks: int
    message: str


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[str]


class ChatMessage(BaseModel):
    role: str
    message: str
    created_at: Optional[datetime] = None


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessage]
