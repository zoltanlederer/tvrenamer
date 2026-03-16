"""
Series Renamer

This script scans a folder containing TV episode files and
renames them into a clean format.

Example:
    The.Office.S02E05.mkv
    ->
    The Office - S02E05.mkv

The script extracts:
- show name
- season number
- episode number

and builds a standardized filename.
"""

# ===============================
# MODULE IMPORTS
# ===============================

# pathlib is a modern Python module for working with file paths.
# It is easier and safer than using older modules like os.path.
# Path represents a file or folder path as an object.
from pathlib import Path

# re is Python's "regular expression" module.
# Regular expressions are powerful patterns used to search text.
# We use them to detect things like S02E05 inside filenames.
import re

# Command-line arguments
import argparse


# -------------------------------
# COMMAND-LINE ARGUMENTS
# -------------------------------
# Example usage:
# Preview renaming in "test_files" folder, dot style:
#   python renamer.py
#   python renamer.py --dry-run
# Actually rename files, dash style:
#   python renamer.py --style dash
# Rename files in a custom folder:
#   python renamer.py --folder /path/to/my/files

parser = argparse.ArgumentParser(
    description="Rename TV series files in a folder to a clean format."
)

# Folder argument (optional, defaults to "test_files")
parser.add_argument(
    "-f", "--folder",
    type=str,
    default="test_files",  # default folder if none provided
    help="Path to the folder containing video files"
)

# Style argument: dash or dot
parser.add_argument(
    "-s", "--style",
    type=str,
    choices=["dash", "dot"],
    default="dot",  # default style
    help="Filename style: dash = 'The Office - S02E06', dot = 'The.Office.S02E06'"
)

# Dry-run argument: preview only
parser.add_argument(
    "-d", "--dry-run",
    action="store_true",  # True if flag is provided, otherwise False
    help="Preview changes without renaming files"
)

# Parse the arguments (reads what the user typed when running the script)
args = parser.parse_args()


# ===============================
# GLOBAL SETTINGS
# ===============================

# Defaults are already handled in parser.add_argument()
# These will always have valid values:
# - folder: either default or user-provided
# - style: either default or user-provided
# - dry_run: True if user specified --dry-run, otherwise False

# Default folder to scan
folder = Path(args.folder)

# Choose the filename style for the renamer
# Options:
#   "dash" → The Office - S02E06.mkv
#   "dot"  → The.Office.S02E06.mkv
style = args.style

# If True → preview only (no files renamed)
# If False → files will actually be renamed
dry_run = args.dry_run

print(f"Folder: {folder}")
print(f"Style: {style}")
print(f"Dry run: {dry_run}\n")


# Supported video and subtitle file types
MEDIA_EXTENSIONS = {
    ".mkv", ".mp4", ".avi", ".mov",
    ".srt", ".sub", ".ass", ".vtt"
}

# ===============================
# REGEX PATTERNS
# ===============================

# This pattern searches for the typical episode format:
#
# S02E05
#
# Explanation:
#
# S        → the letter S
# (\d{2})  → exactly two digits (season number)
# E        → the letter E
# (\d{2})  → exactly two digits (episode number)
#
# Parentheses () create "groups".
# Groups allow us to extract parts of the match.
#
# Example match:
#   S02E05
#
# group(1) → 02
# group(2) → 05
#
pattern = re.compile(r"S(\d{2})E(\d{2})", re.IGNORECASE)

# This pattern extracts the show name before the episode code.
#
# Example filename:
#   The.Office.S02E05
#
# Pattern explanation:
#
# ^          → start of string
# (.*?)      → capture ANY characters (lazy match)
# S\d{2}E\d{2} → season/episode pattern
#
# This means:
# capture everything BEFORE the S02E05 part
#
show_pattern = re.compile(r"^(.*?)S\d{2}E\d{2}", re.IGNORECASE)


# ===============================
# FUNCTION: EXTRACT SEASON + EPISODE
# ===============================

