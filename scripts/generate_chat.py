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
import textwrap

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFileDialog

base_dir = os.path.dirname(os.path.abspath(__file__))

# CONSTANTS
WORLD_WIDTH = 1777
WORLD_Y_INIT_MESSAGE = 231
WORLD_DY = 70
WORLD_HEIGHTS_MESSAGE = [WORLD_Y_INIT_MESSAGE + i * WORLD_DY for i in range(5)]
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
    "[BOT] CHARACTER has connected to the admin panel.",
]
LEFT_FONT_SIZE = 45
LEFT_FONT_COLOR = (157, 161, 164)
LEFT_TEXTS = [
    "CHARACTER left the party.",
    "CHARACTER has departed.",
    "CHARACTER vanished into the void.",
    "CHARACTER went to get pizza...",
    "CHARACTER disconnected.",
    "CHARACTER logged off.",
    "CHARACTER is no longer with us.",
    "CHARACTER left the building.",
    "CHARACTER exited stage left.",
    "CHARACTER poofed out of existence.",
]

# Typing indicator constants
TYPING_HEIGHT = 100
TYPING_DOT_COLOR = (142, 146, 151)
TYPING_DOT_SIZE = 8
TYPING_DOT_SPACING = 14
TYPING_TEXT_OFFSET = 20
TYPING_ANIMATION_FRAMES = 3
TYPING_FRAME_DURATION = 0.3

PROFPIC_WIDTH = 120
PROFPIC_POSITION = (36, 45)

NAME_FONT_SIZE = 50
TIME_FONT_SIZE = 40
MESSAGE_FONT_SIZE = 50
NAME_FONT_COLOR = (255, 255, 255)
TIME_FONT_COLOR = (148, 155, 164)
MESSAGE_FONT_COLOR = (220, 222, 225)
NAME_POSITION = (190, 53)
TIME_POSITION_Y = 67
NAME_TIME_SPACING = 25
MESSAGE_X = 190
MESSAGE_Y_INIT = 115
MESSAGE_DY = 70
MESSAGE_POSITIONS = [(MESSAGE_X, MESSAGE_Y_INIT + i * MESSAGE_DY) for i in range(5)]

# Add to constants section
STATUS_INDICATORS = {
    'online': (67, 181, 129),    # Green
    'idle': (250, 168, 26),      # Yellow
    'dnd': (240, 71, 71),        # Red
    'offline': (116, 127, 141)   # Gray
}
STATUS_TEXTS = {
    'online': "CHARACTER is now online",
    'idle': "CHARACTER is now idle",
    'dnd': "CHARACTER is now in Do Not Disturb mode",
    'offline': "CHARACTER went offline"
}
STATUS_SIZE = 20  # Diameter of status indicator
STATUS_BORDER = 3  # White border width
# Add to constants section
EMBED_COLOR_BAR_WIDTH = 5
EMBED_WIDTH = 500
EMBED_PADDING = 15
EMBED_TITLE_FONT_SIZE = 40
EMBED_DESC_FONT_SIZE = 35

# Load fonts and character data
font = "whitney"
font_dir = os.path.join(base_dir, os.pardir, "assets", "fonts", font)
name_font = ImageFont.truetype(os.path.join(font_dir, 'semibold.ttf'), NAME_FONT_SIZE)
time_font = ImageFont.truetype(os.path.join(font_dir, 'semibold.ttf'), TIME_FONT_SIZE)
message_font = ImageFont.truetype(os.path.join(font_dir, 'medium.ttf'), MESSAGE_FONT_SIZE)
message_italic_font = ImageFont.truetype(os.path.join(font_dir, 'medium_italic.ttf'), MESSAGE_FONT_SIZE)
message_bold_font = ImageFont.truetype(os.path.join(font_dir, 'bold.ttf'), MESSAGE_FONT_SIZE)
message_italic_bold_font = ImageFont.truetype(os.path.join(font_dir, 'bold_italic.ttf'), MESSAGE_FONT_SIZE)
message_mention_font = ImageFont.truetype(os.path.join(font_dir, 'semibold.ttf'), MESSAGE_FONT_SIZE)
message_mention_italic_font = ImageFont.truetype(os.path.join(font_dir, 'semibold_italic.ttf'), MESSAGE_FONT_SIZE)

