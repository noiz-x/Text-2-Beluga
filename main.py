# main.py

"""
Main entry point for Beluga video generation toolkit
"""
from ui.interface import BelugaUI
import logging
import curses

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Launch curses-based user interface"""
    try:
        curses.wrapper(lambda stdscr: BelugaUI(stdscr).run())
    except Exception as e:
        print(f"Critical error: {str(e)}")
        input("Press Enter to exit...")

if __name__ == '__main__':
    main()