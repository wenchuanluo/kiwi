# app/cli/menu_printer.py
# app/cli/menu_printer.py
import sys
from typing import Dict, Tuple, List, Iterable, Optional, Any

from rich.console import Console
from rich.table import Table
from rich import box

from app.cli import constants
from app.domain.MenuFunctions import MenuFunctions

import app.service.login_service as auth
import app.service.user_service as user_service
import app.service.portfolio_service as portfolio_service
import app.service.security_service as security_service
from app.domain import User, Portfolio, Security, Investment, Transaction
from app.database import get_session


_console = Console()

# -----------------------------
# Menus (module-level constant)
# -----------------------------
_menus: Dict[int, str] = {
    # Login menu
    constants.LOGIN_MENU: """[bold]Login[/bold]
----
1. Login
0. Exit
""",

    # Main menu
    constants.MAIN_MENU: """[bold]Main Menu[/bold]
----
1. Manage Users
2. Manage portfolios
3. Marketplace
4. Review transactions
0. Logout
""",

    # Manage Users (admin only)
    constants.MANAGE_USERS_MENU: """[bold]Manage Users[/bold]
----
1. View users
2. Create new user
3. Delete user
4. View user's transactions  [admin]
0. Back
""",

    # Marketplace (accessible to all users)
    constants.MARKETPLACE_MENU: """[bold]Marketplace[/bold]
----
1. View available securities
2. Add security to a portfolio (Buy)
0. Back
""",

    constants.MANAGE_PORTFOLIOS_MENU: """[bold]Manage Portfolios[/bold]
----
1. View portfolios
2. Create new portfolio
3. Delete portfolio
4. Sell securities
0. Back
""",
}


# ------------------------------------------------
# UI helper functions
# ------------------------------------------------
def print_error(message: str) -> None:
    """Print an error message in a consistent style."""
    _console.print(f"[bold red]Error:[/bold red] {message}")


def print_success(message: str) -> None:
    """Print a success message in a consistent style."""
    _console.print(f"[bold green]{message}[/bold green]")


def _to_manage_users_menu_guarded() -> int:
    """
    Only admins can enter Manage Users menu.
    If current user is not admin, show an error and stay on Main Menu.
    """
    u = auth.get_current_user()
    if not u or u.role != "admin":
        print_error("Only admins can manage users.")
        return constants.MAIN_MENU
    return constants.MANAGE_USERS_MENU


def _mk_table(title: str) -> Table:
    """Create a nicely formatted Rich table with a given title."""
    return Table(
        title=title,
        expand=True,
        box=box.SIMPLE_HEAVY,
        pad_edge=False,
        show_header=True,
        header_style="bold",
    )


# ----------------------------------------------------
# (A) Gather login inputs (with visible password input)
# ----------------------------------------------------
def get_login_inputs() -> tuple[str, str]:
    """Prompt for username and password (visible while typing)."""
    username = _console.input("Username: ")
    password = _console.input("Password: ")
    _console.print("")
    return username, password


# -------------------------------------------------
# (B) Robust integer input (no ValueError crashes)
# -------------------------------------------------
def _ask_int(prompt: str) -> int:
    """Keep asking until the user enters a valid integer."""
    while True:
        s = _console.input(prompt)
        try:
            return int(s)
        except ValueError:
            print_error("Please enter a number (e.g., 1, 2, 3).")


def _ask_positive_float(prompt: str) -> float:
    """Ask until a positive float is provided."""
    while True:
        s = _console.input(prompt)
        try:
            val = float(s)
            if val <= 0:
                raise ValueError
            return val
        except ValueError:
            print_error("Please enter a positive number (e.g., 1 or 2.5).")


# --------------------------------------------------------
# (C) Login executor: set session and navigate to main menu
# --------------------------------------------------------
def login() -> None:
    """
    Handle the login flow:
    - Ask for credentials
    - Authenticate against the database
    - On success, go to Main Menu
    - On failure, stay on Login Menu
    """
    username, password = get_login_inputs()
    user = auth.login(username, password)

    if user is None:
        print_error("Invalid username or password.")
        return print_menu(constants.LOGIN_MENU)

    print_success(f"Welcome, {username}!")
    print_menu(constants.MAIN_MENU)


