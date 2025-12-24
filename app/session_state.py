# app/session_state.py
from typing import Optional
from app.domain import User

# Global variable to hold the current user object
_current_user: Optional[User] = None


def get_current_user() -> Optional[User]:
    """
    Return the currently logged-in User object, or None if no user is logged in.
    """
    return _current_user


def get_current_username() -> Optional[str]:
    """
    Convenience helper: return current username, or None.
    """
    user = get_current_user()
    return user.username if user else None


def set_current_user(user: User) -> None:
    """
    Set the current user after a successful login.
    """
    global _current_user
    if not isinstance(user, User):
        raise TypeError("Attempted to set session state with a non-User object.")
    _current_user = user


def clear_session() -> None:
    """
    Clear the current session (used on logout and in tests).
    """
    global _current_user
    _current_user = None
