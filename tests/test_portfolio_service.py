import pytest
from app.domain import User, Portfolio, Security, Investment, Transaction
from app.service.portfolio_service import (
    list_portfolios,
    get_portfolio,
    create_portfolio,
    delete_portfolio,
    portfolio_total_value,
    buy_security,
    sell_security,
    PortfolioOperationError,
)

# ---------------------------------------------------------
#  list_portfolios
# ---------------------------------------------------------
def test_list_portfolios_all_and_by_owner(db_session):
    """list_portfolios should return correct portfolios by filter."""
    u1 = User(username="u1", password="p", firstname="U", lastname="1", role="user")
    u2 = User(username="u2", password="p", firstname="U", lastname="2", role="user")
    db_session.add_all([u1, u2])
    db_session.commit()

    p1 = Portfolio(name="P1", description="d", owner="u1")
    p2 = Portfolio(name="P2", description="d", owner="u2")
    db_session.add_all([p1, p2])
    db_session.commit()

    all_ps = list_portfolios()
    u1_ps = list_portfolios(owner_username="u1")

    assert len(all_ps) == 2
    assert len(u1_ps) == 1
    assert u1_ps[0].owner == "u1"


# ---------------------------------------------------------
#  get_portfolio
# ---------------------------------------------------------
def test_get_portfolio_success(db_session):
    owner = User(username="owner", password="p", firstname="O", lastname="W", role="user")
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="P1", description="desc", owner="owner")
    db_session.add(p)
    db_session.commit()

    retrieved = get_portfolio(p.id)

    assert retrieved is not None
    assert retrieved.id == p.id
    assert retrieved.name == "P1"


def test_get_portfolio_not_found(db_session):
    retrieved = get_portfolio(9999)
    assert retrieved is None


# ---------------------------------------------------------
#  create_portfolio
# ---------------------------------------------------------
def test_create_portfolio_success(db_session):
    u = User(username="creator", password="p", firstname="A", lastname="B", role="user")
    db_session.add(u)
    db_session.commit()

    p = create_portfolio("creator", "MyPortfolio", "desc")

    assert p.id is not None
    assert p.owner == "creator"
    assert p.name == "MyPortfolio"
    assert p.description == "desc"


def test_create_portfolio_no_description(db_session):
    u = User(username="creator2", password="p", firstname="A", lastname="B", role="user")
    db_session.add(u)
    db_session.commit()

    p = create_portfolio("creator2", "MinimalPortfolio")

    assert p.id is not None
    assert p.description is None


def test_create_portfolio_fail_no_user(db_session):
    with pytest.raises(PortfolioOperationError) as exc_info:
        create_portfolio("nonexistent_user", "Portfolio")
    assert "does not exist" in str(exc_info.value)


# ---------------------------------------------------------
#  delete_portfolio
# ---------------------------------------------------------
def test_delete_portfolio_success_by_admin(db_session):
    owner = User(username="owner", password="p", firstname="O", lastname="W", role="user")
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="P1", description="d", owner="owner")
    db_session.add(p)
    db_session.commit()

    admin = db_session.get(User, "admin")
    assert admin is not None

    delete_portfolio(p.id, requesting_user=admin)

    assert db_session.get(Portfolio, p.id) is None


def test_delete_portfolio_success_by_owner(db_session):
    owner = User(username="owner2", password="p", firstname="O", lastname="W", role="user")
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="P2", description="d", owner="owner2")
    db_session.add(p)
    db_session.commit()

    delete_portfolio(p.id, requesting_user=owner)

    assert db_session.get(Portfolio, p.id) is None


def test_delete_portfolio_success_no_requesting_user(db_session):
    owner = User(username="owner3", password="p", firstname="O", lastname="W", role="user")
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="P3", description="d", owner="owner3")
    db_session.add(p)
    db_session.commit()

    delete_portfolio(p.id, requesting_user=None)

    assert db_session.get(Portfolio, p.id) is None


def test_delete_portfolio_fail_nonexistent(db_session):
    admin = db_session.get(User, "admin")
    assert admin is not None

    with pytest.raises(PortfolioOperationError) as exc_info:
        delete_portfolio(9999, requesting_user=admin)
    assert "does not exist" in str(exc_info.value)


