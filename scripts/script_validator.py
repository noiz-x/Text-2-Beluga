import os
import sys
import re
import argparse
import json
from PyQt5.QtWidgets import QApplication, QFileDialog

base_dir = os.path.dirname(os.path.abspath(__file__))

# Load character data
with open(f'{base_dir}/{os.pardir}/assets/profile_pictures/characters.json', encoding="utf8") as file:
    characters_dict = json.load(file)

def get_filename():
    """Opens a file dialog and returns the selected filename."""
    app = QApplication(sys.argv)
    options = QFileDialog.Options()
    filename, _ = QFileDialog.getOpenFileName(
        None, "Select Script Text File", "", "Text Files (*.txt);;All Files (*)", options=options
    )
    app.exit()
    return filename

def validate_script_lines(lines):
    errors = []
    valid_statuses = ['online', 'idle', 'dnd', 'offline']
    state = "waiting_for_block"
    current_character = None
    has_typing_indicator = False

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        if line.startswith("STATUS "):
            parts = line.split()
            if len(parts) != 3:
                errors.append(f"Line {idx}: Invalid STATUS format - should be 'STATUS [name] [status]'")
                continue
            _, character, status = parts
            if character not in characters_dict:
                errors.append(f"Line {idx}: Unknown character '{character}' in STATUS command")
            if status not in valid_statuses:
                errors.append(f"Line {idx}: Invalid status '{status}' in STATUS command")
            continue
        
        if line.startswith("WELCOME ") or line.startswith("LEAVE ") or line.startswith("#"):
            continue
            
        if line == "":
            # Only validate empty blocks if they had a typing indicator without messages
            if state == "expecting_messages" and not has_typing_indicator:
                errors.append(f"Line {idx-1}: Empty message block for {current_character}")
            state = "waiting_for_block"
            current_character = None
            has_typing_indicator = False
            continue

        if state == "waiting_for_block":
            if ':' in line:
                # Character declaration line
                if '^:' in line:
                    has_typing_indicator = True
                    name_part = line.split('^:', 1)[0].strip()
                else:
                    has_typing_indicator = False
                    name_part = line.split(':', 1)[0].strip()

                if not name_part:
                    errors.append(f"Line {idx}: Missing character name")
                elif name_part not in characters_dict:
                    errors.append(f"Line {idx}: Character '{name_part}' not found")
                
                current_character = name_part
                state = "expecting_messages" if not has_typing_indicator else "waiting_for_block"
                
        elif state == "expecting_messages":
            if '$embed(' in line:
                if not re.match(r'.*?\$embed\(#?[0-9a-fA-F]{6},\s*.+,\s*.+\)', line):
                    errors.append(f"Line {idx}: Invalid embed format. Expected: $embed(#HEXCOLOR,Title,Description)")
            elif '$^' not in line:
                errors.append(f"Line {idx}: Missing duration separator '$^'")
            else:
                # Validate message duration format
                duration_part = line.split('$^', 1)[1].split('#!')[0].strip()
                try:
                    float(duration_part)
                except ValueError:
                    errors.append(f"Line {idx}: Invalid duration format '{duration_part}'")
                
            state = "waiting_for_block"

    # Final validation for last block
    if state == "expecting_messages" and not has_typing_indicator:
        errors.append(f"Unterminated message block for {current_character} at end of file")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate a script text file for chat generation.")
    parser.add_argument("script_file", nargs="?", help="Path to the script text file. If not provided, a file dialog will open.")
    args = parser.parse_args()

    if args.script_file:
        filename = args.script_file
    else:
        filename = get_filename()

    if not filename or not os.path.isfile(filename):
        print("No valid file selected. Exiting.")
        sys.exit(1)

    with open(filename, encoding="utf8") as f:
        lines = f.read().splitlines()

    errors = validate_script_lines(lines)

    if errors:
        print("Script validation found issues:")
        for error in errors:
            print("  -", error)
    else:
        print("Script validation successful: no problems found.")

if __name__ == '__main__':
    # main()
    print('Please run the main.py script!')