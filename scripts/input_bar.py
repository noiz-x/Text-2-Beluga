# scripts/input_bar.py

#!/usr/bin/env python3
"""
input_bar.py

Generates the bottom input bar image with a rounded message input field and icons.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Constants
SIDEBAR_WIDTH = 220
SCREEN_WIDTH = 1777
SCREEN_HEIGHT = 900
BOTTOM_BAR_HEIGHT = 60
INPUT_FIELD_COLOR = (64, 68, 75)  # #40444b
BOTTOM_BAR_COLOR = (64, 68, 75)

# Calculate chat area width
CHAT_WIDTH = SCREEN_WIDTH - SIDEBAR_WIDTH

def generate_input_bar() -> Image.Image:
    canvas = Image.new('RGB', (CHAT_WIDTH, BOTTOM_BAR_HEIGHT), BOTTOM_BAR_COLOR)
    draw = ImageDraw.Draw(canvas)
    
    # Input field dimensions
    input_height = 45
    input_top = (BOTTOM_BAR_HEIGHT - input_height) // 2
    draw.rounded_rectangle([15, input_top, CHAT_WIDTH - 15, input_top + input_height],
                           radius=20, fill=INPUT_FIELD_COLOR)
    
    # For simplicity, use default font; you can load a custom font if needed
    draw.text((30, input_top + 10), "Message #westworld", fill=(142, 146, 151))
    
    # Left icons
    draw.text((25, input_top + 10), "🙂", fill=(142, 146, 151))
    draw.text((60, input_top + 10), "📎", fill=(142, 146, 151))
    
    # Right icons
    draw.text((CHAT_WIDTH - 90, input_top + 10), "🎮", fill=(142, 146, 151))
    draw.text((CHAT_WIDTH - 50, input_top + 10), "GIF", fill=(142, 146, 151))
    
    return canvas

if __name__ == "__main__":
    input_img = generate_input_bar()
    input_img.save("input_bar.png")
    print("Input bar image saved as input_bar.png")
