# main.py 
from .cli.menu_printer import print_menu 
from .cli import constants

def main() -> None:
    print_menu(constants.LOGIN_MENU)

if __name__ == "__main__":
    main()