def test_delete_portfolio_fail_not_owner(db_session):
    u1 = User(username="u1", password="p", firstname="U", lastname="1", role="user")
    u2 = User(username="u2", password="p", firstname="U", lastname="2", role="user")
    db_session.add_all([u1, u2])
    db_session.commit()

    p = Portfolio(name="P1", description="d", owner="u1")
    db_session.add(p)
    db_session.commit()

    with pytest.raises(PortfolioOperationError) as exc_info:
        delete_portfolio(p.id, requesting_user=u2)
    msg = str(exc_info.value).lower()
    assert "not" in msg and ("allow" in msg or "permit" in msg or "owner" in msg)


def test_delete_portfolio_fail_has_positions(db_session):
    owner = User(username="owner_pos", password="p", firstname="O", lastname="W", role="user")
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="P_pos", description="d", owner="owner_pos")
    db_session.add(p)
    db_session.commit()

    # AAPL was added in baseline
    # include required purchase_price to satisfy NOT NULL constraint
    inv = Investment(portfolio_id=p.id, ticker="AAPL", quantity=10.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    admin = db_session.get(User, "admin")
    assert admin is not None

    with pytest.raises(PortfolioOperationError) as exc_info:
        delete_portfolio(p.id, requesting_user=admin)
    assert "still holds" in str(exc_info.value).lower() or "position" in str(exc_info.value).lower()

def test_delete_portfolio_fail_has_transactions(db_session):
    owner = User(username="owner_tx", password="p", firstname="O", lastname="W", role="user")
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="P_tx", description="d", owner="owner_tx")
    db_session.add(p)
    db_session.commit()

    tx = Transaction(
        type="BUY",
        username="owner_tx",
        portfolio_id=p.id,
        ticker="AAPL",
        quantity=10.0,
        price=150.0,
        amount=1500.0,
        balance_after=8500.0,
    )
    db_session.add(tx)
    db_session.commit()

    admin = db_session.get(User, "admin")

    with pytest.raises(PortfolioOperationError) as exc_info:
        delete_portfolio(p.id, requesting_user=admin)
    assert "transaction" in str(exc_info.value).lower() or "audit" in str(exc_info.value).lower()


# ---------------------------------------------------------
#  portfolio_total_value
# ---------------------------------------------------------
def test_portfolio_total_value_empty(db_session):
    owner = User(username="owner_val", password="p", firstname="O", lastname="W", role="user")
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="P_val", description="d", owner="owner_val")
    db_session.add(p)
    db_session.commit()

    total = portfolio_total_value(p)

    assert total == 0.0


def test_portfolio_total_value_with_positions(db_session):
    owner = User(username="owner_total", password="p", firstname="O", lastname="W", role="user")
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="P_total", description="d", owner="owner_total")
    db_session.add(p)
    db_session.commit()

    # AAPL, TSLA were added in baseline with prices 175.0 and 250.0 respectively
    inv1 = Investment(portfolio_id=p.id, ticker="AAPL", quantity=10.0, purchase_price=0.0)
    inv2 = Investment(portfolio_id=p.id, ticker="TSLA", quantity=5.0, purchase_price=0.0)
    db_session.add_all([inv1, inv2])
    db_session.commit()

    total = portfolio_total_value(p)

    # 10 * 175 + 5 * 250 = 3000
    assert total == 3000.0


