# app/cli/menu_printer.py
from typing import Dict, Tuple, Optional
from rich.console import Console
from cli import constants
from domain.MenuFunctions import MenuFunctions
import db
import sys
from rich.table import Table

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
    """Authenticate user; on success set session and go to main menu."""
    username, password = get_login_inputs()
    # Use db.login to validate; it raises ValueError on failure
    user = db.login(username, password)
    db.current_user = user  # record session (simple in-memory session)
    print_success(f"Welcome, {user.firstname}!")
    print_menu(constants.MAIN_MENU)
    
def view_securities_executor() -> None:
    """
    Executor for Marketplace -> 'View securities'.
    Prints a simple table: ticker, name, reference price.
    """
    rows = db.list_securities()
    if not rows:
        print_error("No securities available.")
        return

    table = Table(title="Available Securities")
    table.add_column("Ticker", justify="left")
    table.add_column("Name", justify="left")
    table.add_column("Reference Price", justify="right")

    for r in rows:
        table.add_row(
            str(r["ticker"]),
            str(r["name"]),
            f'{float(r["reference_price"]):.2f}'
        )

    _console.print(table)
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

def buy_security_executor() -> None:
    """
    Executor for Marketplace -> 'Add security to a portfolio (Buy)'.
    Prompts: Portfolio ID, Ticker, Quantity.
    Uses reference price by default.
    """
    # Show user's portfolios (short summary) to help choose an ID
    if db.current_user:
        portfolios = db.list_portfolios(owner_username=db.current_user.username)
        if portfolios:
            _console.print("[bold]Your portfolios:[/bold]")
            t = Table(show_header=True, header_style="bold")
            t.add_column("ID", justify="right")
            t.add_column("Name", justify="left")
            for p in portfolios:
                t.add_row(str(p["id"]), str(p["name"]))
            _console.print(t)

    pid = _ask_int("Portfolio ID: ")
    ticker = _console.input("Ticker: ").strip().upper()
    qty = _ask_positive_float("Quantity: ")

    try:
        result = db.buy_security(portfolio_id=pid, ticker=ticker, quantity=qty, price=None)
        print_success(
            f"Bought {result['quantity']} {result['ticker']} @ {result['price']:.2f} "
            f"(cost {result['cost']:.2f}). New balance: {result['balance_after']:.2f}"
        )
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
    f"{constants.MAIN_MENU}.1": MenuFunctions(executor=None, navigator=lambda: constants.MANAGE_USERS_MENU),
    f"{constants.MAIN_MENU}.2": MenuFunctions(executor=None, navigator=lambda: constants.MANAGE_PORTFOLIOS_MENU),

    # NEW: Main Menu option 3 navigates to Marketplace menu
    f"{constants.MAIN_MENU}.3": MenuFunctions(executor=None, navigator=lambda: constants.MARKETPLACE_MENU),

    # Placeholder: Future Marketplace actions
    f"{constants.MARKETPLACE_MENU}.1": MenuFunctions(
    executor=view_securities_executor,
    navigator=None,
    ),
    # Marketplace: 2 = buy security
    f"{constants.MARKETPLACE_MENU}.2": MenuFunctions(
    executor=buy_security_executor,
    navigator=None,
    ),
}


    