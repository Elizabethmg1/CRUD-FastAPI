import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database.config import create_db_and_tables
from app.routers import ALL_ROUTERS


def parse_allowed_origins() -> list[str]:
    raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


app = FastAPI(
    title="Pruebas Backend API",
    description="API de gestión de empleados.",
    version="0.1.0",
)

allowed_origins = parse_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail},
    )


_VALIDATION_MESSAGES: dict[str, str] = {
    "field required": "Faltan campos obligatorios",
    "value is not a valid integer": "El valor debe ser un número entero",
    "value is not a valid email address": "El correo electrónico no es válido",
    "string should have at least": "DNI inválido: debe tener entre 7 y 9 dígitos",
    "string should have at most": "DNI inválido: debe tener entre 7 y 9 dígitos",
    "ensure this value has at least": "DNI inválido: debe tener entre 7 y 9 dígitos",
    "ensure this value has at most": "DNI inválido: debe tener entre 7 y 9 dígitos",
}


def _traducir_error(msg: str) -> str:
    msg_lower = msg.lower()
    for key, traduccion in _VALIDATION_MESSAGES.items():
        if key in msg_lower:
            return traduccion
    return msg.replace("Value error, ", "")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    message = _traducir_error(errors[0]["msg"]) if errors else "Datos inválidos"
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": message},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Error interno del servidor"},
    )


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/", tags=["health"])
def read_root() -> dict[str, str]:
    return {"status": "ok", "service": "pruebas-backend"}


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


for router in ALL_ROUTERS:
    app.include_router(router)
