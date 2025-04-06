from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
from pilmoji import Pilmoji
import sys
import datetime
import os
import json
import random
import regex
import re

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFileDialog


base_dir = os.path.dirname(os.path.abspath(__file__))

# CONSTANTS
WORLD_WIDTH = 1777
WORLD_Y_INIT_MESSAGE = 231
WORLD_DY = 70
WORLD_HEIGHTS_MESSAGE = [WORLD_Y_INIT_MESSAGE + i * WORLD_DY for i in range(5)]  # Max 5 messages
WORLD_COLOR = (54, 57, 63, 255)

WORLD_HEIGHT_JOINED = 100
JOINED_FONT_SIZE = 45
JOINED_FONT_COLOR = (157, 161, 164)
JOINED_TEXTS = [
    "CHARACTER joined the party.",
    "CHARACTER is here.",
    "Welcome, CHARACTER. We hope you brought pizza.",
    "A wild CHARACTER appeared.",
    "CHARACTER just landed.",
    "CHARACTER just slid into the server.",
    "CHARACTER just showed up.",
    "Welcome CHARACTER. Say hi!",
    "CHARACTER hopped into the server.",
    "Everyone welcome CHARACTER!",
    "Glad you're here, CHARACTER!",
    "Good to see you, CHARACTER!",
    "Yay you made it, CHARACTER!",
]

PROFPIC_WIDTH = 120
PROFPIC_POSITION = (36, 45)

NAME_FONT_SIZE = 50
TIME_FONT_SIZE = 40
MESSAGE_FONT_SIZE = 50
NAME_FONT_COLOR = (255, 255, 255)
TIME_FONT_COLOR = (148, 155, 164)
MESSAGE_FONT_COLOR = (220, 222, 225)
NAME_POSITION = (190, 53)
TIME_POSITION_Y = 67  # X to be determined from name length
NAME_TIME_SPACING = 25
MESSAGE_X = 190
MESSAGE_Y_INIT = 115
MESSAGE_DY = 70
MESSAGE_POSITIONS = [(MESSAGE_X, MESSAGE_Y_INIT + i * MESSAGE_DY) for i in range(5)]

# Load fonts
font = "whitney" # Change this according to the font you want to use
font_dir = os.path.join(base_dir, os.pardir, "assets", "fonts", font)
name_font = ImageFont.truetype(os.path.join(font_dir, 'semibold.ttf'), NAME_FONT_SIZE)
time_font = ImageFont.truetype(os.path.join(font_dir, 'semibold.ttf'), TIME_FONT_SIZE)
message_font = ImageFont.truetype(os.path.join(font_dir, 'medium.ttf'), MESSAGE_FONT_SIZE)
message_italic_font = ImageFont.truetype(os.path.join(font_dir, 'medium_italic.ttf'), MESSAGE_FONT_SIZE)
message_bold_font = ImageFont.truetype(os.path.join(font_dir, 'bold.ttf'), MESSAGE_FONT_SIZE)
message_italic_bold_font = ImageFont.truetype(os.path.join(font_dir, 'bold_italic.ttf'), MESSAGE_FONT_SIZE)
message_mention_font = ImageFont.truetype(os.path.join(font_dir, 'semibold.ttf'), MESSAGE_FONT_SIZE)
message_mention_italic_font = ImageFont.truetype(os.path.join(font_dir, 'semibold_italic.ttf'), MESSAGE_FONT_SIZE)

# Load profile picture dictionary
with open(f'{base_dir}/{os.pardir}/assets/profile_pictures/characters.json', encoding="utf8") as file:
    characters_dict = json.load(file)


def is_emoji_message(message):
    """Return True if the message contains only emoji characters."""
    return bool(message) and all(regex.match(r'^\p{Emoji}+$', char) for char in message.strip())