with open(f'{base_dir}/{os.pardir}/assets/profile_pictures/characters.json', encoding="utf8") as file:
    characters_dict = json.load(file)

def generate_embed(title, description, color_rgb):
    """Creates Discord-style rich embed"""
    title_font = ImageFont.truetype(os.path.join(font_dir, 'semibold.ttf'), EMBED_TITLE_FONT_SIZE)
    desc_font = ImageFont.truetype(os.path.join(font_dir, 'medium.ttf'), EMBED_DESC_FONT_SIZE)
    
    # Calculate text heights
    title_height = title_font.getbbox(title)[3]
    wrapped_desc = textwrap.wrap(description, width=45)
    desc_height = sum(desc_font.getbbox(line)[3] + 5 for line in wrapped_desc)
    
    total_height = EMBED_PADDING*2 + title_height + desc_height
    
    embed = Image.new('RGBA', (EMBED_WIDTH, total_height), (47, 49, 54))
    draw = ImageDraw.Draw(embed)
    
    # Color bar
    draw.rectangle(
        [(0, 0), (EMBED_COLOR_BAR_WIDTH, total_height)],
        fill=color_rgb
    )
    
    # Title
    draw.text(
        (EMBED_PADDING + EMBED_COLOR_BAR_WIDTH, EMBED_PADDING),
        title,
        (255, 255, 255),
        font=title_font
    )
    
    # Description
    y = EMBED_PADDING + title_height + 10
    for line in wrapped_desc:
        draw.text(
            (EMBED_PADDING + EMBED_COLOR_BAR_WIDTH, y),
            line,
            (200, 200, 200),
            font=desc_font
        )
        y += desc_font.getbbox(line)[3] + 5
    
    return embed

def generate_status_message(name, time, status, arrow_x, color=NAME_FONT_COLOR):
    """Generates a status change message with colored indicator"""
    template_img = Image.new('RGBA', (WORLD_WIDTH, WORLD_HEIGHT_JOINED), WORLD_COLOR)
    draw_template = ImageDraw.Draw(template_img)
    
    # Status indicator circle
    status_size = 20
    draw_template.ellipse(
        [arrow_x, 40, arrow_x + status_size, 40 + status_size],
        fill=STATUS_INDICATORS[status]
    )
    
    # Message text
    text = STATUS_TEXTS[status].replace("CHARACTER", name)
    text_x = arrow_x + status_size + 20
    text_y = (WORLD_HEIGHT_JOINED - name_font.getbbox(text)[3]) // 2
    
    draw_template.text((text_x, text_y), text, color, font=name_font)
    
    # Time text
    time_text = f'Today at {time} PM'
    time_x = WORLD_WIDTH - 300
    draw_template.text((time_x, text_y), time_text, TIME_FONT_COLOR, font=time_font)
    
    return template_img

def generate_typing_indicator(name, color, frame=0):
    """Generates animated typing indicator with bouncing dots"""
    template = Image.new('RGBA', (WORLD_WIDTH, TYPING_HEIGHT), WORLD_COLOR)
    draw = ImageDraw.Draw(template)
    
    # Draw name and "is typing" text
    text = f"{name} is typing"
    text_x = NAME_POSITION[0]
    text_y = (TYPING_HEIGHT - name_font.getbbox(text)[3]) // 2
    draw.text((text_x, text_y), text, color, font=name_font)
    
    # Calculate dots position
    text_width = name_font.getbbox(text)[2]
    dots_x = text_x + text_width + TYPING_TEXT_OFFSET
    dots_y = text_y + name_font.getbbox(text)[3] // 2
    
    # Dot animation positions (middle dot bounces)
    dot_offsets = [0, 3 - abs(frame - 1), 0]
    
    # Draw three animated dots
    for i in range(3):
        dot_position = (
            dots_x + i * (TYPING_DOT_SIZE + TYPING_DOT_SPACING),
            dots_y - dot_offsets[i]
        )
        draw.ellipse(
            [dot_position, (dot_position[0] + TYPING_DOT_SIZE, 
                          dot_position[1] + TYPING_DOT_SIZE)],
            fill=TYPING_DOT_COLOR
        )
    
    return template


