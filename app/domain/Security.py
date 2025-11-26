# app/domain/Security.py
# app/domain/Security.py


from typing import List
from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Security(Base):
    __tablename__ = "security"

    # columns
    ticker: Mapped[str] = mapped_column(String(10), primary_key=True)
    issuer: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    # relationships
    investments: Mapped[List["Investment"]] = relationship(
        "Investment", back_populates="security"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="security"
    )

    def __str__(self) -> str:
        return f"#Security: ticker={self.ticker}; issuer={self.issuer}; price={self.price}"

