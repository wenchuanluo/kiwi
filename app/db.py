from domain.User import User
from typing import Dict, List

_user: Dict[str, User] = {
    "admin": User("admin", "adminpass", "Admin Firstname", "Admin Lastname", 0.0)
}

def query_user(username: str) -> User|None:
    try:
        return _user[username]
    except KeyError as ke:
        return None

def query_all_users() -> list[User]:
    return list(_user.values())


def create_new_user(user: User):
    # check if user already exists otherwise add to db
    _user[user.username] = user