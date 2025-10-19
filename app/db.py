from domain.User import User
from datetime import datetime
from typing import Dict, List, Optional, TypedDict

# ---- Types (optional but recommended) ----
class SecurityRow(TypedDict):
    ticker: str
    issuer: str
    reference_price: float

# --- Seed securities catalog (mock database) ---------------------------------
# Keep the structure simple: ticker -> {issuer, reference_price}
_securities: Dict[str, Dict[str, float | str]] = {
    "AAPL": {"issuer": "Apple Inc.",      "reference_price": 190.00},
    "MSFT": {"issuer": "Microsoft Corp.", "reference_price": 420.00},
    "GOOGL": {"issuer": "Alphabet Inc.",  "reference_price": 155.00},
}
# ---------------- Current user (spec name + alias) ----------------
logged_in_user: Optional[User] = None     # spec 用名
current_user: Optional[User] = None       # 兼容你现有的调用

def set_current_user(u: Optional[User]) -> None:
    global logged_in_user, current_user
    logged_in_user = u
    current_user = u

def get_current_user() -> Optional[User]:
    return logged_in_user

def logout() -> None:
    set_current_user(None)

# -------------------------------
# Transactions (simple log store)
# -------------------------------
_transactions: List[Dict[str, object]] = []
_next_txn_id: int = 1

def _log_transaction(*, ttype: str, username: str, portfolio_id: int,
                     ticker: str, quantity: float, price: float, amount: float,
                     balance_after: float) -> Dict[str, object]:
    """
    Append a transaction record and return it.
    We keep a simple dict structure for the CLI.
    """
    global _next_txn_id
    row = {
        "id": _next_txn_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": ttype,  # "BUY" or "SELL"
        "username": username,
        "portfolio_id": portfolio_id,
        "ticker": ticker,
        "quantity": float(quantity),
        "price": float(price),
        "amount": float(amount),             # BUY cost / SELL proceeds
        "balance_after": float(balance_after),
    }
    _transactions.append(row)
    _next_txn_id += 1
    return row

def list_transactions(username: Optional[str] = None) -> List[Dict[str, object]]:
    """Return all transactions or only those of a given username."""
    if username is None:
        return list(_transactions)
    return [t for t in _transactions if t["username"] == username]

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

def list_securities() -> List[SecurityRow]:
    """
    Return a list of dicts, each containing:
      {'ticker': str, 'issuer': str, 'reference_price': float}
    This is used by the CLI to print a table.
    """
    rows: List[SecurityRow] = []
    for ticker, data in _securities.items():
        rows.append({
            "ticker": ticker,
            "issuer": str(data["issuer"]),
            "reference_price": float(data["reference_price"]),
        })
    return rows

def get_security(ticker: str) -> Optional[SecurityRow]:
    data = _securities.get(ticker.upper())
    if not data:
        return None
    return {
        "ticker": ticker.upper(),
        "issuer": str(data["issuer"]),
        "reference_price": float(data["reference_price"]),
    }

    
# ---------- Portfolio helpers: list/get/value/create/delete/sell ----------

def list_portfolios(owner_username: Optional[str] = None) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for p in _portfolios.values():
        if owner_username is None or p["owner_username"] == owner_username:
            rows.append(p)
    return rows

def get_portfolio(portfolio_id: int) -> Optional[Dict[str, object]]:
    return _portfolios.get(portfolio_id)


def portfolio_total_value(portfolio: Dict[str, object]) -> float:
    """
    Compute total value using reference prices.
    """
    holdings: Dict[str, float] = portfolio["holdings"]  # type: ignore[assignment]
    total = 0.0
    for ticker, qty in holdings.items():
        sec = get_security(ticker)
        if sec:
            total += float(qty) * float(sec["reference_price"])
    return total

def create_portfolio(owner_username: str, name: str, description: str, strategy: str) -> Dict[str, object]:
    """
    Create a new portfolio for the owner. Returns the created portfolio dict.
    """
    global _next_portfolio_id
    if not owner_username or not name:
        raise ValueError("Owner username and portfolio name are required.")

    new_id = _next_portfolio_id
    _next_portfolio_id += 1

    p = {
        "id": new_id,
        "owner_username": owner_username,
        "name": name,
        "description": description,
        "strategy": strategy,
        "holdings": {},
    }
    _portfolios[new_id] = p
    return p

def delete_portfolio(portfolio_id: int, requesting_user: Optional["User"] = None) -> None:
    """
    Delete a portfolio by id. Only the owner can delete it.
    Spec: holdings must be empty to allow deletion.
    """
    p = _portfolios.get(portfolio_id)
    if not p:
        raise ValueError(f"Portfolio ID {portfolio_id} does not exist.")
    if requesting_user and p["owner_username"] != requesting_user.username:
        raise ValueError("You do not own this portfolio.")
    holdings: Dict[str, float] = p["holdings"]  # type: ignore[assignment]
    if holdings and sum(holdings.values()) > 0:
        raise ValueError("Portfolio investments must be liquidated before deletion.")
    del _portfolios[portfolio_id]

