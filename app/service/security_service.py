# app/service/security_service.py

from typing import Dict, List, Optional, Any

from app.db import db
from app.domain import Security
from app.service import portfolio_service


def list_securities() -> List[Dict[str, object]]:
    """Return all securities in a marketplace-friendly format."""
    session = db.session
    securities = session.query(Security).all()

    results: List[Dict[str, object]] = []
    for s in securities:
        results.append(
            {
                "ticker": s.ticker,
                "name": s.issuer,
                "reference_price": float(s.price),
            }
        )
    return results


def buy_security(
    portfolio_id: int,
    ticker: str,
    quantity: float,
    price: Optional[float] = None,
    requesting_username: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Thin wrapper around portfolio_service.buy_security.
    """
    return portfolio_service.buy_security(
        portfolio_id=portfolio_id,
        ticker=ticker,
        quantity=quantity,
        price=price,
        requesting_username=requesting_username,
    )
