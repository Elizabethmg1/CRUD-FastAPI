from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database.config import get_session
from app.models.models import Empleado, EmpleadoCreate, EmpleadoRead, EmpleadoUpdate

router = APIRouter(prefix="/empleados", tags=["Empleados"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/", response_model=list[EmpleadoRead])
def listar_empleados(session: SessionDep):
    empleados = session.exec(select(Empleado)).all()
    return empleados


@router.get("/{empleado_id}", response_model=EmpleadoRead)
def obtener_empleado(empleado_id: int, session: SessionDep):
    empleado = session.get(Empleado, empleado_id)
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con id {empleado_id} no encontrado",
        )
    return empleado


@router.post("/", response_model=EmpleadoRead, status_code=status.HTTP_201_CREATED)
def crear_empleado(payload: EmpleadoCreate, session: SessionDep):
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


@router.patch("/{empleado_id}", response_model=EmpleadoRead)
def actualizar_empleado(
    empleado_id: int, payload: EmpleadoUpdate, session: SessionDep
):
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


@router.delete("/{empleado_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_empleado(empleado_id: int, session: SessionDep):
    empleado = session.get(Empleado, empleado_id)
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con id {empleado_id} no encontrado",
        )
    session.delete(empleado)
    session.commit()
