import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
