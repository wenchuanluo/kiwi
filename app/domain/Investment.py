# app/domain/Investment.py
from sqlalchemy import Integer, String, Float, ForeignKey
from typing import TYPE_CHECKING, List
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Investment(Base):
    __tablename__ = "investment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

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
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)

    # relationships
    portfolio: Mapped["Portfolio"] = relationship(
        "Portfolio", back_populates="investments"
    )
    security: Mapped["Security"] = relationship(
        "Security", back_populates="investments"
    )

    def __str__(self) -> str:
        return (
            f"#Investment: id={self.id}; portfolio_id={self.portfolio_id}; "
            f"ticker={self.ticker}; qty={self.quantity}; purchase_price={self.purchase_price}"
        )
