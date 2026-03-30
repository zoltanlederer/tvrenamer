"""
TVRenamer

This script scans a selected folder containing TV episode files and renames them into a clean, standardized format, and with API integration automatically adds the correct episode title.
The selected format styles can be dot, space, dash, and plex style.

Example:
space → The Office S02E05.mkv
dot → The.Office.S02E05.mkv
dash → The-Office-S02E05.mkv
plex → The Office - S02E05.mkv
"""

from pathlib import Path
import sys
import re
import argparse
import requests

parser = argparse.ArgumentParser(description='The program scans a folder containing TV episode files and renames them into a clean format including the episode titles.')
parser.add_argument('-f', '--folder', default='test_files', help='add the path of the folder')
parser.add_argument('-s', '--style', default='dot', choices=['dot', 'space', 'dash', 'plex'], help='choose the output filename style: dot (default) → The.Office.S02E05.mkv | space → The Office S02E05.mkv | dash → The-Office-S02E05.mkv | plex → The Office - S02E05.mkv ')
parser.add_argument('-d', '--dry-run', action='store_true', help='run the program without renaming the files, perfect for testing')
parser.add_argument('-v', '--verbose', action='store_true', help='show detailed output for each file processed')
args = parser.parse_args()

style = args.style
dry_run = args.dry_run
verbose = args.verbose

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
    
    match = re.search(r"S\d{2}E\d{2}-?(E\d{2})?", filename, re.IGNORECASE)    
    if match:
        raw = match.group().replace('-', '') # always remove dash S02E05E06
        # if it has a second episode (length > 6)
        if len(raw) > 6: # more than just "S02E05"
            return (raw[:6] + '-' + raw[6:]).upper() # e.g. "S02E05-E06"
        else:
            return raw.upper() # e.g. "S02E05"
    return None


def group_files(video_files):
    """Group media files by their episode code and return a dictionary."""
    
    episode_groups = {}

    # Create the groups
    for file in video_files:
        episode_code = get_episode_code(file.name) # episode codes e.g. S02E05

        if episode_code is None:
            continue

        if episode_code not in episode_groups:
            episode_groups[episode_code] = [] # Create a list within the episode_groups dict, e.g. {'S02E05': [PosixPath('test_files/The Office - S02E05.mkv'), PosixPath('test_files/The Office - S02E05.srt')], 'S02E06': [PosixPath('test_files/The Office - S02E06.mkv'), PosixPath('test_files/The Office - S02E06.srt')]}

        episode_groups[episode_code].append(file) # Add file object (file path) to the list
    
    return episode_groups # e.g. {'S02E05': [PosixPath('test_files/The Office - S02E05.mkv'), PosixPath('test_files/The Office - S02E05.srt')], 'S02E06': [PosixPath('test_files/The Office - S02E06.mkv'), PosixPath('test_files/The Office - S02E06.srt')]}


def extract_show_name(filename, episode_code):
    """Return only a clean show name"""
    # episode_code: S02E05
    # filename: Path object e.g. PosixPath('test_files/The.Office.S02E06.720p.WEB-DL.mkv')

    episode_code_no_dash = episode_code.replace('-', '')  # remove dash: S02E09-E10 -> S02E09E10
    episode_code_dash_as_space = episode_code.replace('-', ' ')  # dash to space: S02E09-E10 -> S02E09 E10

    # Clean the show name
    show_name = filename.stem # file name without suffix e.g. The.Office.S02E06.720p.WEB-DL
    show_name = show_name.upper() # convert to uppercase
    show_name = show_name.replace('.', ' ').replace('_', ' ').replace('-', ' ') # e.g. The Office S02E06 720p WEB DL
    # keep only the part before the episode code, e.g. "The Office "
    if episode_code_no_dash in show_name:
        show_name = show_name.split(episode_code_no_dash)[0]
    elif episode_code_dash_as_space in show_name:
        show_name = show_name.split(episode_code_dash_as_space)[0]
    show_name = show_name.strip() # remove leading and trailing spaces "The Office"
    show_name = show_name.title()  # convert to title case

    return show_name #The Office


def build_new_filename(filename, episode_code, style):
    """Return a clean show name and episode code as a filename string, e.g. 'The Office - S02E05'"""
   
    show_name = extract_show_name(filename, episode_code)

    # Create the new file name string (without extension)
    if style == 'dot':
        return f'{show_name.replace(" ", ".")}.{episode_code}'
    elif style == 'space':
        return f'{show_name} {episode_code}'
    elif style == 'dash':
        return f'{show_name.replace(" ", "-")}-{episode_code}'
    elif style == 'plex':
        return f'{show_name} - {episode_code}'
    else:
        # fallback in case style is unknown
        return f'{show_name} - {episode_code}'


def rename_files(renames, dry_run):
    """ Rename files based on prepared (old_path, new_name) pairs. If dry_run is True, only simulate the renaming without modifying files. """
    
    result = { "succeeded": [], "failed": [] } #{'succeeded': ['The Office - S02E05', ''The Office - S02E06'], 'failed': ['The Office - S02E07']}
    # Rename the files based on the prepared pairs
    for old_name, new_name in renames:
        # Rename the files with the new string
        if old_name.name == new_name:
            continue # skip if the file is already correctly named

        new_path = old_name.with_name(new_name) # Create the full path for the rename, e.g. test_files/The Office - S02E05.mkv
        
        if not dry_run:
            try:  
                old_name.rename(new_path)
                result["succeeded"].append(new_name)
            except Exception as e:
                result["failed"].append(f"{old_name.name} -> {new_name}")
        else:
            result["succeeded"].append(new_name)
    
    return result


