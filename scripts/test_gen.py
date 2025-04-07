# scripts/generate_chat.py

from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import GoogleEmojiSource
import os
import json
import random
import regex
import re
from typing import List, Dict, Any

########################
#    GLOBAL SETTINGS   #
########################

# Canvas dimensions
SCREEN_WIDTH = 1777
SCREEN_HEIGHT = 900

# UI Components
SIDEBAR_WIDTH = 220
TOP_BAR_HEIGHT = 50
BOTTOM_BAR_HEIGHT = 60
AVATAR_SIZE = 40

# Discord color scheme
COLORS = {
    "sidebar_bg": (47, 49, 54),
    "chat_bg": (54, 57, 63),
    "header_bg": (47, 49, 54),
    "input_bg": (64, 68, 75),
    "reaction": (64, 68, 75),
    "mention": (74, 75, 114)
}

# Font configuration
FONT_BASE = os.path.join(os.path.dirname(__file__), os.pardir, "assets", "fonts", "whitney")
FONTS = {
    "name": ImageFont.truetype(os.path.join(FONT_BASE, "semibold.ttf"), 45),
    "time": ImageFont.truetype(os.path.join(FONT_BASE, "medium.ttf"), 35),
    "message": ImageFont.truetype(os.path.join(FONT_BASE, "medium.ttf"), 45),
    "bold": ImageFont.truetype(os.path.join(FONT_BASE, "bold.ttf"), 45),
    "italic": ImageFont.truetype(os.path.join(FONT_BASE, "medium_italic.ttf"), 45),
    "mention": ImageFont.truetype(os.path.join(FONT_BASE, "semibold.ttf"), 45),
    "mention_italic": ImageFont.truetype(os.path.join(FONT_BASE, "semibold_italic.ttf"), 45)
}

########################
#   CORE COMPONENTS    #
########################

