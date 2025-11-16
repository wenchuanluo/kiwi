# app/service/portfolio_service.py

from typing import List, Optional, Callable, Dict, Any
from domain.User import User
from domain.Portfolio import Portfolio
import db


def list_portfolios(owner_username: Optional[str] = None) -> List[Portfolio]:
    """Return portfolios; optionally filter by owner username."""
    return db.list_portfolios(owner_username)


def get_portfolio(portfolio_id: int) -> Optional[Portfolio]:
    """Fetch a single portfolio by id, or None if not found."""
    return db.get_portfolio(portfolio_id)


def create_portfolio(
    owner_username: str,
    name: str,
    description: str,
    strategy: str,
) -> Portfolio:
    """Create a new portfolio owned by the given user."""
    return db.create_portfolio(owner_username, name, description, strategy)


def delete_portfolio(
    portfolio_id: int,
    requesting_user: Optional[User] = None
) -> None:
    """Delete a portfolio if the requesting user is the owner (or admin)."""
    db.delete_portfolio(portfolio_id, requesting_user=requesting_user)


def portfolio_total_value(
    portfolio: Portfolio,
    pricer: Optional[Callable[[str], float]] = None
) -> float:
    """Compute total market value using the given pricer or reference prices."""
    return db.portfolio_total_value(portfolio, pricer)


def buy_security(
    portfolio_id: int,
    ticker: str,
    quantity: float,
    price: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Execute a BUY in the given portfolio (updates holdings & user balance).
    Returns a summary dict (kept for UI messaging), while storage is object-based.
    """
    return db.buy_security(portfolio_id, ticker, quantity, price)


def sell_security(
    portfolio_id: int,
    ticker: str,
    quantity: float,
    price: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Execute a SELL in the given portfolio (updates holdings & user balance).
    Returns a summary dict (kept for UI messaging), while storage is object-based.
    """
    return db.sell_security(portfolio_id, ticker, quantity, price)


def list_transactions(username: Optional[str] = None):
    """List transactions for a specific user or all users (admin)."""
    return db.list_transactions(username)
