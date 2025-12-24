# app/domain/Portfolio.py
from typing import List
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import db  

class Portfolio(db.Model):  
    __tablename__ = "portfolio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    owner: Mapped[str] = mapped_column(
        String(30),
        ForeignKey("user.username"),
        nullable=False,
    )

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
