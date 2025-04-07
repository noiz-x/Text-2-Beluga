# core/generator.py

import os
import random
import json
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from PIL import Image, ImageFont, ImageDraw
from pilmoji import Pilmoji
import regex
from PyQt5.QtWidgets import QApplication, QFileDialog
from utils.constants import BASE_DIR, ASSETS_DIR, Font

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CharacterConfig:
    profile_pic: Path
    role_color: Tuple[int, int, int]

@dataclass
class MessageSegment:
    text: str
    is_bold: bool = False
    is_italic: bool = False
    is_mention: bool = False

class ChatGenerator:
    """Generates Discord-style chat images from script data"""
    
    def __init__(self, assets_dir: Path = ASSETS_DIR):
        self.assets_dir = assets_dir
        self.characters = self._load_characters()
        self.fonts = self._load_fonts()
        self._validate_resources()
        
        # Layout constants
        self.WORLD_WIDTH = 1777
        self.WORLD_Y_INIT_MESSAGE = 231
        self.WORLD_DY = 70
        self.PROFPIC_WIDTH = 120
        self.NAME_FONT_SIZE = 50
        self.MESSAGE_FONT_SIZE = 50
        
        # Joined message templates
        self.JOINED_TEXTS = [
            "CHARACTER joined the party.",
            "CHARACTER is here.",
            "Welcome, CHARACTER. We hope you brought pizza.",
            # ... (rest of the templates)
        ]

    def _load_characters(self) -> Dict[str, CharacterConfig]:
        """Load character configurations from JSON"""
        # In all file loading operations, add resolve():
        chars_path = (self.assets_dir / "profile_pictures" / "characters.json").resolve()
        with open(chars_path, 'r', encoding='utf-8') as f:
            char_data = json.load(f)
        
        return {
            name: CharacterConfig(
                profile_pic=self.assets_dir / "profile_pictures" / data["profile_pic"],
                role_color=tuple(data["role_color"])
            )
            for name, data in char_data.items()
        }

    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load all required font variants"""
        font_dir = self.assets_dir / "fonts" / "whitney"
        for variant, filename in Font.VARIANTS.items():
          font_path = font_dir / filename
          if not font_path.exists():
              raise FileNotFoundError(f"Missing font file: {font_path}")
        return {
            'name': ImageFont.truetype(str(font_dir / "semibold.ttf"), self.NAME_FONT_SIZE),
            'time': ImageFont.truetype(str(font_dir / "semibold.ttf"), 40),  # Time font size fixed at 40
            'message': ImageFont.truetype(str(font_dir / "medium.ttf"), self.MESSAGE_FONT_SIZE),
            'message_italic': ImageFont.truetype(str(font_dir / "medium_italic.ttf"), self.MESSAGE_FONT_SIZE),
            # ... (other font variants)
        }

    def _validate_resources(self) -> None:
        """Verify all required resources exist"""
        missing = []
        for char, config in self.characters.items():
            if not config.profile_pic.exists():
                missing.append(f"Profile pic for {char}: {config.profile_pic}")
        
        for font_name, font_obj in self.fonts.items():
            if font_obj is None:
                missing.append(f"Font {font_name}")
        
        if missing:
            raise FileNotFoundError(f"Missing resources:\n{'\n'.join(missing)}")

    @staticmethod
    def is_emoji_message(message: str) -> bool:
        """Check if message contains only emoji characters"""
        return bool(message) and all(
            regex.match(r'^\p{Emoji}+$', char) 
            for char in message.strip()
        )

    def generate_chat(
        self,
        messages: List[str],
        name_time: Tuple[str, str],
        character_name: str,
        output_path: Optional[Path] = None
    ) -> Image.Image:
        """
        Generate a chat bubble image with formatted messages
        
        Args:
            messages: List of message strings
            name_time: (username, timestamp) tuple
            character_name: Name of character sending messages
            output_path: Optional path to save image
            
        Returns:
            Generated PIL Image
        """
        if character_name not in self.characters:
            raise ValueError(f"Unknown character: {character_name}")
            
        char_config = self.characters[character_name]
        prof_pic = self._process_profile_pic(char_config.profile_pic)
        
        # Calculate positions and dimensions
        name_text, time_text = name_time
        time_position = self._calculate_time_position(name_text)
        
        # Create base image with dynamic height
        height = self._calculate_image_height(messages)
        template = Image.new('RGBA', (self.WORLD_WIDTH, height), (54, 57, 63, 255))
        
        # Draw profile picture
        template.paste(prof_pic, (36, 45), prof_pic)
        
        # Draw name and timestamp
        draw = ImageDraw.Draw(template)
        draw.text((190, 53), name_text, char_config.role_color, font=self.fonts['name'])
        draw.text(time_position, f"Today at {time_text} PM", (148, 155, 164), font=self.fonts['time'])
        
        # Render messages
        self._render_messages(draw, template, messages)
        
        if output_path:
            os.makedirs(output_path.parent, exist_ok=True)
            template.save(output_path)
            
        return template

    def _process_profile_pic(self, pic_path: Path) -> Image.Image:
        """Process profile picture into circular mask"""
        prof_pic = Image.open(pic_path)
        prof_pic.thumbnail((self.PROFPIC_WIDTH, self.PROFPIC_WIDTH))
        
        mask = Image.new("L", prof_pic.size, 0)
        ImageDraw.Draw(mask).ellipse(
            [(0, 0), (self.PROFPIC_WIDTH, self.PROFPIC_WIDTH)],
            fill=255
        )
        prof_pic.putalpha(mask)
        return prof_pic

    def _calculate_time_position(self, name_text: str) -> Tuple[int, int]:
        """Calculate properly aligned time position"""
        name_ascent = self.fonts['name'].getmetrics()[0]
        time_ascent = self.fonts['time'].getmetrics()[0]
        baseline_y = 53 + name_ascent
        name_width = self.fonts['name'].getlength(name_text)
        
        return (
            190 + int(name_width) + 25,  # NAME_TIME_SPACING = 25
            baseline_y - time_ascent
        )

    def _calculate_image_height(self, messages: List[str]) -> int:
        """Calculate dynamic image height based on messages"""
        base_height = self.WORLD_Y_INIT_MESSAGE + (len(messages) - 1) * self.WORLD_DY
        
        # Adjust for emoji messages
        # Fix missing parenthesis:
        emoji_height = sum(
            (self.fonts['message'].getbbox("💀")[3] + 8)  # Added closing )
            for msg in messages
            if self.is_emoji_message(msg)
        )
        
        return base_height + emoji_height

    def _render_messages(
        self,
        draw: ImageDraw.Draw,
        template: Image.Image,
        messages: List[str]
    ) -> None:
        """Render all message segments with proper formatting"""
        y_offset = 0
        for i, message in enumerate(messages):
            if not message.strip():
                continue
                
            x, base_y = 190, 115 + i * 70  # MESSAGE_X = 190, MESSAGE_Y_INIT = 115, MESSAGE_DY = 70
            y_pos = base_y + y_offset
            
            if self.is_emoji_message(message):
                self._render_emoji_message(template, message, x, y_pos)
                y_offset += self.fonts['message'].getbbox(message)[3]
            else:
                self._render_text_message(draw, template, message, x, y_pos)

    def _render_emoji_message(
        self,
        template: Image.Image,
        message: str,
        x: int,
        y: int
    ) -> None:
        """Render emoji-only message with larger emojis"""
        with Pilmoji(template) as pilmoji:
            pilmoji.text(
                (x, y),
                message,
                (220, 222, 225),  # MESSAGE_FONT_COLOR
                font=self.fonts['message'],
                emoji_position_offset=(0, 8),
                emoji_scale_factor=2
            )

    def _render_text_message(
        self,
        draw: ImageDraw.Draw,
        template: Image.Image,
        message: str,
        start_x: int,
        y: int
    ) -> None:
        """Render formatted text message with mentions, bold, italics"""
        segments = self._parse_message_segments(message)
        current_x = start_x
        
        with Pilmoji(template) as pilmoji:
            for seg in segments:
                font = self._select_font(seg)
                color = (201, 205, 251) if seg.is_mention else (220, 222, 225)
                
                if seg.is_mention:
                    self._draw_mention_background(draw, seg.text, current_x, y, font)
                    current_x += 16  # Padding
                
                pilmoji.text(
                    (current_x, y),
                    seg.text,
                    color,
                    font=font,
                    emoji_position_offset=(0, 8),
                    emoji_scale_factor=1.2
                )
                
                text_width = font.getlength(seg.text)
                current_x += int(text_width) + (16 if seg.is_mention else 0)

    def _parse_message_segments(self, message: str) -> List[MessageSegment]:
        """Parse message into formatted segments"""
        # Split by formatting markers (**bold**, __italic__, @mentions)
        tokens = re.split(r'(\*\*|__|@\w+)', message)
        segments = []
        bold = italic = False
        
        for token in tokens:
            if not token:
                continue
            elif token == '**':
                bold = not bold
            elif token == '__':
                italic = not italic
            elif token.startswith('@'):
                segments.append(MessageSegment(
                    text=token,
                    is_mention=True,
                    is_bold=bold,
                    is_italic=italic
                ))
            else:
                segments.append(MessageSegment(
                    text=token,
                    is_bold=bold,
                    is_italic=italic
                ))
                
        return segments

    def _select_font(self, segment: MessageSegment) -> ImageFont.FreeTypeFont:
        """Select appropriate font based on segment formatting"""
        if segment.is_mention:
            if segment.is_bold and segment.is_italic:
                return self.fonts['message_mention_italic']
            elif segment.is_bold:
                return self.fonts['message_mention']
            elif segment.is_italic:
                return self.fonts['message_mention_italic']
            return self.fonts['message_mention']
        
        if segment.is_bold and segment.is_italic:
            return self.fonts['message_italic_bold']
        elif segment.is_bold:
            return self.fonts['message_bold']
        elif segment.is_italic:
            return self.fonts['message_italic']
        return self.fonts['message']

    def _draw_mention_background(
        self,
        draw: ImageDraw.Draw,
        text: str,
        x: int,
        y: int,
        font: ImageFont.FreeTypeFont
    ) -> None:
        """Draw rounded rectangle background for mentions"""
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        bg_box = [
            x,
            y + bbox[1] - 8,  # padding
            x + text_width + 32,  # extra padding
            y + bbox[3] + 8
        ]
        
        draw.rounded_rectangle(
            bg_box,
            fill=(74, 75, 114),  # Mention background color
            radius=10
        )

    def generate_joined_message(
        self,
        character_name: str,
        time_str: str,
        output_path: Optional[Path] = None
    ) -> Image.Image:
        """Generate 'user joined' notification image"""
        if character_name not in self.characters:
            raise ValueError(f"Unknown character: {character_name}")
            
        char_config = self.characters[character_name]
        template_text = random.choice(self.JOINED_TEXTS)
        arrow_x = random.randint(50, 80)
        
        # Create base image
        template = Image.new(
            'RGBA',
            (self.WORLD_WIDTH, 100),  # WORLD_HEIGHT_JOINED = 100
            (54, 57, 63, 255)
        )
        
        # Add green arrow
        arrow = Image.open(self.assets_dir / "green_arrow.png")
        arrow.thumbnail((40, 40))
        template.paste(arrow, (arrow_x, 30), arrow)
        
        # Render text
        self._render_joined_text(
            template,
            template_text,
            character_name,
            char_config.role_color,
            time_str,
            arrow_x + arrow.width + 60
        )
        
        if output_path:
            os.makedirs(output_path.parent, exist_ok=True)
            template.save(output_path)
            
        return template

    def _render_joined_text(
        self,
        template: Image.Image,
        template_text: str,
        character_name: str,
        color: Tuple[int, int, int],
        time_str: str,
        text_x: int
    ) -> None:
        """Render text components for joined message"""
        before, _, after = template_text.partition("CHARACTER")
        draw = ImageDraw.Draw(template)
        
        with Pilmoji(template) as pilmoji:
            # Render "before" text
            if before:
                pilmoji.text(
                    (text_x, 30),
                    before,
                    (157, 161, 164),  # JOINED_FONT_COLOR
                    font=self.fonts['message']
                )
                text_x += int(self.fonts['message'].getlength(before))
            
            # Render character name
            pilmoji.text(
                (text_x, 30),
                character_name,
                color,
                font=self.fonts['name']
            )
            text_x += int(self.fonts['name'].getlength(character_name))
            
            # Render "after" text
            if after:
                pilmoji.text(
                    (text_x, 30),
                    after,
                    (157, 161, 164),
                    font=self.fonts['message']
                )
                text_x += int(self.fonts['message'].getlength(after))
            
            # Render timestamp
            time_text = f"Today at {time_str} PM"
            pilmoji.text(
                (text_x + 30, 37),  # Adjusted for vertical alignment
                time_text,
                (148, 155, 164),  # TIME_FONT_COLOR
                font=self.fonts['time']
            )

    def process_script(
        self,
        script_path: Path,
        output_dir: Path = Path("../chat"),
        frame_duration: int = 30
    ) -> None:
        """
        Process complete script file into sequence of images
        
        Args:
            script_path: Path to script file
            output_dir: Directory to save generated images
            frame_duration: Default duration for frames (seconds)
        """
        with open(script_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()]
        
        current_time = datetime.now()
        msg_number = 1
        current_character = None
        current_messages = []
        
        os.makedirs(output_dir, exist_ok=True)
        
        for line in lines:
            if not line or line.startswith('#'):
                continue
                
            if line.startswith("WELCOME"):
                # Handle join messages
                parts = line.split('$^')
                char_name = line.split()[1].split('$^')[0]
                
                if len(parts) > 1:
                    duration = float(parts[1].split('#!')[0])
                else:
                    duration = frame_duration
                
                self.generate_joined_message(
                    character_name=char_name,
                    time_str=f"{current_time.hour % 12 or 12}:{current_time.minute:02d}",
                    output_path=output_dir / f"{msg_number:03d}.png"
                )
                
                current_time += timedelta(seconds=duration)
                msg_number += 1
            elif ':' in line and not current_messages:
                # New character block
                current_character = line.split(':')[0]
                current_messages = []
            elif '$^' in line:
                # Regular message
                message_part = line.split('$^', 1)
                current_messages.append(message_part)
                
                self.generate_chat(
                    messages=current_messages,
                    name_time=(
                        current_character,
                        f"{current_time.hour % 12 or 12}:{current_time.minute:02d}"
                    ),
                    character_name=current_character,
                    output_path=output_dir / f"{msg_number:03d}.png"
                )
                
                duration_part = line.split('$^')[1].split('#!')[0]
                duration = float(duration_part) if duration_part else frame_duration
                current_time += timedelta(seconds=duration)
                msg_number += 1

    @staticmethod
    def get_filename() -> Optional[Path]:
        """Open file dialog to select script file"""
        app = QApplication([])
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            None,
            "Select Script File",
            "",
            "Text Files (*.txt);;All Files (*)",
            options=options
        )
        return Path(filename) if filename else None