# -------------------------------------------------
# Portfolio-related executors
# -------------------------------------------------
def view_portfolios_executor() -> None:
    """Show current user's portfolios with total value and holdings."""
    user = auth.get_current_user()
    if not user:
        print_error("No active session. Please login.")
        return

    portfolios = portfolio_service.list_portfolios(owner_username=user.username)
    if not portfolios:
        _console.print("[yellow]You have no portfolios yet.[/yellow]")
        return

    table = Table(
        title="Your Portfolios",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan",
        expand=False,
        pad_edge=False,
    )
    table.add_column("ID", justify="center", width=6, no_wrap=True)
    table.add_column("Name", width=22)
    table.add_column("Total Value", justify="right", width=14, no_wrap=True)
    table.add_column("Holdings (ticker:qty)", width=40)

    # We will query investments per portfolio to display holdings.
    session = get_session()
    try:
        for p in portfolios:  # p is a Portfolio ORM object
            # Compute total value using service layer
            total_val = portfolio_service.portfolio_total_value(p)

            # Get holdings from Investment table
            investments = (
                session.query(Investment)
                .filter(Investment.portfolio_id == p.id)
                .all()
            )
            if investments:
                holdings_str = " | ".join(
                    f"{inv.ticker}:{float(inv.quantity):g}" for inv in investments
                )
            else:
                holdings_str = "-"

            table.add_row(
                str(p.id),
                p.name,
                f"{total_val:,.2f}",
                holdings_str,
            )
    finally:
        session.close()

    _console.print(table)


def create_portfolio_executor() -> None:
    """Create a new portfolio for the current user."""
    u = auth.get_current_user()
    if not u:
        print_error("No active session. Please login.")
        return

    name = _console.input("Name: ").strip()
    desc = _console.input("Description: ").strip()

    try:
        p = portfolio_service.create_portfolio(
            owner_username=u.username,
            name=name,
            description=desc,
        )
        print_success(f"Created portfolio #{p.id} - {p.name}")
    except Exception as e:
        print_error(str(e))


def delete_portfolio_executor() -> None:
    """Delete one of the current user's portfolios (or admin any portfolio)."""
    u = auth.get_current_user()
    if not u:
        print_error("No active session. Please login.")
        return

    pid = _ask_int("Portfolio ID: ")

    try:
        portfolio_service.delete_portfolio(pid, requesting_user=u)
        print_success(f"Deleted portfolio {pid}.")
    except Exception as e:
        print_error(str(e))


def buy_security_executor() -> None:
    u = auth.get_current_user()
    if not u:
        print_error("Please login.")
        return

    # Show user's own portfolios
    portfolios = portfolio_service.list_portfolios(owner_username=u.username)
    if portfolios:
        t = Table(show_header=True, header_style="bold")
        t.add_column("ID", justify="right")
        t.add_column("Name")
        for p in portfolios:
            t.add_row(str(p.id), p.name)
        _console.print(t)

    pid = _ask_int("Portfolio ID: ")
    ticker = _console.input("Ticker: ").strip().upper()
    qty = _ask_positive_float("Quantity: ")

    try:
        result = security_service.buy_security(
            portfolio_id=pid,
            ticker=ticker,
            quantity=qty,
            price=None,
            requesting_username=u.username,   # pass current user
        )
        print_success(
            f"Bought {result['quantity']} {result['ticker']} @ {result['price']:.2f} "
            f"(cost {result['trade_value']:.2f}). "
            f"New balance: {result['new_balance']:.2f}"
        )
    except Exception as e:
        print_error(str(e))



def sell_security_executor() -> None:
    """Sell a security from one of the current user's portfolios."""
    u = auth.get_current_user()
    if not u:
        print_error("Please login.")
        return

    portfolios = portfolio_service.list_portfolios(owner_username=u.username)
    if portfolios:
        t = Table(show_header=True, header_style="bold")
        t.add_column("ID", justify="right")
        t.add_column("Name")
        for p in portfolios:
            t.add_row(str(p.id), p.name)
        _console.print(t)

    pid = _ask_int("Portfolio ID: ")
    ticker = _console.input("Ticker: ").strip().upper()
    qty = _ask_positive_float("Quantity: ")

    price_text = _console.input(
        "Sale price [blank = use market price]: "
    ).strip()
    price = float(price_text) if price_text else None

    try:
        result = portfolio_service.sell_security(
            portfolio_id=pid,
            ticker=ticker,
            quantity=qty,
            price=price,
            requesting_username=u.username,   # pass current user
        )
        src = "(manual)" if price is not None else "(market)"
        print_success(
            f"Sold {result['quantity']} {result['ticker']} @ {result['price']:.2f} {src} "
            f"(proceeds {result['trade_value']:.2f}). "
            f"New balance: {result['new_balance']:.2f}"
        )
    except Exception as e:
        print_error(str(e))


