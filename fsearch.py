import os
import sys
import ctraceback
sys.excepthook = ctraceback.CTraceback

from rich import print
import argparse
import fnmatch
from pathlib import Path

def fast_find(base_dir, pattern, max_depth, include_dirs=True, case_insensitive=False):
    """
    Fast search for files or directories matching a pattern with or without '*' wildcard.
    
    :param base_dir: Starting directory.
    :param pattern: Pattern to match (e.g., "*.txt", "mydir*", or "myfile").
    :param max_depth: Maximum depth to search.
    :param include_dirs: Whether to include directories in the search results.
    :param case_insensitive: If True, match is case-insensitive.
    :return: List of matched paths.
    """
    matches = []
    is_wildcard = '*' in pattern or '?' in pattern
    # print(f"is_wildcard: {is_wildcard}")
    print(f"case_insensitive: {case_insensitive}")

    def search(current_dir, current_depth):
        if current_depth > max_depth:
            return

        with os.scandir(current_dir) as entries:
            for entry in entries:
                # Normalize names for case-insensitive matching
                entry_name = entry.name.lower() if case_insensitive else entry.name
                match_pattern = pattern.lower() if case_insensitive else pattern

                # Match based on wildcard or exact name
                if is_wildcard:
                    if fnmatch.fnmatch(entry_name, match_pattern):
                        if include_dirs or entry.is_file():
                            matches.append(entry.path)
                else:
                    if entry_name == match_pattern or match_pattern in entry_name:
                        if include_dirs or entry.is_file():
                            matches.append(entry.path)

                # Recurse into directories
                if entry.is_dir(follow_symlinks=False):
                    search(entry.path, current_depth + 1)

    search(base_dir, 0)
    return matches

def find_with_depth(base_dir, pattern, max_depth, include_dirs=True, case_insensitive=True):
    """
    Search for files or directories matching a pattern with or without '*' wildcard.
    
    :param base_dir: Starting directory.
    :param pattern: Pattern to match (e.g., "*.txt", "mydir*", or "myfile").
    :param max_depth: Maximum depth to search.
    :param include_dirs: Whether to include directories in the search results.
    :param case_insensitive: If True, match is case-insensitive.
    :return: List of matched paths.
    """
    base = Path(base_dir)
    matches = []
    is_wildcard = '*' in pattern or '?' in pattern
    match_pattern = pattern.lower() if case_insensitive else pattern

    for p in base.rglob("*"):
        relative_depth = len(p.relative_to(base).parts)
        if relative_depth <= max_depth:
            name_to_match = p.name.lower() if case_insensitive else p.name

            # Match based on wildcard or exact name
            if is_wildcard:
                if fnmatch.fnmatch(name_to_match, match_pattern):
                    if include_dirs or p.is_file():
                        matches.append(p)
            else:
                if name_to_match == match_pattern or match_pattern in name_to_match:
                    if include_dirs or p.is_file():
                        matches.append(p)

    return matches

def usage():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('SEARCH', help = "What you want search to", action = 'store')
    parser.add_argument('-m', '--method', action = 'store', help= 'Method [1,2] default is "1"', default=1, type = int)
    parser.add_argument('-c', '--case-sensitive', action = 'store_true', help = "Search with case sensitive pattern")
    parser.add_argument('-d', '--deep', help = 'How deep you want to search', action = 'store', type = int, default = 1)
    parser.add_argument('-p', '--path', help = f'Where you want to search to, default is {os.getcwd()}', default = Path.cwd().__str__(), action = 'store')
    parser.add_argument('-D', '--dir', help = 'Search with directory too', action = 'store_true')
    parser.add_argument('-e', '--export', help = 'Export to [html,text,csv]', action = 'store')

    if len(sys.argv) == 1:
        parser.print_help()
    else:
        args = parser.parse_args()
        data = []
        if args.method == 1:
            data = fast_find(args.path, args.SEARCH, args.deep, args.dir, args.case_sensitive)
            
        elif args.method == 2:
            data = find_with_depth(args.path, args.SEARCH, args.deep, args.dir, args.case_sensitive)
        
        if data:
            print(f"\n[white on red]FOUNDS:[/] [black on #00FFFF]{len(data)}[/]\n")
            
            zfill = len(str(len(data)))
            for index, item in enumerate(data):
                print(f"[bold #FFAAFF]{str(index + 1).zfill(zfill)}[/]. [bold #FFFF00]{item}[/]")

# Example usage
# results = fast_find("/path/to/search", "mydir*", 2, include_dirs=False)
# print("Matched results:", results)

if __name__ == '__main__':
    usage()