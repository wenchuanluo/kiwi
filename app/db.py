from domain.User import User
from typing import Dict, List, Optional   # CHANGED: 加 Optional

# --- Seed securities catalog (mock database) ---------------------------------
# Keep the structure simple: ticker -> {name, reference_price}
_securities: Dict[str, Dict[str, float | str]] = {
    "AAPL": {"name": "Apple Inc.",       "reference_price": 190.00},
    "MSFT": {"name": "Microsoft Corp.",  "reference_price": 420.00},
    "GOOGL": {"name": "Alphabet Inc.",   "reference_price": 155.00},
}

def list_securities() -> List[Dict[str, float | str]]:
    """
    Return a list of dicts, each containing:
      {'ticker': str, 'name': str, 'reference_price': float}
    This is used by the CLI to print a table.
    """
    rows: List[Dict[str, float | str]] = []
    for ticker, data in _securities.items():
        rows.append({
            "ticker": ticker,
            "name": data["name"],
            "reference_price": float(data["reference_price"]),
        })
    return rows

def get_security(ticker: str) -> Optional[Dict[str, float | str]]:
    """
    Return a single security dict or None if not found.
    """
    data = _securities.get(ticker.upper())
    if not data:
        return None
    return {
        "ticker": ticker.upper(),
        "name": data["name"],
        "reference_price": float(data["reference_price"]),
    }

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
