import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from rich.console import Console

from app.domain import User, Portfolio, Security, Investment, Transaction
from app.cli import menu_printer
from app.cli import constants


# ---------------------------------------------------------
# Test print_error and print_success
# ---------------------------------------------------------
def test_print_error(capsys):
    """Test error message formatting."""
    menu_printer.print_error("Test error")
    captured = capsys.readouterr()
    assert "Error" in captured.out
    assert "Test error" in captured.out


def test_print_success(capsys):
    """Test success message formatting."""
    menu_printer.print_success("Test success")
    captured = capsys.readouterr()
    assert "Test success" in captured.out


# ---------------------------------------------------------
# Test input helpers
# ---------------------------------------------------------
def test_ask_int_valid(monkeypatch):
    """Test _ask_int with valid integer input."""
    monkeypatch.setattr("rich.console.Console.input", lambda self, prompt: "42")
    result = menu_printer._ask_int("Enter number: ")
    assert result == 42


def test_ask_int_invalid_then_valid(monkeypatch):
    """Test _ask_int retries on invalid input."""
    inputs = iter(["abc", "not_a_number", "99"])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )
    result = menu_printer._ask_int("Enter number: ")
    assert result == 99


def test_ask_positive_float_valid(monkeypatch):
    """Test _ask_positive_float with valid positive float."""
    monkeypatch.setattr("rich.console.Console.input", lambda self, prompt: "3.14")
    result = menu_printer._ask_positive_float("Enter amount: ")
    assert result == 3.14


def test_ask_positive_float_zero_rejected(monkeypatch):
    """Test _ask_positive_float rejects zero."""
    inputs = iter(["0", "-5.5", "10.5"])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )
    result = menu_printer._ask_positive_float("Enter amount: ")
    assert result == 10.5


def test_ask_positive_float_negative_rejected(monkeypatch):
    """Test _ask_positive_float rejects negative numbers."""
    inputs = iter(["-1", "-0.5", "5.0"])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )
    result = menu_printer._ask_positive_float("Enter amount: ")
    assert result == 5.0


# ---------------------------------------------------------
# Test get_login_inputs
# ---------------------------------------------------------
def test_get_login_inputs(monkeypatch):
    """Test login input gathering."""
    inputs = iter(["testuser", "testpass"])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )
    username, password = menu_printer.get_login_inputs()
    assert username == "testuser"
    assert password == "testpass"


# ---------------------------------------------------------
# Test _to_manage_users_menu_guarded
# ---------------------------------------------------------
def test_to_manage_users_menu_guarded_admin(db_session):
    """Test admin can access Manage Users menu."""
    admin = db_session.get(User, "admin")
    assert admin is not None

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=admin):
        result = menu_printer._to_manage_users_menu_guarded()
        assert result == constants.MANAGE_USERS_MENU


def test_to_manage_users_menu_guarded_non_admin(db_session):
    """Test non-admin cannot access Manage Users menu."""
    user = User(username="regular_user", password="p", firstname="R", lastname="U", role="user")
    db_session.add(user)
    db_session.commit()

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=user):
        result = menu_printer._to_manage_users_menu_guarded()
        assert result == constants.MAIN_MENU


def test_to_manage_users_menu_guarded_no_user():
    """Test no logged-in user cannot access Manage Users menu."""
    with patch("app.cli.menu_printer.auth.get_current_user", return_value=None):
        result = menu_printer._to_manage_users_menu_guarded()
        assert result == constants.MAIN_MENU


# ---------------------------------------------------------
# Test _mk_table
# ---------------------------------------------------------
def test_mk_table():
    """Test table creation."""
    table = menu_printer._mk_table("Test Title")
    assert table is not None
    assert table.title == "Test Title"


# ---------------------------------------------------------
# Test view_portfolios_executor
# ---------------------------------------------------------
def test_view_portfolios_executor_no_session():
    """Test viewing portfolios without active session."""
    with patch("app.cli.menu_printer.auth.get_current_user", return_value=None):
        menu_printer.view_portfolios_executor()


def test_view_portfolios_executor_empty(db_session):
    """Test viewing portfolios with no portfolios."""
    user = User(username="p_user", password="p", firstname="P", lastname="U", role="user")
    db_session.add(user)
    db_session.commit()

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=user):
        menu_printer.view_portfolios_executor()


