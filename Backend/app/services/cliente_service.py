from sqlmodel import Session, select

from app.models.models import Cliente

MAX_RESULTADOS_AUTOCOMPLETE = 10


def search_clientes(
    session: Session,
    search: str | None = None,
    limit: int = MAX_RESULTADOS_AUTOCOMPLETE,
) -> list[Cliente]:
    """Busca clientes por coincidencia parcial en el nombre. Optimizado para autocomplete."""
    query = select(Cliente)
    if search:
        query = query.where(Cliente.nombre.ilike(f"%{search}%"))
    query = query.limit(min(limit, MAX_RESULTADOS_AUTOCOMPLETE))
    return session.exec(query).all()
