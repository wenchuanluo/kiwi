# app/database.py: here we are setting up the database connection using SQLAlchemy and create a function to get new sessions to the database.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from app.config import database_config


class Base(DeclarativeBase):
    pass


def _get_connection_string(config: dict) -> str:
    user = config["user"]
    password = config["password"]
    host = config["host"]
    port = config["port"]
    database = config["database"]
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


engine = create_engine(
    _get_connection_string(database_config),
    echo=False,
    pool_pre_ping=True
)


LocalSession = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_session() -> Session:
    return LocalSession()

