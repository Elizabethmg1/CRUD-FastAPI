from datetime import date
from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlmodel import Session

from app.database.config import get_session
from app.models.models import RegistroHorasRead
from app.services.registro_horas_service import get_registro_horas

router = APIRouter(prefix="/registro-horas", tags=["Registro de Horas"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/", response_model=list[RegistroHorasRead])
def listar_registro_horas(
    session: SessionDep,
    fecha: date | None = Query(default=None, description="Filtrar por fecha (YYYY-MM-DD)"),
    empleado: str | None = Query(default=None, description="Filtrar por nombre o DNI del empleado"),
    cliente: str | None = Query(default=None, description="Filtrar por nombre de cliente (parcial)"),
    direccion: str | None = Query(default=None, description="Filtrar por dirección (parcial)"),
    search: str | None = Query(default=None, description="Búsqueda general"),
):
    """Retorna el registro de horas con filtros opcionales."""
    return get_registro_horas(session, fecha, empleado, cliente, direccion, search)


@router.get("/export")
def exportar_registro_horas(
    session: SessionDep,
    fecha: date | None = Query(default=None, description="Filtrar por fecha (YYYY-MM-DD)"),
    empleado: str | None = Query(default=None, description="Filtrar por nombre o DNI del empleado"),
    cliente: str | None = Query(default=None, description="Filtrar por nombre de cliente (parcial)"),
    direccion: str | None = Query(default=None, description="Filtrar por dirección (parcial)"),
    search: str | None = Query(default=None, description="Búsqueda general"),
):
    """Exporta el registro de horas a un archivo Excel (.xlsx)."""
    registros = get_registro_horas(session, fecha, empleado, cliente, direccion, search)

    wb = Workbook()
    ws = wb.active
    ws.title = "RegistroHoras"

    headers = [
        "fecha",
        "empleado",
        "cliente",
        "direccion",
        "hora_entrada",
        "hora_salida",
        "horas_estimadas",
        "horas_realizadas",
        "horas_extras",
        "horas_a_descontar",
        "estado",
        "message",
    ]
    ws.append(headers)

    for item in registros:
        ws.append(
            [
                item.fecha.isoformat(),
                item.empleado,
                item.cliente,
                item.direccion,
                item.hora_entrada,
                item.hora_salida,
                item.horas_estimadas,
                item.horas_realizadas,
                item.horas_extras,
                item.horas_a_descontar,
                item.estado,
                item.message,
            ]
        )

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    headers_resp = {
        "Content-Disposition": "attachment; filename=registro_horas.xlsx",
    }

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers_resp,
    )
