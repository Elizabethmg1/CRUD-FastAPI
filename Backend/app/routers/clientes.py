from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.database.config import get_session
from app.models.models import ClienteCreate, ClienteRead
from app.services.cliente_service import search_clientes

router = APIRouter(prefix="/clientes", tags=["Clientes"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/", response_model=list[ClienteRead])
def buscar_clientes(
    session: SessionDep,
    search: str | None = Query(default=None, description="Texto para búsqueda parcial por nombre"),
    limit: int = Query(default=10, ge=1, le=50, description="Cantidad máxima de resultados"),
):
    """Busca clientes por nombre (coincidencia parcial). Optimizado para autocomplete."""
    return search_clientes(session, search, limit)


@router.post("/", response_model=ClienteRead, status_code=201)
def crear_cliente(payload: ClienteCreate, session: SessionDep):
    """Crea un nuevo cliente."""
    from app.models.models import Cliente

    cliente = Cliente.model_validate(payload)
    session.add(cliente)
    session.commit()
    session.refresh(cliente)
    return cliente
