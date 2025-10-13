# app/service/security_service.py
from typing import Dict, List, Optional
import db

def list_securities() -> List[Dict[str, object]]:
    """Return all tradable securities (ticker, name, reference_price)."""
    return db.list_securities()  # see note below if this doesn't exist

def buy_security(portfolio_id: int, ticker: str, quantity: float, price: Optional[float] = None) -> Dict[str, object]:
    """Execute a BUY and debit balance."""
    return db.buy_security(portfolio_id, ticker, quantity, price)
