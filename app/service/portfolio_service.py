# app/service/portfolio_service.py
from typing import Dict, List, Optional
from domain.User import User
import db

def list_portfolios(owner_username: Optional[str] = None) -> List[Dict[str, object]]:
    """Return portfolios; optionally filter by owner username."""
    return db.list_portfolios(owner_username)

def portfolio_total_value(portfolio: Dict[str, object]) -> float:
    """Compute total value using reference prices."""
    return db.portfolio_total_value(portfolio)

def create_portfolio(owner_username: str, name: str, description: str, strategy: str) -> Dict[str, object]:
    """Create a portfolio for the owner."""
    return db.create_portfolio(owner_username, name, description, strategy)

def delete_portfolio(portfolio_id: int, requesting_user: Optional[User] = None) -> None:
    """Delete portfolio if owned by the requester."""
    return db.delete_portfolio(portfolio_id, requesting_user=requesting_user)

def sell_security(portfolio_id: int, ticker: str, quantity: float, price: Optional[float] = None) -> Dict[str, object]:
    """Execute a SELL and credit balance."""
    return db.sell_security(portfolio_id, ticker, quantity, price)

def list_transactions(username: Optional[str] = None):
    """List transactions for the given user (or all)."""
    return db.list_transactions(username)
