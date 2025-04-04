import os
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

# Typing indicator constants (same as in generate_chat.py)
TYPING_FRAME_DURATION = 0.3  # Duration per frame in seconds
TYPING_ANIMATION_FRAMES = 3  # Number of animation frames

base_dir = os.path.dirname(os.path.abspath(__file__))

def add_sounds(filename):
    video = VideoFileClip("output.mp4")
    duration = 0
    audio_clips = []
    typing_enabled = True  # Default to enabled

    with open(filename, encoding="utf8") as f:
        for line in f.read().splitlines():
            line = line.strip()
            if line == '':
                typing_enabled = True  # Reset to default
                continue
            if line.startswith('#'):
                continue
            if line.startswith("WELCOME") or line.startswith("LEAVE"):
                if "#!" in line:
                    parts = line.split('$^')
                    duration_part, sound_part = parts[1].split("#!")
                    audio_file = f'{base_dir}/{os.pardir}/assets/sounds/mp3/{sound_part.strip()}.mp3'
                    audio_clips.append(AudioFileClip(audio_file).set_start(duration))
                    duration += float(duration_part)
                else:
                    duration += float(line.split('$^')[1])
                continue
            if ':' in line:
                # Check for typing toggle
                typing_enabled = '^:' in line
                if typing_enabled:
                    typing_sound = f'{base_dir}/{os.pardir}/assets/sounds/mp3/typing.mp3'
                    if os.path.exists(typing_sound):
                        audio_clips.append(
                            AudioFileClip(typing_sound).set_start(duration)
                        )
                    duration += TYPING_FRAME_DURATION * TYPING_ANIMATION_FRAMES
                continue
            if '$^' in line:
                if "#!" in line:
                    parts = line.split('$^')
                    duration_part, sound_part = parts[1].split("#!")
                    audio_file = f'{base_dir}/{os.pardir}/assets/sounds/mp3/{sound_part.strip()}.mp3'
                    audio_clips.append(AudioFileClip(audio_file).set_start(duration))
                    duration += float(duration_part)
                else:
                    duration += float(line.split('$^')[1])

    if audio_clips:
        composite_audio = CompositeAudioClip(audio_clips)
        video = video.set_audio(composite_audio)

    video.write_videofile(f'{base_dir}/{os.pardir}/final_video.mp4', codec="libx264", audio_codec="aac")
    os.remove("output.mp4")    