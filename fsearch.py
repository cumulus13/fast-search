import os
import sys
import ctraceback
sys.excepthook = ctraceback.CTraceback

from rich import print
import argparse
import fnmatch
from pathlib import Path

def is_binary_file(file_path, num_bytes=1024):
    try:
        with open(file_path, 'rb') as file:
            chunk = file.read(num_bytes)
            if b'\0' in chunk:  # Check for null bytes, often present in binary files
                return True
            # Attempt decoding as text to catch unusual characters
            try:
                chunk.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
    except IOError:
        print(f"[white on red blink]Could not read file:[/] [bold #FFFF00]{file_path}[/]")
        return True  # Treat unreadable files as binary for safety

def open_file_safely(file_path):
    if not is_binary_file(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.readlines()
                # print("File content:", content)
                return content
        except:
            pass
    # else:
    #     print(f"[bold FF00FF]Skipping binary file:[/] [bold #FFFF00]{file_path}[/]")

    return ''

def search_in_file(pattern, file_path):
    content = open_file_safely(file_path)
    if content:
        try:
            f = list(filter(lambda k: pattern in k[1], list(enumerate(content))))
            return f
        except:
            ctraceback.CTraceback(*sys.exc_info())
    return ''

# # Example usage:
# file_path = "example.txt"  # Replace with your file path
# open_file_safely(file_path)


def fast_find(base_dir, pattern, max_depth, include_dirs=True, case_insensitive=False, infile = False, ext = []):
    """
    Fast search for files or directories matching a pattern with or without '*' wildcard.
    
    :param base_dir: Starting directory.
    :param pattern: Pattern to match (e.g., "*.txt", "mydir*", or "myfile").
    :param max_depth: Maximum depth to search.
    :param include_dirs: Whether to include directories in the search results.
    :param case_insensitive: If True, match is case-insensitive.
    :param file: If True then find text/string inside file
    :return: List of matched paths.
    """
    
    if isinstance(ext, str or bytes): ext = [ext.decode() if hasattr(ext, 'decode') else ext]

    matches = []
    is_wildcard = '*' in pattern or '?' in pattern
    # print(f"is_wildcard: {is_wildcard}")
    print(f"case_insensitive: {case_insensitive}")

    if infile: include_dirs = False
    print(f"include_dirs: {include_dirs}")
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
                            if infile:
                                f = search_in_file(match_pattern.replace('*',''), entry.path)
                                if f: matches.append([entry.path, f])
                            else:        
                                matches.append(entry.path)
                else:
                    if entry_name == match_pattern or match_pattern in entry_name:
                        if include_dirs or entry.is_file():
                            matches.append(entry.path)
                    elif entry.is_file() and infile:
                        if ext and list(filter(lambda k: os.path.splitext(entry.path)[-1].lower() in k, ext)):
                            # print(f"entry_name: {entry_name}")
                            f = search_in_file(match_pattern.replace('*',''), entry.path)
                            if f: matches.append([entry.path, f])
                        else:
                            # print(f"entry_name: {entry_name}")
                            f = search_in_file(match_pattern.replace('*',''), entry.path)
                            if f: matches.append([entry.path, f])
                            
                # Recurse into directories
                if entry.is_dir(follow_symlinks=False):
                    search(entry.path, current_depth + 1)

    search(base_dir, 0)
    return matches

def find_with_depth(base_dir, pattern, max_depth, include_dirs=True, case_insensitive=True, infile = False):
    """
    Search for files or directories matching a pattern with or without '*' wildcard.
    
    :param base_dir: Starting directory.
    :param pattern: Pattern to match (e.g., "*.txt", "mydir*", or "myfile").
    :param max_depth: Maximum depth to search.
    :param include_dirs: Whether to include directories in the search results.
    :param case_insensitive: If True, match is case-insensitive.
    :return: List of matched paths.
    """
    if infile: include_dirs = False
    print(f"include_dirs: {include_dirs}")
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
                        if infile:
                            f = search_in_file(match_pattern.replace('*',''), str(p.resolve()))
                            matches.append([str(p.resolve())], f)
                        else:        
                            matches.append(p)
            else:
                if name_to_match == match_pattern or match_pattern in name_to_match:
                    if include_dirs or p.is_file():
                        if infile:
                            f = search_in_file(pattern.replace('*',''), str(p.resolve()))
                            if f: matches.append([str(p.resolve())], f)
                        else:        
                            matches.append(p.resolve())
                    

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
    parser.add_argument('-f', '--file', help = 'find text inside file', action = 'store_true')

    if len(sys.argv) == 1:
        parser.print_help()
    else:
        args = parser.parse_args()
        data = []
        if args.method == 1:
            data = fast_find(args.path, args.SEARCH, args.deep, args.dir, args.case_sensitive, args.file)
            
        elif args.method == 2:
            data = find_with_depth(args.path, args.SEARCH, args.deep, args.dir, args.case_sensitive, args.file)
        
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