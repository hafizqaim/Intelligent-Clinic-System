import enum
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

class Base(DeclarativeBase):
    pass

class Role(enum.Enum):
    admin = "admin"
    doctor = "doctor"
    nurse = "nurse"
    user = "user"


class Users(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), foreign_key="clinics.id", nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False, default=Role.user)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