def is_emoji_message(message):
    """Return True if the message contains only emoji characters."""
    return bool(message) and all(regex.match(r'^\p{Emoji}+$', char) for char in message.strip())

def generate_chat(messages, name_time, profpic_file, color, current_status):
    """
    Generates a chat image given the list of messages, name & time info,
    profile picture file, and a role color.
    """
    name_text = name_time[0]
    if name_text == "Bot":
        name_text += " [BOT]"
    time_text = f'Today at {name_time[1]} PM'
    
    # Calculate baseline-aligned time position
    name_ascent, _ = name_font.getmetrics()
    time_ascent, _ = time_font.getmetrics()
    baseline_y = NAME_POSITION[1] + name_ascent
    time_position = (
        NAME_POSITION[0] + name_font.getbbox(name_text)[2] + NAME_TIME_SPACING,
        baseline_y - time_ascent
    )

    character_name = name_time[0]
    status_color = STATUS_INDICATORS[current_status.get(character_name, "online")]
    
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
    
    status_color = STATUS_INDICATORS[characters_dict[name_text].get("status", "online")]
    
    # Draw white background circle first for border effect
    # Calculate status position (centered in bottom-right of profile pic)
    status_radius = STATUS_SIZE // 2
    border_offset = STATUS_BORDER // 2
    
    # Center coordinates for both circles
    center_x = PROFPIC_POSITION[0] + PROFPIC_WIDTH - status_radius - 5
    center_y = PROFPIC_POSITION[1] + PROFPIC_WIDTH - status_radius - 5
    
    # Draw white border circle (slightly larger)
    border_radius = status_radius + STATUS_BORDER
    draw_template.ellipse(
        [
            (center_x - border_radius, center_y - border_radius),
            (center_x + border_radius, center_y + border_radius)
        ],
        fill=(255, 255, 255)  # White
    )
    
    # Draw status circle (perfectly centered within border)
    draw_template.ellipse(
        [
            (center_x - status_radius, center_y - status_radius),
            (center_x + status_radius, center_y + status_radius)
        ],
        fill=status_color
    )

    # Rest of the drawing operations...
    draw_template.text(NAME_POSITION, name_text, color, font=name_font)
    draw_template.text(time_position, time_text, TIME_FONT_COLOR, font=time_font)

    y_offset = 0
    embed = None
    for i, message in enumerate(messages):
        message = message.strip()
        if not message:
            continue

        if '$embed(' in message:
            parts = message.split('$embed(')
            message_text = parts[0].strip()
            embed_params = parts[1].split(')', 1)[0].split(',')
            
            color_hex = embed_params[0].strip().lstrip('#')
            color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
            title = embed_params[1].strip() if len(embed_params) > 1 else ""
            description = embed_params[2].strip() if len(embed_params) > 2 else ""
            
            embed = generate_embed(title, description, color_rgb)
            message = message_text
        
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
        tokens = re.split(r'(\*\*|__|~~)', message)
        bold = italic = strikethrough = False
        with Pilmoji(template) as pilmoji:
            for token in tokens:
                if token == '**':
                    bold = not bold
                elif token == '__':
                    italic = not italic
                elif token == '~~':
                    strikethrough = not strikethrough
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
                            # In the message rendering section (mentions handling):
                            if "Bot" in part:
                                bg_color = (47, 49, 54)  # Discord embed background
                            else:
                                bg_color = (74, 75, 114)
                            draw_template.rounded_rectangle(bg_box, fill=bg_color, radius=10)
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
                            # current_x += font_used.getbbox(part)[2] - font_used.getbbox(part)[0]

                            if strikethrough:
                                # Calculate strikethrough position
                                ascent, descent = font_used.getmetrics()
                                text_height = ascent + descent
                                strike_y = y_pos + ascent // 2
                                # Draw line covering the text width
                                text_width = font_used.getbbox(part)[2] - font_used.getbbox(part)[0]
                                draw_template.line(
                                    [(current_x, strike_y), 
                                    (current_x + text_width, strike_y)],
                                    fill=MESSAGE_FONT_COLOR,
                                    width=2
                                )
                            
                            current_x += font_used.getbbox(part)[2] - font_used.getbbox(part)[0]
    if embed:
        total_height = template.height + embed.height + 20
        combined = Image.new('RGBA', (WORLD_WIDTH, total_height), WORLD_COLOR)
        combined.paste(template, (0, 0))
        combined.paste(embed, (MESSAGE_X - 20, template.height + 10))
        return combined

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
    
    # Inside generate_joined_message(...):
    if name == "Bot":
        arrow = Image.open(f"{base_dir}/{os.pardir}/assets/shield_icon.png")
    else:
        arrow = Image.open(f"{base_dir}/{os.pardir}/assets/arrow_join.png")
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