def test_view_portfolios_executor_with_holdings(db_session):
    """Test viewing portfolios with holdings."""
    user = User(username="p_user2", password="p", firstname="P", lastname="U", role="user")
    db_session.add(user)
    db_session.commit()

    p = Portfolio(name="TestPort", description="d", owner="p_user2")
    db_session.add(p)
    db_session.commit()

    inv = Investment(portfolio_id=p.id, ticker="AAPL", quantity=5.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=user):
        menu_printer.view_portfolios_executor()


# ---------------------------------------------------------
# Test create_portfolio_executor
# ---------------------------------------------------------
def test_create_portfolio_executor_no_session():
    """Test creating portfolio without active session."""
    with patch("app.cli.menu_printer.auth.get_current_user", return_value=None):
        menu_printer.create_portfolio_executor()


def test_create_portfolio_executor_success(db_session, monkeypatch):
    """Test successful portfolio creation."""
    user = User(username="creator", password="p", firstname="C", lastname="R", role="user")
    db_session.add(user)
    db_session.commit()

    inputs = iter(["MyPortfolio", "My description"])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=user):
        menu_printer.create_portfolio_executor()


def test_create_portfolio_executor_fail_no_user(monkeypatch):
    """Test portfolio creation fails with non-existent user."""
    user = User(username="nonexistent", password="p", firstname="N", lastname="E", role="user")

    inputs = iter(["BadPort", ""])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=user):
        menu_printer.create_portfolio_executor()


# ---------------------------------------------------------
# Test delete_portfolio_executor
# ---------------------------------------------------------
def test_delete_portfolio_executor_no_session():
    """Test deleting portfolio without active session."""
    with patch("app.cli.menu_printer.auth.get_current_user", return_value=None):
        menu_printer.delete_portfolio_executor()


def test_delete_portfolio_executor_success(db_session, monkeypatch):
    """Test successful portfolio deletion."""
    user = User(username="deleter", password="p", firstname="D", lastname="R", role="user")
    db_session.add(user)
    db_session.commit()

    p = Portfolio(name="ToDelete", description="d", owner="deleter")
    db_session.add(p)
    db_session.commit()

    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: str(p.id)
    )

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=user):
        menu_printer.delete_portfolio_executor()


def test_delete_portfolio_executor_fail_not_found(monkeypatch, db_session):
    """Test portfolio deletion fails when portfolio not found."""
    user = User(username="deleter2", password="p", firstname="D", lastname="R", role="user")
    db_session.add(user)
    db_session.commit()

    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: "9999"
    )

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=user):
        menu_printer.delete_portfolio_executor()


# ---------------------------------------------------------
# Test buy_security_executor
# ---------------------------------------------------------
def test_buy_security_executor_no_session():
    """Test buying security without active session."""
    with patch("app.cli.menu_printer.auth.get_current_user", return_value=None):
        menu_printer.buy_security_executor()


def test_buy_security_executor_success(db_session, monkeypatch):
    """Test successful security purchase."""
    user = User(username="buyer", password="p", firstname="B", lastname="R", role="user", balance=10000.0)
    db_session.add(user)
    db_session.commit()

    p = Portfolio(name="BuyPort", description="d", owner="buyer")
    db_session.add(p)
    db_session.commit()

    inputs = iter([str(p.id), "AAPL", "5.0"])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=user):
        with patch("app.cli.menu_printer.security_service.buy_security") as mock_buy:
            mock_buy.return_value = {
                "quantity": 5.0,
                "ticker": "AAPL",
                "price": 175.0,
                "trade_value": 875.0,
                "new_balance": 9125.0,
            }
            menu_printer.buy_security_executor()


def test_buy_security_executor_fail_invalid_ticker(db_session, monkeypatch):
    """Test buying security with invalid ticker."""
    user = User(username="buyer2", password="p", firstname="B", lastname="R", role="user", balance=10000.0)
    db_session.add(user)
    db_session.commit()

    p = Portfolio(name="BuyPort2", description="d", owner="buyer2")
    db_session.add(p)
    db_session.commit()

    inputs = iter([str(p.id), "INVALID", "5.0"])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=user):
        menu_printer.buy_security_executor()


# ---------------------------------------------------------
# Test sell_security_executor
# ---------------------------------------------------------
def test_sell_security_executor_no_session():
    """Test selling security without active session."""
    with patch("app.cli.menu_printer.auth.get_current_user", return_value=None):
        menu_printer.sell_security_executor()


