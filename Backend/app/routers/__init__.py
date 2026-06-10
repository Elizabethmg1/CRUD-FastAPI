from app.routers.asistencias import router as asistencias_router
from app.routers.clientes import router as clientes_router
from app.routers.empleados import router as empleados_router
from app.routers.jornadas import router as jornadas_router

ALL_ROUTERS = [
    empleados_router,
    jornadas_router,
    clientes_router,
    asistencias_router,
]
