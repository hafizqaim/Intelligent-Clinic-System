import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Integer
from sqlalchemy.orm import mapped_column, Mapped
from app.database import Base
from datetime import datetime
import pgvector


class DocumentEmbeddings(Base):
    __tablename__ = "document_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), foreign_key="clinics.id", nullable=False)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[pgvector.Vector] = mapped_column(pgvector.Vector(dim=384), nullable=False)  
    created_at: Mapped[datetime] = mapped_column(datetime, default=datetime.utcnow)