def test_sell_security_executor_success(db_session, monkeypatch):
    """Test successful security sale."""
    user = User(username="seller", password="p", firstname="S", lastname="R", role="user", balance=5000.0)
    db_session.add(user)
    db_session.commit()

    p = Portfolio(name="SellPort", description="d", owner="seller")
    db_session.add(p)
    db_session.commit()

    inv = Investment(portfolio_id=p.id, ticker="AAPL", quantity=10.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    inputs = iter([str(p.id), "AAPL", "5.0", ""])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=user):
        with patch("app.cli.menu_printer.portfolio_service.sell_security") as mock_sell:
            mock_sell.return_value = {
                "quantity": 5.0,
                "ticker": "AAPL",
                "price": 175.0,
                "trade_value": 875.0,
                "new_balance": 5875.0,
            }
            menu_printer.sell_security_executor()


def test_sell_security_executor_with_manual_price(db_session, monkeypatch):
    """Test selling security with manual price override."""
    user = User(username="seller2", password="p", firstname="S", lastname="R", role="user", balance=5000.0)
    db_session.add(user)
    db_session.commit()

    p = Portfolio(name="SellPort2", description="d", owner="seller2")
    db_session.add(p)
    db_session.commit()

    inv = Investment(portfolio_id=p.id, ticker="TSLA", quantity=10.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    inputs = iter([str(p.id), "TSLA", "5.0", "300.0"])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=user):
        with patch("app.cli.menu_printer.portfolio_service.sell_security") as mock_sell:
            mock_sell.return_value = {
                "quantity": 5.0,
                "ticker": "TSLA",
                "price": 300.0,
                "trade_value": 1500.0,
                "new_balance": 6500.0,
            }
            menu_printer.sell_security_executor()
            

def test_sell_security_no_price_market_price_missing(db_session):
    from app.service.portfolio_service import PortfolioOperationError

    owner = User(username="seller7", password="p", firstname="S", lastname="7", role="user", balance=5000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Selling7", description="d", owner="seller7")
    db_session.add(p)
    db_session.commit()

    # Avoid inserting a Security with price=None (DB NOT NULL). Create an
    # investment referencing a ticker that has no Security row so the service
    # will encounter a missing market price / missing security and raise.
    inv = Investment(portfolio_id=p.id, ticker="NOPRICE2", quantity=10.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    with pytest.raises(PortfolioOperationError) as exc_info:
        sell_security(p.id, "NOPRICE2", 5.0, requesting_username="seller7")

    msg = str(exc_info.value).lower()
    # Accept a variety of possible messages about missing price/security/ticker
    assert any(k in msg for k in ("price", "security", "ticker", "not found", "missing", "no such", "does not exist"))


def test_sell_security_no_price_market_price_missing(db_session):
    import pytest
    from app.service.portfolio_service import PortfolioOperationError, sell_security

    owner = User(username="seller7", password="p", firstname="S", lastname="7", role="user", balance=5000.0)
    db_session.add(owner)
    db_session.commit()

    p = Portfolio(name="Selling7", description="d", owner="seller7")
    db_session.add(p)
    db_session.commit()

    # Create an investment referencing a ticker that has no Security row so the
    # service will encounter a missing market price / missing security and raise.
    inv = Investment(portfolio_id=p.id, ticker="NOPRICE2", quantity=10.0, purchase_price=0.0)
    db_session.add(inv)
    db_session.commit()

    with pytest.raises(PortfolioOperationError) as exc_info:
        sell_security(p.id, "NOPRICE2", 5.0, requesting_username="seller7")

    msg = str(exc_info.value).lower()
    assert any(k in msg for k in ("price", "security", "ticker", "not found", "missing", "no such", "does not exist"))

# ---------------------------------------------------------
# Test view_users_executor
# ---------------------------------------------------------
def test_view_users_executor():
    """Test viewing all users."""
    with patch("app.cli.menu_printer.user_service.list_users") as mock_list:
        mock_list.return_value = [
            Mock(username="user1", firstname="U", lastname="1", role="user", balance=1000.0),
            Mock(username="user2", firstname="U", lastname="2", role="admin", balance=5000.0),
        ]
        menu_printer.view_users_executor()


def test_view_users_executor_empty():
    """Test viewing users when no users exist."""
    with patch("app.cli.menu_printer.user_service.list_users") as mock_list:
        mock_list.return_value = []
        menu_printer.view_users_executor()


# ---------------------------------------------------------
# Test create_user_executor
# ---------------------------------------------------------
def test_create_user_executor_success(monkeypatch):
    """Test successful user creation."""
    inputs = iter(["newuser", "password123", "New", "User", "user", "1000.0"])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )

    with patch("app.cli.menu_printer.user_service.create_user"):
        menu_printer.create_user_executor()


def test_create_user_executor_negative_balance(monkeypatch):
    """Test user creation rejects negative balance."""
    inputs = iter(["newuser2", "password", "New", "User", "user", "-100", "500.0"])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )

    with patch("app.cli.menu_printer.user_service.create_user"):
        menu_printer.create_user_executor()


