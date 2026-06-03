from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.models import Empleado, JornadaLaboral, JornadaLaboralCreate, JornadaLaboralUpdate


def _get_or_404(jornada_id: int, session: Session) -> JornadaLaboral:
    jornada = session.get(JornadaLaboral, jornada_id)
    if not jornada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jornada con id {jornada_id} no encontrada",
        )
    return jornada


def _validar_empleado(empleado_id: int, session: Session) -> None:
    empleado = session.get(Empleado, empleado_id)
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empleado con id {empleado_id} no encontrado",
        )
    if not empleado.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El empleado con id {empleado_id} está inactivo",
        )


def get_all_jornadas(session: Session) -> list[JornadaLaboral]:
    """Devuelve todas las jornadas registradas."""
    return session.exec(select(JornadaLaboral)).all()


def get_jornada_by_id(jornada_id: int, session: Session) -> JornadaLaboral:
    """Busca una jornada por su id. Lanza 404 si no existe."""
    return _get_or_404(jornada_id, session)


def filter_jornadas(
    session: Session,
    empleado_id: int | None = None,
    cliente: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
) -> list[JornadaLaboral]:
    """
    Filtra jornadas por empleado, cliente y/o rango de fechas.
    Todos los filtros son opcionales y se combinan entre sí.
    """
    query = select(JornadaLaboral)

    if empleado_id is not None:
        query = query.where(JornadaLaboral.empleado_id == empleado_id)
    if cliente is not None:
        query = query.where(JornadaLaboral.cliente.ilike(f"%{cliente}%"))
    if fecha_desde is not None:
        query = query.where(JornadaLaboral.fecha >= fecha_desde)
    if fecha_hasta is not None:
        query = query.where(JornadaLaboral.fecha <= fecha_hasta)

    return session.exec(query).all()


def create_jornada(payload: JornadaLaboralCreate, session: Session) -> JornadaLaboral:
    """
    Crea una nueva jornada laboral.
    Valida que el empleado exista y esté activo.
    Lanza 422 si hora_fin es menor o igual a hora_inicio.
    """
    _validar_empleado(payload.empleado_id, session)

    if payload.hora_fin <= payload.hora_inicio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La hora de fin debe ser posterior a la hora de inicio",
        )

    jornada = JornadaLaboral.model_validate(payload)
    session.add(jornada)
    session.commit()
    session.refresh(jornada)
    return jornada


def update_jornada(
    jornada_id: int, payload: JornadaLaboralUpdate, session: Session
) -> JornadaLaboral:
    """
    Actualiza los campos enviados de una jornada existente.
    Lanza 404 si no existe. Valida empleado y coherencia de horarios.
    """
    jornada = _get_or_404(jornada_id, session)
    datos = payload.model_dump(exclude_unset=True)

    if "empleado_id" in datos:
        _validar_empleado(datos["empleado_id"], session)

    hora_inicio = datos.get("hora_inicio", jornada.hora_inicio)
    hora_fin = datos.get("hora_fin", jornada.hora_fin)
    if hora_fin <= hora_inicio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La hora de fin debe ser posterior a la hora de inicio",
        )

    jornada.sqlmodel_update(datos)
    jornada.updated_at = datetime.now(timezone.utc)
    session.add(jornada)
    session.commit()
    session.refresh(jornada)
    return jornada


def delete_jornada(jornada_id: int, session: Session) -> None:
    """Elimina una jornada por su id. Lanza 404 si no existe."""
    jornada = _get_or_404(jornada_id, session)
    session.delete(jornada)
    session.commit()
