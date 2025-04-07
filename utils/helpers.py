# utils/helpers.py

"""
General utilities and helper functions used throughout the application
"""
import os
import json
import re
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Generator, Dict, Any
from datetime import datetime, timedelta
from PIL import Image, ImageFont, ImageDraw
import regex

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# File System Utilities
# --------------------------------------------------
def safe_create_directory(path: Path) -> None:
    """Create directory if it doesn't exist with safety checks"""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create directory {path}: {e}")
        raise

def clear_directory(dir_path: Path) -> None:
    """Remove all files in a directory without deleting the directory itself"""
    for item in dir_path.glob('*'):
        if item.is_file():
            try:
                item.unlink()
            except OSError as e:
                logger.warning(f"Could not delete {item}: {e}")

def get_sorted_images(image_dir: Path) -> List[Path]:
    """Get sorted list of PNG images in directory"""
    return sorted(
        [f for f in image_dir.glob("*.png") if f.is_file()],
        key=lambda x: int(x.stem)
    )

# --------------------------------------------------
# Text and Font Utilities
# --------------------------------------------------
def wrap_text(text: str, width: int, font: ImageFont.FreeTypeFont) -> List[str]:
    """Wrap text to specified width using font metrics"""
    lines = []
    current_line = []
    current_width = 0
    
    for word in text.split():
        word_width = font.getlength(word + ' ')
        if current_width + word_width <= width:
            current_line.append(word)
            current_width += word_width
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_width = word_width
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def calculate_text_dimensions(text: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
    """Calculate text bounding box dimensions"""
    bbox = font.getbbox(text)
    return (bbox[2] - bbox[0], bbox[3] - bbox[1])

def load_font(font_path: Path, size: int) -> ImageFont.FreeTypeFont:
    """Load font with error handling"""
    if not font_path.exists():
        raise FileNotFoundError(f"Font file not found: {font_path}")
    
    try:
        return ImageFont.truetype(str(font_path), size)
    except IOError as e:
        logger.error(f"Failed to load font {font_path}: {e}")
        raise

# --------------------------------------------------
# Time and Duration Utilities
# --------------------------------------------------
def format_timestamp(dt: datetime) -> str:
    """Format datetime to 'Today at H:MM PM' format"""
    return f"{dt.hour % 12 or 12}:{dt.minute:02d}"

def calculate_duration(duration_str: str) -> float:
    """Parse duration string with fallback handling"""
    try:
        return float(duration_str)
    except (ValueError, TypeError):
        logger.warning(f"Invalid duration format: {duration_str}")
        return 3.0  # Default fallback duration

# --------------------------------------------------
# Validation Utilities
# --------------------------------------------------
def validate_sound_effect(sound_name: str, assets_dir: Path) -> bool:
    """Check if sound effect exists in library"""
    sound_path = assets_dir / "sounds" / "mp3" / f"{sound_name}.mp3"
    return sound_path.exists()

def validate_hex_color(color_str: str) -> bool:
    """Validate hexadecimal color format"""
    return re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color_str) is not None

# --------------------------------------------------
# Resource Management
# --------------------------------------------------
def load_character_config(config_path: Path) -> Dict[str, Any]:
    """Load character configuration from JSON file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load character config: {e}")
        raise

def cleanup_temp_files(files: List[Path]) -> None:
    """Clean up temporary files with error suppression"""
    for file_path in files:
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.debug(f"Could not delete temp file {file_path}: {e}")

# --------------------------------------------------
# UI Utilities
# --------------------------------------------------
def format_ui_text(text: str, width: int) -> List[str]:
    """Format text for UI display with proper wrapping"""
    return textwrap.wrap(text, width=width, replace_whitespace=False)

def get_user_input(prompt: str, validator: callable) -> Any:
    """Get validated user input with retry logic"""
    while True:
        user_input = input(prompt)
        if validator(user_input):
            return user_input
        print("Invalid input, please try again.")

# --------------------------------------------------
# Image Processing Utilities
# --------------------------------------------------
def process_profile_picture(image_path: Path, size: int) -> Image.Image:
    """Process profile picture into circular mask"""
    img = Image.open(image_path)
    img.thumbnail((size, size))
    
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse([(0, 0), (size, size)], fill=255)
    img.putalpha(mask)
    return img

def apply_rounded_corners(image: Image.Image, radius: int) -> Image.Image:
    """Apply rounded corners to image"""
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), image.size], radius=radius, fill=255)
    image.putalpha(mask)
    return image

# --------------------------------------------------
# Script Parsing Utilities
# --------------------------------------------------
def parse_script_line(line: str) -> Tuple[str, float, Optional[str]]:
    """Parse a script line into components"""
    line = line.strip()
    if not line or line.startswith('#'):
        return ('comment', 0.0, None)
    
    if line.startswith("WELCOME"):
        parts = line.split('$^', 1)
        duration_part = parts[1].split('#!')[0] if len(parts) > 1 else '3.0'
        sound = parts[1].split('#!')[1].strip() if '#!' in line else None
        return ('welcome', float(duration_part), sound)
    
    if '$^' in line:
        parts = line.split('$^', 1)
        duration_part = parts[1].split('#!')[0]
        sound = parts[1].split('#!')[1].strip() if '#!' in line else None
        return ('message', float(duration_part), sound)
    
    return ('name', 0.0, None)

def generate_frame_data(script_path: Path) -> Generator[Dict[str, Any], None, None]:
    """Generate frame data from script file"""
    current_time = datetime.now()
    
    with open(script_path, 'r', encoding='utf-8') as f:
        for line in f:
            line_type, duration, sound = parse_script_line(line)
            
            if line_type == 'welcome':
                yield {
                    'type': 'welcome',
                    'time': current_time,
                    'duration': duration,
                    'sound': sound
                }
                current_time += timedelta(seconds=duration)
            elif line_type == 'message':
                yield {
                    'type': 'message',
                    'time': current_time,
                    'duration': duration,
                    'sound': sound
                }
                current_time += timedelta(seconds=duration)