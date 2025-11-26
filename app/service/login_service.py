# app/service/login_service.py

from typing import Optional

from app.domain import User, Portfolio, Security, Investment, Transaction
from app.database import get_session
from app import session_state


def login(username: str, password: str) -> Optional[User]:
    """
    Validate credentials against the database.
    If valid, store the user in session_state and return the User.
    If invalid, return None.
    """
    session = get_session()
    try:
        user = session.get(User, username)
        if user is None:
            return None
        if user.password != password:
            return None

        # Store in session state
        session_state.set_current_user(user)
        return user
    finally:
        session.close()


def logout() -> None:
    """
    Clear the current session.
    """
    session_state.clear_session()


def get_current_user() -> Optional[User]:
    """
    Convenience wrapper to read the current user from session_state.
    Kept here so CLI layers can continue importing from login_service.
    """
    return session_state.get_current_user()
