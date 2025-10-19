# app/domain/Transaction.py
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

TxnType = Literal["BUY", "SELL"]

@dataclass
class Transaction:
    """
    Domain model for a trade record used in 'review transactions'.
    """
    id: int
    timestamp: datetime
    type: TxnType
    username: str
    portfolio_id: int
    ticker: str
    quantity: float
    price: float
    amount: float          # BUY cost or SELL proceeds (positive)
    balance_after: float
