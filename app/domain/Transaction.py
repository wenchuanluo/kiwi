# app/domain/Transaction.py
from datetime import datetime
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import db  

class Transaction(db.Model):  # inherits from db.Model
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    type: Mapped[str] = mapped_column(String(10), nullable=False)  # "BUY" or "SELL"

    username: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("user.username"),
        nullable=False,
    )

    portfolio_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("portfolio.id"),
        nullable=False,
    )

    ticker: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("security.ticker"),
        nullable=False,
    )

    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)         # cost/proceeds
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="transactions")
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="transactions")
    security: Mapped["Security"] = relationship("Security", back_populates="transactions")

    def __str__(self) -> str:
        return (
            f"#Transaction: id={self.id}; type={self.type}; username={self.username}; "
            f"portfolio_id={self.portfolio_id}; ticker={self.ticker}; "
            f"qty={self.quantity}; price={self.price}; amount={self.amount}; "
            f"balance_after={self.balance_after}; time={self.timestamp}"
        )
