# app/service/security_service.py

from typing import Dict, List, Optional, Any

from app.database import get_session
from app.domain import User, Portfolio, Security, Investment, Transaction
from app.service import portfolio_service




def list_securities() -> List[Dict[str, object]]:
    """Return all securities in a marketplace-friendly format."""
    session = get_session()
    try:
        securities = session.query(Security).all()
        results: List[Dict[str, object]] = []
        for s in securities:
            results.append(
                {
                    "ticker": s.ticker,
                    # map issuer -> name for the marketplace UI
                    "name": s.issuer,
                    "reference_price": float(s.price),
                }
            )
        return results
    finally:
        session.close()


def buy_security(
    portfolio_id: int,
    ticker: str,
    quantity: float,
    price: Optional[float] = None,
    requesting_username: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a BUY and debit balance.

    This is now a thin wrapper around portfolio_service.buy_security so
    existing callers in the Marketplace menu can continue to call
    security_service.buy_security without change.
    """
    return portfolio_service.buy_security(
        portfolio_id=portfolio_id,
        ticker=ticker,
        quantity=quantity,
        price=price,
        requesting_username=requesting_username,
    )
