# app/service/portfolio_service.py


from typing import List, Optional, Callable, Dict, Any
from app.database import get_session
from app.domain import User, Portfolio, Security, Investment, Transaction




class PortfolioOperationError(Exception):
    """Generic error for portfolio operations."""



def list_portfolios(owner_username: Optional[str] = None) -> List[Portfolio]:
    """Return all portfolios, or only those owned by a specific user."""
    session = get_session()
    try:
        q = session.query(Portfolio)
        if owner_username is not None:
            q = q.filter(Portfolio.owner == owner_username)
        return q.all()
    finally:
        session.close()


def get_portfolio(portfolio_id: int) -> Optional[Portfolio]:
    """Retrieve a portfolio by its ID."""
    session = get_session()
    try:
        return session.get(Portfolio, portfolio_id)
    finally:
        session.close()


def create_portfolio(
    owner_username: str,
    name: str,
    description: Optional[str] = None,
) -> Portfolio:
    """
    Create a new portfolio for a given owner user.
    """
    session = get_session()
    try:
        owner = session.get(User, owner_username)
        if owner is None:
            raise PortfolioOperationError(f"User '{owner_username}' does not exist.")

        portfolio = Portfolio(
            name=name,
            description=description,
            owner=owner_username,
        )

        session.add(portfolio)
        session.commit()
        session.refresh(portfolio)
        return portfolio
    finally:
        session.close()


def delete_portfolio(
    portfolio_id: int,
    requesting_user: Optional[User] = None,
) -> None:
    """
    Delete a portfolio if the requesting user is allowed:
    - Admin can delete any portfolio.
    - User can delete only their own portfolio.
    - You CANNOT delete a portfolio that:
        * still holds any investments (positions), or
        * has transaction history (kept for audit trail).
    """
    session = get_session()
    try:
        portfolio = session.get(Portfolio, portfolio_id)
        if portfolio is None:
            raise PortfolioOperationError(
                f"Portfolio '{portfolio_id}' does not exist."
            )

        # 1) permission check
        if requesting_user is not None:
            is_admin = getattr(requesting_user, "role", "user") == "admin"
            is_owner = requesting_user.username == portfolio.owner
            if not (is_admin or is_owner):
                raise PortfolioOperationError(
                    "You are not allowed to delete this portfolio."
                )

        # 2) cannot delete if there are still investments (positions)
        position_count = (
            session.query(Investment)
            .filter(Investment.portfolio_id == portfolio_id)
            .count()
        )
        if position_count > 0:
            raise PortfolioOperationError(
                "Cannot delete portfolio that still holds investments. "
                "Please sell all positions first."
            )

        # 3) cannot delete if there are transaction records (audit trail)
        tx_count = (
            session.query(Transaction)
            .filter(Transaction.portfolio_id == portfolio_id)
            .count()
        )
        if tx_count > 0:
            raise PortfolioOperationError(
                "Cannot delete portfolio that has transaction history. "
                "Transaction records are kept for audit."
            )

        # 4) safe to delete
        session.delete(portfolio)
        session.commit()
    finally:
        session.close()




def portfolio_total_value(
    portfolio: Portfolio,
    pricer: Optional[Callable[[str], float]] = None,
) -> float:
    """
    Calculate the total market value of a portfolio's holdings.
    """
    session = get_session()
    try:
        investments = (
            session.query(Investment)
            .filter(Investment.portfolio_id == portfolio.id)
            .all()
        )

        total = 0.0
        for inv in investments:
            if pricer is not None:
                price = pricer(inv.ticker)
            else:
                if inv.security is None or inv.security.price is None:
                    raise PortfolioOperationError(
                        f"No price found for ticker '{inv.ticker}'."
                    )
                price = inv.security.price

            total += float(inv.quantity) * float(price)

        return float(total)
    finally:
        session.close()


# Buy/Sell Operations + Transaction Logging
def _resolve_trade_price(session, ticker: str, price_override: Optional[float]) -> float:
    """Helper to determine execution price."""
    if price_override is not None:
        return float(price_override)

    security = session.get(Security, ticker)
    if security is None or security.price is None:
        raise PortfolioOperationError(
            f"No price available for ticker '{ticker}'. Please provide price."
        )
    return float(security.price)


