from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.database.config import get_session
from app.models.models import EmpleadoCreate, EmpleadoRead, EmpleadoUpdate
from app.services.empleado_service import (
    create_empleado,
    delete_empleado,
    get_all_empleados,
    get_empleado_by_id,
    search_empleados,
    toggle_empleado_activo,
    update_empleado,
)

router = APIRouter(prefix="/empleados", tags=["Empleados"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/", response_model=list[EmpleadoRead])
def listar_empleados(session: SessionDep):
    """Retorna todos los empleados."""
    return get_all_empleados(session)


@router.get("/buscar", response_model=list[EmpleadoRead])
def buscar_empleados(
    session: SessionDep,
    q: str = Query(min_length=1, description="Texto a buscar en nombre o DNI"),
):
    """Busca empleados por nombre completo o DNI (búsqueda parcial, sin distinción de mayúsculas)."""
    return search_empleados(q, session)


@router.get("/{empleado_id}", response_model=EmpleadoRead)
def obtener_empleado(empleado_id: int, session: SessionDep):
    """Retorna un empleado según su id."""
    return get_empleado_by_id(empleado_id, session)


@router.post("/", response_model=EmpleadoRead, status_code=status.HTTP_201_CREATED)
def crear_empleado(payload: EmpleadoCreate, session: SessionDep):
    """Crea un nuevo empleado con los datos recibidos."""
    return create_empleado(payload, session)


@router.patch("/{empleado_id}", response_model=EmpleadoRead)
def actualizar_empleado(empleado_id: int, payload: EmpleadoUpdate, session: SessionDep):
    """Actualiza parcialmente los datos de un empleado existente."""
    return update_empleado(empleado_id, payload, session)


@router.patch("/{empleado_id}/toggle-activo", response_model=EmpleadoRead)
def toggle_activo_empleado(empleado_id: int, session: SessionDep):
    """Activa o desactiva un empleado según su estado actual."""
    return toggle_empleado_activo(empleado_id, session)


@router.delete("/{empleado_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_empleado(empleado_id: int, session: SessionDep):
    """Elimina un empleado según su id."""
    delete_empleado(empleado_id, session)
