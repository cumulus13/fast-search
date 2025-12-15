# fsearch - Fast File and Content Search Utility

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)

A blazingly fast, production-ready command-line tool for searching files and content with advanced filtering capabilities.

## 🚀 Features

- **Lightning Fast**: Two optimized search methods (scandir and rglob)
- **Content Search**: Search for text inside files with line number display
- **Smart Filtering**: Include/exclude files by pattern (wildcards supported)
- **Case Control**: Case-sensitive or case-insensitive matching
- **Depth Control**: Limit search depth to avoid deep recursion
- **Safe & Robust**: Handles binary files, permissions errors, and large files gracefully
- **Memory Efficient**: Streaming file reading with line length protection
- **Rich Output**: Colored, formatted output with match highlighting
- **Debug Mode**: Verbose logging for troubleshooting

## 📦 Installation

### Requirements

```bash
pip install make-colors
```

#### Optional

Optional (for enhanced features):

```bash
pip install licface pydebugger richcolorlog
```

### Install Script

```bash
# Clone or download fsearch.py
chmod +x fsearch.py

# Optional: Add to PATH (*nix)
sudo cp fsearch.py /usr/local/bin/fsearch

# Optional: Add to PATH (*windows)
copy /y fsearch.py c:\Windows\System32
```

## 🔧 Usage

### Basic Syntax

```bash
fsearch [OPTIONS] PATTERN
```

### Common Examples

#### 1. Search for files by name

```bash
# Find all Python files in current directory
fsearch "*.py"

# Find files containing "config" in name (depth 3)
fsearch config -d 3

# Case-sensitive search for "README"
fsearch README -C
```

#### 2. Search for content inside files

```bash
# Find "import os" in Python files
fsearch "import os" -f -i "*.py"

# Find "TODO" in all text files
fsearch TODO -f -i "*.txt,*.md"

# Find "function" in JavaScript/TypeScript files (deep search)
fsearch function -f -i "*.js,*.ts,*.jsx,*.tsx" -d 5
```

#### 3. Advanced filtering

```bash
# Search only in Python and shell scripts
fsearch "#!/usr/bin" -f -i "*.py,*.sh"

# Exclude directories, files only
fsearch test -D

# Search in specific directory
fsearch "*.log" -p /var/log -d 2
```

#### 4. Performance optimization

```bash
# Use method 1 (faster, default) for large directories
fsearch pattern -m 1 -d 10

# Use method 2 (Path.rglob) for complex patterns
fsearch pattern -m 2
```

## 📋 Options

### Required Arguments

| Argument | Description |
|----------|-------------|
| `PATTERN` | Pattern to search for (supports wildcards: `*`, `?`) |

### Optional Arguments

| Option | Description | Default |
|--------|-------------|---------|
| `-m, --method {1,2}` | Search method: 1=scandir (faster), 2=rglob | `1` |
| `-c, --case-insensitive` | Enable case-insensitive search | `True` |
| `-C, --case-sensitive` | Enable case-sensitive search | `False` |
| `-d, --deep DEPTH` | Maximum search depth (0 = current dir only) | `1` |
| `-p, --path PATH` | Directory to search in | Current directory |
| `-D, --no-dir` | Exclude directories, search files only | Include dirs |
| `-f, --file` | Search for text inside files | Filename search |
| `-i, --include PATTERNS` | Only include files matching patterns (e.g., `"*.py,*.txt"`) | All files |
| `-e, --export {html,text,csv}` | Export results (not yet implemented) | - |
| `--debug` | Enable debug mode with verbose logging | Disabled |

## 💡 Use Cases

### 1. Find Configuration Files

```bash
# Find all config files
fsearch "*config*" -d 5

# Find YAML/JSON config files
fsearch config -i "*.yaml,*.yml,*.json" -d 3
```

### 2. Code Search

```bash
# Find Python files importing a specific module
fsearch "import requests" -f -i "*.py" -d 10

# Find all TODO comments in code
fsearch "TODO" -f -i "*.py,*.js,*.java,*.go" -d 5

# Find function definitions
fsearch "def " -f -i "*.py" -d 3
```

### 3. Log Analysis

```bash
# Find error messages in logs
fsearch "ERROR" -f -i "*.log" -p /var/log

# Find specific date in logs
fsearch "2025-12-15" -f -i "*.log" -d 2
```

### 4. Documentation Search

```bash
# Find markdown files mentioning "API"
fsearch "API" -f -i "*.md" -d 5

# Find all README files
fsearch "README*" -d 10
```

### 5. Security Auditing

```bash
# Find hardcoded passwords
fsearch "password" -f -i "*.py,*.js,*.java" -d 10 -C

# Find API keys
fsearch "api_key" -f -i "*.py,*.env" -d 5
```

## 🎨 Output Format

### File Search Output

```
FOUND: 3

1. /home/user/project/main.py
2. /home/user/project/utils/helper.py
3. /home/user/project/tests/test_main.py
```

### Content Search Output

```
FOUND: 2

1. /home/user/project/main.py
  15. import os
  16. import sys
  42. from os.path import join

2. /home/user/project/utils/helper.py
  5. import os
```