def test_portfolio_total_value_with_custom_pricer(db_session):
    owner = User(username="owner_pricer", password="p", firstname="O", lastname="W", role="user")
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="P_pricer", description="d", owner="owner_pricer")
    db_session.add(p)
    db_session.commit()

    # include required purchase_price to satisfy NOT NULL constraint
    inv = Investment(portfolio_id=p.id, ticker="AAPL", quantity=10.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    def custom_pricer(ticker):
        return 350.0

    total = portfolio_total_value(p, pricer=custom_pricer)

    assert total == 3500.0  # 10 * 350

def test_portfolio_total_value_missing_security_price(db_session):
    owner = User(username="owner_missing", password="p", firstname="O", lastname="W", role="user")
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="P_missing", description="d", owner="owner_missing")
    db_session.add(p)
    db_session.commit()

    # Do NOT add a Security row with price=None (DB enforces NOT NULL).
    # Instead create an Investment that references a non-existent ticker so
    # portfolio_total_value will encounter a missing price/security and raise.
    inv = Investment(portfolio_id=p.id, ticker="UNKNOWN", quantity=10.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    with pytest.raises(PortfolioOperationError) as exc_info:
        portfolio_total_value(p)
    assert "price" in str(exc_info.value).lower()


# ---------------------------------------------------------
#  buy_security
# ---------------------------------------------------------
def test_buy_security_success_new_position(db_session):
    owner = User(username="trader1", password="p", firstname="T", lastname="1", role="user", balance=10000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Trading1", description="d", owner="trader1")
    db_session.add(p)
    db_session.commit()

    # TSLA was added in baseline with price=250.0
    result = buy_security(p.id, "TSLA", 10.0, requesting_username="trader1")

    assert result["action"] == "BUY"
    assert result["ticker"] == "TSLA"
    assert result["quantity"] == 10.0
    assert result["price"] == 250.0
    assert result["trade_value"] == 2500.0
    assert result["new_balance"] == 7500.0
    assert result["new_position_quantity"] == 10.0

    refreshed_user = db_session.get(User, "trader1")
    assert refreshed_user.balance == 7500.0

    inv = db_session.query(Investment).filter(
        Investment.portfolio_id == p.id,
        Investment.ticker == "TSLA"
    ).one()
    assert inv.quantity == 10.0

    tx = db_session.query(Transaction).filter(
        Transaction.username == "trader1",
        Transaction.portfolio_id == p.id,
        Transaction.ticker == "TSLA"
    ).one()
    assert tx.type == "BUY"
    assert tx.quantity == 10.0


def test_buy_security_success_update_position(db_session):
    owner = User(username="trader2", password="p", firstname="T", lastname="2", role="user", balance=10000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Trading2", description="d", owner="trader2")
    db_session.add(p)
    db_session.commit()

    # LULU was added in baseline with price=168.0
    inv = Investment(portfolio_id=p.id, ticker="LULU", quantity=5.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    result = buy_security(p.id, "LULU", 3.0, requesting_username="trader2")

    assert result["new_position_quantity"] == 8.0

    updated_inv = db_session.query(Investment).filter(
        Investment.portfolio_id == p.id,
        Investment.ticker == "LULU"
    ).one()
    assert updated_inv.quantity == 8.0

def test_buy_security_with_price_override(db_session):
    owner = User(username="trader3", password="p", firstname="T", lastname="3", role="user", balance=10000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Trading3", description="d", owner="trader3")
    db_session.add(p)
    db_session.commit()

    result = buy_security(p.id, "LULU", 2.0, price=2500.0, requesting_username="trader3")

    assert result["price"] == 2500.0
    assert result["trade_value"] == 5000.0


def test_buy_security_fail_negative_qty(db_session):
    with pytest.raises(PortfolioOperationError) as exc_info:
        buy_security(1, "AAPL", -5.0)
    assert "positive" in str(exc_info.value).lower()

    with pytest.raises(PortfolioOperationError):
        buy_security(1, "AAPL", 0.0)


def test_buy_security_fail_portfolio_not_found(db_session):
    with pytest.raises(PortfolioOperationError) as exc_info:
        buy_security(9999, "AAPL", 5.0)
    assert "portfolio" in str(exc_info.value).lower()


def test_buy_security_fail_security_not_found(db_session):
    owner = User(username="trader4", password="p", firstname="T", lastname="4", role="user", balance=10000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Trading4", description="d", owner="trader4")
    db_session.add(p)
    db_session.commit()

    with pytest.raises(PortfolioOperationError) as exc_info:
        buy_security(p.id, "NONEXISTENT", 5.0, requesting_username="trader4")
    assert "security" in str(exc_info.value).lower() or "ticker" in str(exc_info.value).lower()


def test_buy_security_fail_insufficient_balance(db_session):
    owner = User(username="trader5", password="p", firstname="T", lastname="5", role="user", balance=1000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Trading5", description="d", owner="trader5")
    db_session.add(p)
    db_session.commit()

    sec = Security(ticker="NVDA", issuer="Nvidia Inc.", price=500.00)
    db_session.add(sec)
    db_session.commit()

    with pytest.raises(PortfolioOperationError) as exc_info:
        buy_security(p.id, "NVDA", 5.0, requesting_username="trader5")
    assert "balance" in str(exc_info.value).lower()


def test_buy_security_fail_not_owner(db_session):
    owner = User(username="owner_buy", password="p", firstname="O", lastname="B", role="user", balance=10000.0)
    other = User(username="other_buy", password="p", firstname="O", lastname="B", role="user", balance=10000.0)
    db_session.add_all([owner, other])
    db_session.commit()

    p = Portfolio(name="OwnerPortfolio", description="d", owner="owner_buy")
    db_session.add(p)
    db_session.commit()

    with pytest.raises(PortfolioOperationError) as exc_info:
        buy_security(p.id, "LULU", 5.0, requesting_username="other_buy")

    msg = str(exc_info.value).lower()
    # Accept actual messages like "you do not own this portfolio." in addition to previous expectations
    assert "not permitted" in msg or "owner" in msg or "do not own" in msg
    

def test_buy_security_no_price_market_price_missing(db_session):
    owner = User(username="trader6", password="p", firstname="T", lastname="6", role="user", balance=10000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Trading6", description="d", owner="trader6")
    db_session.add(p)
    db_session.commit()

    # Do not insert a Security row with price=None (DB enforces NOT NULL).
    # Expect the service to raise because the security is missing (or has no price).
    with pytest.raises(PortfolioOperationError) as exc_info:
        buy_security(p.id, "NOPRICE", 5.0, requesting_username="trader6")

    msg = str(exc_info.value).lower()
    assert "security" in msg or "ticker" in msg or "price" in msg


# ---------------------------------------------------------
#  sell_security
# ---------------------------------------------------------
def test_sell_security_success_partial(db_session):
    owner = User(username="seller1", password="p", firstname="S", lastname="1", role="user", balance=5000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Selling1", description="d", owner="seller1")
    db_session.add(p)
    db_session.commit()

    inv = Investment(portfolio_id=p.id, ticker="LULU", quantity=20.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    result = sell_security(p.id, "LULU", 8.0, requesting_username="seller1")

    assert result["action"] == "SELL"
    assert result["ticker"] == "LULU"
    assert result["quantity"] == 8.0
    assert result["price"] == 168.0
    assert result["trade_value"] == 1344.0
    assert result["new_balance"] == 6344.0
    assert result["remaining_position_quantity"] == 12.0

    refreshed_user = db_session.get(User, "seller1")
    assert refreshed_user.balance == 6344.0

    updated_inv = db_session.query(Investment).filter(
        Investment.portfolio_id == p.id,
        Investment.ticker == "LULU"
    ).one()
    assert updated_inv.quantity == 12.0


def test_sell_security_success_entire_position(db_session):
    owner = User(username="seller2", password="p", firstname="S", lastname="2", role="user", balance=5000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Selling2", description="d", owner="seller2")
    db_session.add(p)
    db_session.commit()

    # include purchase_price to satisfy NOT NULL constraint
    inv = Investment(portfolio_id=p.id, ticker="TSLA", quantity=10.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    result = sell_security(p.id, "TSLA", 10.0, requesting_username="seller2")

    assert result["remaining_position_quantity"] == 0.0

    deleted_inv = db_session.query(Investment).filter(
        Investment.portfolio_id == p.id,
        Investment.ticker == "TSLA"
    ).one_or_none()
    assert deleted_inv is None



def test_sell_security_with_price_override(db_session):
    owner = User(username="seller3", password="p", firstname="S", lastname="3", role="user", balance=5000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Selling3", description="d", owner="seller3")
    db_session.add(p)
    db_session.commit()

    # include purchase_price to satisfy NOT NULL constraint
    inv = Investment(portfolio_id=p.id, ticker="TSLA", quantity=100.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    result = sell_security(p.id, "TSLA", 50.0, price=375.0, requesting_username="seller3")

    assert result["price"] == 375.0
    assert result["trade_value"] == 18750


def test_sell_security_logs_transaction(db_session):
    owner = User(username="seller4", password="p", firstname="S", lastname="4", role="user", balance=5000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Selling4", description="d", owner="seller4")
    db_session.add(p)
    db_session.commit()

    # include purchase_price to satisfy NOT NULL constraint
    inv = Investment(portfolio_id=p.id, ticker="TSLA", quantity=25.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    sell_security(p.id, "TSLA", 5.0, requesting_username="seller4")

    tx = db_session.query(Transaction).filter(
        Transaction.username == "seller4",
        Transaction.portfolio_id == p.id,
        Transaction.ticker == "TSLA"
    ).one()
    assert tx.type == "SELL"
    assert tx.quantity == 5.0


def test_sell_security_fail_negative_qty(db_session):
    with pytest.raises(PortfolioOperationError) as exc_info:
        sell_security(1, "AAPL", -5.0)
    assert "positive" in str(exc_info.value).lower()

    with pytest.raises(PortfolioOperationError):
        sell_security(1, "AAPL", 0.0)


def test_sell_security_fail_portfolio_not_found(db_session):
    with pytest.raises(PortfolioOperationError) as exc_info:
        sell_security(9999, "AAPL", 5.0)
    assert "portfolio" in str(exc_info.value).lower()


def test_sell_security_fail_not_owner(db_session):
    owner = User(username="owner_sell", password="p", firstname="O", lastname="S", role="user", balance=5000.0)
    other = User(username="other_sell", password="p", firstname="O", lastname="S", role="user", balance=5000.0)
    db_session.add_all([owner, other])
    db_session.commit()

    p = Portfolio(name="OwnerPortfolio2", description="d", owner="owner_sell")
    db_session.add(p)
    db_session.commit()

    # include purchase_price to satisfy NOT NULL constraint
    inv = Investment(portfolio_id=p.id, ticker="TSLA", quantity=10.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    with pytest.raises(PortfolioOperationError) as exc_info:
        sell_security(p.id, "TSLA", 5.0, requesting_username="other_sell")
    msg = str(exc_info.value).lower()
    assert "not permitted" in msg or "owner" in msg or "do not own" in msg


def test_sell_security_fail_position_not_found(db_session):
    owner = User(username="seller5", password="p", firstname="S", lastname="5", role="user", balance=5000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Selling5", description="d", owner="seller5")
    db_session.add(p)
    db_session.commit()

    with pytest.raises(PortfolioOperationError) as exc_info:
        sell_security(p.id, "NONOWNED", 5.0, requesting_username="seller5")
    assert "not found" in str(exc_info.value).lower() or "insufficient" in str(exc_info.value).lower()



def test_sell_security_fail_insufficient_quantity(db_session):
    owner = User(username="seller6", password="p", firstname="S", lastname="6", role="user", balance=5000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Selling6", description="d", owner="seller6")
    db_session.add(p)
    db_session.commit()

    # include purchase_price to satisfy NOT NULL constraint
    inv = Investment(portfolio_id=p.id, ticker="TSLA", quantity=5.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    with pytest.raises(PortfolioOperationError) as exc_info:
        sell_security(p.id, "TSLA", 10.0, requesting_username="seller6")
    assert "insufficient" in str(exc_info.value).lower()


def test_sell_security_no_price_market_price_missing(db_session):
    owner = User(username="seller7", password="p", firstname="S", lastname="7", role="user", balance=5000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Selling7", description="d", owner="seller7")
    db_session.add(p)
    db_session.commit()

    # Do not insert a Security row with price=None (DB enforces NOT NULL).
    # Instead create an Investment that references a non-existent ticker so
    # sell_security will encounter a missing price/security and raise.
    inv = Investment(portfolio_id=p.id, ticker="NOPRICE2", quantity=10.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    with pytest.raises(PortfolioOperationError) as exc_info:
        sell_security(p.id, "NOPRICE2", 5.0, requesting_username="seller7")
    assert "price" in str(exc_info.value).lower()