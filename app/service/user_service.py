# app/service/user_service.py
from typing import List, Optional
from domain.User import User
import db

def list_users() -> List[User]:
    """Return all users."""
    return db.list_users()

def create_user(user: User) -> None:
    """Create a user with validations handled in db.py."""
    db.create_new_user(user)

def delete_user(username: str, requester: Optional[User] = None) -> None:
    """Delete a user with safety checks (cannot delete self/last admin)."""
    db.delete_user(username, requester=requester)