def buy_security(
    portfolio_id: int,
    ticker: str,
    quantity: float,
    price: Optional[float] = None,
    requesting_username: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a BUY:
    - portfolio_id: ID of the portfolio should align with an existing portfolio and its owner.
    - ticker: Security ticker to buy.
    - quantity: Number of shares to buy (must be positive).
    - price: Optional override price per share; if None, use current market price.
    - Deduct user balance
    - Increase/create investment
    - Log transaction
    """
    if quantity <= 0:
        raise PortfolioOperationError("Quantity must be positive for BUY.")

    session = get_session()
    try:
        portfolio = session.get(Portfolio, portfolio_id)
        if portfolio is None:
            raise PortfolioOperationError("Portfolio does not exist.")

        user = session.get(User, portfolio.owner)
        security = session.get(Security, ticker)
        
        # verify portfolio ownership
        if requesting_username is not None and portfolio.owner != requesting_username:
            raise PortfolioOperationError("You do not own this portfolio.")

        if security is None:
            raise PortfolioOperationError(f"Security '{ticker}' does not exist.")

        exec_price = _resolve_trade_price(session, ticker, price)
        trade_value = quantity * exec_price

        if user.balance < trade_value:
            raise PortfolioOperationError("Insufficient balance.")

        # update or create investment
        investment = (
            session.query(Investment)
            .filter(Investment.portfolio_id == portfolio_id,
                    Investment.ticker == ticker)
            .one_or_none()
        )

        if investment is None:
            investment = Investment(
                portfolio_id=portfolio_id,
                ticker=ticker,
                quantity=quantity,
                purchase_price=exec_price,
            )
            session.add(investment)
        else:
            # avg purchase price
            old_qty = investment.quantity
            new_qty = old_qty + quantity
            old_cost = old_qty * investment.purchase_price
            new_cost = trade_value
            investment.quantity = new_qty
            investment.purchase_price = (old_cost + new_cost) / new_qty

        # update balance
        user.balance -= trade_value

        # log transaction
        tx = Transaction(
            type="BUY",
            username=user.username,
            portfolio_id=portfolio_id,
            ticker=ticker,
            quantity=quantity,
            price=exec_price,
            amount=trade_value,
            balance_after=user.balance,
        )
        session.add(tx)

        session.commit()
        session.refresh(user)
        session.refresh(investment)

        return {
            "action": "BUY",
            "ticker": ticker,
            "quantity": float(quantity),
            "price": float(exec_price),
            "trade_value": float(trade_value),
            "new_balance": float(user.balance),
            "new_position_quantity": float(investment.quantity),
        }

    finally:
        session.close()


def sell_security(
    portfolio_id: int,
    ticker: str,
    quantity: float,
    price: Optional[float] = None,
    requesting_username: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a SELL:
    - Increase user balance
    - Decrease/remove investment
    - Log transaction
    """
    if quantity <= 0:
        raise PortfolioOperationError("Quantity must be positive for SELL.")

    session = get_session()
    try:
        portfolio = session.get(Portfolio, portfolio_id)
        if portfolio is None:
            raise PortfolioOperationError("Portfolio does not exist.")

        user = session.get(User, portfolio.owner)
        # verify portfolio ownership
        if requesting_username is not None and portfolio.owner != requesting_username:
            raise PortfolioOperationError("You do not own this portfolio.")
        investment = (
            session.query(Investment)
            .filter(Investment.portfolio_id == portfolio_id,
                    Investment.ticker == ticker)
            .one_or_none()
        )

        if investment is None or investment.quantity < quantity:
            raise PortfolioOperationError("Insufficient holdings.")

        exec_price = _resolve_trade_price(session, ticker, price)
        trade_value = quantity * exec_price

        # update investment
        investment.quantity -= quantity
        if investment.quantity == 0:
            session.delete(investment)

        # update balance
        user.balance += trade_value

        # log tx
        tx = Transaction(
            type="SELL",
            username=user.username,
            portfolio_id=portfolio_id,
            ticker=ticker,
            quantity=quantity,
            price=exec_price,
            amount=trade_value,
            balance_after=user.balance,
        )
        session.add(tx)

        session.commit()
        session.refresh(user)

        return {
            "action": "SELL",
            "ticker": ticker,
            "quantity": float(quantity),
            "price": float(exec_price),
            "trade_value": float(trade_value),
            "new_balance": float(user.balance),
            "remaining_position_quantity":
                float(investment.quantity) if investment.quantity else 0.0,
        }

    finally:
        session.close()



# List transactions
def list_transactions(username: Optional[str] = None):
    """List transactions for a specific user or all users (admin)."""
    session = get_session()
    try:
        q = session.query(Transaction)
        if username:
            q = q.filter(Transaction.username == username)
        return q.order_by(Transaction.timestamp.desc()).all()
    finally:
        session.close()
