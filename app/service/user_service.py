# app/service/user_service.py
from typing import List, Optional

from app.domain import User, Portfolio, Security, Investment, Transaction
from app.db import db

class UnsupportedUserOperationError(Exception):
    """Raised when a user operation violates business rules."""
    pass

def list_users() -> List[User]:
    """Return all users from the database."""
    session = db.session
    users: List[User] = session.query(User).all()
    return users

def create_user(user: User) -> None:
    """
    Create a new user in the database.
    Raises ValueError if the username already exists.
    Raises UnsupportedUserOperationError if trying to create an admin user.
    """
    session = db.session

    if getattr(user, "role", "user") != "user":
        raise UnsupportedUserOperationError(
            "Only regular users can be created. Admin accounts must be seeded."
        )

    existing = session.get(User, user.username)
    if existing is not None:
        raise ValueError(f"User '{user.username}' already exists.")

    session.add(user)
    session.commit()
    session.refresh(user)

def delete_user(username: str, requester: Optional[User] = None) -> None:
    """
    Delete a user with safety checks:
      - Cannot delete yourself (if requester is provided).
      - Cannot delete the last remaining admin.
      - Cannot delete a user who still owns portfolios.
      - Raises ValueError if the user does not exist.
    """
    if requester is not None and requester.username == username:
        raise UnsupportedUserOperationError("You cannot delete your own account.")

    session = db.session
    user = session.get(User, username)
    if user is None:
        raise ValueError(f"User '{username}' does not exist.")

    if user.role == "admin":
        admin_count = session.query(User).filter(User.role == "admin").count()
        if admin_count <= 1:
            raise UnsupportedUserOperationError("Cannot delete the last remaining admin user.")

    portfolio_count = session.query(Portfolio).filter(Portfolio.owner == username).count()
    if portfolio_count > 0:
        raise UnsupportedUserOperationError(
            f"Cannot delete user '{username}' because they still own "
            f"{portfolio_count} portfolio(s). Please delete or reassign "
            "those portfolios first."
        )

    session.delete(user)
    session.commit()

def authenticate(username: str, password: str) -> Optional[User]:
    """
    Simple login check.
    Returns the User if username/password match, or None otherwise.
    """
    session = db.session
    user = session.get(User, username)
    if user is None:
        return None
    if user.password != password:
        return None
    return user