class DiscordUI:
    def __init__(self):
        self.canvas = Image.new('RGBA', (SCREEN_WIDTH, SCREEN_HEIGHT), COLORS["chat_bg"])
        self.draw = ImageDraw.Draw(self.canvas)
        self.message_stack = []
        self.current_y = TOP_BAR_HEIGHT + 20

    def draw_sidebar(self):
        """Draw server list and channels"""
        # Sidebar background
        self.draw.rectangle([0, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT], fill=COLORS["sidebar_bg"])
        
        # Server icons
        for i in range(3):
            pos = (SIDEBAR_WIDTH//2 - 24, 50 + i*80)
            self.draw.ellipse([pos[0], pos[1], pos[0]+48, pos[1]+48], fill=(114,137,218))
        
        # Channel list
        channels = ["general", "westworld", "memes"]
        for idx, channel in enumerate(channels):
            y_pos = 300 + idx*50
            self.draw.text((30, y_pos), f"#{channel}", (148,155,164), font=FONTS["name"])

    def draw_header(self):
        """Draw channel header with topic"""
        self.draw.rectangle([SIDEBAR_WIDTH, 0, SCREEN_WIDTH, TOP_BAR_HEIGHT], fill=COLORS["header_bg"])
        self.draw.text((SIDEBAR_WIDTH+30, 15), "#westworld", (255,255,255), font=FONTS["bold"])
        self.draw.text((SIDEBAR_WIDTH+30, 35), "Discussion hub for Westworld fans", (148,155,164), font=FONTS["time"])

    def draw_input(self):
        """Draw message input box"""
        input_height = 45
        self.draw.rounded_rectangle(
            [SIDEBAR_WIDTH+30, SCREEN_HEIGHT-BOTTOM_BAR_HEIGHT+10, 
             SCREEN_WIDTH-30, SCREEN_HEIGHT-15],
            radius=20, fill=COLORS["input_bg"]
        )
        self.draw.text(
            (SIDEBAR_WIDTH+60, SCREEN_HEIGHT-BOTTOM_BAR_HEIGHT+25),
            "Message #westworld", (142,146,151), font=FONTS["message"]
        )

    def process_message(self, message: Dict[str, Any]):
        """Process a message dictionary into UI elements"""
        # Avatar and name header
        self.draw_avatar(message)
        self.draw_name_header(message)
        
        # Message content
        self.draw_text_content(message["content"])
        
        # Reactions
        if message.get("reactions"):
            self.draw_reactions(message["reactions"])

        self.current_y += 40  # Space between messages

    def draw_avatar(self, message: Dict[str, Any]):
        """Draw user avatar"""
        avatar_img = Image.open(message["avatar"]).resize((AVATAR_SIZE, AVATAR_SIZE))
        mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0)
        ImageDraw.Draw(mask).ellipse([0,0,AVATAR_SIZE,AVATAR_SIZE], fill=255)
        self.canvas.paste(avatar_img, (SIDEBAR_WIDTH+30, self.current_y), mask)

    def draw_name_header(self, message: Dict[str, Any]):
        """Draw username and timestamp"""
        name_width = FONTS["name"].getlength(message["author"])
        time_text = f'Today at {message["timestamp"]}'
        
        # Username
        self.draw.text(
            (SIDEBAR_WIDTH+90, self.current_y), 
            message["author"], message["color"], font=FONTS["name"]
        )
        
        # Timestamp
        self.draw.text(
            (SIDEBAR_WIDTH+100 + name_width, self.current_y+5),
            time_text, (148,155,164), font=FONTS["time"]
        )
        
        self.current_y += 50  # Move to message content

    def draw_text_content(self, content: str):
        """Draw formatted message content with emoji and mention support"""
        x_pos = SIDEBAR_WIDTH + 90
        y_pos = self.current_y
        
        with Pilmoji(self.canvas) as pilmoji:
            tokens = re.split(r'(\*\*|__|@\w+)', content)
            bold = italic = False
            
            for token in tokens:
                if token in ["**", "__"]:
                    # Toggle formatting states
                    if token == "**": bold = not bold
                    if token == "__": italic = not italic
                    continue
                
                if token.startswith("@"):
                    # Handle mentions with special styling
                    self.draw_mention(token[1:], int(x_pos), int(y_pos))
                    x_pos += FONTS["mention"].getlength(f"@{token}") + 15
                else:
                    # Handle regular text with formatting
                    font = self._get_font(bold, italic)
                    pilmoji.text((int(x_pos), int(y_pos)), token, 
                                (220,222,225), font=font)
                    x_pos += font.getlength(token)
        
        self.current_y += 60  # Line height


    def draw_reactions(self, reactions: List[Dict]):
        """Draw reaction pills under message"""
        x_pos = SIDEBAR_WIDTH + 90
        y_pos = self.current_y
        
        for reaction in reactions:
            text = f'{reaction["emoji"]} {reaction["count"]}' if reaction["count"] > 1 else reaction["emoji"]
            text_width = FONTS["message"].getlength(text)
            
            # Convert coordinates to integers
            rx_pos = int(x_pos)
            ry_pos = int(y_pos)
            
            # Reaction background
            self.draw.rounded_rectangle(
                [rx_pos-10, ry_pos-5, rx_pos+int(text_width)+20, ry_pos+45],
                radius=15, fill=COLORS["reaction"]
            )
            
            # Reaction content - ensure integer coordinates
            with Pilmoji(self.canvas) as pilmoji:
                pilmoji.text((rx_pos, ry_pos), text, (255,255,255), font=FONTS["message"])
            
            x_pos += text_width + 40

        self.current_y += 60  # Space after reactions

    def draw_mention(self, username: str, x: int, y: int):
        """Draw a mention with background pill styling"""
        # Calculate text dimensions
        text = f"@{username}"
        text_width = FONTS["bold"].getlength(text)
        text_height = FONTS["bold"].getmetrics()[0]  # Get ascent
        
        # Create mention background
        padding = 10
        self.draw.rounded_rectangle(
            [x - padding//2, y - padding//2, 
            x + text_width + padding, y + text_height + padding//2],
            radius=15, fill=COLORS["mention"]
        )
        
        # Draw mention text
        with Pilmoji(self.canvas) as pilmoji:
            pilmoji.text((x, y), text, (201, 205, 251), font=FONTS["bold"])

    def _get_font(self, bold: bool, italic: bool):
        """Select appropriate font based on formatting"""
        if bold and italic:
            return FONTS["bold_italic"]
        if bold:
            return FONTS["bold"]
        if italic:
            return FONTS["italic"]
        return FONTS["message"]

########################
#    MAIN EXECUTION    #
########################

if __name__ == "__main__":
    # Example message data
    messages = [
        {
            "author": "Billy",
            "avatar": "assets/profile_pictures/perm/billy.jpeg",
            "color": (114, 137, 218),
            "timestamp": "8:15 PM",
            "content": "**These violent delights** have __violent ends__",
            "reactions": [
                {"emoji": "🤖", "count": 2},
                {"emoji": "❤️", "count": 1}
            ]
        },
        {
            "author": "Nerd",
            "avatar": "assets/profile_pictures/perm/nerd.jpg",
            "color": (188, 101, 242),
            "timestamp": "8:17 PM",
            "content": "Have you ever seen anything so full of **splendor**? @Billy",
            "reactions": [
                {"emoji": "👏", "count": 3}
            ]
        }
    ]

    # Generate UI
    ui = DiscordUI()
    ui.draw_sidebar()
    ui.draw_header()
    
    for msg in messages:
        ui.process_message(msg)
    
    ui.draw_input()
    ui.canvas.save("discord_chat.png")