def get_season_episode(filename: str):
    """
    Extract season and episode numbers from a filename.

    Example input:
        "The.Office.S02E05"

    Output:
        (2, 5)

    If no match is found:
        (None, None)
    """

    # pattern.search() scans the string looking for the regex pattern.
    match = pattern.search(filename)

    # If the regex found something, match will contain a Match object.
    if match:

        # match.group(1) returns the FIRST captured group.
        # In our regex: (\d{2}) after S
        # Example:
        # S02E05 → group(1) = "02"
        season = int(match.group(1))

        # match.group(2) returns the SECOND captured group.
        # Example:
        # S02E05 → group(2) = "05"
        episode = int(match.group(2))

        # int() converts the string "02" → number 2
        # This allows us to treat them as real numbers.
        return season, episode

    # If nothing matched, return None values.
    return None, None


# ===============================
# FUNCTION: FORMAT EPISODE CODE
# ===============================

def format_episode_code(season: int, episode: int) -> str:
    """
    Convert season and episode numbers into standard format.

    Example:
        season = 2
        episode = 5

    Output:
        "S02E05"
    """

    # f-strings allow inserting variables into strings.
    #
    # {season:02} means:
    #   - show the number with 2 digits
    #   - add leading zero if needed
    #
    # Example:
    #   2 → 02
    #
    return f"S{season:02}E{episode:02}"


# ===============================
# FUNCTION: EXTRACT SHOW NAME
# ===============================

def extract_show_name(filename: str) -> str:
    """
    Extract the show name from a filename.

    Example input:
        "The.Office.S02E05"

    Output:
        "The Office"
    """

    # Normalize separators first
    filename = filename.replace(".", " ").replace("_", " ")

    match_show = show_pattern.search(filename)

    if match_show:

        # group(1) contains the captured show name portion.
        # Example:
        #
        # "The.Office.S02E05"
        #
        # group(1) → "The.Office."
        #
        show_name = match_show.group(1)

        # Replace dots with spaces
        show_name = show_name.replace(".", " ")

        # Replace underscores with spaces
        show_name = show_name.replace("_", " ")

        # strip() removes spaces from start and end.
        show_name = show_name.strip()

        # Remove trailing separators like "-" or "."
        show_name = show_name.rstrip("-_. ")

        # Convert to Title Case
        show_name = show_name.title()

        return show_name

    # If we couldn't extract a show name,
    # return a fallback value.
    return "Unknown Show"


# ===============================
# FUNCTION: BUILD FINAL FILENAME
# ===============================


def build_new_filename(show_name: str, episode_code: str, extension: str) -> str:
    """
    Combine show name, episode code, and file extension based on the selected style.

    style = "dash"  → The Office - S02E06.mkv
    style = "dot"   → The.Office.S02E06.mkv
    """
    # Dash style
    if style == "dash":
        return f"{show_name} - {episode_code}{extension}"

    # Dot style
    if style == "dot":
        show_name_clean = show_name.replace(" ", ".")
        return f"{show_name_clean}.{episode_code}{extension}"

    # fallback in case style is unknown
    return f"{show_name} - {episode_code}{extension}"


# ===============================
# PREVIEW TABLE AND FINAL CONFIRMATION
# ===============================
#
# This section collects all files that need to be renamed,
# prints a table showing the original and new filenames,
# and optionally asks the user to confirm before actually renaming.
# Features:
#   - Skips hidden files like .DS_Store
#   - Skips unsupported file types
#   - Skips files where the new name already exists
#   - Prints a neat preview table
#   - Dry-run mode shows table only
#   - Real-run mode asks for confirmation before renaming
#

# Create an empty list to store files we plan to rename.
# Each item will be a tuple: (original_name, new_name, file_path, new_path)
files_to_rename = []

