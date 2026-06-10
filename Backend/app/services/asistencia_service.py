from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlmodel import Session, select

from app.models.models import (
    Asistencia,
    AsistenciaCreate,
    AsistenciaRead,
    Cliente,
    Empleado,
    TipoAsistencia,
)

# Ventana de tiempo para detectar registros duplicados
DUPLICATE_WINDOW_SECONDS = 60


def _get_empleado_by_dni(dni: str, session: Session) -> Empleado:
    empleado = session.exec(select(Empleado).where(Empleado.dni == dni)).first()
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado",
        )
    if not empleado.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El empleado está inactivo",
        )
    return empleado


def _get_cliente(cliente_id: int, session: Session) -> Cliente:
    cliente = session.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado",
        )
    return cliente


def _ultimo_registro(empleado_id: int, session: Session) -> Asistencia | None:
    return session.exec(
        select(Asistencia)
        .where(Asistencia.empleado_id == empleado_id)
        .order_by(desc(Asistencia.fecha_hora))
        .limit(1)
    ).first()


def _make_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def create_asistencia(payload: AsistenciaCreate, session: Session) -> None:
    """
    Registra una asistencia (entrada o salida).
    Valida: empleado activo, cliente existente, sin duplicados y coherencia entrada/salida.
    """
    empleado = _get_empleado_by_dni(payload.dni, session)
    _get_cliente(payload.cliente_id, session)

    ultimo = _ultimo_registro(empleado.id, session)
    ahora = datetime.now(timezone.utc)

    if ultimo:
        ultimo_dt = _make_aware(ultimo.fecha_hora)

        # Registro duplicado: mismo tipo en menos de DUPLICATE_WINDOW_SECONDS
        if ultimo.tipo == payload.tipo:
            segundos = (ahora - ultimo_dt).total_seconds()
            if segundos < DUPLICATE_WINDOW_SECONDS:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Registro duplicado: ya se registró este tipo en el último minuto",
                )

        # No permitir dos entradas consecutivas
        if payload.tipo == TipoAsistencia.entrada and ultimo.tipo == TipoAsistencia.entrada:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una entrada activa",
            )

        # No permitir salida sin entrada previa activa
        if payload.tipo == TipoAsistencia.salida and ultimo.tipo == TipoAsistencia.salida:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No hay una entrada activa para registrar la salida",
            )
    else:
        # Sin registros previos: sólo se permite entrada
        if payload.tipo == TipoAsistencia.salida:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No hay una entrada activa para registrar la salida",
            )

    asistencia = Asistencia(
        tipo=payload.tipo,
        empleado_id=empleado.id,
        cliente_id=payload.cliente_id,
        direccion=payload.direccion,
        fecha_hora=ahora,
    )
    session.add(asistencia)
    session.commit()


def get_historial(
    session: Session,
    dni: str | None = None,
    cliente: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    tipo: TipoAsistencia | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[AsistenciaRead]:
    """
    Devuelve el historial de asistencias con filtros opcionales combinables.
    Ordenado por fecha_hora descendente, paginado.
    """
    from sqlalchemy import select as sa_select

    stmt = (
        sa_select(
            Asistencia.id,
            Asistencia.tipo,
            Empleado.dni,
            Cliente.nombre.label("cliente"),
            Asistencia.direccion,
            Asistencia.fecha_hora,
        )
        .join(Empleado, Asistencia.empleado_id == Empleado.id)
        .join(Cliente, Asistencia.cliente_id == Cliente.id)
    )

    if dni:
        stmt = stmt.where(Empleado.dni == dni)
    if cliente:
        stmt = stmt.where(Cliente.nombre.ilike(f"%{cliente}%"))
    if desde:
        stmt = stmt.where(Asistencia.fecha_hora >= datetime(desde.year, desde.month, desde.day))
    if hasta:
        stmt = stmt.where(
            Asistencia.fecha_hora < datetime(hasta.year, hasta.month, hasta.day) + timedelta(days=1)
        )
    if tipo:
        stmt = stmt.where(Asistencia.tipo == tipo)

    stmt = stmt.order_by(desc(Asistencia.fecha_hora)).offset(skip).limit(limit)

    rows = session.execute(stmt).mappings().all()
    return [AsistenciaRead(**row) for row in rows]
