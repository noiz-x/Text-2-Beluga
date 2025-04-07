# core/validator.py

import re
import logging

from pathlib import Path
from typing import List, Optional, Tuple, Generator
from dataclasses import dataclass

from utils.constants import ASSETS_DIR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ValidationError:
    line_number: int
    message: str
    line_preview: str

class ScriptValidator:
    """Validates script files for Beluga-style video generation"""
    
    def __init__(
        self,
        assets_dir: Path = ASSETS_DIR,
        max_line_length: int = 200,
        allowed_duration_range: Tuple[float, float] = (0.1, 30.0)
    ):
        self.assets_dir = assets_dir
        self.max_line_length = max_line_length
        self.min_duration, self.max_duration = allowed_duration_range
        
        # Compile regex patterns once
        self.mention_pattern = re.compile(r'@\w+')
        self.formatting_pattern = re.compile(r'(\*\*|__)')
        self.emoji_pattern = re.compile(r'^\p{Emoji}+$', re.UNICODE)

    def validate(self, script_path: Path) -> List[ValidationError]:
        """
        Validate a script file and return structured errors
        
        Args:
            script_path: Path to script file
            
        Returns:
            List of validation errors with context
        """
        errors = []
        line_gen = self._read_script_lines(script_path)
        
        state = "waiting_for_name"
        current_block_lines = []
        
        try:
            for line_number, line in line_gen:
                line = line.rstrip('\n')
                current_block_lines.append(line)
                
                # Cleanup empty lines at block end
                if not line.strip():
                    current_block_lines = []
                    state = "waiting_for_name"
                    continue
                
                error = None
                if line.startswith('#'):
                    continue
                elif line.startswith("WELCOME"):
                    error = self._validate_welcome_line(line_number, line)
                elif state == "waiting_for_name":
                    error = self._validate_name_line(line_number, line)
                    state = "collecting_messages" if not error else state
                else:
                    error = self._validate_message_line(line_number, line)
                
                if error:
                    errors.append(error)
                    # Reset state on critical errors
                    if "name line" in error.message.lower():
                        state = "waiting_for_name"
                
                # Check line length after basic validation
                if len(line) > self.max_line_length:
                    errors.append(ValidationError(
                        line_number=line_number,
                        message=f"Line exceeds maximum length ({self.max_line_length} characters)",
                        line_preview=self._preview_line(line)
                    ))
                    
        except UnicodeDecodeError as e:
            errors.append(ValidationError(
                line_number=0,
                message=f"File decoding failed: {str(e)}",
                line_preview=""
            ))
        
        return errors

    def _read_script_lines(self, path: Path) -> Generator[Tuple[int, str], None, None]:
        """Read script lines with proper error handling"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line_number, line in enumerate(f, start=1):
                    yield line_number, line
        except FileNotFoundError:
            logger.error(f"Script file not found: {path}")
            raise

    def _validate_welcome_line(self, line_number: int, line: str) -> Optional[ValidationError]:
        """Validate WELCOME message lines"""
        if not line.startswith("WELCOME "):
            return ValidationError(
                line_number=line_number,
                message="WELCOME line must start with 'WELCOME '",
                line_preview=self._preview_line(line)
            )
            
        parts = line.split('$^')
        if len(parts) < 2:
            return ValidationError(
                line_number=line_number,
                message="WELCOME line missing duration separator ($^)",
                line_preview=self._preview_line(line)
            )
            
        return self._validate_duration_part(
            line_number=line_number,
            line=line,
            duration_part=parts[1]
        )

    def _validate_name_line(self, line_number: int, line: str) -> Optional[ValidationError]:
        """Validate character name lines"""
        if ':' not in line:
            return ValidationError(
                line_number=line_number,
                message="Name line missing required colon (:) separator",
                line_preview=self._preview_line(line)
            )
            
        name_part = line.split(':', 1)[0].strip()
        if not name_part:
            return ValidationError(
                line_number=line_number,
                message="Name part before colon is empty",
                line_preview=self._preview_line(line)
            )
            
        if re.search(r'\s{2,}', name_part):
            return ValidationError(
                line_number=line_number,
                message="Name contains consecutive spaces",
                line_preview=self._preview_line(line)
            )
            
        return None

    def _validate_message_line(self, line_number: int, line: str) -> Optional[ValidationError]:
        """Validate message content lines"""
        if '$^' not in line:
            return ValidationError(
                line_number=line_number,
                message="Message line missing required duration separator ($^)",
                line_preview=self._preview_line(line)
            )
            
        parts = line.split('$^', 1)
        message_part = parts[0].strip()
        duration_part = parts[1].strip()
        
        # Validate message content
        if msg_error := self._validate_message_content(line_number, message_part):
            return msg_error
            
        # Validate duration and sound effects
        return self._validate_duration_part(line_number, line, duration_part)

    def _validate_message_content(self, line_number: int, message: str) -> Optional[ValidationError]:
        """Validate message formatting and content"""
        # Check balanced formatting markers
        if self.formatting_pattern.search(message):
            bold_count = message.count('**')
            italic_count = message.count('__')
            
            if bold_count % 2 != 0:
                return ValidationError(
                    line_number=line_number,
                    message="Unbalanced bold markers (**)",
                    line_preview=self._preview_line(message)
                )
                
            if italic_count % 2 != 0:
                return ValidationError(
                    line_number=line_number,
                    message="Unbalanced italic markers (__)",
                    line_preview=self._preview_line(message)
                )
                
        # Check valid mentions
        for mention in self.mention_pattern.findall(message):
            if len(mention) < 2:  # Minimum @ + 1 character
                return ValidationError(
                    line_number=line_number,
                    message=f"Invalid mention format: {mention}",
                    line_preview=self._preview_line(message)
                )
                
        return None

    def _validate_duration_part(
        self,
        line_number: int,
        full_line: str,
        duration_part: str
    ) -> Optional[ValidationError]:
        """Validate duration and optional sound effect"""
        duration_str = duration_part.split('#!')[0].strip()
        sound_part = duration_part.split('#!')[1].strip() if '#!' in duration_part else None
        
        try:
            duration = float(duration_str)
            if not (self.min_duration <= duration <= self.max_duration):
                return ValidationError(
                    line_number=line_number,
                    message=f"Duration {duration:.2f}s out of allowed range ({self.min_duration}-{self.max_duration}s)",
                    line_preview=self._preview_line(full_line)
                )
        except ValueError:
            return ValidationError(
                line_number=line_number,
                message=f"Invalid duration format: {duration_str}",
                line_preview=self._preview_line(full_line)
            )
            
        if sound_part:
            return self._validate_sound_effect(line_number, sound_part, full_line)
            
        return None

    def _validate_sound_effect(
        self,
        line_number: int,
        sound_name: str,
        full_line: str
    ) -> Optional[ValidationError]:
        """Validate sound effect existence and naming"""
        if not re.match(r'^[\w-]+$', sound_name):
            return ValidationError(
                line_number=line_number,
                message=f"Invalid sound name format: {sound_name}",
                line_preview=self._preview_line(full_line)
            )
            
        sound_path = self.assets_dir / 'sounds' / 'mp3' / f'{sound_name}.mp3'
        if not sound_path.exists():
            return ValidationError(
                line_number=line_number,
                message=f"Sound effect not found: {sound_name}.mp3",
                line_preview=self._preview_line(full_line)
            )
            
        return None

    @staticmethod
    def _preview_line(line: str, max_length: int = 50) -> str:
        """Create shortened line preview for error messages"""
        line = line.strip()
        if len(line) <= max_length:
            return line
        return f"{line[:max_length]}..."


def get_filename() -> Optional[Path]:
    """Open file dialog to select script file (QT version)"""
    from PyQt5.QtWidgets import QApplication, QFileDialog
    
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