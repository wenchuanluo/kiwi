from typing import Dict, Tuple
from rich.console import Console
from cli import constants
from domain.MenuFunctions import MenuFunctions
import db
import sys
_console = Console()
_menus: Dict[int, str] = {
    constants.LOGIN_MENU: "----\nWelcome to Kiwi\n----\n1. Login\n0. Exit",
    constants.MAIN_MENU: "----\nMain Menu\n----\n1. Manage Users\n2. Manage portfolios\n3. Market places\n0. Logout",
    constants.MANAGE_USERS_MENU: "----\nManage Users\n----\n1. View User\n2. Add User\n3. Delete Users\n0. Back to Main Menu"
}



def get_login_inputs() -> tuple[str, str]:
    username = _console.input("Username: ")
    password = _console.input("Password: ")
    _console.print("\n")
    return username, password

# throw an error if login fails, return nothing otherwise
def login():
    username, password = get_login_inputs()
    user =db.query_user(username)
    # either the user is none so the username is incorrect
    # if not user:
    #     print_error("Username does not exist")
    #     print_menu(constants.LOGIN_MENU)
        
    # else:
    #     if user.password == password:
    #         print_menu(constants.MAIN_MENU)
    #     else:
    #         print_error("Login failed")
    #         print_menu(constants.LOGIN_MENU)
    if not user or user.password != password:
            raise Exception("Error: Login failed")
    
    
# purpose: to define the functions that needs to be executed depending on the user selection
# user selection depends on the menu
_router: Dict[str, MenuFunctions] = {
    "0.1": MenuFunctions(executor=login, navigator=lambda: constants.MAIN_MENU) # login
}


def print_error(error: str):
    _console.print(error, style="red")


def handle_user_selection(menu_id: int, user_selection: int):
    # handle terminal inputs (the 0 option)
    if user_selection == 0:
        if menu_id == constants.LOGIN_MENU:
            sys.exit(0) #terminate the application
        elif menu_id == constants.MAIN_MENU:
            print_menu(constants.LOGIN_MENU)
        else:
            print_menu(constants.LOGIN_MENU)
    formatted_user_input = f"{str(menu_id)}.{str(user_selection)}"
    menu_functions = _router[formatted_user_input]
    try:
        if menu_functions.executor:
            menu_functions.executor()
        if menu_functions.navigator:
            print_menu(menu_functions.navigator())
    except Exception as e:
        print_error(str(e))
        print_menu(menu_id)

def print_menu(menu_id: int):
    _console.print(_menus[menu_id])
    user_selection = int(_console.input(">> ")) # check if the user input is valid
    handle_user_selection(menu_id, user_selection)
    
    