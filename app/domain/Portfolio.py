# app/domain/Portfolio.py
from typing import List
from domain.Investment import Investment
class Portfolio:
    """
    Represents a user's investment portfolio.
    Contains multiple Investment objects in the holdings list.
    """

    def __init__(self, id: int, name: str, description: str, owner_username: str):
        self.id: int = id
        self.name: str = name
        self.description: str = description
        self.owner_username: str = owner_username
        self.holdings: List[Investment] = []  # ✅ list of Investment objects

    def add_investment(self, investment: Investment) -> None:
        """Add new investment or update existing ticker quantity."""
        for inv in self.holdings:
            if inv.ticker == investment.ticker:
                inv.update_quantity(investment.quantity)
                return
        self.holdings.append(investment)

    def remove_investment(self, ticker: str, quantity: float) -> bool:
        """Reduce or remove investment; return True if successful."""
        for inv in self.holdings:
            if inv.ticker == ticker:
                if inv.quantity < quantity:
                    return False
                inv.update_quantity(-quantity)
                if inv.quantity == 0:
                    self.holdings.remove(inv)
                return True
        return False

