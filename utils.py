#utils.py
import os

def clear():
    """Clears the terminal screen."""
    if os.name=='posix':
        os.system("clear")
    elif os.name=='nt':
        os.system("cls")
    else:
        os.system("clear")

def get_key(stdscr):
    """Prompts the user to press an arrow key and returns the key code."""
    stdscr.addstr("Press an arrow key...\n")
    return stdscr.getch()