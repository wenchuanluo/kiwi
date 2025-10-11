from domain.User import User
from typing import Dict, List, Optional   # CHANGED: 加 Optional

# --- Seed securities catalog (mock database) ---------------------------------
# Keep the structure simple: ticker -> {name, reference_price}
_securities: Dict[str, Dict[str, float | str]] = {
    "AAPL": {"name": "Apple Inc.",       "reference_price": 190.00},
    "MSFT": {"name": "Microsoft Corp.",  "reference_price": 420.00},
    "GOOGL": {"name": "Alphabet Inc.",   "reference_price": 155.00},
}
# -------------------------------
# Seed portfolios (mock database)
# -------------------------------
# Portfolio model (simple dict for now):
# {
#   "id": int,
#   "owner_username": str,
#   "name": str,
#   "description": str,
#   "strategy": str,
#   "holdings": dict[str, float]  # ticker -> quantity
# }
_portfolios: Dict[int, Dict[str, object]] = {
    # Seed: admin owns one empty portfolio so you can buy right away
    1: {
        "id": 1,
        "owner_username": "admin",
        "name": "Admin Portfolio",
        "description": "Seed portfolio for the admin user",
        "strategy": "Core",
        "holdings": {},  # start empty
    }
}
_next_portfolio_id: int = 2  # if you later create more portfolios

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
    
def list_portfolios(owner_username: Optional[str] = None) -> List[Dict[str, object]]:
    """
    Return all portfolios or only those belonging to a specific user.
    """
    rows: List[Dict[str, object]] = []
    for p in _portfolios.values():
        if owner_username is None or p["owner_username"] == owner_username:
            rows.append(p)
    return rows

def get_portfolio(portfolio_id: int) -> Optional[Dict[str, object]]:
    """
    Return a portfolio dict or None.
    """
    return _portfolios.get(portfolio_id)

def get_market_price(ticker: str) -> float:
    """
    Return the reference market price for a ticker (raises if not found).
    """
    sec = get_security(ticker)
    if not sec:
        raise ValueError(f"Unknown ticker '{ticker}'.")
    return float(sec["reference_price"])


_user: Dict[str, User] = {
    "admin": User("admin", "adminpass", "Admin Firstname", "Admin Lastname", 100000.0)
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

def buy_security(portfolio_id: int, ticker: str, quantity: float, price: Optional[float] = None) -> Dict[str, object]:
    """
    Execute a BUY:
      - Validate current session user
      - Validate portfolio ownership
      - Validate ticker & quantity
      - Use given price or reference price
      - Check balance >= cost
      - Deduct balance and increase holdings

    Returns a summary dict with keys: portfolio_id, ticker, quantity, price, cost, balance_after.
    """
    if current_user is None:
        raise ValueError("No active session. Please login.")

    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise ValueError(f"Portfolio ID {portfolio_id} does not exist.")

    # Ownership check: only owner can trade this portfolio
    if portfolio["owner_username"] != current_user.username:
        raise ValueError("You do not own this portfolio.")

    ticker = ticker.upper().strip()
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")

    # Decide the price (reference price by default)
    trade_price = float(price) if price is not None else get_market_price(ticker)
    cost = trade_price * float(quantity)

    # Balance check
    if current_user.balance < cost:
        raise ValueError(f"Insufficient funds. Needed {cost:.2f}, available {current_user.balance:.2f}.")

    # Deduct balance
    current_user.balance -= cost

    # Update holdings
    holdings: Dict[str, float] = portfolio["holdings"]  # type: ignore[assignment]
    holdings[ticker] = float(holdings.get(ticker, 0.0) + float(quantity))

    return {
        "portfolio_id": portfolio_id,
        "ticker": ticker,
        "quantity": float(quantity),
        "price": trade_price,
        "cost": cost,
        "balance_after": current_user.balance,
    }
