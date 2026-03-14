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


# ===============================
# FOLDER SETUP
# ===============================

# Path("test_files") creates a Path object pointing to a folder
# named "test_files" in the current directory.
#
# Example structure:
#
# project_folder/
#   renamer.py
#   test_files/
#       The.Office.S02E05.mkv
#       The.Office.S02E06.mkv
#
folder = Path("test_files")


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

        return show_name

    # If we couldn't extract a show name,
    # return a fallback value.
    return "Unknown Show"


# ===============================
# FUNCTION: BUILD FINAL FILENAME
# ===============================

def build_new_filename(show_name: str, episode_code: str, extension: str) -> str:
    """
    Combine show name, episode code and file extension.

    Example:
        show_name = "The Office"
        episode_code = "S02E05"
        extension = ".mkv"

    Result:
        "The Office - S02E05.mkv"
    """

    return f"{show_name} - {episode_code}{extension}"


# ===============================
# MAIN LOOP: PROCESS FILES
# ===============================

# folder.iterdir() loops through everything inside the folder
# (files AND directories).
for file in folder.iterdir():

    # file.is_file() ensures we only process files,
    # not subfolders.
    if not file.is_file():
        continue

    # file.stem returns filename WITHOUT extension.
    #
    # Example:
    # "The.Office.S02E05.mkv"
    #
    # file.stem → "The.Office.S02E05"
    #
    season, episode = get_season_episode(file.stem)

    # If no season/episode was found, skip the file.
    if season is None:
        print(f"{file.name} -> No match found")
        continue

    # Format the episode code
    episode_code = format_episode_code(season, episode)

    # Extract the show name
    show_name = extract_show_name(file.stem)

    # Build the final filename
    new_name = build_new_filename(show_name, episode_code, file.suffix)

    # file.suffix returns the extension
    # Example: ".mkv"
    #
    new_path = file.with_name(new_name)

    # Print preview
    print(f"Original: {file.name}")
    print(f"New name: {new_name}")
    print(f"Rename: {file.name} -> {new_name}")
    print()

    # Uncomment this line to actually rename the file
    # file.rename(new_path)