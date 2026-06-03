from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.database.config import get_session
from app.models.models import JornadaLaboralCreate, JornadaLaboralRead, JornadaLaboralUpdate
from app.services.jornada_service import (
    create_jornada,
    delete_jornada,
    filter_jornadas,
    get_all_jornadas,
    get_jornada_by_id,
    update_jornada,
)

router = APIRouter(prefix="/jornadas", tags=["Jornadas Laborales"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/", response_model=list[JornadaLaboralRead])
def listar_jornadas(session: SessionDep):
    """Retorna todas las jornadas laborales registradas."""
    return get_all_jornadas(session)


@router.get("/filtrar", response_model=list[JornadaLaboralRead])
def filtrar_jornadas(
    session: SessionDep,
    empleado_id: int | None = Query(default=None, description="Filtrar por ID de empleado"),
    cliente: str | None = Query(default=None, description="Filtrar por nombre de cliente (parcial)"),
    fecha_desde: date | None = Query(default=None, description="Fecha de inicio del rango (YYYY-MM-DD)"),
    fecha_hasta: date | None = Query(default=None, description="Fecha de fin del rango (YYYY-MM-DD)"),
):
    """Filtra jornadas por empleado, cliente y/o rango de fechas. Todos los filtros son opcionales."""
    return filter_jornadas(session, empleado_id, cliente, fecha_desde, fecha_hasta)


@router.get("/{jornada_id}", response_model=JornadaLaboralRead)
def obtener_jornada(jornada_id: int, session: SessionDep):
    """Retorna una jornada laboral según su id."""
    return get_jornada_by_id(jornada_id, session)


@router.post("/", response_model=JornadaLaboralRead, status_code=status.HTTP_201_CREATED)
def crear_jornada(payload: JornadaLaboralCreate, session: SessionDep):
    """Crea una nueva jornada laboral con los datos recibidos."""
    return create_jornada(payload, session)


@router.patch("/{jornada_id}", response_model=JornadaLaboralRead)
def actualizar_jornada(jornada_id: int, payload: JornadaLaboralUpdate, session: SessionDep):
    """Actualiza parcialmente los datos de una jornada existente."""
    return update_jornada(jornada_id, payload, session)


@router.delete("/{jornada_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_jornada(jornada_id: int, session: SessionDep):
    """Elimina una jornada laboral según su id."""
    delete_jornada(jornada_id, session)