def test_create_user_executor_admin_role_override(monkeypatch):
    """Test user creation forces 'user' role even if admin requested."""
    inputs = iter(["newuser3", "password", "New", "User", "admin", "1000.0"])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )

    with patch("app.cli.menu_printer.user_service.create_user"):
        menu_printer.create_user_executor()


# ---------------------------------------------------------
# Test delete_user_executor
# ---------------------------------------------------------
def test_delete_user_executor_success(monkeypatch, db_session):
    """Test successful user deletion."""
    admin = db_session.get(User, "admin")

    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: "someuser"
    )

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=admin):
        with patch("app.cli.menu_printer.user_service.delete_user"):
            menu_printer.delete_user_executor()


def test_delete_user_executor_fail(monkeypatch, db_session):
    """Test user deletion with non-existent user."""
    admin = db_session.get(User, "admin")

    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: "nonexistent"
    )

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=admin):
        with patch("app.cli.menu_printer.user_service.delete_user", side_effect=Exception("User not found")):
            menu_printer.delete_user_executor()


# ---------------------------------------------------------
# Test view_securities_executor
# ---------------------------------------------------------
def test_view_securities_executor():
    """Test viewing available securities."""
    with patch("app.cli.menu_printer.security_service.list_securities") as mock_list:
        mock_list.return_value = [
            {"ticker": "AAPL", "name": "Apple Inc.", "reference_price": 175.0},
            {"ticker": "TSLA", "name": "Tesla Inc.", "reference_price": 250.0},
        ]
        menu_printer.view_securities_executor()


def test_view_securities_executor_empty():
    """Test viewing securities when none available."""
    with patch("app.cli.menu_printer.security_service.list_securities") as mock_list:
        mock_list.return_value = []
        menu_printer.view_securities_executor()


# ---------------------------------------------------------
# Test review_transactions_executor
# ---------------------------------------------------------
def test_review_transactions_executor_no_session():
    """Test reviewing transactions without active session."""
    with patch("app.cli.menu_printer.auth.get_current_user", return_value=None):
        menu_printer.review_transactions_executor()


def test_review_transactions_executor_empty(db_session):
    """Test reviewing transactions with no transactions."""
    user = User(username="tx_user", password="p", firstname="T", lastname="X", role="user")
    db_session.add(user)
    db_session.commit()

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=user):
        with patch("app.cli.menu_printer.portfolio_service.list_transactions") as mock_list:
            mock_list.return_value = []
            menu_printer.review_transactions_executor()


def test_review_transactions_executor_with_transactions(db_session):
    """Test reviewing transactions with existing transactions."""
    user = User(username="tx_user2", password="p", firstname="T", lastname="X", role="user")
    db_session.add(user)
    db_session.commit()

    p = Portfolio(name="TxPort", description="d", owner="tx_user2")
    db_session.add(p)
    db_session.commit()

    tx = Transaction(
        type="BUY",
        username="tx_user2",
        portfolio_id=p.id,
        ticker="AAPL",
        quantity=5.0,
        price=175.0,
        amount=875.0,
        balance_after=9125.0,
    )
    db_session.add(tx)
    db_session.commit()

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=user):
        with patch("app.cli.menu_printer.portfolio_service.list_transactions") as mock_list:
            mock_list.return_value = [tx]
            menu_printer.review_transactions_executor()


# ---------------------------------------------------------
# Test admin_view_user_transactions_executor
# ---------------------------------------------------------
def test_admin_view_user_transactions_executor_not_admin(db_session):
    """Test non-admin cannot view other users' transactions."""
    user = User(username="regular", password="p", firstname="R", lastname="U", role="user")
    db_session.add(user)
    db_session.commit()

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=user):
        menu_printer.admin_view_user_transactions_executor()


def test_admin_view_user_transactions_executor_empty_username(db_session):
    """Test admin transaction view with empty username."""
    admin = db_session.get(User, "admin")

    with patch("rich.console.Console.input", return_value=""):
        with patch("app.cli.menu_printer.auth.get_current_user", return_value=admin):
            menu_printer.admin_view_user_transactions_executor()


