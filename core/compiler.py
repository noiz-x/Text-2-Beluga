# core/compiler.py

import os
import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
import logging
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FrameData:
    image_path: Path
    duration: float
    sound_effect: Optional[Path] = None

class VideoCompiler:
    """Handles compilation of images into video with audio effects"""
    
    def __init__(
        self,
        output_resolution: Tuple[int, int] = (1280, 720),
        framerate: int = 25,
        crf: int = 25
    ):
        self.output_resolution = output_resolution
        self.framerate = framerate
        self.crf = crf
        self.temp_files = []

    def __del__(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_file}: {e}")

    def _generate_concat_file(self, frames: List[FrameData]) -> Path:
        """Generate FFmpeg concat file for image sequence"""
        concat_path = Path("image_sequence.txt")
        self.temp_files.append(concat_path)
        
        with open(concat_path, 'w', encoding='utf-8') as f:
            for frame in frames:
                f.write(f"file '{frame.image_path.absolute()}'\n")
                f.write(f"duration {frame.duration}\n")
            # Add last frame with minimal duration to ensure inclusion
            f.write(f"file '{frames[-1].image_path.absolute()}'\n")
            f.write("duration 0.04\n")
        
        return concat_path

    def _build_ffmpeg_command(self, concat_path: Path, output_path: Path) -> List[str]:
        """Construct FFmpeg command for video compilation"""
        width, height = self.output_resolution
        return [
            "ffmpeg",
            "-y",  # Overwrite without asking
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_path),
            "-vcodec", "libx264",
            "-r", str(self.framerate),
            "-crf", str(self.crf),
            "-vf", (
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
            ),
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]

    def _process_audio(self, video_path: Path, frames: List[FrameData]) -> Path:
        """Add sound effects to the video"""
        video = VideoFileClip(str(video_path))
        audio_clips = []
        current_time = 0.0

        for frame in frames:
            if frame.sound_effect and frame.sound_effect.exists():
                try:
                    audio = AudioFileClip(str(frame.sound_effect))
                    audio = audio.set_start(current_time)
                    audio_clips.append(audio)
                except Exception as e:
                    logger.error(f"Failed to load sound effect {frame.sound_effect}: {e}")
            current_time += frame.duration

        if audio_clips:
            composite_audio = CompositeAudioClip(audio_clips)
            video = video.set_audio(composite_audio)

        output_path = video_path.parent / "final_video.mp4"
        video.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            threads=4,
            logger=logger
        )
        video.close()
        
        return output_path

    def compile(
        self,
        image_dir: Path,
        script_path: Path,
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        Compile images into video with synchronized audio effects
        
        Args:
            image_dir: Directory containing sequence of PNG images
            script_path: Path to script file with timing/sound data
            output_dir: Directory for output video (defaults to image_dir)
            
        Returns:
            Path to generated video file
        """
        if not output_dir:
            output_dir = image_dir
        
        # Validate inputs
        if not image_dir.exists():
            raise FileNotFoundError(f"Image directory not found: {image_dir}")
        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")
        
        # Get sorted list of images
        image_files = sorted(
            [f for f in image_dir.glob("*.png") if f.is_file()],
            key=lambda x: int(x.stem)
        )
        if not image_files:
            raise ValueError(f"No PNG images found in {image_dir}")

        # Parse script for durations and sound effects
        frames = self._parse_script(script_path, image_files)
        
        # Generate intermediate video
        concat_file = self._generate_concat_file(frames)
        temp_video = output_dir / "temp_video.mp4"
        self.temp_files.append(temp_video)
        
        ffmpeg_cmd = self._build_ffmpeg_command(concat_file, temp_video)
        try:
            subprocess.run(ffmpeg_cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg failed with code {e.returncode}") from e
        
        # Add audio and produce final output
        final_video = self._process_audio(temp_video, frames)
        return final_video

    def _parse_script(
        self,
        script_path: Path,
        image_files: List[Path]
    ) -> List[FrameData]:
        """Parse script file to extract frame durations and sound effects"""
        frames = []
        current_index = 0
        
        with open(script_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith("WELCOME"):
                    # Handle welcome messages
                    parts = line.split('$^')
                    if len(parts) < 2:
                        continue
                        
                    duration_part = parts[1].split('#!')[0].strip()
                    try:
                        duration = float(duration_part)
                    except ValueError:
                        logger.warning(f"Invalid duration in line: {line}")
                        continue
                    
                    sound_effect = None
                    if '#!' in parts[1]:
                        sound_name = parts[1].split('#!')[1].strip()
                        sound_effect = Paths.SOUNDS / f"{sound_name}.mp3"
                    
                    if current_index < len(image_files):
                        frames.append(FrameData(
                            image_path=image_files[current_index],
                            duration=duration,
                            sound_effect=sound_effect
                        ))
                        current_index += 1
                else:
                    # Handle regular messages
                    if '$^' not in line:
                        continue
                        
                    parts = line.split('$^')
                    duration_part = parts[1].split('#!')[0].strip()
                    try:
                        duration = float(duration_part)
                    except ValueError:
                        logger.warning(f"Invalid duration in line: {line}")
                        continue
                    
                    sound_effect = None
                    if '#!' in parts[1]:
                        sound_name = parts[1].split('#!')[1].strip()
                        sound_effect = Path(f"../assets/sounds/mp3/{sound_name}.mp3")
                    
                    if current_index < len(image_files):
                        frames.append(FrameData(
                            image_path=image_files[current_index],
                            duration=duration,
                            sound_effect=sound_effect
                        ))
                        current_index += 1
        
        return frames