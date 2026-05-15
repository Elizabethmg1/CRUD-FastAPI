from sqlmodel import Session, SQLModel, create_engine

SQLITE_URL = "sqlite:///./empleados.db"

# check_same_thread=False es necesario para SQLite con FastAPI
engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    echo=True,
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
