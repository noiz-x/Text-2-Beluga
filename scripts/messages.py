# scripts/messages.py
import os
import re
import textwrap
from typing import List, Dict, Any, Tuple

from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import GoogleEmojiSource

# Global cache for avatars to avoid multiple disk reads
avatar_cache = {}

class MessageConfig:
    def __init__(self):
        # Dimensions
        self.CHAT_WIDTH = 1150
        self.AVATAR_SIZE = 40
        self.REPLY_AVATAR_SIZE = 24
        self.MAX_MESSAGE_WIDTH = 600
        self.REACTION_PILL_PADDING = 10
        self.REACTION_PILL_HEIGHT = 30
        self.REPLY_INDENT = 44
        
        # Colors
        self.BG_COLOR = (54, 57, 63)
        self.NAME_COLOR = (255, 255, 255)
        self.TIME_COLOR = (148, 155, 164)
        self.MESSAGE_COLOR = (220, 222, 225)
        self.REACTION_BG = (64, 68, 75)
        self.REPLY_BAR_COLOR = (114, 137, 218)
        self.REPLY_TEXT_COLOR = (148, 155, 164)
        # Special colors for channel and user mentions
        self.channel_color = (88, 101, 242)
        self.mention_color = (114, 137, 218)
        
        # Fonts
        self.font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "assets", "fonts", "whitney")
        self.name_font = ImageFont.truetype(os.path.join(self.font_dir, "semibold.ttf"), 16)
        self.time_font = ImageFont.truetype(os.path.join(self.font_dir, "medium.ttf"), 14)
        self.message_font = ImageFont.truetype(os.path.join(self.font_dir, "medium.ttf"), 15)
        # For bold text, we use the semibold variant
        self.bold_font = ImageFont.truetype(os.path.join(self.font_dir, "semibold.ttf"), 15)
        # For italics we assume an italic variant exists; if not, you may substitute with a proper italic font
        self.italic_font = ImageFont.truetype(os.path.join(self.font_dir, "medium.ttf"), 15)
        # You could also define a bold-italic variant if available
        self.bold_italic_font = self.bold_font

        self.reaction_font = ImageFont.truetype(os.path.join(self.font_dir, "medium.ttf"), 14)
        self.reply_font = ImageFont.truetype(os.path.join(self.font_dir, "medium.ttf"), 13)

        # Spacing
        self.AVATAR_OFFSET = 15
        self.TEXT_X_OFFSET = 65
        self.LINE_SPACING = 25
        self.REACTION_SPACING = 15
        self.REPLY_SPACING = 8

        # Online status indicator settings
        self.ONLINE_INDICATOR_SIZE = 10
        self.ONLINE_INDICATOR_COLORS = {
            "online": (67, 181, 129),
            "idle": (250, 166, 26),
            "dnd": (240, 71, 71),
            "offline": (116, 127, 141)
        }

config = MessageConfig()