def generate_left_message(name, time, template_str, arrow_x, color=NAME_FONT_COLOR):
    """Generates a Discord-like leave message with a white arrow"""
    before_text, after_text = template_str.split("CHARACTER", 1) if "CHARACTER" in template_str else ("", "")
    time_text = f'Today at {time} PM'
    
    template_img = Image.new(mode='RGBA', size=(WORLD_WIDTH, WORLD_HEIGHT_JOINED), color=WORLD_COLOR)
    draw_template = ImageDraw.Draw(template_img)
    
    arrow = Image.open(f"{base_dir}/{os.pardir}/assets/arrow_leave.png")  # Different arrow
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
def generate_joined_message_stack(joined_messages, hour, is_leave=False):
    """Generates stacked messages, now supporting leave messages"""
    total_height = WORLD_HEIGHT_JOINED * len(joined_messages)
    template_img = Image.new(mode='RGBA', size=(WORLD_WIDTH, total_height), color=WORLD_COLOR)
    
    for idx, key in enumerate(joined_messages):
        name = key.split(' ')[1].split('$^')[0]
        color = characters_dict[name]["role_color"]
        time_str = f'{hour}:{joined_messages[key][2].minute:02d}'
        
        if is_leave:
            joined_img = generate_left_message(name, time_str, joined_messages[key][0], 
                                             joined_messages[key][1], color)
        else:
            joined_img = generate_joined_message(name, time_str, joined_messages[key][0], 
                                              joined_messages[key][1], color)
                                              
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
    os.makedirs(f'{base_dir}/{os.pardir}/chat', exist_ok=True)
    current_time = init_time
    current_name = None
    current_lines = []
    msg_number = 1
    joined_messages = {}
    name_time = []
    typing_enabled = True  # Default to enabled for backward compatibility
    if current_name == "Bot":
        typing_enabled = False  # Bots don't show typing
    current_status = {name: data.get("status", "online") for name, data in characters_dict.items()}

    for line in lines:
        if line.startswith("STATUS "):
            try:
                parts = line.split('$^')
                status_parts = parts[0].split()
                _, character, new_status = status_parts
                duration = parts[1].split('#!')[0] if '#!' in parts[1] else parts[1]
                
                # Generate status message image
                hour = current_time.hour % 12 or 12
                status_img = generate_status_message(
                    character,
                    f"{hour}:{current_time.minute:02d}",
                    new_status,
                    random.randint(50, 80),
                    characters_dict[character]["role_color"]
                )
                status_img.save(f'{base_dir}/{os.pardir}/chat/{msg_number:03d}.png')
                
                current_time += datetime.timedelta(seconds=float(duration))
                msg_number += 1
                current_status[character] = new_status
                continue
            except Exception as e:
                print(f"Error processing STATUS: {e}")
                continue

        if line == '':
            current_name = None
            current_lines = []
            name_time = []
            joined_messages = {}
            typing_enabled = True  # Reset to default for next block
            continue

        if line.startswith('#'):
            joined_messages = {}
            continue

        if line.startswith("WELCOME "):
            joined_messages[line] = [random.choice(JOINED_TEXTS), random.randint(50, 80), current_time]
            hour = current_time.hour % 12 or 12
            image = generate_joined_message_stack(joined_messages, hour, is_leave=False)
            image.save(f'{base_dir}/{os.pardir}/chat/{msg_number:03d}.png')
            current_time += datetime.timedelta(seconds=dt)
            msg_number += 1
            continue
        elif line.startswith("LEAVE "):  # New leave message handling
            joined_messages[line] = [random.choice(LEFT_TEXTS), random.randint(50, 80), current_time]
            hour = current_time.hour % 12 or 12
            image = generate_joined_message_stack(joined_messages, hour, is_leave=True)
            image.save(f'{base_dir}/{os.pardir}/chat/{msg_number:03d}.png')
            current_time += datetime.timedelta(seconds=dt)
            msg_number += 1
            continue
        else:
            joined_messages = {}

        if ':' in line:
            # Check for typing toggle syntax
            if '^:' in line:
                current_name = line.split('^:', 1)[0].strip().lstrip('@')
                typing_enabled = True
            else:
                current_name = line.split(':', 1)[0].strip().lstrip('@')
                typing_enabled = False

            if not current_name:
                raise ValueError(f"Empty character name in line: {line}")
            if current_name not in characters_dict:
                raise ValueError(f"Character '{current_name}' not found in characters.json")

            hour = current_time.hour % 12 or 12
            name_time = [current_name, f'{hour}:{current_time.minute:02d}']
            
            # Generate typing indicator if enabled
            if typing_enabled:
                for frame in range(TYPING_ANIMATION_FRAMES):
                    typing_img = generate_typing_indicator(
                        current_name,
                        characters_dict[current_name]["role_color"],
                        frame
                    )
                    typing_img.save(f'{base_dir}/{os.pardir}/chat/{msg_number:03d}.png')
                    msg_number += 1
                current_time += datetime.timedelta(
                    seconds=TYPING_FRAME_DURATION * TYPING_ANIMATION_FRAMES
                )
            continue

        # Process message line
        if current_name and '$^' in line:
            message = line.split('$^')[0].strip()
            current_lines.append(message)
            image = generate_chat(
                messages=current_lines,
                name_time=name_time,
                profpic_file=os.path.join(
                    f'{base_dir}/{os.pardir}/assets/profile_pictures', 
                    characters_dict[current_name]["profile_pic"]
                ),
                color=characters_dict[current_name]["role_color"],
                current_status=current_status  # Add this parameter
            )
            image.save(f'{base_dir}/{os.pardir}/chat/{msg_number:03d}.png')
            duration_part = line.split('$^')[1].split('#!')[0] if '#!' in line else line.split('$^')[1]
            current_time += datetime.timedelta(seconds=float(duration_part))
            msg_number += 1

        image = generate_chat(
            messages=current_lines,
            name_time=name_time,
            profpic_file=os.path.join(
                f'{base_dir}/{os.pardir}/assets/profile_pictures', 
                characters_dict[current_name]["profile_pic"]
            ),
            color=characters_dict[current_name]["role_color"],
            current_status=current_status  # Add this parameter
        )

if __name__ == '__main__':
    """
    final_video = f'{base_dir}/{os.pardir}/output.mp4'
    if os.path.isfile(final_video):
        os.remove(final_video)
    if os.path.exists(f'{base_dir}/{os.pardir}/chat'):
        for file in os.listdir(f'{base_dir}/{os.pardir}/chat'):
            os.remove(os.path.join(f'{base_dir}/{os.pardir}/chat', file))
        os.rmdir(f'{base_dir}/{os.pardir}/chat')

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