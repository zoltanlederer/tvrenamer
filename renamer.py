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
    """Return only a clean show name from the folder"""
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


def build_new_filename(official_name, episode_code, episodes_title, style):
    """Return a formatted show name with episode code and title as a filename string, e.g. 'The Office - S02E05 - Title'"""
    
    show_name = official_name # e.g. The Office

    # Create the new file name string (without extension)
    # also check if episode code in the file doesn't exist e.g. The.Office.S99E99.mkv in that case just return the base format, otherwise includes the title
    if style == 'dot':
        base = f'{show_name.replace(" ", ".")}.{episode_code}'
        if episodes_title: 
            return f'{base}.{episodes_title.replace(" ", ".").title()}'
        return base
    elif style == 'space':
        base = f'{show_name} {episode_code}'
        if episodes_title:
            return f'{base} {episodes_title}'
        return base
    elif style == 'dash':
        base = f'{show_name.replace(" ", "-")}-{episode_code}'
        if episodes_title:
            return f'{base}-{episodes_title.replace(" ", "-").title()}'
        return base
    elif style == 'plex':
        base = f'{show_name} - {episode_code}'
        if episodes_title:
            return f'{base} - {episodes_title.title()}'
        return base
    else:
        # fallback in case style is unknown
        base = f'{show_name} - {episode_code}'
        if episodes_title:
            return f'{base} - {episodes_title.title()}'
        return base


def prepare_renames(video_files, episode_groups, all_episodes_title, style, official_name):
    """ Prepare the files to rename in a tuple as old path and new name. Also check for file name conflicts. """
    # episode_groups e.g. {'S02E05': [PosixPath('test_files/The.Office.S02E05.mkv'), PosixPath('test_files/The.Office.S02E05.srt')], 'S02E06': [PosixPath('test_files/The.Office.S02E06.mkv'), PosixPath('test_files/The.Office.S02E06.srt')]}
    
    # Create pairs of files based on which episode code (S02E05) has in the group
    renames = []
    used_names = set() # track used filenames to prevent duplicate names and accidental file overwrites
    # Add all existing files to used_names to prevent overwriting them during rename
    for file in video_files:
        used_names.add(file.name)

    # e.g. episode_code => S02E05
    # e.g. files => [PosixPath('test_files/The.Office.S02E05.mkv'), PosixPath('test_files/The Office - S02E05.mkv')]
    for episode_code, files in episode_groups.items():
        # e.g. filename => test_files/The.Office.S02E05.mkv        
        for filename in files:
            # all_episodes_title.get(episode_code, None) => returns None if episode code not found, instead of crashing with KeyError (instead of => all_episodes_title[episode_code])
            new_name = build_new_filename(official_name, episode_code, all_episodes_title.get(episode_code, None), style) # e.g. The.Office.S02E05.Title
            
            original_name = new_name # store the original file name in case of name conflict
            counter = 2
            
            used_names.discard(filename.name)  # temporarily removes the current file so it doesn't conflict with itself

            # if the new_name exists in the used_names, then run the loop and append a number in brackets, e.g. (2)
            while new_name + filename.suffix in used_names:
                if style == 'dot':
                    new_name = f'{original_name}.({counter})'
                elif style == 'dash':
                    new_name = f'{original_name}-({counter})'
                else:
                    new_name = f'{original_name} ({counter})'
                counter += 1

            used_names.add(new_name + filename.suffix) # include extension to avoid false conflicts between .mkv and .srt
            pair = (filename, new_name + filename.suffix) # creates a tuple e.g. (PosixPath('test_files/...'), 'The.Office.S02E05.title.mkv')
            renames.append(pair)

    print(renames)
    # returns: e.g.  
    # [(PosixPath('test_files/The.Office.S02E05.mkv'), 'The Office - S02E05 - Halloween.mkv'),
    # (PosixPath('test_files/The.Office.S02E05.srt'), 'The Office - S02E05 - Halloween.srt'),
    # (PosixPath('test_files/The.Office.S02E06.mkv'), 'The Office - S02E06 - The Fight.mkv'),
    # (PosixPath('test_files/The.Office.S02E06.srt'), 'The Office - S02E06 - The Fight.srt')]
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


def get_show_detail(show_name):
    """ Fetch TV show ID and name from TVmaze API """
    try:
        show_url = f'https://api.tvmaze.com/singlesearch/shows?q={show_name}'
        show_details = requests.get(show_url).json()
        show_id = show_details['id']
        show_name = show_details['name']        
        return {'id': show_id, 'name': show_name}
    except requests.exceptions.ConnectionError:
        print('No internet connection. Please check your network.')
        sys.exit()
    except requests.exceptions.Timeout:
        print('Request timed out.')
        sys.exit()
    except KeyError:
        print(f'Show "{show_name}" not found on TVmaze.')
        sys.exit()
    except Exception as e:
        print('Something went wrong, please try again.')
        sys.exit()


def get_all_episodes_title(show_id):
    """ Fetch TV show's all episodes title into a dictionary"""

    try:
        episodes_url = f"https://api.tvmaze.com/shows/{show_id}/episodes"
        episodes_details = requests.get(episodes_url).json()
        dictionary_of_episodes = {}

        for episode in episodes_details:
            episode_code = f"S{episode['season']:02}E{episode['number']:02}"
            episode_title = f"{episode['name']}"
            dictionary_of_episodes[episode_code] = episode_title

        return dictionary_of_episodes # e.g. {'S01E01': 'Pilot', 'S01E02': 'Diversity Day'....}
    except requests.exceptions.ConnectionError:
        print('No internet connection. Please check your network.')
        sys.exit()
    except requests.exceptions.Timeout:
        print('Request timed out.')
        sys.exit()
    except KeyError:
        print(f'Could not fetch episodes for show ID {show_id}.')
        sys.exit()
    except Exception as e:
        print('Something went wrong, please try again.')
        sys.exit()


def confirm_show_name(detected_name):
    """ Ask user to confirm or correct the detected show name """

    prompt = (f"Confirm TV Show name: {detected_name}\n"
              "Press Enter to accept, or type a new name\n"
              "('q' to quit): ")
    answer = input(prompt)
    
    if answer == 'q':
        sys.exit("Process cancelled by user.")
    elif answer != '':
        return answer
    else:
        return detected_name
  

def confirm():
    answer = input('Proceed? [y/N]: ').strip().lower()
    if answer in ('y', 'yes'):
        return True
    else:
        print('Process cancelled')
        return False
    

# Get files and groups
video_files = get_media_files(folder, MEDIA_EXTENSIONS)
if len(video_files) <= 0:
    print(f'{folder} folder is empty!')
    sys.exit()
    
episode_groups = group_files(video_files)

# Get show name and fetch episode titles from API
episode_code = get_episode_code(video_files[0].name) # e.g. S02E05
show_name = extract_show_name(video_files[0], episode_code)
show_name_confirmed = confirm_show_name(show_name)
show_detail = get_show_detail(show_name_confirmed) # use confirmed name
official_name = show_detail['name'] # Use the show name from TVmaze API

all_episodes_title = get_all_episodes_title(show_detail['id'])

# Prepare renames with episode titles
renames = prepare_renames(video_files, episode_groups, all_episodes_title, style, official_name)
show_preview(renames)

if confirm():
    result = rename_files(renames, dry_run)
    show_summary(result, dry_run)