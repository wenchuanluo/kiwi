from domain.User import User
from typing import Dict, List, Optional   # CHANGED: 加 Optional

_user: Dict[str, User] = {
    "admin": User("admin", "adminpass", "Admin Firstname", "Admin Lastname", 0.0)
}

# NEW: current logged-in use
current_user: Optional[User] = None

def query_user(username: str) -> User|None:
    try:
        return _user[username]
    except KeyError as ke:
        return None

def query_all_users() -> list[User]:
    return list(_user.values())

    # CHANGED:     # check if user already exists otherwise add to db

    if user.username in _user:
        raise ValueError(f"Username '{user.username}' already exists.")
    _user[user.username] = user

# NEW: successfully, return user, otherwise raise exception
def login(username: str, password: str) -> User:
    user = _user.get(username)
    if not user or user.password != password:
        raise ValueError("Invalid username or password.")
    return user