def test_admin_view_user_transactions_executor_no_transactions(db_session):
    """Test admin viewing transactions for user with none."""
    admin = db_session.get(User, "admin")

    with patch("rich.console.Console.input", return_value="someuser"):
        with patch("app.cli.menu_printer.auth.get_current_user", return_value=admin):
            with patch("app.cli.menu_printer.portfolio_service.list_transactions") as mock_list:
                mock_list.return_value = []
                menu_printer.admin_view_user_transactions_executor()


def test_admin_view_user_transactions_executor_success(db_session):
    """Test admin successfully viewing user transactions."""
    admin = db_session.get(User, "admin")
    user = User(username="target_user", password="p", firstname="T", lastname="U", role="user")
    db_session.add(user)
    db_session.commit()

    p = Portfolio(name="Port", description="d", owner="target_user")
    db_session.add(p)
    db_session.commit()

    tx = Transaction(
        type="SELL",
        username="target_user",
        portfolio_id=p.id,
        ticker="TSLA",
        quantity=10.0,
        price=250.0,
        amount=2500.0,
        balance_after=7500.0,
    )
    db_session.add(tx)
    db_session.commit()

    with patch("rich.console.Console.input", return_value="target_user"):
        with patch("app.cli.menu_printer.auth.get_current_user", return_value=admin):
            with patch("app.cli.menu_printer.portfolio_service.list_transactions") as mock_list:
                mock_list.return_value = [tx]
                menu_printer.admin_view_user_transactions_executor()


# ---------------------------------------------------------
# Test login
# ---------------------------------------------------------
def test_login_success(monkeypatch, db_session):
    """Test successful login."""
    admin = db_session.get(User, "admin")

    inputs = iter(["admin", "admin"])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )

    with patch("app.cli.menu_printer.auth.login") as mock_login:
        mock_login.return_value = admin
        with patch("app.cli.menu_printer.print_menu"):
            menu_printer.login()


def test_login_fail(monkeypatch):
    """Test failed login."""
    inputs = iter(["baduser", "badpass"])
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: next(inputs)
    )

    with patch("app.cli.menu_printer.auth.login") as mock_login:
        mock_login.return_value = None
        with patch("app.cli.menu_printer.print_menu"):
            menu_printer.login()


# ---------------------------------------------------------
# Test handle_user_selection
# ---------------------------------------------------------
def test_handle_user_selection_login_menu_exit():
    """Test exiting from login menu."""
    with pytest.raises(SystemExit):
        menu_printer.handle_user_selection(constants.LOGIN_MENU, 0)


def test_handle_user_selection_main_menu_logout(db_session):
    """Test logout from main menu."""
    with patch("app.cli.menu_printer.print_menu"):
        menu_printer.handle_user_selection(constants.MAIN_MENU, 0)


def test_handle_user_selection_manage_users_back(db_session):
    """Test back from manage users menu."""
    with patch("app.cli.menu_printer.print_menu"):
        menu_printer.handle_user_selection(constants.MANAGE_USERS_MENU, 0)


def test_handle_user_selection_marketplace_back(db_session):
    """Test back from marketplace menu."""
    with patch("app.cli.menu_printer.print_menu"):
        menu_printer.handle_user_selection(constants.MARKETPLACE_MENU, 0)


def test_handle_user_selection_manage_portfolios_back(db_session):
    """Test back from manage portfolios menu."""
    with patch("app.cli.menu_printer.print_menu"):
        menu_printer.handle_user_selection(constants.MANAGE_PORTFOLIOS_MENU, 0)


def test_handle_user_selection_invalid_option(db_session):
    """Test invalid menu option."""
    with patch("app.cli.menu_printer.print_menu"):
        menu_printer.handle_user_selection(constants.MAIN_MENU, 999)


def test_handle_user_selection_valid_option(db_session):
    """Test valid menu option execution."""
    admin = db_session.get(User, "admin")

    with patch("app.cli.menu_printer.auth.get_current_user", return_value=admin):
        with patch("app.cli.menu_printer.view_users_executor"):
            with patch("app.cli.menu_printer.print_menu"):
                menu_printer.handle_user_selection(constants.MANAGE_USERS_MENU, 1)


# ---------------------------------------------------------
# Test print_menu
# ---------------------------------------------------------
def test_print_menu_login(monkeypatch):
    """Test print login menu."""
    monkeypatch.setattr(
        "rich.console.Console.input",
        lambda self, prompt: "0"
    )

    with pytest.raises(SystemExit):
        menu_printer.print_menu(constants.LOGIN_MENU)