## ⚙️ Search Methods

### Method 1: scandir (Default)

- **Pros**: Faster for most use cases, lower memory usage
- **Cons**: May be slower for very specific patterns
- **Use when**: General file/content search, large directories

```bash
fsearch pattern -m 1
```

### Method 2: rglob

- **Pros**: Better for complex glob patterns
- **Cons**: Slightly higher memory usage
- **Use when**: Complex wildcard patterns, small to medium directories

```bash
fsearch pattern -m 2
```

## 🛡️ Safety Features

### Binary File Detection

Automatically detects and skips binary files to prevent:
- Memory crashes from reading large binaries
- Garbled output from non-text files
- Performance degradation

### Memory Protection

- **Line length limit**: 10,000 characters per line (configurable)
- **Streaming read**: Files read line-by-line, not all at once
- **Safe encoding**: Handles encoding errors gracefully with `errors='ignore'`

### Permission Handling

- Gracefully skips files/directories with permission errors
- Continues search without crashing
- Logs errors in debug mode

### Input Validation

- Validates path exists and is a directory
- Validates depth is non-negative
- Validates method choice
- Provides clear error messages

## 🐛 Debug Mode

Enable detailed logging and error traces:

```bash
fsearch pattern --debug
```

Debug mode shows:
- File access errors
- Binary files skipped
- Long lines truncated
- Permission denied errors
- Complete stack traces

## 📊 Performance Tips

### 1. Limit Search Depth

```bash
# Bad: Search entire home directory recursively
fsearch pattern -p ~/ -d 100

# Good: Limit depth
fsearch pattern -p ~/ -d 3
```

### 2. Use Include Patterns

```bash
# Bad: Search all files
fsearch "import" -f

# Good: Only search relevant files
fsearch "import" -f -i "*.py"
```

### 3. Start from Specific Directory

```bash
# Bad: Search from root
fsearch pattern -p / -d 10

# Good: Search from specific project
fsearch pattern -p ~/projects/myapp -d 5
```

### 4. Use Files-Only Mode for Content Search

```bash
# Automatically excludes directories
fsearch pattern -f -i "*.py"
```

## 🔒 Security Considerations

### Symlink Handling

- Follows symlinks to files: ✅
- Follows symlinks to directories: ❌ (prevents infinite loops)

### Path Traversal

- Validates base path exists
- Does not follow `..` or absolute paths in patterns
- Safe for untrusted pattern input

### Sensitive Data

When searching for sensitive information (passwords, keys):
- Use `-C` for case-sensitive search to reduce false positives
- Use specific include patterns to limit scope
- Be careful with output redirection

## 📝 Examples by Scenario

### Web Development

```bash
# Find all React components
fsearch "*.jsx" -d 5

# Find API endpoints
fsearch "app.get\|app.post" -f -i "*.js" -d 3

# Find console.log statements
fsearch "console.log" -f -i "*.js,*.jsx,*.ts,*.tsx" -d 5
```

### Python Development

```bash
# Find all test files
fsearch "test_*.py" -d 5

# Find deprecated functions
fsearch "@deprecated" -f -i "*.py" -d 10

# Find all class definitions
fsearch "^class " -f -i "*.py" -d 5
```

### System Administration

```bash
# Find large log files
fsearch "*.log" -p /var/log -d 2

# Find cron jobs
fsearch "cron" -f -p /etc -d 2

# Find systemd service files
fsearch "*.service" -p /etc/systemd -d 3
```

### DevOps

```bash
# Find Dockerfiles
fsearch "Dockerfile*" -d 5

# Find Kubernetes configs
fsearch "*.yaml" -p ./k8s -d 2

# Find CI/CD configs
fsearch ".gitlab-ci.yml\|.github" -d 3
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 👤 Author

**Hadi Cahyadi**
- Email: cumulus13@gmail.com
- GitHub: [@cumulus13](https://github.com/cumulus13)

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/cumulus13)

[![Donate via Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/cumulus13)
 
[Support me on Patreon](https://www.patreon.com/cumulus13)

## 🙏 Acknowledgments

- Built with Python's `os.scandir()` and `pathlib`
- Uses `ctraceback` for enhanced error reporting
- Colorized output with `make_colors` and `rich`

## 📚 Additional Resources

- [Python fnmatch documentation](https://docs.python.org/3/library/fnmatch.html)
- [os.scandir() reference](https://docs.python.org/3/library/os.html#os.scandir)
- [pathlib.Path.rglob() reference](https://docs.python.org/3/library/pathlib.html#pathlib.Path.rglob)

## 🔄 Version History

### v1.0.4 (2025-12-15) - Production Ready
- ✅ Complete rewrite with production-ready code
- ✅ Fixed all critical bugs
- ✅ Added comprehensive error handling
- ✅ Added input validation
- ✅ Memory efficiency improvements
- ✅ Consistent API and data structures
- ✅ Full documentation

### v1.0.0 (Initial)
- Basic file and content search functionality

---

**Need help?** Use `fsearch --help` or open an issue on GitHub.