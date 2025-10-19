# app/domain/Investment.py

from typing import Optional

class Investment:
    """
    Represents a single investment holding in a portfolio.
    Each investment corresponds to one security (ticker).
    """

    def __init__(self, ticker: str, quantity: float, purchase_price: float):
        self.ticker: str = ticker
        self.quantity: float = quantity
        self.purchase_price: float = purchase_price

    def __repr__(self) -> str:
        return f"Investment(ticker={self.ticker}, qty={self.quantity}, price={self.purchase_price})"

    def update_quantity(self, delta: float) -> None:
        """Increase or decrease quantity (used for buy/sell)."""
        self.quantity += delta
        if self.quantity < 0:
            self.quantity = 0
