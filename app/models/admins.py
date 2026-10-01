import enum

from sqlalchemy import (
    BigInteger,
    Enum,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RoleEnum(enum.Enum):
    ADMIN = 'admin'
    MANAGER = 'manager'


class AdminAuth(Base):
    __tablename__ = "admauth"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(250))
    password: Mapped[str | None] = mapped_column(Text)
    role: Mapped[RoleEnum | None] = mapped_column(Enum(RoleEnum))