def parse_markdown(text: str) -> List[Dict]:
    """
    Parses the input text for markdown-like formatting tokens.
    Supported tokens:
      - Bold: **text**
      - Italics: *text*
      - Underline: __text__
      - Strike-through: ~~text~~
      - Also detects @mentions and #channels for distinct coloring.
    Returns a list of segments where each segment is a dict with:
      "text", "bold", "italic", "underline", "strike", "color"
    """
    segments = []
    # Pattern to match markdown tokens and special mentions.
    pattern = r'(\*\*.*?\*\*|__.*?__|~~.*?~~|\*.*?\*|\|[@#]\w+|(?<!\|)[@#]\w+)'
    last_index = 0
    for match in re.finditer(pattern, text):
        start, end = match.span()
        if start > last_index:
            # Append plain text preceding the token.
            segments.append({
                "text": text[last_index:start],
                "bold": False,
                "italic": False,
                "underline": False,
                "strike": False,
                "color": None
            })
        token = match.group(0)
        if token.startswith("**") and token.endswith("**"):
            segments.append({
                "text": token[2:-2],
                "bold": True,
                "italic": False,
                "underline": False,
                "strike": False,
                "color": None
            })
        elif token.startswith("__") and token.endswith("__"):
            segments.append({
                "text": token[2:-2],
                "bold": False,
                "italic": False,
                "underline": True,
                "strike": False,
                "color": None
            })
        elif token.startswith("~~") and token.endswith("~~"):
            segments.append({
                "text": token[2:-2],
                "bold": False,
                "italic": False,
                "underline": False,
                "strike": True,
                "color": None
            })
        elif token.startswith("*") and token.endswith("*"):
            segments.append({
                "text": token[1:-1],
                "bold": False,
                "italic": True,
                "underline": False,
                "strike": False,
                "color": None
            })
        elif token.startswith("#"):
            segments.append({
                "text": token,
                "bold": False,
                "italic": False,
                "underline": False,
                "strike": False,
                "color": config.channel_color
            })
        elif token.startswith("@"):
            segments.append({
                "text": token,
                "bold": False,
                "italic": False,
                "underline": False,
                "strike": False,
                "color": config.mention_color
            })
        else:
            segments.append({
                "text": token,
                "bold": False,
                "italic": False,
                "underline": False,
                "strike": False,
                "color": None
            })
        last_index = end
    if last_index < len(text):
        segments.append({
            "text": text[last_index:],
            "bold": False,
            "italic": False,
            "underline": False,
            "strike": False,
            "color": None
        })
    return segments

