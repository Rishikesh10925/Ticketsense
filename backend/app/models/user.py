import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class User(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('customer','support_agent','manager','enterprise_admin','ai_admin','knowledge_manager','security_admin','end_user','department_engineer','admin')", name="ck_users_role"
        ),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
