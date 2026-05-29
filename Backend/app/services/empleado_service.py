from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.models import Empleado, EmpleadoCreate, EmpleadoUpdate


def get_all_empleados(session: Session) -> list[Empleado]:
    """Devuelve la lista completa de empleados registrados."""
    return session.exec(select(Empleado)).all()


def search_empleados(q: str, session: Session) -> list[Empleado]:
    """
    Busca empleados cuyo nombre completo o DNI contengan el texto recibido.
    La búsqueda es case-insensitive.
    """
    termino = f"%{q}%"
    return session.exec(
        select(Empleado).where(
            Empleado.nombre_completo.ilike(termino) | Empleado.dni.ilike(termino)
        )
    ).all()


def get_empleado_by_id(empleado_id: int, session: Session) -> Empleado:
    """Busca un empleado por su id. Lanza 404 si no existe."""
    empleado = session.get(Empleado, empleado_id)
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con id {empleado_id} no encontrado",
        )
    return empleado


def create_empleado(payload: EmpleadoCreate, session: Session) -> Empleado:
    """
    Crea un nuevo empleado.
    Lanza 409 si ya existe otro empleado con el mismo DNI.
    """
    dni_existente = session.exec(
        select(Empleado).where(Empleado.dni == payload.dni)
    ).first()
    if dni_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un empleado con el DNI {payload.dni}",
        )
    empleado = Empleado.model_validate(payload)
    session.add(empleado)
    session.commit()
    session.refresh(empleado)
    return empleado


def update_empleado(
    empleado_id: int, payload: EmpleadoUpdate, session: Session
) -> Empleado:
    """
    Actualiza los campos enviados de un empleado existente.
    Lanza 404 si no existe y 409 si el nuevo DNI ya pertenece a otro empleado.
    """
    empleado = session.get(Empleado, empleado_id)
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con id {empleado_id} no encontrado",
        )

    datos = payload.model_dump(exclude_unset=True)

    if "dni" in datos:
        conflicto = session.exec(
            select(Empleado)
            .where(Empleado.dni == datos["dni"])
            .where(Empleado.id != empleado_id)
        ).first()
        if conflicto:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El DNI {datos['dni']} ya está en uso por otro empleado",
            )

    empleado.sqlmodel_update(datos)
    empleado.updated_at = datetime.now(timezone.utc)
    session.add(empleado)
    session.commit()
    session.refresh(empleado)
    return empleado


def toggle_empleado_activo(empleado_id: int, session: Session) -> Empleado:
    """
    Invierte el estado is_active de un empleado.
    Lanza 404 si no existe.
    """
    empleado = session.get(Empleado, empleado_id)
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con id {empleado_id} no encontrado",
        )
    empleado.is_active = not empleado.is_active
    empleado.updated_at = datetime.now(timezone.utc)
    session.add(empleado)
    session.commit()
    session.refresh(empleado)
    return empleado


def delete_empleado(empleado_id: int, session: Session) -> None:
    """Elimina un empleado por su id. Lanza 404 si no existe."""
    empleado = session.get(Empleado, empleado_id)
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con id {empleado_id} no encontrado",
        )
    session.delete(empleado)
    session.commit()
