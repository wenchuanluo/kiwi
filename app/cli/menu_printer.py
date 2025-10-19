# app/cli/menu_printer.py
from typing import Dict, Tuple, Optional
from rich.console import Console
from cli import constants
from domain.MenuFunctions import MenuFunctions
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # add /app to sys.path
# from ... import db  <-- remove this line if present
from service import login_service as auth
from service import user_service, portfolio_service, security_service
from domain.User import User
from rich.table import Table
from rich.table import Table
from domain.User import User
from rich import box
import db
import shutil


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
0. Back
""",
 # NEW: Marketplace (accessible to all users)
    constants.MARKETPLACE_MENU: """[bold]Marketplace[/bold]
----
1. View available securities
2. Add security to a portfolio (Buy)
0. Back
"""
,
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
# UI helpers (kept minimal; pure presentation only)
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
    # Determine terminal width
    return Table(
        title=title,
        expand=True,           # 
        box=box.SIMPLE_HEAVY,  # 
        pad_edge=False,        # 
        show_header=True,
        header_style="bold"
    )


# ----------------------------------------------------
# (A) Gather login inputs (with hidden password input)
# ----------------------------------------------------
def get_login_inputs() -> tuple[str, str]:
    """Prompt for username and password (visible while typing)."""
    username = _console.input("Username: ")
    password = _console.input("Password: ")  # restored visible input
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

# --------------------------------------------------------
# (C) Login executor: set session and navigate to main menu
# --------------------------------------------------------
def login() -> None:
    username, password = get_login_inputs()
    user = auth.login(username, password)
    auth.set_current_user(user)  # 
    import db
    db.set_current_user(user)    # 

    print_success(f"Welcome, {username}!")
    print_menu(constants.MAIN_MENU)


    
def view_securities_executor() -> None:
    """Print ticker, Issuer, reference price."""
    rows = security_service.list_securities()
    if not rows:
        print_error("No securities available.")
        return
    table = Table(title="Available Securities")
    table.add_column("Ticker"); table.add_column("Issuer"); table.add_column("Reference Price", justify="right")
    for r in rows:
        # security_service.list_securities() returns rows with key 'issuer' (lowercase)
        issuer = r.get("issuer") or r.get("Issuer") or ""
        table.add_row(str(r["ticker"]), str(issuer), f'{float(r["reference_price"]):.2f}')
    _console.print(table)


def buy_security_executor() -> None:
    """Buy a security into a portfolio."""
    u = auth.get_current_user()
    if not u:
        print_error("Please login.")
        return

    # show user's portfolios
    portfolios = portfolio_service.list_portfolios(owner_username=u.username)
    if portfolios:
        t = Table(show_header=True, header_style="bold"); t.add_column("ID", justify="right"); t.add_column("Name")
        for p in portfolios: t.add_row(str(p["id"]), str(p["name"]))
        _console.print(t)

    pid = _ask_int("Portfolio ID: ")
    ticker = _console.input("Ticker: ").strip().upper()
    qty = _ask_positive_float("Quantity: ")
    try:
        result = security_service.buy_security(portfolio_id=pid, ticker=ticker, quantity=qty, price=None)
        print_success(
            f"Bought {result['quantity']} {result['ticker']} @ {result['price']:.2f} "
            f"(cost {result['cost']:.2f}). New balance: {result['balance_after']:.2f}"
        )
    except Exception as e:
        print_error(str(e))

        
        
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
    


_console = Console()

def view_users_executor() -> None:
    """Print a table of all users (username, first, last, role, balance)."""
    rows = db.list_users()
    if not rows:
        try:
            print_error("No users found.")
        except NameError:
            _console.print("[bold red]No users found.[/bold red]")
        return

    term_width = _console.size.width
    compact = term_width < 80  

    table = Table(
        title="[b]ALL Users[/b]",
        box=box.SQUARE,          # 
        show_edge=True,
        border_style="cyan",
        header_style="bold cyan",
        pad_edge=True,
        expand=False,            # 
        row_styles=["none", "dim"],  # 
        show_lines=False,
    )

    if compact:
        
        table.add_column("User",   justify="left",  no_wrap=True, min_width=8,  max_width=16, overflow="ellipsis")
        table.add_column("First",  justify="left",  no_wrap=True, min_width=8,  max_width=16, overflow="ellipsis")
        table.add_column("Last",   justify="left",  no_wrap=True, min_width=8,  max_width=16, overflow="ellipsis")
        table.add_column("Role",   justify="center",no_wrap=True, min_width=5,  max_width=8,  overflow="ellipsis")
        table.add_column("Balance",justify="right", no_wrap=True, min_width=10, max_width=14)
    else:
        
        nbsp = "\u00A0"
        table.add_column("Username",        justify="left",  no_wrap=True, min_width=12, max_width=20, overflow="ellipsis")
        table.add_column(f"First{nbsp}name",justify="left",  no_wrap=True, min_width=12, max_width=20, overflow="ellipsis")
        table.add_column(f"Last{nbsp}name", justify="left",  no_wrap=True, min_width=12, max_width=20, overflow="ellipsis")
        table.add_column("Role",            justify="center",no_wrap=True, min_width=6,  max_width=10, overflow="ellipsis")
        table.add_column("Balance",         justify="right", no_wrap=True, min_width=12, max_width=16)

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
    username = _console.input("Username: ").strip()
    password = _console.input("Password: ").strip()
    first    = _console.input("First name: ").strip()
    last     = _console.input("Last name: ").strip()
    role     = _console.input("Role (admin/user): ").strip().lower()
    # balance (non-negative)
    while True:
        bal_str = _console.input("Initial balance: ").strip()
        try:
            balance = float(bal_str); 
            if balance < 0: raise ValueError
            break
        except ValueError:
            print_error("Balance must be a non-negative number.")
    try:
        user = User(username, password, first, last, balance, role=role)
        user_service.create_user(user)
        print_success(f"User '{username}' created.")
    except Exception as e:
        print_error(str(e))


def delete_user_executor() -> None:
    username = _console.input("Username to delete: ").strip()
    try:
        requester = auth.get_current_user()
        user_service.delete_user(username, requester=requester)
        print_success(f"User '{username}' deleted.")
    except Exception as e:
        print_error(str(e))

        
def view_portfolios_executor() -> None:
    u = auth.get_current_user()
    if not u:
        print_error("Please login."); return
    rows = portfolio_service.list_portfolios(owner_username=u.username)
    if not rows:
        print_error("You have no portfolios yet."); return

    table = Table(title="Your Portfolios")
    table.add_column("ID", justify="right"); table.add_column("Name")
    table.add_column("Total Value", justify="right"); table.add_column("Holdings (ticker:qty)")
    for p in rows:
        total = portfolio_service.portfolio_total_value(p)
        holdings = p["holdings"]
        summary = ", ".join(f"{t}:{q}" for t, q in holdings.items()) if holdings else "-"
        table.add_row(str(p["id"]), str(p["name"]), f"{total:.2f}", summary)
    _console.print(table)


def create_portfolio_executor() -> None:
    u = auth.get_current_user()
    if not u:
        print_error("Please login."); return
    name = _console.input("Name: ").strip()
    description = _console.input("Description: ").strip()
    strategy = _console.input("Strategy: ").strip()
    try:
        p = portfolio_service.create_portfolio(u.username, name, description, strategy)
        print_success(f"Created portfolio #{p['id']} ({p['name']}).")
    except Exception as e:
        print_error(str(e))


def delete_portfolio_executor() -> None:
    u = auth.get_current_user()
    if not u:
        print_error("Please login."); return
    pid = _ask_int("Portfolio ID to delete: ")
    try:
        portfolio_service.delete_portfolio(pid, requesting_user=u)
        print_success(f"Deleted portfolio {pid}.")
    except Exception as e:
        print_error(str(e))


def sell_security_executor() -> None:
    u = auth.get_current_user()
    if not u:
        print_error("Please login."); return
    portfolios = portfolio_service.list_portfolios(owner_username=u.username)
    if portfolios:
        t = Table(show_header=True, header_style="bold"); t.add_column("ID", justify="right"); t.add_column("Name")
        for p in portfolios: t.add_row(str(p["id"]), str(p["name"]))
        _console.print(t)

    pid = _ask_int("Portfolio ID: ")
    ticker = _console.input("Ticker: ").strip().upper()
    qty = _ask_positive_float("Quantity: ")

    # user can ask price; if not, just use market price
    price_text = _console.input("Sale price [blank = use market price]: ").strip()
    price = float(price_text) if price_text else None

    try:
        result = portfolio_service.sell_security(pid, ticker, qty, price=price)  # import price
        src = "(manual)" if price is not None else "(market)"
        print_success(
            f"Sold {result['quantity']} {result['ticker']} @ {result['price']:.2f} {src} "
            f"(proceeds {result['proceeds']:.2f}). New balance: {result['balance_after']:.2f}"
        )
    except Exception as e:
        print_error(str(e))



# def review_transactions_executor() -> None:
#     """
#     Print the current user's transactions in a table.
#     """
#     if not auth.get_current_user():
#         print_error("Please login.")
#         return

