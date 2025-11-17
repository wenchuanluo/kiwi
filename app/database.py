# app/database.py

from sqlalchemy import create_engine
from app.config import database_config   


def _get_connection_string(config: dict) -> str:
    user = config["user"]
    password = config["password"]
    host = config["host"]
    port = config["port"]
    database = config["database"]
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


engine = create_engine(_get_connection_string(database_config))