# -------------------------------------------------
# User-related executors
# -------------------------------------------------
def view_users_executor() -> None:
    """Print a table of all users (username, first, last, role, balance)."""
    rows = user_service.list_users()
    if not rows:
        _console.print("[bold red]No users found.[/bold red]")
        return

    term_width = _console.size.width
    compact = term_width < 80

    table = Table(
        title="[b]ALL Users[/b]",
        box=box.SQUARE,
        show_edge=True,
        border_style="cyan",
        header_style="bold cyan",
        pad_edge=True,
        expand=False,
        row_styles=["none", "dim"],
        show_lines=False,
    )

    if compact:
        table.add_column(
            "User",
            justify="left",
            no_wrap=True,
            min_width=8,
            max_width=16,
            overflow="ellipsis",
        )
        table.add_column(
            "First",
            justify="left",
            no_wrap=True,
            min_width=8,
            max_width=16,
            overflow="ellipsis",
        )
        table.add_column(
            "Last",
            justify="left",
            no_wrap=True,
            min_width=8,
            max_width=16,
            overflow="ellipsis",
        )
        table.add_column(
            "Role",
            justify="center",
            no_wrap=True,
            min_width=5,
            max_width=8,
            overflow="ellipsis",
        )
        table.add_column(
            "Balance",
            justify="right",
            no_wrap=True,
            min_width=10,
            max_width=14,
        )
    else:
        nbsp = "\u00A0"
        table.add_column(
            "Username",
            justify="left",
            no_wrap=True,
            min_width=12,
            max_width=20,
            overflow="ellipsis",
        )
        table.add_column(
            f"First{nbsp}name",
            justify="left",
            no_wrap=True,
            min_width=12,
            max_width=20,
            overflow="ellipsis",
        )
        table.add_column(
            f"Last{nbsp}name",
            justify="left",
            no_wrap=True,
            min_width=12,
            max_width=20,
            overflow="ellipsis",
        )
        table.add_column(
            "Role",
            justify="center",
            no_wrap=True,
            min_width=6,
            max_width=10,
            overflow="ellipsis",
        )
        table.add_column(
            "Balance",
            justify="right",
            no_wrap=True,
            min_width=12,
            max_width=16,
        )

    for u in rows:
        table.add_row(
            getattr(u, "username", ""),
            getattr(u, "firstname", ""),
            getattr(u, "lastname", ""),
            getattr(u, "role", ""),
            f"{getattr(u, 'balance', 0):,.2f}",
        )

    _console.print(table)


def create_user_executor() -> None:
    """Create a new regular user (role=user)."""
    username = _console.input("Username: ").strip()
    password = _console.input("Password: ").strip()
    first = _console.input("First name: ").strip()
    last = _console.input("Last name: ").strip()
    role_input = _console.input("Role (admin/user): ").strip().lower()

    # Enforce that only regular users are created here.
    role = "user"
    if role_input != "user":
        print_error(
            "Only regular users can be created from this menu. "
            "Creating user with role='user'."
        )

    # balance (non-negative)
    while True:
        bal_str = _console.input("Initial balance: ").strip()
        try:
            balance = float(bal_str)
            if balance < 0:
                raise ValueError
            break
        except ValueError:
            print_error("Balance must be a non-negative number.")

    try:
        user = User(
            username=username,
            password=password,
            firstname=first,
            lastname=last,
            balance=balance,
            role=role,
        )
        user_service.create_user(user)
        print_success(f"User '{username}' created.")
    except Exception as e:
        print_error(str(e))


def delete_user_executor() -> None:
    """Delete a user (with safety checks in service layer)."""
    username = _console.input("Username to delete: ").strip()
    try:
        requester = auth.get_current_user()
        user_service.delete_user(username, requester=requester)
        print_success(f"User '{username}' deleted.")
    except Exception as e:
        print_error(str(e))