def prepare_renames(video_files, episode_groups, style):
    """ Prepare the files to rename in a tuple as old path and new name. Also check for file name conflicts. """

    # episode_groups e.g. {'S02E05': [PosixPath('test_files/The.Office.S02E05.mkv'), PosixPath('test_files/The.Office.S02E05.srt')], 'S02E06': [PosixPath('test_files/The.Office.S02E06.mkv'), PosixPath('test_files/The.Office.S02E06.srt')]}
    # Create pairs of files based on which episode code (S02E05) has in the group
    renames = []
    used_names = set() # track used filenames to prevent duplicate names and accidental file overwrites

    # Add all existing files to used_names to prevent overwriting them during rename
    for file in video_files:
        used_names.add(file.name)

    for episode, files in episode_groups.items():
        for file in files:
            new_name = build_new_filename(file, episode, style) # e.g. The.Office.S02E05

            original_name = new_name # store the original file name in case of name conflict
            counter = 2
            
            used_names.discard(file.name)  # temporarily removes the current file so it doesn't conflict with itself

            # if the new_name exists in the used_names, then run the loop and append a number in brackets, e.g. (2)
            while new_name + file.suffix in used_names:
                if style == 'dot':
                    new_name = f'{original_name}.({counter})'
                elif style == 'dash':
                    new_name = f'{original_name}-({counter})'
                else:
                    new_name = f'{original_name} ({counter})'
                counter += 1

            used_names.add(new_name + file.suffix) # include extension to avoid false conflicts between .mkv and .srt
            pair = (file, new_name + file.suffix) # creates a tuple e.g. (PosixPath('test_files/...'), 'The.Office.S02E05.mkv')
            renames.append(pair)

    # returns: e.g.  
    # [(PosixPath('test_files/The.Office.S02E05.mkv'), 'The Office - S02E05'),
    # (PosixPath('test_files/The.Office.S02E05.srt'), 'The Office - S02E05'),
    # (PosixPath('test_files/The.Office.S02E06.mkv'), 'The Office - S02E06'),
    # (PosixPath('test_files/The.Office.S02E06.srt'), 'The Office - S02E06')]
    return renames


def show_preview(renames):
    """ Display the before/after table for the renamed files """

    sorted_renames = sorted(renames, key=lambda x: x[0].name) # sort alphabetically for easier reading
    unchanged = 0
    max_width = max(len(old_name.name) for old_name, _ in sorted_renames) # calculate the longest filename dynamically and use that as the column width
    print("-" * (max_width + 30))
    print(f"{'Original Name':<{max_width}} {'New Name':<{max_width}}")
    print("-" * (max_width + 30))
    for old_name, new_name in sorted_renames:
        if old_name.name == new_name:
            print(f'{old_name.name:<{max_width}} {"(no change)":<{max_width}}')
            unchanged += 1
        else:
            print(f'{old_name.name:<{max_width}} {new_name:<{max_width}}')
    print("-" * (max_width + 30))
    print(f"Total: {len(sorted_renames)} files | To rename: {len(sorted_renames)-unchanged} | No change: {unchanged}")
    print("-" * (max_width + 30))


def show_summary(result, dry_run):
    """ Display the result after renaming the files """

    sorted_result = sorted(result['failed']) # sort alphabetically for easier reading
    print("-" * 70)
    print("Summary")
    print("-" * 70)
    if not dry_run:
        print(f"✅ {len(result['succeeded'])} file(s) successfully renamed")
    else:
        print(f"✅ {len(result['succeeded'])} file(s) would be renamed")

    if result['failed']:    
        print(f"❌ {len(sorted_result)} file(s) failed")
        for file in sorted_result:
            print(f"   • {file}")
    else:
        print(f"❌ 0 file(s) failed")
    print("-" * 70)


def confirm():
    answer = input('Proceed? [y/N]: ').strip().lower()
    if answer in ('y', 'yes'):
        return True
    else:
        print('Process cancelled')
        return False


def extract_season_episode_numbers(episode_code):
    season = episode_code[1:3]
    episode = episode_code[4:6]

    return {'season': season, 'episode': episode}


# def get_show_name(renames):
#     episode_code = get_episode_code(renames[0][1])
#     # remove the extension (from right split where has a dot, then replace episode code, then remove the last character)
#     get_show_name = renames[0][1].rsplit('.',1)[0].replace(episode_code, '')[:-1]
#     return (get_show_name)


def get_show_id(show_name):
    """ Fetch TV show ID from TVmaze API """
    show_url = f'https://api.tvmaze.com/singlesearch/shows?q={show_name}'
    show_details = requests.get(show_url).json()
    show_id = show_details['id']
    return show_id

video_files = get_media_files(folder, MEDIA_EXTENSIONS)
episode_groups = group_files(video_files)
renames = prepare_renames(video_files, episode_groups, style)
show_preview(renames)


# show_name = get_show_name(renames)
# get_show_id(show_name)

if confirm():
    old_path, new_name = renames[0]    
    episode_code = get_episode_code(new_name)
    show_name = extract_show_name(old_path, episode_code) # e.g. The Office (old_path => PosixPath('test_files/The-Office-S02E05.mkv'), episode_code => S02E05)
    show_id = get_show_id(show_name)

    # extract_episode_code = extract_season_episode_numbers(episode_code)
    result = rename_files(renames, dry_run)
    show_summary(result, dry_run)

# code = extract_season_episode_numbers("S02E05")
# print(code['season'])