#     rows = db.list_transactions(username=auth.get_current_user().username)
#     if not rows:
#         print_error("No transactions found.")
#         return

def review_transactions_executor() -> None:
    u = auth.get_current_user()
    if not u:
        print_error("Please login."); return
    rows = portfolio_service.list_transactions(username=u.username)
    if not rows:
        print_error("No transactions found."); return
    # Use a wider table, prevent wrapping for key columns and right-align numbers
    table = Table(
        title=f"Transactions for {u.username}",
        expand=True,
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold",
    )

    table.add_column("ID", justify="right", no_wrap=True, width=6)
    table.add_column("Time", justify="left", no_wrap=True, min_width=19)
    table.add_column("Type", justify="center", no_wrap=True, width=7)
    table.add_column("Portfolio", justify="right", no_wrap=True, width=10)
    table.add_column("Ticker", justify="left", no_wrap=True, width=8)
    table.add_column("Qty", justify="right", no_wrap=True, min_width=8)
    table.add_column("Price", justify="right", no_wrap=True, min_width=10)
    table.add_column("Amount", justify="right", no_wrap=True, min_width=12)
    table.add_column("Balance After", justify="right", no_wrap=True, min_width=14)

    for r in rows:
        # Defensive access and consistent formatting
        tid = str(r.get("id", ""))
        ts = str(r.get("timestamp", ""))
        ttype = str(r.get("type", ""))
        pid = str(r.get("portfolio_id", ""))
        ticker = str(r.get("ticker", ""))
        qty = float(r.get("quantity", 0.0))
        price = float(r.get("price", 0.0))
        amount = float(r.get("amount", 0.0))
        bal_after = float(r.get("balance_after", 0.0))

        table.add_row(
            tid,
            ts,
            ttype,
            pid,
            ticker,
            f"{qty:,.2f}",
            f"{price:,.2f}",
            f"{amount:,.2f}",
            f"{bal_after:,.2f}",
        )

    _console.print(table)






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
    
    if menu_id == constants.MANAGE_PORTFOLIOS_MENU and user_selection == 0:
        return print_menu(constants.MAIN_MENU)



    # Build router key and resolve target action
    formatted_user_input = f"{menu_id}.{user_selection}"
    menu_functions = _router.get(formatted_user_input)  # type: ignore[name-defined]

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
# Only register what's already implemented in your codebase.
# Keep it minimal to match your class demo. We wire up just:
# - Login menu: option 1 -> login()
# Other menus (Manage Users / Portfolios / Marketplace) can be added later
# feature-by-feature without changing the structure here.
_router: Dict[str, MenuFunctions] = {
    # Existing entries
    f"{constants.LOGIN_MENU}.1": MenuFunctions(executor=login, navigator=None),

    # Main Menu navigations
    f"{constants.MAIN_MENU}.1": MenuFunctions(
        executor=None,
        navigator=_to_manage_users_menu_guarded,
    ),

    f"{constants.MAIN_MENU}.2": MenuFunctions(
    executor=None, navigator=lambda: constants.MANAGE_PORTFOLIOS_MENU
    ),

    # NEW: Main Menu option 3 navigates to Marketplace menu
    f"{constants.MAIN_MENU}.3": MenuFunctions(executor=None, navigator=lambda: constants.MARKETPLACE_MENU),

    # Main Menu: 4 = Review transactions (print table then return to Main)
    f"{constants.MAIN_MENU}.4": MenuFunctions(
        executor=review_transactions_executor,
        navigator=lambda: constants.MAIN_MENU,
    ),

    # Manage Portfolios actions (return back to the same menu after action)
    f"{constants.MANAGE_PORTFOLIOS_MENU}.1": MenuFunctions(
        executor=view_portfolios_executor, navigator=lambda: constants.MANAGE_PORTFOLIOS_MENU
    ),
    f"{constants.MANAGE_PORTFOLIOS_MENU}.2": MenuFunctions(
        executor=create_portfolio_executor, navigator=lambda: constants.MANAGE_PORTFOLIOS_MENU
    ),
    f"{constants.MANAGE_PORTFOLIOS_MENU}.3": MenuFunctions(
        executor=delete_portfolio_executor, navigator=lambda: constants.MANAGE_PORTFOLIOS_MENU
    ),
    f"{constants.MANAGE_PORTFOLIOS_MENU}.4": MenuFunctions(
        executor=sell_security_executor, navigator=lambda: constants.MANAGE_PORTFOLIOS_MENU
    ),

    # Marketplace: after action, stay in Marketplace
    f"{constants.MARKETPLACE_MENU}.1": MenuFunctions(
        executor=view_securities_executor,
        navigator=lambda: constants.MARKETPLACE_MENU,   # ← NEW
    ),
    
    f"{constants.MARKETPLACE_MENU}.2": MenuFunctions(
        executor=buy_security_executor,
        navigator=lambda: constants.MARKETPLACE_MENU,   # ← NEW
    ),

    # Manage Users actions (after action, return to Manage Users menu)
    f"{constants.MANAGE_USERS_MENU}.1": MenuFunctions(
        executor=view_users_executor,
        navigator=lambda: constants.MANAGE_USERS_MENU,  # ← NEW
    ),
    f"{constants.MANAGE_USERS_MENU}.2": MenuFunctions(
        executor=create_user_executor,
        navigator=lambda: constants.MANAGE_USERS_MENU,  # ← NEW
    ),
    f"{constants.MANAGE_USERS_MENU}.3": MenuFunctions(
        executor=delete_user_executor,
        navigator=lambda: constants.MANAGE_USERS_MENU,  # ← NEW
    ),
}


    