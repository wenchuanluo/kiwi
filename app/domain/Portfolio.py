# app/domain/Portfolio.py
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Portfolio:
    """
    Domain model for a portfolio (data only).
    """
    id: int
    owner_username: str
    name: str
    description: str = ""
    strategy: str = ""
    holdings: Dict[str, float] = field(default_factory=dict)

    def position(self, ticker: str) -> float:
        return float(self.holdings.get(ticker.upper(), 0.0))

    def add(self, ticker: str, qty: float) -> None:
        t = ticker.upper()
        self.holdings[t] = self.position(t) + float(qty)

    def remove(self, ticker: str, qty: float) -> None:
        t = ticker.upper()
        new_qty = self.position(t) - float(qty)
        if new_qty > 0:
            self.holdings[t] = new_qty
        else:
            self.holdings.pop(t, None)
