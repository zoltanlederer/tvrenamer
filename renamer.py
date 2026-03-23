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

from pathlib import Path
import sys
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--folder', default='test_files')
parser.add_argument('-d', '--dry-run', action='store_true')
args = parser.parse_args()

dry_run = args.dry_run

VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov'}
SUBTITLE_EXTENSIONS = {'.srt', '.sub', '.ass', '.vtt'}
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | SUBTITLE_EXTENSIONS

folder = Path(args.folder)
if not folder.exists():
    print(f'{folder} folder not found!')
    sys.exit()


def get_media_files(folder, extensions):
    """Return a list of video or subtitle file paths from the given folder, ignoring hidden files."""
    video_files = []

    for file in folder.iterdir():
        if file.name.startswith('.'):
            continue  # skip hidden files like .DS_Store on macOS
        if file.suffix.lower() not in extensions:
            continue # skip non media extensions

        video_files.append(file)
    
    return video_files


def get_episode_code(filename):
    """Return the episode code in S02E05 format, or None if not found."""
    match = re.search(r"S\d{2}E\d{2}", filename)
    if match:
        return match.group()
    return None


def rename_episode_groups(episode_groups, folder, dry_run):
    """ Group together the files by their season/episode, including cleaning the file names, then it renames it. If we use the dry_run mode it won't rename it, only print the result instead. """

    # Create the groups
    for file in get_media_files(folder, MEDIA_EXTENSIONS):
        episode_code = get_episode_code(file.name) # episode codes e.g. S02E05

        if episode_code is None:
            continue

        if episode_code not in episode_groups:
            episode_groups[episode_code] = [] # Create a list within the episode_goups dict, e.g. {'S02E05': [PosixPath('test_files/The Office - S02E05.mkv'), PosixPath('test_files/The Office - S02E05.srt')], 'S02E06': [PosixPath('test_files/The Office - S02E06.mkv'), PosixPath('test_files/The Office - S02E06.srt')]}

        episode_groups[episode_code].append(file) # Add file object (file path) to the list
   
    # Rename the files based on which episode code (S02E05) has
    for episode, files in episode_groups.items():
        # episode: S02E05
        # files: list of path e.g. [PosixPath('test_files/The Office - S02E05.mkv'), PosixPath('test_files/The Office - S02E05.srt')]
        print('episode', episode)
        for file in files:
            print(f'- {file.name}')
        
        first_file = files[0] # use the first file's name only, to rename all files within the group

        show_name = first_file.stem # file name without suffix e.g. The Office - S02E05
        show_name = show_name.replace('.', ' ').replace('_', ' ')
        show_name = show_name.split(episode)[0] # keep only the part before the episode code, e.g. "The Office -"
        show_name = show_name.rstrip(' -') # remove the trailing " -", e.g. "The Office -" -> "The Office"
        show_name = show_name.strip() # remove extra space after the name, e.g. "The Office "

        new_name = f'{show_name} - {episode}' # Create the new file name string (without extension)

        # Rename the files with the new string
        for file in files:
            final_name = f'{new_name}{file.suffix}' # e.g. The Office - S02E05.mkv

            if file.name == final_name:
                continue # skip if the file is already correctly named

            new_path = file.with_name(final_name) # Create the full path for the rename, e.g. test_files/The Office - S02E05.mkv

            if not dry_run:                
                file.rename(new_path)
            else:
                print(new_path)


rename_episode_groups({}, folder, dry_run)
