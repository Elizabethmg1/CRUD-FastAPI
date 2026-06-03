from app.routers.empleados import router as empleados_router
from app.routers.jornadas import router as jornadas_router

ALL_ROUTERS = [
    empleados_router,
    jornadas_router,
]
