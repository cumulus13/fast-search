#!/usr/bin/env python3

# File: fsearch.py
# Author: Hadi Cahyadi <cumulus13@gmail.com>
# Date: 2025-12-15
# Description: Fast file and content search utility
# License: MIT

import os
import sys
HAS_CTRACEBACK=False
try:
    import ctraceback
    HAS_CTRACEBACK=True
except:
    pass
import traceback
import logging

# Debug mode setup
DEBUG_MODE = len(sys.argv) > 1 and any('--debug' == arg for arg in sys.argv)
if DEBUG_MODE:
    print("🐞 Debug mode enabled")
    os.environ["DEBUG"] = "1"
    os.environ['LOGGING'] = "1"
    os.environ.pop('NO_LOGGING', None)
    os.environ['TRACEBACK'] = "1"
    os.environ["LOGGING"] = "1"
    try:
        from pydebugger.debug import debug
    except:
        print("install pydebugger first ! (pip install 'pydebugger')")
        sys.exit(1)
else:
    os.environ['NO_LOGGING'] = "1"

tprint = None  # type: ignore

try:
    from richcolorlog import setup_logging, print_exception as tpring  # type: ignore
    logger = setup_logging('fsearch')
except:
    import logging

    try:
        from .custom_logging import get_logger  # type: ignore
    except ImportError:
        from custom_logging import get_logger  # type: ignore
        
    logger = get_logger('fsearch', level=logging.INFO)

if not tprint:
    def tprint(*args, **kwargs):
        traceback.print_exc(*args, **kwargs)

# import signal
if HAS_CTRACEBACK:
    sys.excepthook = ctraceback.CTraceback  # type: ignore
    from ctraceback.custom_traceback import console
# from rich import print
import argparse
try:
    from licface import CustomRichHelpFormatter
except ImportError:
    CustomRichHelpFormatter = argparse.RawTextHelpFormatter

import fnmatch
from pathlib import Path
# import shutil
from make_colors import make_colors  # type: ignore

# Constants
DEFAULT_CHECK_BYTES = 1024
MAX_LINE_LENGTH = 10000  # Prevent memory issues with very long lines


class SearchError(Exception):
    """Base exception for search errors"""
    pass