# -------------------------------------------------
# Marketplace executors
# -------------------------------------------------
def view_securities_executor() -> None:
    """Show available securities (ticker, issuer, reference price)."""
    rows = security_service.list_securities()
    if not rows:
        print_error("No securities available.")
        return

    table = Table(
        title="Available Securities",
        box=box.SQUARE,
        show_header=True,
        header_style="bold cyan",
        expand=True,
    )
    table.add_column("Ticker", justify="center", no_wrap=True)
    table.add_column("Issuer", justify="left")
    table.add_column("Reference Price", justify="right", no_wrap=True)

    # rows is List[Dict[str, object]]: {"ticker", "name", "reference_price"}
    for info in rows:
        ticker = str(info.get("ticker", ""))
        issuer = str(info.get("name", ""))
        ref_px = float(info.get("reference_price", 0.0))
        table.add_row(ticker, issuer, f"{ref_px:,.2f}")

    _console.print(table)


# -------------------------------------------------
# Transaction-related executors
# -------------------------------------------------
def review_transactions_executor() -> None:
    """
    Print the current user's transactions in a table.
    """
    u = auth.get_current_user()
    if not u:
        print_error("Please login.")
        return

    rows = portfolio_service.list_transactions(username=u.username)
    if not rows:
        print_error("No transactions found.")
        return

    _render_transactions_table(rows, f"Transactions for {u.username}")


def _render_transactions_table(rows: Iterable[Any], title: str) -> None:
    """
    Render a list of transactions in a table.

    rows can be either:
    - ORM Transaction objects, or
    - dict-like records with the same keys.
    """
    table = Table(
        title=title,
        expand=True,
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold",
    )
    table.add_column("ID", justify="right", no_wrap=True, width=4)
    table.add_column("Time", justify="left", no_wrap=True, min_width=17)
    table.add_column("Type", justify="center", no_wrap=True, width=5)
    table.add_column("Portfolio", justify="right", no_wrap=True, width=8)
    table.add_column("Ticker", justify="left", no_wrap=True, width=8)
    table.add_column("Qty", justify="right", no_wrap=True, min_width=6)
    table.add_column("Price", justify="right", no_wrap=True, min_width=8)
    table.add_column("Amount", justify="right", no_wrap=True, min_width=10)
    table.add_column("Balance After", justify="right", no_wrap=True, min_width=18)

    for r in rows:
        if isinstance(r, Transaction):
            table.add_row(
                str(r.id),
                str(r.timestamp),
                r.type,
                str(r.portfolio_id),
                r.ticker,
                f"{float(r.quantity):,.2f}",
                f"{float(r.price):,.2f}",
                f"{float(r.amount):,.2f}",
                f"{float(r.balance_after):,.2f}",
            )
        else:
            # dict-like fallback
            table.add_row(
                str(r.get("id", "")),
                str(r.get("timestamp", "")),
                str(r.get("type", "")),
                str(r.get("portfolio_id", "")),
                str(r.get("ticker", "")),
                f'{float(r.get("quantity", 0.0)):,.2f}',
                f'{float(r.get("price", 0.0)):,.2f}',
                f'{float(r.get("amount", 0.0)):,.2f}',
                f'{float(r.get("balance_after", 0.0)):,.2f}',
            )

    _console.print(table)


def admin_view_user_transactions_executor() -> None:
    """Admin-only: view another user's transactions."""
    u = auth.get_current_user()
    if not u or u.role != "admin":
        print_error("Only admins can view other users' transactions.")
        return

    target = _console.input("Username to inspect: ").strip()
    if not target:
        print_error("Username cannot be empty.")
        return

    try:
        rows = portfolio_service.list_transactions(username=target)
        if not rows:
            print_error(f"No transactions found for '{target}'.")
            return
        _render_transactions_table(rows, f"Transactions for {target}")
    except Exception as e:
        print_error(str(e))


