# scripts/side_bar.py
"""
side_bar.py

Generates the sidebar image with server icons and channel list.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Constants
SCREEN_HEIGHT = 900
SIDEBAR_WIDTH = 220
SIDEBAR_BG_COLOR = (47, 49, 54)  # #2f3136
SEPARATOR_COLOR = (35, 36, 40)

def generate_sidebar() -> Image.Image:
    canvas = Image.new('RGB', (SIDEBAR_WIDTH, SCREEN_HEIGHT), SIDEBAR_BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    
    # Draw server icons
    icon_size = 48
    icon_spacing = 70
    top_margin = 10
    x_center = SIDEBAR_WIDTH // 2
    for i in range(3):
        y_center = top_margin + icon_size // 2 + i * icon_spacing
        # Draw a circular server icon
        draw.ellipse(
            [x_center - icon_size//2, y_center - icon_size//2,
             x_center + icon_size//2, y_center + icon_size//2],
            fill=(114, 137, 218)
        )
        # For the first icon, draw an online status indicator
        if i == 0:
            draw.ellipse(
                [x_center + icon_size//2 - 8, y_center + icon_size//2 - 8,
                 x_center + icon_size//2 + 4, y_center + icon_size//2 + 4],
                fill=(59, 165, 93)
            )
    
    # Draw horizontal separator
    separator_y = top_margin + 3 * icon_spacing + 20
    draw.rectangle([0, separator_y, SIDEBAR_WIDTH, separator_y + 2], fill=SEPARATOR_COLOR)
    
    # Draw channel list with active highlight
    channels = ["general", "westworld", "memes"]
    channel_y = separator_y + 30
    active_channel = "westworld"
    for ch in channels:
        if ch == active_channel:
            draw.rectangle([0, channel_y - 5, SIDEBAR_WIDTH, channel_y + 25], fill=(57, 60, 67))
            draw.rectangle([0, channel_y - 5, 4, channel_y + 25], fill=(255, 255, 255))
            text_color = (255, 255, 255)
        else:
            text_color = (148, 155, 164)
        draw.text((20, channel_y), f"#{ch}", fill=text_color)
        channel_y += 30
    
    return canvas

if __name__ == "__main__":
    sidebar_img = generate_sidebar()
    sidebar_img.save("side_bar.png")
    print("Sidebar image saved as side_bar.png")
