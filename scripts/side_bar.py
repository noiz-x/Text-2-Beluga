# scripts/side_bar.py

from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import GoogleEmojiSource 

# Discord’s exact sidebar color scheme
SIDEBAR_BG_COLOR   = (47, 49, 54)   # #2F3136
SEPARATOR_COLOR    = (54, 57, 63)   # #36393F
HIGHLIGHT_COLOR    = (57, 60, 67)   # #393C43
ACTIVE_STRIP_COLOR = (255, 255, 255)

COLOR_CATEGORY  = (114, 116, 125)  # #72767D
COLOR_INACTIVE  = (185, 187, 190)  # #B9BBBE
COLOR_ACTIVE    = (255, 255, 255)  # #FFFFFF

SCREEN_HEIGHT   = 683
SIDEBAR_WIDTH   = 243
FONT_PATH       = "assets/fonts/whitney/medium.ttf"  # Discord uses Whitney
FONT_SIZE       = 14

CATEGORY_SPACING  = 8   # Vertical gap after a category title
CHANNEL_SPACING   = 4   # Additional spacing between channels
INDENT_X          = 16  # Left indent for text
ACTIVE_LEFT_STRIP = 4   # White strip width for the active channel

def generate_sidebar() -> Image.Image:
    # Create the base image canvas with Discord sidebar background color
    canvas = Image.new("RGB", (SIDEBAR_WIDTH, SCREEN_HEIGHT), SIDEBAR_BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    
    # Load the Whitney font. Fall back to default if not found.
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except IOError:
        font = ImageFont.load_default()

    # 1) Draw the Server Icon (centered at the top)
    server_icon_size = 60
    x_center = SIDEBAR_WIDTH // 2
    y_center = 40
    draw.ellipse(
        [
            x_center - server_icon_size // 2,
            y_center - server_icon_size // 2,
            x_center + server_icon_size // 2,
            y_center + server_icon_size // 2
        ],
        fill=(114, 137, 218)  # Discord blurple for the server icon
    )
    # Online status indicator on the lower-right of the server icon
    status_size = 14
    draw.ellipse(
        [
            x_center + server_icon_size // 2 - status_size + 3,
            y_center + server_icon_size // 2 - status_size + 3,
            x_center + server_icon_size // 2 + 3,
            y_center + server_icon_size // 2 + 3
        ],
        fill=(67, 181, 129)  # Discord online green (#43B581)
    )

    # 2) Server Name below the icon (centered)
    server_name = "Whiteroom 5.0"
    bbox = font.getbbox(server_name)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        (x_center - text_w // 2, y_center + server_icon_size // 2 + 8),
        server_name,
        fill=COLOR_ACTIVE,
        font=font
    )

    # Separator below the server name
    sep_top = y_center + server_icon_size // 2 + text_h + 16
    draw.rectangle([0, sep_top, SIDEBAR_WIDTH, sep_top + 2], fill=SEPARATOR_COLOR)

    # 3) Channel List Data (categories and channels)
    # Channel names include Discord-standard symbols and spacing.
    channel_data = [
        (
            "INTRODUCTION \U0001F451",
            [
                ("#booster-perks", False),
                ("#ask-whiteroomers", False)
            ]
        ),
        (
            "MAIN FACILITY \u25BE",  # ▼ indicates a collapsible category
            [
                ("# 🌟 | introduction", False),
                ("# 🌟 | general", False),
                ("# 🌟 | self-development", True),  # Active channel
                ("# 🌟 | fashion", False),
                ("# 🌟 | relationships", False),
                ("# 🌟 | suggestions", False),
                ("# 🌟 | talk-to-koji", False),
                ("# 🤖 | bots", False),
                ("# ✍️ | how-to-write-posts", False),
                ("# 🤝 | community-collaboration", False),
                ("# 🔨 | community-services", False)
            ]
        ),
        (
            "DAILY \u25BE",
            [
                ("\U0001F3C6 qotd", False),
                ("\U0001F3C6 knowledge-of-the-day", False),
                ("\U0001F3C6 what-i-learned-today", False),
            ]
        ),
        (
            "VOICE CHANNELS \u25BE",
            [
                ("commands-bot", False),
                ("Game Night", False),
                ("Voice Lobby 1", False),
                ("Voice Lobby 2", False),
            ]
        )
    ]

    y_offset = sep_top + 10
    # Render each category and its channels
    for category_label, channels in channel_data:
        # Convert category label to uppercase for an exact Discord look
        category_label = category_label.upper()
        # Use Pilmoji to render emojis correctly for the category label
        with Pilmoji(canvas, source=GoogleEmojiSource) as pilmoji:
            pilmoji.text((INDENT_X, y_offset), category_label, COLOR_CATEGORY, font)
        bbox_cat = font.getbbox(category_label)
        cat_h = bbox_cat[3] - bbox_cat[1]
        y_offset += cat_h + CATEGORY_SPACING

        # Render each channel within the category
        for ch_name, is_active in channels:
            bbox_ch = font.getbbox(ch_name)
            ch_h = bbox_ch[3] - bbox_ch[1]

            if is_active:
                # Draw the active channel highlight exactly as Discord does
                draw.rectangle([0, y_offset - 2, SIDEBAR_WIDTH, y_offset + ch_h + 4], fill=HIGHLIGHT_COLOR)
                draw.rectangle([0, y_offset - 2, ACTIVE_LEFT_STRIP, y_offset + ch_h + 4], fill=ACTIVE_STRIP_COLOR)
                text_color = COLOR_ACTIVE
            else:
                text_color = COLOR_INACTIVE

            with Pilmoji(canvas, source=GoogleEmojiSource) as pilmoji:
                pilmoji.text((INDENT_X + 20, y_offset), ch_name, text_color, font)
            y_offset += ch_h + CHANNEL_SPACING + 4

        # Draw a separator after each category to match Discord’s sidebar
        draw.rectangle([0, y_offset, SIDEBAR_WIDTH, y_offset + 2], fill=SEPARATOR_COLOR)
        y_offset += 6

    return canvas

if __name__ == "__main__":
    img = generate_sidebar()
    img.save("side_bar.png")
    print("Sidebar image saved as side_bar.png")
