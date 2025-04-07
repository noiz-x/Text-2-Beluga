# utils/constants.py

"""
Central configuration file for all project constants and paths
"""
import curses
import logging
from pathlib import Path
from typing import Tuple, List, Final

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# Base Directory Configuration
# ---------------------------
BASE_DIR: Final[Path] = Path(__file__).parent.parent
ASSETS_DIR: Final[Path] = BASE_DIR / "assets"

# ---------------------------
# File System Paths
# ---------------------------
class Paths:
    """Namespace for all file system paths"""
    PROFILE_PICTURES: Final[Path] = ASSETS_DIR / "profile_pictures"
    SOUNDS: Final[Path] = ASSETS_DIR / "sounds" / "mp3"
    FONTS: Final[Path] = ASSETS_DIR / "fonts"
    CHAR_CONFIG: Final[Path] = PROFILE_PICTURES / "characters.json"
    GREEN_ARROW: Final[Path] = ASSETS_DIR / "green_arrow.png"
    
    CHAT_OUTPUT: Final[Path] = BASE_DIR / "chat"
    FINAL_VIDEO: Final[Path] = BASE_DIR / "final_video.mp4"

# ---------------------------
# Video Generation Settings
# ---------------------------
class Video:
    """Video compilation parameters"""
    RESOLUTION: Final[Tuple[int, int]] = (1280, 720)
    FRAMERATE: Final[int] = 25
    CRF: Final[int] = 25  # Compression Rate Factor (0-51)
    PADDING_COLOR: Final[Tuple[int, int, int]] = (0, 0, 0)  # Black padding
    TEMP_FILE: Final[str] = "image_paths.txt"

# ---------------------------
# Chat Visualization Constants
# ---------------------------
class Chat:
    """Chat bubble rendering parameters"""
    # Dimensions
    WORLD_WIDTH: Final[int] = 1777
    WORLD_HEIGHT_JOINED: Final[int] = 100
    PROFPIC_SIZE: Final[int] = 120
    PROFPIC_POS: Final[Tuple[int, int]] = (36, 45)
    
    # Positioning
    MESSAGE_X: Final[int] = 190
    MESSAGE_Y_INIT: Final[int] = 115
    MESSAGE_DY: Final[int] = 70  # Vertical spacing between messages
    NAME_POS: Final[Tuple[int, int]] = (190, 53)
    TIME_SPACING: Final[int] = 25  # Between name and timestamp
    
    # Font Sizes
    NAME_FONT_SIZE: Final[int] = 50
    TIME_FONT_SIZE: Final[int] = 40
    MESSAGE_FONT_SIZE: Final[int] = 50
    JOINED_FONT_SIZE: Final[int] = 45
    
    # Colors (RGBA)
    BACKGROUND_COLOR: Final[Tuple[int, int, int, int]] = (54, 57, 63, 255)
    NAME_COLOR: Final[Tuple[int, int, int]] = (255, 255, 255)
    TIME_COLOR: Final[Tuple[int, int, int]] = (148, 155, 164)
    MESSAGE_COLOR: Final[Tuple[int, int, int]] = (220, 222, 225)
    MENTION_BG_COLOR: Final[Tuple[int, int, int]] = (74, 75, 114)
    
    # Joined Messages
    JOINED_TEXTS: Final[List[str]] = [
        "CHARACTER joined the party.",
        "CHARACTER is here.",
        "Welcome, CHARACTER. We hope you brought pizza.",
        # ... rest of templates
    ]

# ---------------------------
# Font Configuration
# ---------------------------
class Font:
    """Font settings and file paths"""
    NAME: Final[str] = "whitney"
    VARIANTS: Final[dict] = {
        "name": "semibold.ttf",
        "time": "semibold.ttf",
        "message": "medium.ttf",
        "message_italic": "medium_italic.ttf",
        "message_bold": "bold.ttf",
        "message_italic_bold": "bold_italic.ttf",
        "mention": "semibold.ttf",
        "mention_italic": "semibold_italic.ttf"
    }
    FORMATTING_GUIDE: Final[str] = """
    Proper Script Formatting:
    - Character lines: [Character Name]: Message $^duration
    - Welcome messages: WELCOME [Character] $^duration
    - Formatting: **bold**, __italics__, @mentions
    - Sound effects: #!sound_name
    """

# ---------------------------
# Validation Constants
# ---------------------------
class Validation:
    """Script validation parameters"""
    MAX_LINE_LENGTH: Final[int] = 200
    DURATION_RANGE: Final[Tuple[float, float]] = (0.1, 30.0)  # Min, Max in seconds
    SOUND_PATTERN: Final[str] = r'^[\w-]+$'  # Allowed sound effect names

# ---------------------------
# Audio Processing Constants
# ---------------------------
class Audio:
    """Audio configuration"""
    SUPPORTED_EXTENSIONS: Final[List[str]] = [".mp3", ".wav"]
    DEFAULT_EXTENSION: Final[str] = ".mp3"

# ---------------------------
# UI/UX Constants
# ---------------------------
class UI:
    """User interface settings"""
    COLOR_PAIRS: Final[dict] = {
        1: (curses.COLOR_MAGENTA, curses.COLOR_BLACK),  # Header
        2: (curses.COLOR_BLACK, curses.COLOR_MAGENTA),  # Highlight
        3: (curses.COLOR_WHITE, curses.COLOR_BLACK)     # Normal text
    }
    MARGINS: Final[dict] = {
        "left": 4,
        "right": 4,
        "top": 1
    }
    WRAP_WIDTH: Final[int] = 76  # Text wrapping column limit