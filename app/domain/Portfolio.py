# app/domain/Portfolio.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Portfolio:
    """
    Represents a user's investment portfolio.
    Holdings are kept as a dict: {ticker -> quantity}.
    """
    id: int
    name: str
    description: str
    owner_username: str
    holdings: Dict[str, float] = field(default_factory=dict)

    # --- Encapsulated operations on holdings ---

    def add(self, ticker: str, quantity: float) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        t = ticker.upper().strip()
        self.holdings[t] = float(self.holdings.get(t, 0.0) + float(quantity))

    def remove(self, ticker: str, quantity: float) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        t = ticker.upper().strip()
        current = float(self.holdings.get(t, 0.0))
        if quantity > current:
            raise ValueError(
                f"Insufficient quantity to sell: have {current:g}, need {quantity:g}."
            )
        new_q = current - float(quantity)
        if new_q > 0:
            self.holdings[t] = new_q
        else:
            # exactly zero → remove key
            self.holdings.pop(t, None)

    def has(self, ticker: str, quantity: float) -> bool:
        return float(self.holdings.get(ticker.upper().strip(), 0.0)) >= float(quantity)
