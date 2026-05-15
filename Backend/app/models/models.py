from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)


# ---------------------------------------------------------------------------
# Empleado
# ---------------------------------------------------------------------------


class EmpleadoBase(SQLModel):
    dni: str = Field(
        min_length=7,
        max_length=9,
        index=True,
        sa_column_kwargs={"unique": True},
        description="Documento Nacional de Identidad del empleado",
    )
    nombre_completo: str = Field(
        min_length=1,
        max_length=255,
        description="Nombre y apellido completo",
    )
    observaciones: str | None = Field(
        default=None,
        description="Notas u observaciones adicionales sobre el empleado",
    )
    is_active: bool = Field(
        default=True,
        nullable=False,
        description="Indica si el empleado se encuentra activo",
    )


class Empleado(EmpleadoBase, TimestampMixin, table=True):
    __tablename__ = "empleado"

    id: int | None = Field(default=None, primary_key=True)


class EmpleadoCreate(EmpleadoBase):
    pass


class EmpleadoRead(EmpleadoBase):
    id: int
    created_at: datetime
    updated_at: datetime


class EmpleadoUpdate(SQLModel):
    dni: str | None = Field(default=None, min_length=7, max_length=9)
    nombre_completo: str | None = Field(default=None, min_length=1, max_length=255)
    observaciones: str | None = None
    is_active: bool | None = None