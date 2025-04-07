# utils/types.py

"""
Custom type definitions and data classes for type safety across the project
"""
import logging
from typing import NewType, TypedDict, Tuple, List, Optional
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# Primitive Type Aliases
# ---------------------------
RGBColor = Tuple[int, int, int]
RGBAColor = Tuple[int, int, int, int]
Timestamp = NewType('Timestamp', str)
Milliseconds = NewType('Milliseconds', float)
ImagePath = NewType('ImagePath', Path)
SoundPath = NewType('SoundPath', Path)

# ---------------------------
# Data Classes
# ---------------------------
@dataclass(frozen=True)
class FrameData:
    """Metadata for video frame generation"""
    image_path: Path
    duration: float
    sound_effect: Optional[Path] = None

@dataclass(frozen=True)
class ValidationError:
    """Structured validation error information"""
    line_number: int
    message: str
    line_preview: str

@dataclass(frozen=True)
class MessageSegment:
    """Formatted segment of a chat message"""
    text: str
    is_bold: bool = False
    is_italic: bool = False
    is_mention: bool = False

@dataclass(frozen=True)
class AudioEvent:
    """Audio synchronization event"""
    start_time: float
    sound_path: Path
    duration: float

@dataclass(frozen=True)
class CharacterConfig:
    """Character profile configuration"""
    profile_pic: Path
    role_color: RGBColor
    mention_color: RGBColor = (201, 205, 251)

# ---------------------------
# Typed Dictionaries
# ---------------------------
class FontConfig(TypedDict):
    """Typed dictionary for font configuration"""
    name: str
    size: int
    path: Path

class MenuItem(TypedDict):
    """UI menu item structure"""
    label: str
    handler: callable
    shortcut: Optional[str]

# ---------------------------
# Enumerations
# ---------------------------
class MessageType(Enum):
    """Types of script messages"""
    WELCOME = "welcome"
    REGULAR = "message"
    COMMENT = "comment"
    NAME = "name"

class UIElement(Enum):
    """Types of UI elements"""
    HEADER = 1
    MENU_ITEM = 2
    DESCRIPTION = 3

class FormattingStyle(Enum):
    """Text formatting options"""
    BOLD = "**"
    ITALIC = "__"
    MENTION = "@"

# ---------------------------
# Complex Types
# ---------------------------
class ScriptLine:
    """Parsed script line structure"""
    line_type: MessageType
    content: str
    duration: float
    timestamp: datetime
    sound_effect: Optional[str]

ChatMessages = List[List[MessageSegment]]
ImageSequence = List[Tuple[ImagePath, Milliseconds]]
ValidationResult = Tuple[bool, List[ValidationError]]

# ---------------------------
# Configuration Types
# ---------------------------
class VideoSettings(TypedDict):
    """Video compilation settings"""
    resolution: Tuple[int, int]
    framerate: int
    crf: int
    padding_color: RGBColor

class AudioSettings(TypedDict):
    """Audio processing settings"""
    supported_formats: List[str]
    default_volume: float
    fade_duration: Milliseconds

# ---------------------------
# UI Configuration Types
# ---------------------------
class ColorPair(TypedDict):
    """Curses color pair configuration"""
    foreground: int
    background: int

class UIDimensions(TypedDict):
    """UI layout dimensions"""
    width: int
    height: int
    margins: Tuple[int, int, int, int]  # top, right, bottom, left