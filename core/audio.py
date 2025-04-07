# core/audio.py

import logging
from pathlib import Path
from typing import List, Optional, Tuple, Generator
from dataclasses import dataclass
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class AudioEvent:
    start_time: float
    sound_path: Path
    duration: float

class AudioProcessor:
    """Handles audio effect processing and synchronization with video"""
    
    def __init__(self, assets_dir: Path = Path("../assets")):
        self.assets_dir = assets_dir
        self.sounds_dir = assets_dir / "sounds" / "mp3"
        self._validate_audio_resources()

    def _validate_audio_resources(self) -> None:
        """Verify sound effects directory exists"""
        if not self.sounds_dir.exists():
            raise FileNotFoundError(f"Sound effects directory not found: {self.sounds_dir}")

    def process_audio(
        self,
        video_path: Path,
        script_path: Path,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Add synchronized audio effects to video based on script
        
        Args:
            video_path: Path to generated video file
            script_path: Path to original script file
            output_path: Optional output path for final video
            
        Returns:
            Path to final video file with audio
        """
        output_path = output_path or video_path.parent / "final_video.mp4"
        audio_events = list(self._parse_script_audio_events(script_path))
        
        try:
            video = VideoFileClip(str(video_path))
            composite_audio = self._create_audio_composite(video.duration, audio_events)
            
            if composite_audio:
                video = video.set_audio(composite_audio)
            
            video.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                threads=4,
                logger=logger
            )
            return output_path
            
        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            raise
        finally:
            if 'video' in locals():
                video.close()

    def _parse_script_audio_events(
        self,
        script_path: Path
    ) -> Generator[AudioEvent, None, None]:
        """Extract audio events with timing from script file"""
        current_time = 0.0
        
        for line_type, content in self._parse_script_lines(script_path):
            if line_type == "welcome":
                duration, sound = content
                if sound:
                    yield AudioEvent(
                        start_time=current_time,
                        sound_path=self.sounds_dir / f"{sound}.mp3",
                        duration=duration
                    )
                current_time += duration
            elif line_type == "message":
                duration, sound = content
                if sound:
                    yield AudioEvent(
                        start_time=current_time,
                        sound_path=self.sounds_dir / f"{sound}.mp3",
                        duration=duration
                    )
                current_time += duration

    def _parse_script_lines(
        self,
        script_path: Path
    ) -> Generator[Tuple[str, Tuple], None, None]:
        """Parse script lines into structured components"""
        with open(script_path, 'r', encoding='utf-8') as f:
            name_up_next = True
            
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith("WELCOME"):
                    parts = line.split('$^', 1)
                    duration_str = parts[1].split('#!')[0].strip()
                    sound = parts[1].split('#!')[1].strip() if '#!' in parts[1] else None
                    
                    try:
                        duration = float(duration_str)
                    except ValueError:
                        logger.warning(f"Invalid duration in WELCOME line: {line}")
                        continue
                        
                    yield ("welcome", (duration, sound))
                    
                elif ':' in line and name_up_next:
                    name_up_next = False
                elif '$^' in line:
                    parts = line.split('$^', 1)
                    duration_str = parts[1].split('#!')[0].strip()
                    sound = parts[1].split('#!')[1].strip() if '#!' in parts[1] else None
                    
                    try:
                        duration = float(duration_str)
                    except ValueError:
                        logger.warning(f"Invalid duration in message line: {line}")
                        continue
                        
                    yield ("message", (duration, sound))
                elif line == '':
                    name_up_next = True

    def _create_audio_composite(
        self,
        video_duration: float,
        audio_events: List[AudioEvent]
    ) -> Optional[CompositeAudioClip]:
        """Create composite audio track from sound effects"""
        audio_clips = []
        
        for event in audio_events:
            if not event.sound_path.exists():
                logger.warning(f"Sound file missing: {event.sound_path}")
                continue
            
            try:
                audio_clip = AudioFileClip(str(event.sound_path))
                if audio_clip.duration > event.duration:
                    audio_clip = audio_clip.subclip(0, event.duration)
                
                audio_clip = audio_clip.set_start(event.start_time)
                audio_clips.append(audio_clip)
            except Exception as e:
                logger.error(f"Failed to load {event.sound_path.name}: {str(e)}")
        
        if not audio_clips:
            return None
            
        return CompositeAudioClip(audio_clips).set_duration(video_duration)

    @staticmethod
    def validate_sound_effect(sound_name: str, assets_dir: Path) -> bool:
        """Check if a sound effect exists in the library"""
        sound_path = assets_dir / "sounds" / "mp3" / f"{sound_name}.mp3"
        return sound_path.exists()