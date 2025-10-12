# app/domain/Security.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Security:
    """
    Domain model for a tradable security.
    """
    ticker: str
    name: str
    reference_price: float
