# Modules
from pathlib import Path
import re # regex library

# # Numbers
# season = 2
# episode = 5

# # Strings
# series_name = "The Office"

# # Booleans
# found = True

# print(series_name, "Season", season, "Episode", episode)

# # Lists
# files = ["The.Office.S02E05.mkv", "The.Office.S02E06.mkv"]

# for file in files:
#     print(file)

# # Loops
# for i in range(5):
#     print("Episode", i + 1)

# # Conditionals
# season = 2

# if season == 1:
#     print("First season")
# elif season == 2:
#     print("Second season")
# else:
#     print("Other season")
 
# # Functions
# def episode_label(season, episode):
#     return f"S{season:02}E{episode:02}"

# print(episode_label(2, 5))
# # Output: S02E05

# # Modules /  Reading files in a folder
# # from pathlib import Path
# # import re

#Path to test folder
folder = Path("test_files")

# regex pattern for S01E05 format (case-insensitive)
pattern = re.compile(r"S(\d{2})E(\d{2})", re.IGNORECASE)

# Loop through all files in the folder
for file in folder.iterdir():
    # print("file.name:", file.name)
    match = pattern.search(file.name)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))

        episode_code = f"S{season:02}E{episode:02}"
        extension = file.suffix

        new_name = f"{episode_code}{extension}"

        print("Original", file.name)
        print("New name:", new_name)
        print()

        # print(match.groups())
        # print(f"{file.name} -> Season {season}, Episode {episode}")
        
        # print("FULL MATCH:", match.group(0))
        # print("SEASON:", match.group(1))
        # print("EPISODE:", match.group(2))
        # print("ALL GROUPS:", match.groups())
        # print(file.name, "→", match)
    else:
        print(f"{file.name} -> No match found")