def sell_security(portfolio_id: int, ticker: str, quantity: float, price: Optional[float] = None) -> Dict[str, object]:
    """
    Execute a SELL; validates ownership and holdings; credits user balance.
    Returns a summary dict.
    """
    u = get_current_user()
    if u is None:
        raise ValueError("No active session. Please login.")

    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise ValueError(f"Portfolio ID {portfolio_id} does not exist.")
    if portfolio["owner_username"] != u.username:
        raise ValueError("You do not own this portfolio.")

    ticker = ticker.upper().strip()
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")

    holdings: Dict[str, float] = portfolio["holdings"]  # type: ignore[assignment]
    current_qty = float(holdings.get(ticker, 0.0))
    if current_qty < quantity:
        raise ValueError(f"Insufficient holdings. You have {current_qty} {ticker}.")

    trade_price = float(price) if price is not None else get_market_price(ticker)
    proceeds = trade_price * float(quantity)

    u.balance += proceeds

    new_qty = current_qty - float(quantity)
    if new_qty > 0:
        holdings[ticker] = new_qty
    else:
        holdings.pop(ticker, None)
    
    _log_transaction(
    ttype="SELL",
    username=u.username,
    portfolio_id=portfolio_id,
    ticker=ticker,
    quantity=float(quantity),
    price=trade_price,
    amount=proceeds,  # SELL proceeds
    balance_after=u.balance,
    )


    return {
        "portfolio_id": portfolio_id,
        "ticker": ticker,
        "quantity": float(quantity),
        "price": trade_price,
        "proceeds": proceeds,
        "balance_after": u.balance,
    }


def get_market_price(ticker: str) -> float:
    """
    Return the reference market price for a ticker (raises if not found).
    """
    sec = get_security(ticker)
    if not sec:
        raise ValueError(f"Unknown ticker '{ticker}'.")
    return float(sec["reference_price"])


# Seed admin (role=admin)
_user: Dict[str, User] = {
    "admin": User("admin", "adminpass", "Admin Firstname", "Admin Lastname", 100000.0, role="admin")
}

#current_user: Optional[User] = None

def query_user(username: str) -> Optional[User]:
    return _user.get(username)

def query_all_users() -> List[User]:
    return list(_user.values())



def list_users() -> List[User]:
    """Alias used by CLI to print a table."""
    return query_all_users()

def _count_admins() -> int:
    return sum(1 for u in _user.values() if u.role == "admin")

def create_new_user(user: User) -> None:
    """
    Create user with validations:
    - non-empty username
    - unique username
    - password required
    - role must be 'admin' or 'user'
    - balance must be >= 0
    """
    if not user.username:
        raise ValueError("Username is required.")
    if user.username in _user:
        raise ValueError(f"Username '{user.username}' already exists.")
    if not user.password:
        raise ValueError("Password is required.")
    if user.role not in ("admin", "user"):
        raise ValueError("Role must be 'admin' or 'user'.")
    if user.balance < 0:
        raise ValueError("Balance must be non-negative.")

    _user[user.username] = user

def _user_has_any_portfolios(username: str) -> bool:
    return any(p for p in _portfolios.values() if p["owner_username"] == username)

def delete_user(username: str, *, requester: Optional[User] = None) -> None:
    target = _user.get(username)
    if not target:
        raise ValueError(f"User '{username}' does not exist.")
    if requester and requester.username == username:
        raise ValueError("You cannot delete your own account.")
    if target.role == "admin" and _count_admins() <= 1:
        raise ValueError("Cannot delete the last remaining admin.")
    # ---- spec: if user has portfolios, forbid deletion
    if _user_has_any_portfolios(username):
        raise ValueError("User has existing portfolios. Please delete all portfolios before deleting the user.")
    del _user[username]


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
    u = get_current_user()
    if u is None:
        raise ValueError("No active session. Please login.")

    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise ValueError(f"Portfolio ID {portfolio_id} does not exist.")
    if portfolio["owner_username"] != u.username:
        raise ValueError("You do not own this portfolio.")

    ticker = ticker.upper().strip()
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")

    # Decide the price (reference price by default)
    trade_price = float(price) if price is not None else get_market_price(ticker)
    cost = trade_price * float(quantity)

    # Balance check
    if u.balance < cost:
        raise ValueError(f"Insufficient funds. Needed {cost:.2f}, available {u.balance:.2f}.")
    u.balance -= cost
        

    # Deduct balance
    # current_user.balance -= cost

    # Update holdings
    holdings: Dict[str, float] = portfolio["holdings"]  # type: ignore[assignment]
    holdings[ticker] = float(holdings.get(ticker, 0.0) + float(quantity))
    
    _log_transaction(
    ttype="BUY",
    username=u.username,
    portfolio_id=portfolio_id,
    ticker=ticker,
    quantity=float(quantity),
    price=trade_price,
    amount=cost,
    balance_after=u.balance,
    )

    return {
    "portfolio_id": portfolio_id,
    "ticker": ticker,
    "quantity": float(quantity),
    "price": trade_price,
    "cost": cost,
    "balance_after": u.balance,
}
