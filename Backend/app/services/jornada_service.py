from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.models import Empleado, JornadaLaboral, JornadaLaboralCreate, JornadaLaboralUpdate

MAX_HORAS_JORNADA = 12


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


def _validar_duracion(hora_inicio: time, hora_fin: time) -> None:
    """Lanza 422 si la jornada supera el máximo de horas permitidas."""
    inicio_dt = datetime.combine(date.min, hora_inicio)
    fin_dt = datetime.combine(date.min, hora_fin)
    if (fin_dt - inicio_dt) > timedelta(hours=MAX_HORAS_JORNADA):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"La jornada no puede superar las {MAX_HORAS_JORNADA} horas",
        )


def _validar_solapamiento(
    session: Session,
    empleado_id: int,
    fecha: date,
    hora_inicio: time,
    hora_fin: time,
    exclude_id: int | None = None,
) -> None:
    """Lanza 409 si la jornada se solapa con otra del mismo empleado en la misma fecha."""
    query = select(JornadaLaboral).where(
        JornadaLaboral.empleado_id == empleado_id,
        JornadaLaboral.fecha == fecha,
        JornadaLaboral.hora_inicio < hora_fin,
        JornadaLaboral.hora_fin > hora_inicio,
    )
    if exclude_id is not None:
        query = query.where(JornadaLaboral.id != exclude_id)

    conflicto = session.exec(query).first()
    if conflicto:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"La jornada se solapa con la jornada id={conflicto.id} "
                f"({conflicto.hora_inicio} - {conflicto.hora_fin}) del mismo empleado"
            ),
        )


def _validar_duplicado(
    session: Session,
    empleado_id: int,
    fecha: date,
    hora_inicio: time,
    hora_fin: time,
    exclude_id: int | None = None,
) -> None:
    """Lanza 409 si ya existe una jornada idéntica para el mismo empleado, fecha y horario."""
    query = select(JornadaLaboral).where(
        JornadaLaboral.empleado_id == empleado_id,
        JornadaLaboral.fecha == fecha,
        JornadaLaboral.hora_inicio == hora_inicio,
        JornadaLaboral.hora_fin == hora_fin,
    )
    if exclude_id is not None:
        query = query.where(JornadaLaboral.id != exclude_id)

    if session.exec(query).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una jornada idéntica para ese empleado en esa fecha y horario",
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

    _validar_duracion(payload.hora_inicio, payload.hora_fin)
    _validar_duplicado(session, payload.empleado_id, payload.fecha, payload.hora_inicio, payload.hora_fin)
    _validar_solapamiento(session, payload.empleado_id, payload.fecha, payload.hora_inicio, payload.hora_fin)

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

    empleado_id = datos.get("empleado_id", jornada.empleado_id)
    fecha = datos.get("fecha", jornada.fecha)
    hora_inicio = datos.get("hora_inicio", jornada.hora_inicio)
    hora_fin = datos.get("hora_fin", jornada.hora_fin)

    if hora_fin <= hora_inicio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La hora de fin debe ser posterior a la hora de inicio",
        )

    _validar_duracion(hora_inicio, hora_fin)
    _validar_duplicado(session, empleado_id, fecha, hora_inicio, hora_fin, exclude_id=jornada_id)
    _validar_solapamiento(session, empleado_id, fecha, hora_inicio, hora_fin, exclude_id=jornada_id)

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