def generate_chat(messages, name_time, profpic_file, color):
    """
    Generates a chat image given the list of messages, name & time info,
    profile picture file, and a role color.
    """
    name_text = name_time[0]
    time_text = f'Today at {name_time[1]} PM'
    
    # Calculate baseline-aligned time position
    name_ascent, _ = name_font.getmetrics()
    time_ascent, _ = time_font.getmetrics()
    baseline_y = NAME_POSITION[1] + name_ascent
    time_position = (
        NAME_POSITION[0] + name_font.getbbox(name_text)[2] + NAME_TIME_SPACING,
        baseline_y - time_ascent
    )
    
    # Open and process profile picture
    prof_pic = Image.open(profpic_file)
    prof_pic.thumbnail((sys.maxsize, PROFPIC_WIDTH), Image.LANCZOS)
    mask = Image.new("L", prof_pic.size, 0)
    ImageDraw.Draw(mask).ellipse([(0, 0), (PROFPIC_WIDTH, PROFPIC_WIDTH)], fill=255)
    
    # Adjust vertical size for emoji-only messages
    y_increment = 0
    for msg in messages:
        if is_emoji_message(msg):
            bbox = message_font.getbbox("💀")
            y_increment += (bbox[3] - bbox[1]) + 8

    total_height = WORLD_HEIGHTS_MESSAGE[len(messages) - 1] + y_increment
    template = Image.new(mode='RGBA', size=(WORLD_WIDTH, total_height), color=WORLD_COLOR)
    template.paste(prof_pic, PROFPIC_POSITION, mask)
    draw_template = ImageDraw.Draw(template)
    
    draw_template.text(NAME_POSITION, name_text, color, font=name_font)
    draw_template.text(time_position, time_text, TIME_FONT_COLOR, font=time_font)

    y_offset = 0
    for i, message in enumerate(messages):
        message = message.strip()
        if not message:
            continue

        x, base_y = MESSAGE_POSITIONS[i]
        y_pos = base_y + y_offset
        current_x = x

        if is_emoji_message(message):
            with Pilmoji(template) as pilmoji:
                pilmoji.text((current_x, y_pos), message, MESSAGE_FONT_COLOR, font=message_font,
                             emoji_position_offset=(0, 8), emoji_scale_factor=2)
            y_offset += message_font.getbbox(message)[3]
            continue

        # Tokenize for bold (**), italic (__), and mentions (@...)
        tokens = re.split(r'(\*\*|__)', message)
        bold = italic = False
        with Pilmoji(template) as pilmoji:
            for token in tokens:
                if token == '**':
                    bold = not bold
                elif token == '__':
                    italic = not italic
                else:
                    if not token:
                        continue
                    # Split further by mentions
                    parts = re.split(r'(@\w+)', token)
                    for part in parts:
                        if not part:
                            continue
                        if part.startswith('@'):
                            # Choose font for mentions (mentions are always semibold)
                            if bold and italic:
                                font_used = message_mention_italic_font
                            elif bold:
                                font_used = message_mention_font
                            elif italic:
                                font_used = message_mention_italic_font
                            else:
                                font_used = message_mention_font

                            bbox = font_used.getbbox(part)
                            text_width = bbox[2] - bbox[0]
                            text_top = bbox[1]
                            text_bottom = bbox[3]
                            padding = 8
                            bg_box = [
                                current_x,
                                y_pos + text_top - padding,
                                current_x + text_width + 2 * padding,
                                y_pos + text_bottom + padding
                            ]
                            draw_template.rounded_rectangle(bg_box, fill=(74, 75, 114), radius=10)
                            pilmoji.text((current_x + padding, y_pos), part, (201, 205, 251), font=font_used)
                            current_x += text_width + 2 * padding
                        else:
                            # Determine proper font for regular text
                            if bold and italic:
                                font_used = message_italic_bold_font
                            elif bold:
                                font_used = message_bold_font
                            elif italic:
                                font_used = message_italic_font
                            else:
                                font_used = message_font
                            pilmoji.text((current_x, y_pos), part, MESSAGE_FONT_COLOR, font=font_used,
                                         emoji_position_offset=(0, 8), emoji_scale_factor=1.2)
                            current_x += font_used.getbbox(part)[2] - font_used.getbbox(part)[0]
    return template


