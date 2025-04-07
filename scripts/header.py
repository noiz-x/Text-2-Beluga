# scripts/header.py

#!/usr/bin/env python3
"""
header.py

Generates the channel header image including channel name, topic, and icons.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Constants
SIDEBAR_WIDTH = 220
TOP_BAR_HEIGHT = 50
# Set the width of the header image to be the chat area width (screen width minus sidebar)
CHAT_WIDTH = 1777 - SIDEBAR_WIDTH
HEADER_BG_COLOR = (47, 49, 54)  # #2f3136

# For fonts, adjust the path if necessary
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH_BOLD = os.path.join(BASE_DIR, os.pardir, "assets", "fonts", "whitney", "bold.ttf")

# Load font
NAME_FONT = ImageFont.truetype(FONT_PATH_BOLD, 18)
TIMESTAMP_FONT = ImageFont.truetype(FONT_PATH_BOLD, 14)

def generate_header() -> Image.Image:
    canvas = Image.new('RGB', (CHAT_WIDTH, TOP_BAR_HEIGHT), HEADER_BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    
    # Channel name and topic
    draw.text((15, 12), "#westworld", fill=(255, 255, 255), font=NAME_FONT)
    draw.text((15, 32), "Discussion about Westworld S5", fill=(148, 155, 164), font=TIMESTAMP_FONT)
    
    # Header icons on the right
    icons_x = CHAT_WIDTH - 120
    draw.text((icons_x, 15), "📌", fill=(148, 155, 164), font=NAME_FONT)
    draw.text((icons_x + 40, 15), "👥", fill=(148, 155, 164), font=NAME_FONT)
    draw.text((icons_x + 80, 15), "⚙️", fill=(148, 155, 164), font=NAME_FONT)
    
    return canvas

if __name__ == "__main__":
    header_img = generate_header()
    header_img.save("header.png")
    print("Header image saved as header.png")
