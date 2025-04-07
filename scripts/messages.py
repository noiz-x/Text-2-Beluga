# scripts/messages.py

#!/usr/bin/env python3
"""
messages.py

Generates the message area image including avatars, usernames, timestamps,
wrapped message content, and reaction pills.
"""

from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import GoogleEmojiSource
import os, textwrap
from typing import List, Dict, Any

# Constants
CHAT_WIDTH = 1777 - 220  # Chat area width (screen width minus sidebar)
CANVAS_HEIGHT = 600      # Adjust as needed for number of messages
AVATAR_SIZE = 40
MESSAGE_BG_COLOR = (54, 57, 63)  # #36393f
MAX_MESSAGE_WIDTH = 600

# For simplicity, we use default fonts here. In practice, load custom fonts.
def load_fonts():
    from PIL import ImageFont
    # Adjust font paths as needed
    return {
        "name": ImageFont.load_default(),
        "message": ImageFont.load_default(),
        "timestamp": ImageFont.load_default()
    }
FONTS = load_fonts()

def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        if font.getlength(test_line) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def generate_messages(messages: List[Dict[str, Any]]) -> Image.Image:
    canvas = Image.new('RGB', (CHAT_WIDTH, CANVAS_HEIGHT), MESSAGE_BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    y_offset = 15
    x_avatar = 15
    x_text = x_avatar + AVATAR_SIZE + 10

    with Pilmoji(canvas, source=GoogleEmojiSource) as pilmoji:
        for msg in messages:
            author = msg.get("author", "Unknown")
            avatar_path = msg.get("avatar", "")
            role_color = msg.get("role_color", (255,255,255))
            timestamp = msg.get("timestamp", "00:00")
            content = msg.get("content", "")
            reactions = msg.get("reactions", [])

            # Draw avatar
            if avatar_path and os.path.isfile(avatar_path):
                avatar = Image.open(avatar_path).resize((AVATAR_SIZE, AVATAR_SIZE))
                mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0)
                ImageDraw.Draw(mask).ellipse([0,0,AVATAR_SIZE,AVATAR_SIZE], fill=255)
                canvas.paste(avatar, (x_avatar, y_offset), mask)
            else:
                draw.ellipse([x_avatar, y_offset, x_avatar+AVATAR_SIZE, y_offset+AVATAR_SIZE],
                             fill=role_color)
            
            # Draw username and timestamp
            pilmoji.text((x_text, y_offset), author, font=FONTS["name"], fill=role_color)
            name_width = FONTS["name"].getlength(author)
            pilmoji.text((x_text+name_width+10, y_offset), f"Today at {timestamp}", font=FONTS["timestamp"], fill=(148,155,164))
            y_offset += 25
            
            # Draw message content (wrapped)
            wrapped = wrap_text(content, FONTS["message"], MAX_MESSAGE_WIDTH)
            for line in wrapped:
                pilmoji.text((x_text, y_offset), line, font=FONTS["message"], fill=(255,255,255))
                y_offset += 25
            
            # Draw reactions as simple pills
            if reactions:
                x_react = x_text
                for reaction in reactions:
                    text = f"{reaction['emoji']} {reaction['count']}" if reaction['count'] > 1 else reaction['emoji']
                    text_w = FONTS["message"].getlength(text)
                    pill_padding = 10
                    pill_w = text_w + pill_padding * 2
                    pill_h = 30
                    draw.rounded_rectangle([x_react, y_offset, x_react+pill_w, y_offset+pill_h], radius=pill_h//2, fill=(64,68,75))
                    pilmoji.text((x_react+pill_padding, y_offset+5), text, font=FONTS["message"], fill=(255,255,255))
                    x_react += pill_w + 15
                y_offset += 40
            
            y_offset += 10
    return canvas

if __name__ == "__main__":
    # Sample message data
    sample_messages = [
        {
            "author": "Lone Wanderer",
            "avatar": "",  # Provide valid path if available
            "role_color": (114,137,218),
            "timestamp": "6:17 PM",
            "content": "Anyone start the new season of Westworld? This season was WILD",
            "reactions": [{"emoji": "👍", "count": 2}, {"emoji": "🤖", "count": 1}]
        },
        {
            "author": "Helio",
            "avatar": "",
            "role_color": (88,101,242),
            "timestamp": "6:18 PM",
            "content": "Ohh I could be down to watch. I'm rdy to play anytime. But I'm making a bit of dinner first.",
            "reactions": [{"emoji": "🍿", "count": 3}]
        }
    ]
    messages_img = generate_messages(sample_messages)
    messages_img.save("messages.png")
    print("Messages image saved as messages.png")
