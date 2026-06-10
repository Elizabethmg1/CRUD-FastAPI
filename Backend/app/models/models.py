from __future__ import annotations

import enum
from datetime import date, datetime, time, timezone

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


# ---------------------------------------------------------------------------
# JornadaLaboral
# ---------------------------------------------------------------------------


class JornadaLaboralBase(SQLModel):
    fecha: date = Field(description="Fecha de la jornada laboral")
    hora_inicio: time = Field(description="Hora de inicio de la jornada")
    hora_fin: time = Field(description="Hora de fin de la jornada")
    cliente: str = Field(
        min_length=1,
        max_length=255,
        description="Nombre del cliente al que corresponde la jornada",
    )
    direccion: str = Field(
        min_length=1,
        max_length=500,
        description="Dirección donde se realiza la jornada",
    )
    descripcion: str | None = Field(
        default=None,
        description="Descripción u observaciones de la jornada",
    )
    empleado_id: int = Field(foreign_key="empleado.id", description="ID del empleado asignado")


class JornadaLaboral(JornadaLaboralBase, TimestampMixin, table=True):
    __tablename__ = "jornada_laboral"

    id: int | None = Field(default=None, primary_key=True)


class JornadaLaboralCreate(JornadaLaboralBase):
    pass


class JornadaLaboralRead(JornadaLaboralBase):
    id: int
    created_at: datetime
    updated_at: datetime


class JornadaLaboralUpdate(SQLModel):
    fecha: date | None = None
    hora_inicio: time | None = None
    hora_fin: time | None = None
    cliente: str | None = Field(default=None, min_length=1, max_length=255)
    direccion: str | None = Field(default=None, min_length=1, max_length=500)
    descripcion: str | None = None
    empleado_id: int | None = None


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------


class ClienteBase(SQLModel):
    nombre: str = Field(
        min_length=1,
        max_length=255,
        index=True,
        description="Nombre del cliente",
    )
    direccion: str = Field(
        min_length=1,
        max_length=500,
        description="Dirección principal del cliente",
    )


class Cliente(ClienteBase, table=True):
    __tablename__ = "cliente"

    id: int | None = Field(default=None, primary_key=True)


class ClienteCreate(ClienteBase):
    pass


class ClienteRead(ClienteBase):
    id: int


# ---------------------------------------------------------------------------
# Asistencia
# ---------------------------------------------------------------------------


class TipoAsistencia(str, enum.Enum):
    entrada = "entrada"
    salida = "salida"


class Asistencia(SQLModel, table=True):
    __tablename__ = "asistencia"

    id: int | None = Field(default=None, primary_key=True)
    tipo: TipoAsistencia = Field(description="Tipo de registro: entrada o salida")
    empleado_id: int = Field(foreign_key="empleado.id", description="ID del empleado")
    cliente_id: int = Field(foreign_key="cliente.id", description="ID del cliente")
    direccion: str = Field(max_length=500, description="Dirección donde se registra la asistencia")
    fecha_hora: datetime = Field(default_factory=utcnow, description="Fecha y hora del registro")


class AsistenciaCreate(SQLModel):
    tipo: TipoAsistencia
    dni: str = Field(min_length=7, max_length=9, description="DNI del empleado")
    cliente_id: int = Field(description="ID del cliente")
    direccion: str = Field(min_length=1, max_length=500, description="Dirección del registro")


class AsistenciaRead(SQLModel):
    id: int
    tipo: TipoAsistencia
    dni: str
    cliente: str
    direccion: str
    fecha_hora: datetime


# ---------------------------------------------------------------------------
# Registro de horas
# ---------------------------------------------------------------------------


class RegistroHorasRead(SQLModel):
    fecha: date
    empleado: str
    cliente: str
    direccion: str
    hora_entrada: str | None = None
    hora_salida: str | None = None
    horas_estimadas: float
    horas_realizadas: float
    horas_extras: float
    horas_a_descontar: float
    estado: str | None = None
    message: str | None = None


# ---------------------------------------------------------------------------
# Respuesta estandarizada
# ---------------------------------------------------------------------------


class APIResponse(SQLModel):
    success: bool
    message: str