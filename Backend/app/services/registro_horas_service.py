from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from sqlmodel import Session

from app.models.models import Asistencia, Cliente, Empleado, JornadaLaboral, RegistroHorasRead, TipoAsistencia


@dataclass(frozen=True)
class _AsistenciaItem:
    tipo: TipoAsistencia
    cliente: str
    direccion: str
    fecha_hora: datetime


def _normalizar(texto: str) -> str:
    return texto.strip().lower()


def _format_hora(valor: datetime | None) -> str | None:
    if not valor:
        return None
    return valor.strftime("%H:%M")


def _horas_entre(inicio: time, fin: time) -> float:
    inicio_dt = datetime.combine(date.min, inicio)
    fin_dt = datetime.combine(date.min, fin)
    return (fin_dt - inicio_dt).total_seconds() / 3600


def _horas_entre_dt(inicio: datetime, fin: datetime) -> float:
    return (fin - inicio).total_seconds() / 3600


def _rango_dia(fecha: date) -> tuple[datetime, datetime]:
    inicio = datetime(fecha.year, fecha.month, fecha.day, tzinfo=timezone.utc)
    fin = inicio + timedelta(days=1)
    return inicio, fin


def _fetch_asistencias(
    session: Session, empleado_id: int, fecha: date
) -> list[_AsistenciaItem]:
    from sqlalchemy import select as sa_select

    inicio, fin = _rango_dia(fecha)

    stmt = (
        sa_select(
            Asistencia.tipo,
            Cliente.nombre.label("cliente"),
            Asistencia.direccion,
            Asistencia.fecha_hora,
        )
        .join(Cliente, Asistencia.cliente_id == Cliente.id)
        .where(
            Asistencia.empleado_id == empleado_id,
            Asistencia.fecha_hora >= inicio,
            Asistencia.fecha_hora < fin,
        )
        .order_by(Asistencia.fecha_hora.asc())
    )
    rows = session.execute(stmt).mappings().all()
    return [_AsistenciaItem(**row) for row in rows]


def _resolver_asistencia(
    asistencias: list[_AsistenciaItem],
    jornada_cliente: str,
    jornada_direccion: str,
) -> tuple[
    datetime | None,
    datetime | None,
    str | None,
    str | None,
    bool,
]:
    if not asistencias:
        return None, None, "incompleta", "Sin asistencia registrada", False

    cliente_norm = _normalizar(jornada_cliente)
    direccion_norm = _normalizar(jornada_direccion)
    coincidentes = [
        item
        for item in asistencias
        if _normalizar(item.cliente) == cliente_norm
        and _normalizar(item.direccion) == direccion_norm
    ]

    if not coincidentes:
        return None, None, "inconsistente", "Jornada modificada o eliminada", False

    entradas = [item.fecha_hora for item in coincidentes if item.tipo == TipoAsistencia.entrada]
    salidas = [item.fecha_hora for item in coincidentes if item.tipo == TipoAsistencia.salida]

    if not entradas and not salidas:
        return None, None, "incompleta", "Sin asistencia registrada", False
    if entradas and not salidas:
        return min(entradas), None, "incompleta", "Falta registrar salida", False
    if salidas and not entradas:
        return None, max(salidas), "incompleta", "Falta registrar entrada", False

    entrada = min(entradas)
    salida = max(salidas)
    if salida <= entrada:
        return entrada, salida, "incompleta", "Salida anterior a la entrada", False

    return entrada, salida, None, None, True


def get_registro_horas(
    session: Session,
    fecha: date | None = None,
    empleado: str | None = None,
    cliente: str | None = None,
    direccion: str | None = None,
    search: str | None = None,
) -> list[RegistroHorasRead]:
    from sqlalchemy import or_, select as sa_select

    stmt = (
        sa_select(
            JornadaLaboral,
            Empleado.nombre_completo.label("empleado_nombre"),
            Empleado.dni.label("empleado_dni"),
        )
        .join(Empleado, JornadaLaboral.empleado_id == Empleado.id)
        .order_by(JornadaLaboral.fecha.desc(), JornadaLaboral.hora_inicio.asc())
    )

    if fecha:
        stmt = stmt.where(JornadaLaboral.fecha == fecha)
    if empleado:
        stmt = stmt.where(
            or_(
                Empleado.nombre_completo.ilike(f"%{empleado}%"),
                Empleado.dni.ilike(f"%{empleado}%"),
            )
        )
    if cliente:
        stmt = stmt.where(JornadaLaboral.cliente.ilike(f"%{cliente}%"))
    if direccion:
        stmt = stmt.where(JornadaLaboral.direccion.ilike(f"%{direccion}%"))
    if search:
        stmt = stmt.where(
            or_(
                Empleado.nombre_completo.ilike(f"%{search}%"),
                Empleado.dni.ilike(f"%{search}%"),
                JornadaLaboral.cliente.ilike(f"%{search}%"),
                JornadaLaboral.direccion.ilike(f"%{search}%"),
            )
        )

    jornadas = session.execute(stmt).all()
    cache_asistencias: dict[tuple[int, date], list[_AsistenciaItem]] = {}
    resultados: list[RegistroHorasRead] = []

    for jornada, empleado_nombre, _empleado_dni in jornadas:
        cache_key = (jornada.empleado_id, jornada.fecha)
        asistencias = cache_asistencias.get(cache_key)
        if asistencias is None:
            asistencias = _fetch_asistencias(session, jornada.empleado_id, jornada.fecha)
            cache_asistencias[cache_key] = asistencias

        entrada, salida, estado, mensaje, completa = _resolver_asistencia(
            asistencias, jornada.cliente, jornada.direccion
        )

        horas_estimadas = _horas_entre(jornada.hora_inicio, jornada.hora_fin)
        horas_realizadas = 0.0
        horas_extras = 0.0
        horas_a_descontar = 0.0

        if completa and entrada and salida:
            horas_realizadas = _horas_entre_dt(entrada, salida)
            horas_extras = max(horas_realizadas - horas_estimadas, 0.0)
            horas_a_descontar = max(horas_estimadas - horas_realizadas, 0.0)

        resultados.append(
            RegistroHorasRead(
                fecha=jornada.fecha,
                empleado=empleado_nombre,
                cliente=jornada.cliente,
                direccion=jornada.direccion,
                hora_entrada=_format_hora(entrada),
                hora_salida=_format_hora(salida),
                horas_estimadas=round(horas_estimadas, 2),
                horas_realizadas=round(horas_realizadas, 2),
                horas_extras=round(horas_extras, 2),
                horas_a_descontar=round(horas_a_descontar, 2),
                estado=estado,
                message=mensaje,
            )
        )

    return resultados
