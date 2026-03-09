import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Integer
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

class Base(DeclarativeBase):
    pass

class ChatHistories(Base):
    __tablename__ = "chat_histories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), foreign_key="clinics.id", nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), foreign_key="users.id", nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    