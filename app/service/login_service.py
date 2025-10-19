# app/service/login_service.py
from typing import Optional
from domain.User import User
import db

def login(username: str, password: str) -> User:
    """Validate credentials and return the user."""
    return db.login(username, password)

def get_current_user() -> Optional[User]:
    """Return the current logged-in user (session)."""
    return db.current_user

def set_current_user(user: Optional[User]) -> None:
    """Set or clear the current session user."""
    db.current_user = user
