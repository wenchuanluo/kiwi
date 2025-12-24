# app/domain/User.py

from typing import List
from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import db


class User(db.Model):
    __tablename__ = "user"

    # columns
    username: Mapped[str] = mapped_column(String(30), primary_key=True)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    firstname: Mapped[str] = mapped_column(String(50), nullable=False)
    lastname: Mapped[str] = mapped_column(String(50), nullable=False)
    balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")


    # relationships
    portfolios: Mapped[List["Portfolio"]] = relationship("Portfolio", back_populates="user")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="user")

    def __str__(self) -> str:
        return (
            f"#User: username={self.username}; "
            f"name={self.lastname}, {self.firstname}; "
            f"balance={self.balance}"
        )
