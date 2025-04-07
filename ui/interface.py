# ui/interface.py

"""
Curses-based user interface for Beluga video generation toolkit
"""
import curses
import logging
import textwrap
from typing import List, Dict, Callable, Optional
from pathlib import Path
from dataclasses import dataclass
from PyQt5.QtWidgets import QApplication, QFileDialog

# Import local modules
from core.generator import ChatGenerator
from core.validator import ScriptValidator
from core.compiler import VideoCompiler
from utils.constants import UI, Paths, Font, Validation
from utils.helpers import safe_create_directory, clear_directory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure type hints
CursesWindow = curses.window
ColorPair = int

@dataclass
class MenuItem:
    label: str
    handler: Callable
    shortcut: Optional[str] = None

class BelugaUI:
    """Main UI controller for curses-based interface"""
    
    def __init__(self, stdscr: CursesWindow):
        self.stdscr = stdscr
        self.current_row = 0
        self.should_exit = False
        self.generator = ChatGenerator()
        self.validator = ScriptValidator()
        self.compiler = VideoCompiler()
        
        # Initialize UI properties
        self._init_colors()
        self._init_main_menu()

    def _init_colors(self) -> None:
        """Initialize color pairs from configuration"""
        curses.use_default_colors()
        for pair_id, (fg, bg) in UI.COLOR_PAIRS.items():
            curses.init_pair(pair_id, fg, bg)

    def _init_main_menu(self) -> None:
        """Configure main menu structure"""
        self.menu_stack: List[List[MenuItem]] = [[
            MenuItem("Generate Video", self.run_generate_chat, "G"),
            MenuItem("Validate Script", self.run_validate_script, "V"),
            MenuItem("Instructions", self.show_instructions, "I"),
            MenuItem("Exit", self.exit_app, "Q")
        ]]

    def run(self) -> None:
        """Main UI event loop"""
        while not self.should_exit:
            current_menu = self.menu_stack[-1]
            self._draw_screen(
                header="Text 2 Beluga",
                description=textwrap.dedent("""
                    Welcome to Text2Beluga! Easily generate a Beluga-style video 
                    from a simple text script. Use arrow keys to navigate and 
                    Enter to select options.
                """),
                menu_items=[item.label for item in current_menu],
                current_row=self.current_row
            )
            self._handle_input(current_menu)

    def _draw_screen(
        self,
        header: str,
        description: str,
        menu_items: List[str],
        current_row: int
    ) -> None:
        """Render the current UI state"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        y = UI.MARGINS["top"]

        # Draw header
        self.stdscr.attron(curses.color_pair(1))
        header_lines = textwrap.wrap(header, width - UI.MARGINS["left"] * 2)
        for line in header_lines:
            self.stdscr.addstr(y, UI.MARGINS["left"], line)
            y += 1
        self.stdscr.attroff(curses.color_pair(1))
        y += 1

        # Draw description
        self.stdscr.attron(curses.color_pair(3))
        desc_lines = textwrap.wrap(description, width - UI.MARGINS["left"] * 2)
        for line in desc_lines:
            self.stdscr.addstr(y, UI.MARGINS["left"], line)
            y += 1
        y += 1

        # Draw menu items
        for idx, item in enumerate(menu_items):
            x = UI.MARGINS["left"]
            if idx == current_row:
                self.stdscr.attron(curses.color_pair(2))
                self.stdscr.addstr(y, x, "> " + item)
                self.stdscr.attroff(curses.color_pair(2))
            else:
                self.stdscr.addstr(y, x, "  " + item)
            y += 1

        self.stdscr.refresh()

    def _handle_input(self, menu_items: List[MenuItem]) -> None:
        """Process user keyboard input"""
        key = self.stdscr.getch()
        
        if key in [curses.KEY_UP, ord('k')]:
            self.current_row = max(0, self.current_row - 1)
        elif key in [curses.KEY_DOWN, ord('j')]:
            self.current_row = min(len(menu_items)-1, self.current_row + 1)
        elif key in [curses.KEY_ENTER, 10, 13]:
            menu_items[self.current_row].handler()
        elif key == ord('q'):
            self.should_exit = True

    def run_generate_chat(self) -> None:
        """Handle video generation workflow"""
        if Paths.FINAL_VIDEO.exists():
            Paths.FINAL_VIDEO.unlink()

        script_path = self._get_file_path("Select Script File")
        if not script_path:
            return

        try:
            # Generate chat images
            self._draw_processing("Generating Chat Images...")
            self.generator.process_script(script_path, Paths.CHAT_OUTPUT)

            # Compile video
            self._draw_processing("Compiling Video...")
            self.compiler.compile(Paths.CHAT_OUTPUT, script_path)

            # Cleanup
            clear_directory(Paths.CHAT_OUTPUT)
            self._draw_result("Video generated successfully!")

        except Exception as e:
            logger.error(f"Generation error: {str(e)}", exc_info=True)
            self._draw_error(f"Generation failed: {str(e)}")

    def run_validate_script(self) -> None:
        """Handle script validation workflow"""
        script_path = self._get_file_path("Select Script File")
        if not script_path:
            return

        try:
            self._draw_processing("Validating Script...")
            errors = self.validator.validate(script_path)
            
            if errors:
                error_messages = [f"Line {e.line_number}: {e.message}" for e in errors]
                self._draw_result("Validation issues found:", error_messages)
            else:
                self._draw_result("Script is valid!")

        except Exception as e:
            self._draw_error(f"Validation failed: {str(e)}")

    def show_instructions(self) -> None:
        """Display instructions submenu"""
        instructions_menu = [
            MenuItem("Formatting Guide", self.show_formatting_help),
            MenuItem("Sound Effects", self.browse_sounds),
            MenuItem("Back", lambda: None)
        ]
        self.menu_stack.append(instructions_menu)
        self.current_row = 0

    def show_formatting_help(self) -> None:
        """Display formatting guidelines"""
        content = textwrap.dedent(Font.FORMATTING_GUIDE)
        self._draw_text_screen("Formatting Guide", content)

    def browse_sounds(self) -> None:
        """Browse available sound effects"""
        sound_files = list(Paths.SOUNDS.glob("*.mp3"))
        sound_names = [f.stem for f in sound_files]
        sound_names.append("Back")
        
        self._draw_screen(
            header="Sound Effects",
            description="Select a sound to preview:",
            menu_items=sound_names,
            current_row=self.current_row
        )
        # Implement sound preview logic here

    def _get_file_path(self, title: str) -> Optional[Path]:
        """Show Qt file dialog and return selected path"""
        app = QApplication.instance() or QApplication([])
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            None, title, "", "Text Files (*.txt)", options=options
        )
        app.quit()
        return Path(filename) if filename else None

    def _draw_processing(self, message: str) -> None:
        """Show processing screen"""
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, message, curses.color_pair(1))
        self.stdscr.refresh()

    def _draw_result(self, message: str, details: List[str] = []) -> None:
        """Show result screen"""
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, message, curses.color_pair(1))
        for i, detail in enumerate(details, start=3):
            self.stdscr.addstr(i, 3, detail)
        self.stdscr.addstr("\n\nPress any key to continue...")
        self.stdscr.getch()

    def _draw_error(self, message: str) -> None:
        """Show error screen"""
        self.stdscr.clear()
        self.stdscr.addstr(1, 1, "ERROR:", curses.color_pair(2))
        self.stdscr.addstr(2, 1, message, curses.color_pair(3))
        self.stdscr.addstr("\n\nPress any key to continue...")
        self.stdscr.getch()

    def exit_app(self) -> None:
        """Clean exit handler"""
        self.should_exit = True

def main():
    """Entry point for curses application"""
    curses.wrapper(lambda stdscr: BelugaUI(stdscr).run())

if __name__ == '__main__':
    main()