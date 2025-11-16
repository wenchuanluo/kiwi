# db.py — in-memory “database” layer for Kiwi
# -------------------------------------------
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, TypedDict

from domain.User import User
from domain.Portfolio import Portfolio
from domain.Investment import Investment  # keep import if your IDE references it


# ========= Types =========
class SecurityRow(TypedDict):
    ticker: str
    issuer: str
    reference_price: float


# ========= Auth / Session =========
_current_user: Optional[User] = None

def set_current_user(u: Optional[User]) -> None:
    """Set or clear the current logged-in user."""
    global _current_user
    _current_user = u

def get_current_user() -> Optional[User]:
    """Return the current logged-in user (or None)."""
    return _current_user

def logout() -> None:
    """Clear the current session."""
    set_current_user(None)


# ========= Users =========
_users: Dict[str, User] = {
    # seed admin
    "admin": User(
        username="admin",
        password="adminpass",
        firstname="Admin Firstname",
        lastname="Admin Lastname",
        balance=100000.0,
        role="admin",
    )
}

def query_user(username: str) -> Optional[User]:
    return _users.get(username)

def query_all_users() -> List[User]:
    return list(_users.values())

def list_users() -> List[User]:
    return query_all_users()

def _count_admins() -> int:
    return sum(1 for u in _users.values() if u.role == "admin")

def create_new_user(user: User) -> None:
    if not user.username:
        raise ValueError("Username is required.")
    if user.username in _users:
        raise ValueError(f"Username '{user.username}' already exists.")
    if not user.password:
        raise ValueError("Password is required.")
    if user.role not in ("admin", "user"):
        raise ValueError("Role must be 'admin' or 'user'.")
    if user.balance < 0:
        raise ValueError("Balance must be non-negative.")
    _users[user.username] = user

def _user_has_any_portfolios(username: str) -> bool:
    return any(p.owner_username == username for p in _portfolios.values())

def delete_user(username: str, *, requester: Optional[User] = None) -> None:
    target = _users.get(username)
    if not target:
        raise ValueError(f"User '{username}' does not exist.")
    if requester and requester.username == username:
        raise ValueError("You cannot delete your own account.")
    if target.role == "admin" and _count_admins() <= 1:
        raise ValueError("Cannot delete the last remaining admin.")
    if _user_has_any_portfolios(username):
        raise ValueError("User has existing portfolios. Delete their portfolios first.")
    del _users[username]

def login(username: str, password: str) -> User:
    user = _users.get(username)
    if not user or user.password != password:
        raise ValueError("Invalid username or password.")
    return user


# ========= Securities Catalog =========
# Keep simple dict: ticker -> {issuer, reference_price}
_securities: Dict[str, Dict[str, float | str]] = {
    "AAPL": {"issuer": "Apple Inc.",      "reference_price": 190.00},
    "MSFT": {"issuer": "Microsoft Corp.", "reference_price": 420.00},
    "GOOGL": {"issuer": "Alphabet Inc.",  "reference_price": 155.00},
}

def list_securities() -> List[SecurityRow]:
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

def get_market_price(ticker: str) -> float:
    sec = get_security(ticker)
    if not sec:
        raise ValueError(f"Unknown ticker '{ticker}'.")
    return float(sec["reference_price"])


# ========= Portfolios (OOP, not dicts) =========
_portfolios: Dict[int, Portfolio] = {
    1: Portfolio(
        id=1,
        name="Admin Portfolio",
        description="Seed portfolio for the admin user",
        owner_username="admin",
    )
}
_next_portfolio_id: int = 2

def list_portfolios(owner_username: Optional[str] = None) -> List[Portfolio]:
    return [p for p in _portfolios.values()
            if owner_username is None or p.owner_username == owner_username]

def get_portfolio(portfolio_id: int) -> Optional[Portfolio]:
    return _portfolios.get(portfolio_id)

def portfolio_total_value(p: Portfolio) -> float:
    total = 0.0
    for ticker, qty in p.holdings.items():
        sec = get_security(ticker)
        if sec:
            total += qty * float(sec["reference_price"])
    return total

def create_portfolio(owner_username: str, name: str,
                     description: str, strategy: str) -> Portfolio:
    if not owner_username or not name:
        raise ValueError("Owner username and portfolio name are required.")
    global _next_portfolio_id
    pid = _next_portfolio_id
    _next_portfolio_id += 1
    p = Portfolio(id=pid, name=name, description=description,
                  owner_username=owner_username)
    _portfolios[pid] = p
    return p