def is_binary_file(file_path, num_bytes=DEFAULT_CHECK_BYTES):
    """
    Check if a file is binary by reading the first num_bytes.
    
    Args:
        file_path: Path to file
        num_bytes: Number of bytes to check
        
    Returns:
        bool: True if binary, False if text
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(num_bytes)
            if b'\0' in chunk:
                return True
            # Attempt decoding as text to catch unusual characters
            try:
                chunk.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
    except (IOError, OSError) as e:
        if DEBUG_MODE:
            logger.warning(f"Could not read file: {file_path} - {e}")
        return True

def open_file_safely(file_path):
    if not is_binary_file(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.readlines()
                # console.print("File content:", content)
                return content
        except:
            pass
    # else:
    #     console.print(f"[bold FF00FF]Skipping binary file:[/] [bold #FFFF00]{file_path}[/]")

def read_file_lines(file_path, max_line_length=MAX_LINE_LENGTH):
    """
    Safely read text file lines with memory protection.
    
    Args:
        file_path: Path to file
        max_line_length: Maximum line length to prevent memory issues
        
    Returns:
        list: List of lines or empty list if failed
    """
    if is_binary_file(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = []
            for line_num, line in enumerate(f, 1):
                if len(line) > max_line_length:
                    if DEBUG_MODE:
                        logger.warning(f"Line {line_num} too long in {file_path}, skipping")
                    continue
                lines.append(line)
            return lines
    except (IOError, OSError, UnicodeDecodeError) as e:
        if DEBUG_MODE:
            logger.warning(f"Error reading file {file_path}: {e}")
        return []


def search_in_file(pattern, file_path):
    """
    Search for pattern in file and return matching lines with line numbers.
    
    Args:
        pattern: Text pattern to search for
        file_path: Path to file
        
    Returns:
        list: List of tuples (line_number, line_content) or empty list
    """
    content = read_file_lines(file_path)
    if not content:
        return []
    
    try:
        matches = [(i, line) for i, line in enumerate(content) if pattern in line]
        return matches
    except Exception as e:
        if DEBUG_MODE:
            logger.error(f"Error searching in {file_path}: {e}")
        return []

# # Example usage:
# file_path = "example.txt"  # Replace with your file path
# open_file_safely(file_path)

def parse_include_patterns(include_pattern, case_insensitive=False):
    """
    Parse comma-separated include patterns.
    
    Args:
        include_pattern: String like "*.py,*.txt"
        case_insensitive: Whether to convert to lowercase
        
    Returns:
        list: List of patterns
    """
    if not include_pattern:
        return []
    
    patterns = [p.strip() for p in include_pattern.split(',') if p.strip()]
    if case_insensitive:
        patterns = [p.lower() for p in patterns]
    
    return patterns


def matches_include_pattern(filename, include_patterns, case_insensitive=False):
    """
    Check if filename matches any include pattern.
    
    Args:
        filename: Name of file to check
        include_patterns: List of patterns to match
        case_insensitive: Whether matching is case-insensitive
        
    Returns:
        bool: True if matches or no patterns specified
    """
    if not include_patterns:
        return True
    
    fname = filename.lower() if case_insensitive else filename
    return any(fnmatch.fnmatch(fname, pattern) for pattern in include_patterns)


def fast_find(base_dir, pattern, max_depth, include_dirs=True, 
              case_insensitive=False, search_in_files=False, 
              include_pattern=''):
    """
    Fast search for files or directories matching a pattern.
    
    Args:
        base_dir: Starting directory
        pattern: Pattern to match (supports wildcards)
        max_depth: Maximum depth to search (0 = current dir only)
        include_dirs: Whether to include directories in results
        case_insensitive: If True, match is case-insensitive
        search_in_files: If True, search for pattern inside files
        include_pattern: Only include files matching this pattern (e.g., "*.py,*.txt")
        
    Returns:
        list: List of matches. Format depends on search_in_files:
              - False: ['path1', 'path2', ...]
              - True: [['path1', [(line_num, line_text), ...]], ...]
    """
    # Validate inputs
    if not os.path.exists(base_dir):
        raise SearchError(f"Directory does not exist: {base_dir}")
    
    if not os.path.isdir(base_dir):
        raise SearchError(f"Not a directory: {base_dir}")
    
    if max_depth < 0:
        raise SearchError(f"max_depth must be >= 0, got: {max_depth}")
    
    # Parse include patterns
    include_patterns = parse_include_patterns(include_pattern, case_insensitive)
    if include_patterns:
        console.print(f"[bold cyan]Include patterns:[/] {include_patterns}")
    
    # Setup
    matches = []
    is_wildcard = '*' in pattern or '?' in pattern
    # console.print(f"is_wildcard: {is_wildcard}")
    console.print(f"case_insensitive: {case_insensitive}")
    
    if search_in_files:
        include_dirs = False
    console.print(f"include_dirs: {include_dirs}")
    
    def search(current_dir, current_depth):
        """Recursive search function"""
        if current_depth > max_depth:
            return
        
        try:
            with os.scandir(current_dir) as entries:
                for entry in entries:
                    try:
                        # Skip files not matching include pattern
                        if entry.is_file() and not matches_include_pattern(
                            entry.name, include_patterns, case_insensitive
                        ):
                            continue
                        
                        # Normalize for case-insensitive matching
                        entry_name = entry.name.lower() if case_insensitive else entry.name
                        match_pattern = pattern.lower() if case_insensitive else pattern
                        
                        # Check if entry matches pattern
                        is_match = False
                        if is_wildcard:
                            is_match = fnmatch.fnmatch(entry_name, match_pattern)
                        else:
                            is_match = match_pattern in entry_name
                        
                        # Process matches
                        if is_match and (include_dirs or entry.is_file()):
                            if search_in_files and entry.is_file():
                                found_lines = search_in_file(
                                    match_pattern.replace('*', ''), 
                                    entry.path
                                )
                                if found_lines:
                                    matches.append([entry.path, found_lines])
                            else:
                                matches.append(entry.path)
                        
                        # Search in file content even if filename doesn't match
                        elif search_in_files and entry.is_file():
                            found_lines = search_in_file(
                                match_pattern.replace('*', ''), 
                                entry.path
                            )
                            if found_lines:
                                matches.append([entry.path, found_lines])
                        
                        # Recurse into directories
                        if entry.is_dir(follow_symlinks=False):
                            search(entry.path, current_depth + 1)
                    
                    except (OSError, PermissionError) as e:
                        if DEBUG_MODE:
                            logger.warning(f"Error accessing {entry.path}: {e}")
                        continue
        
        except (OSError, PermissionError) as e:
            if DEBUG_MODE:
                logger.warning(f"Error accessing directory {current_dir}: {e}")
    
    search(base_dir, 0)
    return matches


def find_with_depth(base_dir, pattern, max_depth, include_dirs=True, 
                    case_insensitive=True, search_in_files=False, 
                    include_pattern=''):
    """
    Search using Path.rglob() method.
    
    Args:
        base_dir: Starting directory
        pattern: Pattern to match (supports wildcards)
        max_depth: Maximum depth to search
        include_dirs: Whether to include directories in results
        case_insensitive: If True, match is case-insensitive
        search_in_files: If True, search for pattern inside files
        include_pattern: Only include files matching this pattern
        
    Returns:
        list: List of matches (format same as fast_find)
    """
    # Validate inputs
    if not os.path.exists(base_dir):
        raise SearchError(f"Directory does not exist: {base_dir}")
    
    if max_depth < 0:
        raise SearchError(f"max_depth must be >= 0, got: {max_depth}")
    
    if search_in_files:
        include_dirs = False
    console.print(f"include_dirs: {include_dirs}")
    
    # Parse include patterns
    include_patterns = parse_include_patterns(include_pattern, case_insensitive)
    if include_patterns:
        console.print(f"[bold cyan]Include patterns:[/] {include_patterns}")
    
    base = Path(base_dir)
    matches = []
    is_wildcard = '*' in pattern or '?' in pattern
    match_pattern = pattern.lower() if case_insensitive else pattern
    
    try:
        for p in base.rglob("*"):
            try:
                relative_depth = len(p.relative_to(base).parts)
                if relative_depth > max_depth:
                    continue
                
                # Skip files not matching include pattern
                if p.is_file() and not matches_include_pattern(
                    p.name, include_patterns, case_insensitive
                ):
                    continue
                
                name_to_match = p.name.lower() if case_insensitive else p.name
                
                # Check if matches pattern
                is_match = False
                if is_wildcard:
                    is_match = fnmatch.fnmatch(name_to_match, match_pattern)
                else:
                    is_match = match_pattern in name_to_match
                
                # Process matches
                if is_match and (include_dirs or p.is_file()):
                    if search_in_files and p.is_file():
                        found_lines = search_in_file(
                            match_pattern.replace('*', ''), 
                            str(p.resolve())
                        )
                        if found_lines:
                            matches.append([str(p.resolve()), found_lines])
                    else:
                        matches.append(str(p.resolve()))
                
                # Search in file content even if filename doesn't match
                elif search_in_files and p.is_file():
                    found_lines = search_in_file(
                        match_pattern.replace('*', ''), 
                        str(p.resolve())
                    )
                    if found_lines:
                        matches.append([str(p.resolve()), found_lines])
            
            except (OSError, PermissionError) as e:
                if DEBUG_MODE:
                    logger.warning(f"Error accessing {p}: {e}")
                continue
    
    except Exception as e:
        if DEBUG_MODE:
            logger.error(f"Error during search: {e}")
    
    return matches


def format_output(data, search_in_files=False):
    """
    Format and print search results.
    
    Args:
        data: Search results
        search_in_files: Whether results include file content
    """
    if not data:
        console.print("\n[yellow]No results found[/]\n")
        return
    
    console.print(f"\n[white on red]FOUND:[/] [black on #00FFFF]{len(data)}[/]\n")
    
    zfill = len(str(len(data)))
    for index, item in enumerate(data, 1):
        if DEBUG_MODE:
            debug(index=index, item=item)
        
        if search_in_files and isinstance(item, (list, tuple)) and len(item) >= 2:
            # Format: [filepath, [(line_num, line_text), ...]]
            filepath = item[0]
            console.print(f"[bold #FFAAFF]{str(index).zfill(zfill)}[/]. [bold #FFFF00]{filepath}[/]")
            
            matches = item[1]
            for line_num, line_text in matches:
                console.print(f"  [white on red]{line_num + 1}[/]. [bold red]", end='')
                print(make_colors(line_text.rstrip(), 'lc'))
        else:
            # Simple filepath
            console.print(f"[bold #FFAAFF]{str(index).zfill(zfill)}[/]. [bold #FFFF00]{item}[/]")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        formatter_class=CustomRichHelpFormatter, 
        prog='fsearch',
        description='Fast file and content search utility'
    )
    
    parser.add_argument('SEARCH', help="Pattern to search for")
    parser.add_argument('-m', '--method', type=int, choices=[1, 2], default=1,
                        help='Search method: 1=scandir (faster), 2=rglob')
    parser.add_argument('-c', '--case-insensitive', action='store_true', default=True,
                        help='Enable case-insensitive search (default: True)')
    parser.add_argument('-C', '--case-sensitive', action='store_true',
                        help='Enable case-sensitive search')
    parser.add_argument('-d', '--deep', type=int, default=1,
                        help='Maximum search depth (default: 1)')
    parser.add_argument('-p', '--path', default=str(Path.cwd()),
                        help=f'Search directory (default: current directory)')
    parser.add_argument('-D', '--no-dir', action='store_true',
                        help='Exclude directories from results (files only)')
    parser.add_argument('-e', '--export', choices=['html', 'text', 'csv'],
                        help='Export results to format (not implemented)')
    parser.add_argument('-f', '--file', action='store_true',
                        help='Search for text inside files')
    parser.add_argument('-i', '--include', default='',
                        help='Only include files matching pattern (e.g., "*.py,*.txt")')
    
    if len(sys.argv) == 1:
        parser.print_help()
        return 0
    
    args = parser.parse_args()
    
    # Handle case sensitivity flags
    case_insensitive = args.case_insensitive and not args.case_sensitive
    
    # Validate depth
    if args.deep < 0:
        console.print("[bold red]Error:[/] --deep must be >= 0")
        return 1
    
    # Validate path
    if not os.path.exists(args.path):
        console.print(f"[bold red]Error:[/] Path does not exist: {args.path}")
        return 1
    
    if not os.path.isdir(args.path):
        console.print(f"[bold red]Error:[/] Not a directory: {args.path}")
        return 1
    
    try:
        # Perform search
        search_func = fast_find if args.method == 1 else find_with_depth
        
        data = search_func(
            base_dir=args.path,
            pattern=args.SEARCH,
            max_depth=args.deep,
            include_dirs=not args.no_dir,
            case_insensitive=case_insensitive,
            search_in_files=args.file,
            include_pattern=args.include
        )
        
        # Display results
        format_output(data, search_in_files=args.file)
        
        return 0
    
    except SearchError as e:
        console.print(f"[bold red]Search Error:[/] {e}")
        return 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Search interrupted by user[/]")
        return 130
    except Exception as e:
        console.print(f"[bold red]Unexpected Error:[/] {e}")
        if DEBUG_MODE:
            tprint(e)
        return 1

# Example usage
# results = fast_find("/path/to/search", "mydir*", 2, include_dirs=False)
# console.print("Matched results:", results)

if __name__ == '__main__':
    sys.exit(main())