# ----------------------------------------------------
# (D) Router handler: fallbacks and correct navigation
# ----------------------------------------------------
def handle_user_selection(menu_id: int, user_selection: int) -> None:
    """
    Central dispatcher:
    - Handles explicit 'Back/Exit/Logout' for known menus.
    - Looks up in _router; if not found, shows an error and stays on current menu.
    - Catches business exceptions and keeps the user in the current menu.
    """

    # Login menu: 0 = Exit
    if menu_id == constants.LOGIN_MENU and user_selection == 0:
        import sys
        sys.exit(0)

    # Manage Users: 0 = Back (return to Main Menu)
    if menu_id == constants.MANAGE_USERS_MENU and user_selection == 0:
        return print_menu(constants.MAIN_MENU)

    # Main Menu: 0 = Logout (return to Login Menu)
    if menu_id == constants.MAIN_MENU and user_selection == 0:
        return print_menu(constants.LOGIN_MENU)

    # Marketplace: 0 = Back (return to Main Menu)
    if menu_id == constants.MARKETPLACE_MENU and user_selection == 0:
        return print_menu(constants.MAIN_MENU)

    # Manage Portfolios: 0 = Back (return to Main Menu)
    if menu_id == constants.MANAGE_PORTFOLIOS_MENU and user_selection == 0:
        return print_menu(constants.MAIN_MENU)

    # Build router key and resolve target action
    formatted_user_input = f"{menu_id}.{user_selection}"
    menu_functions = _router.get(formatted_user_input)

    # Unregistered option → friendly message and stay on the same menu
    if not menu_functions:
        print_error("Invalid option. Please choose a valid menu item.")
        return print_menu(menu_id)

    # Execute and/or navigate with robust exception handling
    try:
        if menu_functions.executor:
            menu_functions.executor()
        if menu_functions.navigator:
            print_menu(menu_functions.navigator())
    except Exception as e:
        print_error(str(e))
        print_menu(menu_id)


# ----------------------------------------------
# (E) Print the menu and read a safe int choice
# ----------------------------------------------
def print_menu(menu_id: int) -> None:
    """Render a menu by ID, then read a safe integer selection and dispatch."""
    _console.print(_menus[menu_id])
    user_selection = _ask_int(">> ")
    handle_user_selection(menu_id, user_selection)


# -------------------------
# Router (register actions)
# -------------------------
_router: Dict[str, MenuFunctions] = {
    # Login menu
    f"{constants.LOGIN_MENU}.1": MenuFunctions(executor=login, navigator=None),

    # Main Menu navigations
    f"{constants.MAIN_MENU}.1": MenuFunctions(
        executor=None,
        navigator=_to_manage_users_menu_guarded,
    ),
    f"{constants.MAIN_MENU}.2": MenuFunctions(
        executor=None,
        navigator=lambda: constants.MANAGE_PORTFOLIOS_MENU,
    ),
    f"{constants.MAIN_MENU}.3": MenuFunctions(
        executor=None,
        navigator=lambda: constants.MARKETPLACE_MENU,
    ),
    f"{constants.MAIN_MENU}.4": MenuFunctions(
        executor=review_transactions_executor,
        navigator=lambda: constants.MAIN_MENU,
    ),

    # Manage Portfolios actions
    f"{constants.MANAGE_PORTFOLIOS_MENU}.1": MenuFunctions(
        executor=view_portfolios_executor,
        navigator=lambda: constants.MANAGE_PORTFOLIOS_MENU,
    ),
    f"{constants.MANAGE_PORTFOLIOS_MENU}.2": MenuFunctions(
        executor=create_portfolio_executor,
        navigator=lambda: constants.MANAGE_PORTFOLIOS_MENU,
    ),
    f"{constants.MANAGE_PORTFOLIOS_MENU}.3": MenuFunctions(
        executor=delete_portfolio_executor,
        navigator=lambda: constants.MANAGE_PORTFOLIOS_MENU,
    ),
    f"{constants.MANAGE_PORTFOLIOS_MENU}.4": MenuFunctions(
        executor=sell_security_executor,
        navigator=lambda: constants.MANAGE_PORTFOLIOS_MENU,
    ),

    # Marketplace actions
    f"{constants.MARKETPLACE_MENU}.1": MenuFunctions(
        executor=view_securities_executor,
        navigator=lambda: constants.MARKETPLACE_MENU,
    ),
    f"{constants.MARKETPLACE_MENU}.2": MenuFunctions(
        executor=buy_security_executor,
        navigator=lambda: constants.MARKETPLACE_MENU,
    ),

    # Manage Users actions
    f"{constants.MANAGE_USERS_MENU}.1": MenuFunctions(
        executor=view_users_executor,
        navigator=lambda: constants.MANAGE_USERS_MENU,
    ),
    f"{constants.MANAGE_USERS_MENU}.2": MenuFunctions(
        executor=create_user_executor,
        navigator=lambda: constants.MANAGE_USERS_MENU,
    ),
    f"{constants.MANAGE_USERS_MENU}.3": MenuFunctions(
        executor=delete_user_executor,
        navigator=lambda: constants.MANAGE_USERS_MENU,
    ),
    f"{constants.MANAGE_USERS_MENU}.4": MenuFunctions(
        executor=admin_view_user_transactions_executor,
        navigator=lambda: constants.MANAGE_USERS_MENU,
    ),
}