def delete_portfolio(portfolio_id: int, requesting_user: Optional[User] = None) -> None:
    p = _portfolios.get(portfolio_id)
    if not p:
        raise ValueError(f"Portfolio ID {portfolio_id} does not exist.")
    if requesting_user and p.owner_username != requesting_user.username:
        raise ValueError("You do not own this portfolio.")
    if any(qty > 0 for qty in p.holdings.values()):
        raise ValueError("Liquidate all holdings before deleting the portfolio.")
    del _portfolios[portfolio_id]


# ========= Transactions =========
_transactions: List[Dict[str, object]] = []
_next_txn_id: int = 1

def _log_transaction(*, ttype: str, username: str, portfolio_id: int,
                     ticker: str, quantity: float, price: float, amount: float,
                     balance_after: float) -> Dict[str, object]:
    global _next_txn_id
    row: Dict[str, object] = {
        "id": _next_txn_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": ttype,                # "BUY" or "SELL"
        "username": username,
        "portfolio_id": portfolio_id,
        "ticker": ticker,
        "quantity": float(quantity),
        "price": float(price),
        "amount": float(amount),      # cost (BUY) or proceeds (SELL)
        "balance_after": float(balance_after),
    }
    _transactions.append(row)
    _next_txn_id += 1
    return row

def list_transactions(username: Optional[str] = None) -> List[Dict[str, object]]:
    if username is None:
        return list(_transactions)
    return [t for t in _transactions if t["username"] == username]


# ========= Trading (uses Portfolio objects) =========
def buy_security(portfolio_id: int, ticker: str, quantity: float,
                 price: Optional[float] = None) -> Dict[str, object]:
    u = get_current_user()
    if u is None:
        raise ValueError("No active session. Please login.")

    p = get_portfolio(portfolio_id)
    if not p:
        raise ValueError(f"Portfolio ID {portfolio_id} does not exist.")
    if p.owner_username != u.username:
        raise ValueError("You do not own this portfolio.")

    ticker = ticker.upper().strip()
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")

    trade_price = float(price) if price is not None else get_market_price(ticker)
    cost = trade_price * float(quantity)

    if u.balance < cost:
        raise ValueError(f"Insufficient funds. Needed {cost:.2f}, available {u.balance:.2f}.")

    # update cash & holdings
    u.balance -= cost
    p.holdings[ticker] = float(p.holdings.get(ticker, 0.0) + float(quantity))

    _log_transaction(
        ttype="BUY",
        username=u.username,
        portfolio_id=p.id,
        ticker=ticker,
        quantity=float(quantity),
        price=trade_price,
        amount=cost,
        balance_after=u.balance,
    )

    return {
        "portfolio_id": p.id,
        "ticker": ticker,
        "quantity": float(quantity),
        "price": trade_price,
        "cost": cost,
        "balance_after": u.balance,
    }

def sell_security(portfolio_id: int, ticker: str, quantity: float,
                  price: Optional[float] = None) -> Dict[str, object]:
    u = get_current_user()
    if u is None:
        raise ValueError("No active session. Please login.")

    p = get_portfolio(portfolio_id)
    if not p:
        raise ValueError(f"Portfolio ID {portfolio_id} does not exist.")
    if p.owner_username != u.username:
        raise ValueError("You do not own this portfolio.")

    ticker = ticker.upper().strip()
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")

    current_qty = float(p.holdings.get(ticker, 0.0))
    if current_qty < quantity:
        raise ValueError(f"Insufficient holdings. You have {current_qty} {ticker}.")

    trade_price = float(price) if price is not None else get_market_price(ticker)
    proceeds = trade_price * float(quantity)

    # update cash & holdings
    u.balance += proceeds
    new_qty = current_qty - float(quantity)
    if new_qty > 0:
        p.holdings[ticker] = new_qty
    else:
        p.holdings.pop(ticker, None)

    _log_transaction(
        ttype="SELL",
        username=u.username,
        portfolio_id=p.id,
        ticker=ticker,
        quantity=float(quantity),
        price=trade_price,
        amount=proceeds,
        balance_after=u.balance,
    )

    return {
        "portfolio_id": p.id,
        "ticker": ticker,
        "quantity": float(quantity),
        "price": trade_price,
        "proceeds": proceeds,
        "balance_after": u.balance,
    }
