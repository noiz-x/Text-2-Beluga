# Text 2 Beluga 🎥💬

Easily convert simple text files into full-fledged Beluga-style Discord conversation videos with a plethora of _text formatting options_, _sound effects_, and _much more customisation_ for ***free*** within ***feconds***!

https://github.com/user-attachments/assets/60af59bf-b32b-4a31-bfa6-6605c86457e2
> Turn on sound to watch the full experience  |  **View on [YouTube](https://www.youtube.com/watch?v=QD5cZ_ZrM9g)**\
> _\*script generated by ChatGPT, ignore the cringe\*_

## Features ✨

- 🖼️ **Automatic Message Rendering** - Generate Discord-style message images from text
- 🔊 **Sound Effect Integration** - Add impact sounds and join notifications
- 🎞️ **Video Compilation** - Create seamless MP4 videos with proper timing
- 📝 **Script Validation** - Built-in script error checking
- 😎 **Advanced Formatting** Supports:
    - **Bold** and *italic* text
    - Emojis are supported
    - Mention other characters (`@Character`)
    - Custom durations per message
    - Create custom characters
    - Roll colours for characters

## Prerequisites 📋

- [Python 3.9+](https://www.python.org/downloads/)
- [FFmpeg](https://ffmpeg.org/download.html) (added to system PATH)
- Required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## Installation & Setup 🛠

1. Clone repository
    ```bash
    git clone https://github.com/Binary-Bytes/Text-2-Beluga.git
    cd Text-2-Beluga
    ```

2. Install dependencies
    ```bash
    pip install -r requirements.txt
    ```

3. Configure character settings 
    - Add profile pictures in `assets/profile_pictures/temp/`
    - Character details in `assets/profile_pictures/characters.json`

## Chat Script Format 📜

#### Script Format

Create a text file (`.txt`) with a format as given below.\
_A sample chat script file (`example_script.txt`) is provided in `assets/example/` directory._

```txt
WELCOME Character$^Duration#!SoundEffect

Character:
Message Text$^Duration#!SoundEffect
Another Message$^Duration
```

#### Syntax Rules

1. **Comments:** Lines starting with `#` are ignored

2. **Join Messages:**
    - `WELCOME Character$^Duration#!SoundEffect`
    - Creates "User joined" image

3. **Character Messages:**
    - Start with `Character:`
    - Subsequent lines are messages with format:
    `Message$^Duration[#!sound]`

4. **Formatting:**
    - Bold: `**text**`
    - Italic: `__text__`
    - Combine: `__**text**__`
    - Mention: `@Character`
    - Emojis: `Emojis are supported in messages`
    - Durations: `$^` followed by duration in seconds (must be present at end of each message line, before sound effect, **mandatory**)
    - Sound Effects: `#!` followed by exact name (must be present at end of each message line, **optional**)

5. **Sound Effects:**
    - Reference files in `assets/sounds/mp3/`
    - Format: `#!sound_name` (at end of message line, optional)

## Running the Program 🚀

1. Prepare your script file

2. Run `scripts/main.py` (command-line interface)
    ```bash
    python scripts/main.py
    ```

3. The following options will be presented:
    - ***Generate Video:*** Generate the chat video
    - ***Validate Script:*** Check for errors in the script file `(will be enhanced)`
    - ***Instructions:*** Read all the instructions for chat file syntax, or listen to all the sound effects available by default... _to add a custom sound effect, add it's `.mp3` version in `assets/sounds/mp3/`_
    - ***Exit:*** Close the program

4. When "`Generate Video`" is selected, it will take a few seconds to generate the chat images in `chat/` directory and compile them into a video with sound effects as `final_video.mp4` in the root directory.

5. The script validator majorly checks for the following errors in chat text file `(will be enhanced)`:
    - Missing duration markers (`$^`)
    - Invalid sound effect references
    - Incorrect syntax
    - Missing character name declaration

## Note Regarding Font 🗒️

The sample video shown above was generated with Discord's own proprietary font (`gg sans`), which is not available for public use. The default font used in this repository is `Whitney`. You can replace this font with any other font of your choice in the `assets/fonts/` directory with their appropriate `bold`, `medium`, `semibold`, and `italic` versions.

To use `gg sans`, download the [`ggsans` folder](https://drive.google.com/drive/folders/1Zm8c2o-bStC7nsAGMXALdMVuCkU1hQFY?usp=drive_link) and add it to the `assets/fonts/` directory. Note that this font is not allowed for public use.

If you do use it, make sure to change the value of `font` variable _(line no. 58)_ in `scripts/generate_chat.py` file to `"ggsans"`.

![https://www.reddit.com/r/discordapp/comments/z9xcyk/comparison_and_download_for_discords_new_font_gg/](https://github.com/user-attachments/assets/9b07ee29-d69e-4ce5-ab0b-903dade6a985)

## TODO ✏️

Refer to the [TODO list](NOTES.md) for upcoming features and improvements.\
A Text-2-Beluga discord bot is my top priority as of now.