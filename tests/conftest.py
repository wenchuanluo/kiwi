# tests/conftest.py
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import pytest
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base
from app.domain import User, Security, Portfolio


# ---------------------------------------------------------
# 1. ENGINE FIXTURE (once per entire test session)
# ---------------------------------------------------------
@pytest.fixture(scope="session")
def engine():
    """Create an in-memory SQLite engine for ALL tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


# ---------------------------------------------------------
# 2. DB SESSION FIXTURE (per test)
# ---------------------------------------------------------
@pytest.fixture(scope="function")
def db_session(engine, monkeypatch) -> Generator[Session, None, None]:
    """
    For each test:
    - open a new connection + transaction
    - create a Session bound to that transaction
    - monkeypatch app.database.get_session + service layer
    - load baseline data (including default admin)
    - roll back & close everything at end
    """
    # ---- open connection + transaction ----
    connection = engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    session: Session = TestingSessionLocal()

    # ---- monkeypatch get_session() everywhere ----
    import app.database as db
    from app.service import (
        user_service,
        portfolio_service,
        security_service,
        login_service,
    )

    monkeypatch.setattr(db, "get_session", lambda: session, raising=True)
    monkeypatch.setattr(user_service, "get_session", lambda: session, raising=True)
    monkeypatch.setattr(portfolio_service, "get_session", lambda: session, raising=True)
    monkeypatch.setattr(security_service, "get_session", lambda: session, raising=True)
    monkeypatch.setattr(login_service, "get_session", lambda: session, raising=True)

    # ---- load baseline data (NOW including admin) ----
    _populate_database(session)

    try:
        yield session
    finally:
        # ---- rollback all changes from this test ----
        session.close()
        transaction.rollback()
        connection.close()


# ---------------------------------------------------------
# 3. Baseline data inserted for EVERY test
# ---------------------------------------------------------
def _populate_database(session: Session) -> None:
    """
    Insert baseline data for every test:
    - EXACTLY 1 admin user
    - Some securities
    """
    # ---- DEFAULT ADMIN (always exists in tests) ----
    admin = User(
        username="admin",
        password="adminpass",
        firstname="Admin",
        lastname="Admin",
        role="admin",
        balance=0.0,
    )
    session.add(admin)

    # ---- Securities ----
    securities = [
        Security(ticker="AAPL", issuer="Apple Inc.", price=175.00),
        Security(ticker="TSLA", issuer="Tesla Inc.", price=250.00),
        Security(ticker="LULU", issuer="Lululemon Athletica Inc", price=168.00),
    ]
    session.add_all(securities)

    session.commit()


