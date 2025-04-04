import os
from sound_effects import add_sounds

base_dir = os.path.dirname(os.path.abspath(__file__))

# Typing indicator constants (same as in generate_chat.py)
TYPING_FRAME_DURATION = 0.3  # Duration per frame in seconds
TYPING_ANIMATION_FRAMES = 3  # Number of animation frames

def gen_vid(filename):
    input_folder = f'{base_dir}/{os.pardir}/chat/'
    image_files = sorted([f for f in os.listdir(input_folder) if f.endswith('.png')])
    durations = []
    
    with open(filename, encoding="utf8") as f:
        typing_enabled = True  # Default to enabled
        for line in f.read().splitlines():
            line = line.strip()
            if line == '':
                typing_enabled = True  # Reset to default for next block
                continue
            if line.startswith('#'):
                continue
            if line.startswith("WELCOME") or line.startswith("LEAVE"):  # Updated condition
                durations.append(line.split('$^')[1].split('#!')[0] if '#!' in line else line.split('$^')[1])
                continue
            if ':' in line:
                # Check for typing toggle
                typing_enabled = '^:' in line
                if typing_enabled:
                    durations.extend([str(TYPING_FRAME_DURATION)] * TYPING_ANIMATION_FRAMES)
                continue
            if '$^' in line:
                durations.append(line.split('$^')[1].split('#!')[0] if '#!' in line else line.split('$^')[1])

    # Create image paths file
    with open('image_paths.txt', 'w') as file:    
        for idx, image_file in enumerate(image_files):
            file.write(f"file '{input_folder}{image_file}'\n")
            file.write(f"duration {durations[idx]}\n")
        # Add last frame with short duration
        file.write(f"file '{input_folder}{image_files[-1]}'\n")
        file.write("duration 0.04\n")

    video_width, video_height = 1280, 720
    ffmpeg_cmd = (
        f"ffmpeg -f concat -safe 0 -i image_paths.txt -vcodec libx264 -r 25 -crf 25 "
        f"-vf \"scale={video_width}:{video_height}:force_original_aspect_ratio=decrease,"
        f"pad={video_width}:{video_height}:(ow-iw)/2:(oh-ih)/2\" -pix_fmt yuv420p output.mp4"
    )
    os.system(ffmpeg_cmd)
    os.remove('image_paths.txt')
    add_sounds(filename)