def draw_formatted_text(pilmoji, draw, start_x: int, start_y: int, text: str, max_width: int) -> int:
    """
    Draws text with markdown-like formatting with word-wrapping.
    Splits the input text into segments, selects the proper font for each segment,
    and draws words one by one. Underline and strike-through are rendered manually.
    Returns the y-coordinate after drawing the text.
    """
    segments = parse_markdown(text)
    x = start_x
    y = start_y

    # Process each segment
    for seg in segments:
        # Select the proper font based on formatting.
        if seg["bold"] and seg["italic"]:
            font = config.bold_italic_font
        elif seg["bold"]:
            font = config.bold_font
        elif seg["italic"]:
            font = config.italic_font
        else:
            font = config.message_font
        # Use special color if provided
        color = seg["color"] if seg["color"] is not None else config.MESSAGE_COLOR

        avg_char_width = font.getlength("a")
        available_chars = int(max_width // avg_char_width) if avg_char_width else 50
        words = textwrap.wrap(seg["text"], width=available_chars, drop_whitespace=False)
        for word in words:
            if word == "":
                continue
            word_width = font.getlength(word)
            # If the word exceeds the current line width, wrap to next line.
            if x + word_width > start_x + max_width:
                x = start_x
                y += config.LINE_SPACING
            # Draw the word.
            pilmoji.text((x, y), word, font=font, fill=color)
            # Measure text size for line decorations.
            bbox = font.getbbox(word)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            if seg["underline"]:
                draw.line((x, y + h * 1.5, x + w, y + h * 1.5), fill=color, width=1)
            if seg["strike"]:
                draw.line((x, y + h, x + w, y + h), fill=color, width=1)
            x += word_width
    return y + config.LINE_SPACING

def estimate_text_height(text: str) -> int:
    """
    Estimates the height needed to render the given text (accounting for newlines and wrapping)
    using the plain message font (ignoring markdown markers).
    """
    total_lines = 0
    lines = text.split("\n")
    for line in lines:
        # Remove markdown markers for estimation.
        plain_line = re.sub(r'(\*\*|__|~~|\*)', '', line)
        # Estimate wrapped lines based on average character width.
        char_width = config.message_font.getlength(" ")
        approx_chars = int(config.MAX_MESSAGE_WIDTH // char_width) if char_width else 50
        wrapped = textwrap.wrap(plain_line, width=approx_chars)
        total_lines += max(1, len(wrapped))
    return total_lines * config.LINE_SPACING

def calculate_required_height(messages: List[Dict[str, Any]]) -> int:
    """
    Calculate the total height required for the canvas based on messages.
    Uses the estimated text height (which accounts for markdown formatting) for each message.
    """
    y_offset = 15  # Initial top padding
    for msg in messages:
        # Extra space if the message is a reply.
        if msg.get("reply_to"):
            y_offset += 30 + config.REPLY_SPACING  # Reply component height plus spacing

        # Height for username and timestamp.
        y_offset += config.LINE_SPACING

        # Estimate height for message content.
        y_offset += estimate_text_height(msg["content"])

        # Reactions area.
        if msg.get("reactions"):
            y_offset += config.REACTION_PILL_HEIGHT + 10  # Reaction height + spacing

        # Spacing after each message.
        y_offset += 20

    return y_offset

def get_avatar_image(avatar_path: str, size: int, fallback_color: Tuple[int, int, int]) -> Tuple[Image.Image, Image.Image]:
    """
    Load avatar from cache or file system.
    Returns a tuple of (avatar_image, circular_mask).
    """
    global avatar_cache
    cache_key = (avatar_path, size)
    if cache_key in avatar_cache:
        return avatar_cache[cache_key]

    if os.path.isfile(avatar_path):
        try:
            avatar = Image.open(avatar_path).convert("RGBA").resize((size, size))
        except Exception:
            avatar = None
        if avatar:
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
            avatar_cache[cache_key] = (avatar, mask)
            return avatar, mask

    # Fallback: generate a placeholder circle with the fallback color.
    placeholder = Image.new("RGBA", (size, size), fallback_color)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    avatar_cache[cache_key] = (placeholder, mask)
    return placeholder, mask

def draw_avatar(canvas: Image.Image, avatar_path: str, pos: Tuple[int, int], size: int, fallback_color: Tuple[int, int, int]):
    """
    Draws an avatar on the canvas at the given position.
    """
    avatar, mask = get_avatar_image(avatar_path, size, fallback_color)
    canvas.paste(avatar, pos, mask)

def draw_reply(canvas: Image.Image, draw: ImageDraw.Draw, pilmoji, reply_info: Dict, y_offset: int) -> int:
    """
    Draw reply reference component.
    """
    # Draw vertical reply bar.
    draw.rectangle(
        (config.TEXT_X_OFFSET - 12, y_offset,
         config.TEXT_X_OFFSET - 8, y_offset + 30),
        fill=config.REPLY_BAR_COLOR
    )
    
    # Draw reply avatar.
    avatar_pos = (config.TEXT_X_OFFSET - 6, y_offset + 3)
    draw_avatar(canvas, reply_info.get("avatar", ""), avatar_pos, config.REPLY_AVATAR_SIZE,
                reply_info.get("role_color", config.REPLY_BAR_COLOR))
    
    # Draw reply text (author + preview).
    reply_text = f"Replying to @{reply_info['author']}"
    text_x = config.TEXT_X_OFFSET + config.REPLY_AVATAR_SIZE + 6
    pilmoji.text(
        (text_x, y_offset + 8),
        reply_text,
        font=config.reply_font,
        fill=config.REPLY_TEXT_COLOR
    )
    preview = textwrap.shorten(reply_info["content"], width=40, placeholder="...")
    pilmoji.text(
        (text_x + config.reply_font.getlength(reply_text) + 10, y_offset + 8),
        preview,
        font=config.reply_font,
        fill=config.MESSAGE_COLOR
    )
    
    return y_offset + 30 + config.REPLY_SPACING

def generate_messages(messages: List[Dict[str, Any]]) -> Image.Image:
    """
    Generate a compact Discord-style message list image with optional replies and markdown formatting.
    """
    required_height = calculate_required_height(messages)
    canvas = Image.new("RGB", (config.CHAT_WIDTH, required_height), config.BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    y_offset = 15

    with Pilmoji(canvas, source=GoogleEmojiSource) as pilmoji:
        for msg in messages:
            # Draw reply reference if present.
            if msg.get("reply_to"):
                y_offset = draw_reply(canvas, draw, pilmoji, msg["reply_to"], y_offset)

            # Draw main avatar.
            avatar_pos = (config.AVATAR_OFFSET, y_offset)
            draw_avatar(canvas, msg.get("avatar", ""), avatar_pos, config.AVATAR_SIZE,
                        msg.get("role_color", (114, 137, 218)))
            
            # Online status indicator (if provided).
            if msg.get("status"):
                status = msg["status"].lower()
                indicator_color = config.ONLINE_INDICATOR_COLORS.get(status, config.ONLINE_INDICATOR_COLORS["offline"])
                indicator_size = config.ONLINE_INDICATOR_SIZE
                indicator_pos = (
                    config.AVATAR_OFFSET + config.AVATAR_SIZE - indicator_size,
                    y_offset + config.AVATAR_SIZE - indicator_size,
                    config.AVATAR_OFFSET + config.AVATAR_SIZE,
                    y_offset + config.AVATAR_SIZE
                )
                draw.ellipse(indicator_pos, fill=indicator_color)

            # Draw username and timestamp (with edited indicator if applicable).
            name = msg["author"]
            time_text = f"Today at {msg['timestamp']}"
            if msg.get("edited"):
                time_text += " (edited)"
            
            name_width = config.name_font.getlength(name)
            time_x = config.TEXT_X_OFFSET + name_width + 10
            
            pilmoji.text(
                (config.TEXT_X_OFFSET, y_offset),
                name,
                font=config.name_font,
                fill=config.NAME_COLOR
            )
            pilmoji.text(
                (time_x, y_offset),
                time_text,
                font=config.time_font,
                fill=config.TIME_COLOR
            )
            y_offset += config.LINE_SPACING

            # Draw message content with markdown formatting.
            content_x = config.TEXT_X_OFFSET
            # Split content by explicit newlines.
            for line in msg["content"].split("\n"):
                y_offset = draw_formatted_text(pilmoji, draw, content_x, y_offset, line, config.MAX_MESSAGE_WIDTH)

            # Draw reactions if present.
            if msg.get("reactions"):
                x_react = content_x
                for reaction in msg["reactions"]:
                    text = f'{reaction["emoji"]} {reaction["count"]}' if reaction["count"] > 1 else reaction["emoji"]
                    text_width = int(config.reaction_font.getlength(text))
                    pill_width = text_width + config.REACTION_PILL_PADDING * 2
                    pill_height = config.REACTION_PILL_HEIGHT
                    
                    draw.rounded_rectangle(
                        (x_react, y_offset, x_react + pill_width, y_offset + pill_height),
                        radius=pill_height // 2,
                        fill=config.REACTION_BG
                    )
                    pilmoji.text(
                        (x_react + config.REACTION_PILL_PADDING, y_offset + 5),
                        text,
                        font=config.reaction_font,
                        fill=config.MESSAGE_COLOR
                    )
                    x_react += pill_width + config.REACTION_SPACING
                y_offset += pill_height + 10

            # Add spacing after each message.
            y_offset += 20

    return canvas

if __name__ == "__main__":
    sample_messages = [
        {
            "author": "Kenzo Tenma",
            "avatar": "assets/profile_pictures/perm/billy.jpeg",
            "role_color": (88, 101, 242),
            "timestamp": "7:48 PM",
            "content": "What's your favorite opening? **I like the one from Monster**.\nIt gives me ~~chills~~ every time I hear it. Check out __this underline__ and *italic* text.\nAlso, join #general and say hi to @everyone!",
            "reactions": [{"emoji": "👍", "count": 1}, {"emoji": "❤️", "count": 3}],
            "edited": True,
            "status": "online",
            "reply_to": {
                "author": "1a2z",
                "avatar": "assets/profile_pictures/perm/billy.jpeg",
                "role_color": (114, 137, 218),
                "content": "Lemme search the name of the opening"
            }
        }
    ]
    messages_img = generate_messages(sample_messages)
    messages_img.save("message.png")
    print("Compact message with markdown formatting saved as message.png")
