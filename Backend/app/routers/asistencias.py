from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.database.config import get_session
from app.models.models import APIResponse, AsistenciaCreate, AsistenciaRead, TipoAsistencia
from app.services.asistencia_service import create_asistencia, get_historial

router = APIRouter(prefix="/asistencias", tags=["Asistencias"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
def registrar_asistencia(payload: AsistenciaCreate, session: SessionDep):
    """
    Registra una entrada o salida de empleado.
    Valida: empleado activo, cliente existente, sin duplicados y coherencia entrada/salida.
    """
    create_asistencia(payload, session)
    return APIResponse(success=True, message="Asistencia registrada")


@router.get("/", response_model=list[AsistenciaRead])
def historial_asistencias(
    session: SessionDep,
    dni: str | None = Query(default=None, description="Filtrar por DNI del empleado"),
    cliente: str | None = Query(default=None, description="Filtrar por nombre de cliente (parcial)"),
    desde: date | None = Query(default=None, description="Fecha de inicio del rango (YYYY-MM-DD)"),
    hasta: date | None = Query(default=None, description="Fecha de fin del rango (YYYY-MM-DD)"),
    tipo: TipoAsistencia | None = Query(default=None, description="Filtrar por tipo: entrada o salida"),
    skip: int = Query(default=0, ge=0, description="Registros a saltar (paginación)"),
    limit: int = Query(default=50, ge=1, le=200, description="Máximo de registros a retornar"),
):
    """
    Devuelve el historial de asistencias con filtros opcionales combinables.
    Ordenado por fecha/hora descendente. Soporta paginación con skip/limit.
    """
    return get_historial(session, dni, cliente, desde, hasta, tipo, skip, limit)
