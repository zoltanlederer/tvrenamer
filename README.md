# TVRenamer

TVRenamer is a Python CLI tool that renames TV show episode files with their season number, episode number, and episode title fetched automatically from the TVmaze API.

You can choose between four filename styles: dot (default), space, dash, and plex. When you run the program, it detects the TV show name from your files and lets you confirm or correct it. Before renaming, a preview table shows exactly how each file will be renamed. After confirming, a summary shows how many files were successfully renamed and any failures.

## Features
- **TVmaze API integration** - Fetches episode titles automatically from TVmaze.

- **File scanning and filtering** - Scans a folder and automatically filters supported video and subtitle files (.mkv, .mp4, .srt, etc.)

- **Episode code detection** - Detects season and episode codes from filenames (e.g. S02E05), including double episodes (e.g. S02E05E06)

- **4 filename styles** - Supports four output styles: dot, space, dash and plex

- **Conflict detection and resolution** - Detects filename conflicts and resolves them automatically by adding a number e.g. (2)

- **Preview table** - Displays the before/after table for the renamed files

- **Show name confirmation** - Asks the user to confirm or correct the detected show name

- **Confirmation step** - Final confirmation after preview before the files are renamed.

- **Success/failure summary** - Displays a summary after renaming showing succeeded and failed files

- **Error handling for API calls** - Handles API errors gracefully with clear error messages

- **Dry-run mode** - Preview changes without actually renaming any files

## Requirements
- Python 3.x
- requests library

## Installation

Clone the repo:
```bash
git clone https://github.com/zoltanlederer/tvrenamer.git
cd tvrenamer
```

Install dependencies:
```bash
pip3 install requests
```

## Usage & Options

Usage:
```bash
renamer.py [-h] [-f FOLDER] [-s {dot,space,dash,plex}] [-d] [-v]
```

Options:
```bash
  -h, --help            show this help message and exit
  -f, --folder FOLDER   add the path of the folder
  -s, --style {dot,space,dash,plex}
                        choose the output filename style: 
                        - dot (default) → The.Office.S02E05.mkv 
                        - space → The Office S02E05.mkv 
                        - dash → The-Office-S02E05.mkv 
                        - plex → The Office - S02E05.mkv
  -d, --dry-run         run the program without renaming the files, perfect for testing
  -v, --verbose         show detailed output for each file processed
```

## Examples
```bash
$ python3 renamer.py -s plex
Confirm TV Show name: The Office
Press Enter to accept, or type a new name
('q' to quit): 
---------------------------------------------------------------
Original Name                     New Name                         
---------------------------------------------------------------
The.Office.S02E06.720p.WEB-DL.mkv The Office - S02E06 - The Fight.mkv
The.Office.S02E06.srt             The Office - S02E06 - The Fight.srt
---------------------------------------------------------------
Total: 2 files | To rename: 2 | No change: 0
---------------------------------------------------------------
Proceed? [y/N]: y
----------------------------------------------------------------------
Summary
----------------------------------------------------------------------
✅ 2 file(s) successfully renamed
❌ 0 file(s) failed
----------------------------------------------------------------------
```

## Credits
Episode data provided by [TVmaze](https://www.tvmaze.com)