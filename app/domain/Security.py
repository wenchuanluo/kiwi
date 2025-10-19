# app/domain/Security.py
from dataclasses import dataclass

@dataclass
class Security:
    ticker: str
    issuer: str
    price: float

