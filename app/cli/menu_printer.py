# app/cli/menu_printer.py
from typing import Dict, Tuple, Optional
from rich.console import Console
from cli import constants
from domain.MenuFunctions import MenuFunctions
import db
import sys

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
    # Login menu: choose 1 to perform login() (navigation happens inside login)
    f"{constants.LOGIN_MENU}.1": MenuFunctions(
        executor=login,
        navigator=None,
    ),

    # Examples for future features (leave commented until implemented):
    # f"{constants.MAIN_MENU}.1": MenuFunctions(executor=None, navigator=lambda: constants.MANAGE_USERS_MENU),
    # f"{constants.MAIN_MENU}.2": MenuFunctions(executor=None, navigator=lambda: constants.MANAGE_PORTFOLIOS_MENU),
    # f"{constants.MAIN_MENU}.3": MenuFunctions(executor=None, navigator=lambda: constants.MARKETPLACE_MENU),
}

    