# Loop through all items in the target folder
for file in folder.iterdir():

    # Skip anything that is not a file
    if not file.is_file():
        continue

    # Skip hidden files (like .DS_Store on macOS)
    if file.name.startswith("."):
        continue

    # Only process supported video and subtitle files
    if file.suffix.lower() not in MEDIA_EXTENSIONS:
        continue

    # Extract season and episode numbers from the filename
    season, episode = get_season_episode(file.stem)

    # If no season/episode found, skip this file
    if season is None:
        continue

    # Extract show name (normalized, title-cased)
    show_name = extract_show_name(file.stem)

    # Format the episode code, e.g., S02E05
    episode_code = format_episode_code(season, episode)

    # Build the final filename based on chosen style (dash/dot)
    new_name = build_new_filename(show_name, episode_code, file.suffix)

    # Build a Path object for the new file path
    new_path = file.with_name(new_name)

    # Safety check: skip files if the new filename already exists
    if new_path.exists():
        print(f"Skipping (file already exists): {new_path.name}")
        continue

    # Add this file to the list of files to rename
    files_to_rename.append((file.name, new_name, file, new_path))


# SHOW PREVIEW TABLE
# This prints a neat table of original filenames and what they would be renamed to.

if not files_to_rename:
    # If no files to rename, notify the user
    print("No files found to rename.\n")
else:
    # Print table header
    print("\nPreview Table:")
    print(f"{'Original Name':<40} {'New Name':<40}")
    print("-" * 80)

    # Print each file pair (original -> new name)
    for original, new_name, _, _ in files_to_rename:
        print(f"{original:<40} {new_name:<40}")
    print()  # blank line after table


# FINAL ACTION: DRY RUN OR CONFIRMATION

if dry_run:
    # If dry-run, only show the table
    print("[DRY RUN] No files were actually renamed.\n")
else:
    # Ask the user to confirm renaming
    confirm = input("Proceed with renaming these files? [y/N]: ").strip().lower()

    # If the user confirms with 'y', perform the renaming
    if confirm == "y":
        for _, _, file, new_path in files_to_rename:
            print(f"Renaming: {file.name} -> {new_path.name}")
            file.rename(new_path)
        print("\nAll renaming completed.\n")
    else:
        # Any other input cancels the operation
        print("Renaming canceled by user.\n")


# ===============================
# MAIN LOOP: PROCESS FILES
# ===============================

# # folder.iterdir() loops through everything inside the folder
# # (files AND directories).
# for file in folder.iterdir():

#     # file.is_file() ensures we only process files,
#     # not subfolders.
#     if not file.is_file():
#         continue

#     # Ignore hidden files like .DS_Store
#     if file.name.startswith("."):
#         continue

#     # Skip non-video and subtitle files
#     if file.suffix.lower() not in MEDIA_EXTENSIONS:
#         continue

#     # file.stem returns filename WITHOUT extension.
#     #
#     # Example:
#     # "The.Office.S02E05.mkv"
#     #
#     # file.stem → "The.Office.S02E05"
#     #
#     season, episode = get_season_episode(file.stem)

#     # If no season/episode was found, skip the file.
#     if season is None:
#         print(f"{file.name} -> No match found")
#         continue

#     # Format the episode code
#     episode_code = format_episode_code(season, episode)

#     # Extract the show name
#     show_name = extract_show_name(file.stem)

#     # Build the final filename
#     new_name = build_new_filename(show_name, episode_code, file.suffix)

#     # file.suffix returns the extension
#     # Example: ".mkv"
#     #
#     new_path = file.with_name(new_name)

#     # Safety check: do not overwrite existing files
#     if new_path.exists():
#         print(f"Skipping (file already exists): {new_path}")
#         continue

#     # Print preview
#     print(f"Original: {file.name}")
#     print(f"New name: {new_name}")
#     print(f"Rename: {file.name} -> {new_name}")

#     if dry_run:
#         print(f"[DRY RUN] Would rename: {file} -> {new_path}")
#     else:
#         print(f"Renaming: {file.name} -> {new_path}")
#         file.rename(new_path)

#     print()

#     # Uncomment this line to actually rename the file
#     # file.rename(new_path)