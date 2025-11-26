# app/domain/Portfolio.py

from typing import List
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Portfolio(Base):
    __tablename__ = "portfolio"

    # columns
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    owner: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("user.username"),
        nullable=False,
    )

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="portfolios")
    investments: Mapped[List["Investment"]] = relationship(
        "Investment", back_populates="portfolio", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="portfolio"
    )

    def __str__(self) -> str:
        return (
            f"#Portfolio: name={self.name}; "
            f"description={self.description}; "
            f"user={self.user.username}"
        )