def generate_joined_message(name, time, template_str, arrow_x, color=NAME_FONT_COLOR):
    """
    Generates a Discord-like joined message with a green arrow.
    The character name will be colored with their role color.
    """
    before_text, after_text = template_str.split("CHARACTER", 1) if "CHARACTER" in template_str else ("", "")
    time_text = f'Today at {time} PM'
    
    template_img = Image.new(mode='RGBA', size=(WORLD_WIDTH, WORLD_HEIGHT_JOINED), color=WORLD_COLOR)
    draw_template = ImageDraw.Draw(template_img)
    
    arrow = Image.open(f"{base_dir}/{os.pardir}/assets/green_arrow.png")
    arrow.thumbnail((40, 40))
    text_x = arrow_x + arrow.width + 60

    text_bbox = message_font.getbbox("Sample")
    text_height = text_bbox[3] - text_bbox[1]
    text_y = (WORLD_HEIGHT_JOINED - text_height) // 2
    message_ascent, message_descent = message_font.getmetrics()
    total_text_height = message_ascent + message_descent
    arrow_y = text_y + (total_text_height - arrow.height) // 2

    template_img.paste(arrow, (arrow_x, arrow_y), arrow)
    
    before_width = message_font.getbbox(before_text)[2] if before_text else 0
    name_width = name_font.getbbox(name)[2]
    with Pilmoji(template_img) as pilmoji:
        if before_text:
            pilmoji.text((text_x, text_y), before_text, JOINED_FONT_COLOR, font=message_font)
        name_x = text_x + before_width
        pilmoji.text((name_x, text_y), name, color, font=name_font)
        if after_text:
            after_x = name_x + name_width
            pilmoji.text((after_x, text_y), after_text, JOINED_FONT_COLOR, font=message_font)
        
        total_msg_width = before_width + name_width + message_font.getbbox(after_text)[2]
        time_x = text_x + total_msg_width + 30
        time_baseline = text_y + message_ascent
        time_y = time_baseline - time_font.getmetrics()[0]
        pilmoji.text((time_x, time_y), time_text, TIME_FONT_COLOR, font=time_font)
    
    return template_img


def generate_joined_message_stack(joined_messages, hour):
    """
    Generates a stacked image for multiple joined messages.
    """
    total_height = WORLD_HEIGHT_JOINED * len(joined_messages)
    template_img = Image.new(mode='RGBA', size=(WORLD_WIDTH, total_height), color=WORLD_COLOR)
    
    for idx, key in enumerate(joined_messages):
        name = key.split(' ')[1].split('$^')[0]
        color = characters_dict[name]["role_color"]
        time_str = f'{hour}:{joined_messages[key][2].minute:02d}'
        joined_img = generate_joined_message(name, time_str, joined_messages[key][0], joined_messages[key][1], color)
        template_img.paste(joined_img, (0, idx * WORLD_HEIGHT_JOINED))
    
    return template_img


def get_filename():
    app = QApplication(sys.argv)
    options = QFileDialog.Options()
    filename, _ = QFileDialog.getOpenFileName(
        None, "Select Text File", "", "Text Files (*.txt);;All Files (*)", options=options
    )
    app.exit()
    return filename


def save_images(lines, init_time, dt=30):
    os.makedirs('../chat', exist_ok=True)

    name_up_next = True
    current_time = init_time
    current_name = None
    current_lines = []
    msg_number = 1
    joined_messages = {}
    name_time = []

    for line in lines:
        if line == '':
            name_up_next = True
            current_lines = []
            name_time = []
            joined_messages = {}
            continue

        if line.startswith('#'):
            joined_messages = {}
            continue

        if line.startswith("WELCOME "):
            joined_messages[line] = [random.choice(JOINED_TEXTS), random.randint(50, 80), current_time]
            hour = current_time.hour % 12 or 12
            image = generate_joined_message_stack(joined_messages, hour)
            image.save(f'../chat/{msg_number:03d}.png')
            current_time += datetime.timedelta(seconds=dt)
            msg_number += 1
            continue
        else:
            joined_messages = {}

        if name_up_next:
            current_name = line.split(':')[0]
            hour = current_time.hour % 12 or 12
            name_time = [current_name, f'{hour}:{current_time.minute:02d}']
            name_up_next = False
            continue

        current_lines.append(line.split('$^')[0])
        image = generate_chat(
            messages=current_lines,
            name_time=name_time,
            profpic_file=os.path.join(f'{base_dir}/{os.pardir}/assets/profile_pictures', characters_dict[current_name]["profile_pic"]),
            color=characters_dict[current_name]["role_color"]
        )
        image.save(f'../chat/{msg_number:03d}.png')
        current_time += datetime.timedelta(seconds=dt)
        msg_number += 1


if __name__ == '__main__':
    """
    final_video = '../final_video.mp4'
    if os.path.isfile(final_video):
        os.remove(final_video)
    if os.path.exists('../chat'):
        for file in os.listdir('../chat'):
            os.remove(os.path.join('../chat', file))
        os.rmdir('../chat')

    filename = get_filename()
    with open(filename, encoding="utf8") as f:
        lines = f.read().splitlines()

    current_time = datetime.datetime.now()
    save_images(lines, init_time=current_time)

    # The following function is imported from compile_images.py
    from compile_images import gen_vid
    gen_vid(filename)
    """
    
    print('Please run the main.py script!')