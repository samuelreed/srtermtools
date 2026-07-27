# AI Agent Instructions for srtermtools

## Project Overview
`srtermtools` is a collection of **standalone, independent** command-line utilities designed for shell rc file integration (`.zshrc`, `.bashrc`). Each tool is a **self-contained Python 3 script** providing lightweight status checks, reminders, and monitoring. Key design principle: **silent by default** unless thresholds are met, optimized for non-intrusive shell startup.

## Architecture Patterns

### CLI Tool Structure
All tools follow this **strict, consistent pattern**:

```python
#!/usr/bin/env python3
"""
Usage:
    toolname.py <command> [options]
"""
from docopt import docopt

class ToolClass(object):
    # Core logic encapsulated in class
    pass

if __name__ == "__main__":
    args = docopt(__doc__, version="0.1")
    # Process args and run
```

**Critical elements:**
- **Shebang**: `#!/usr/bin/env python3` - enables direct execution (`./tool.py`)
- **docopt**: Usage string in module docstring is the **source of truth** for CLI parsing
- **Class-based**: Logic isolated in classes (`SiteCheck`, `AQIChecker`, `OldCal`)
- **Main guard**: Required for script execution
- **Type hints**: Functions use `typing` annotations (`Tuple[str, str]`, `Optional[int]`)

### Configuration Management
- **INI files in home directory**: `~/.aqi.ini` (see `example.aqi.ini`)
- **Format**: Standard `configparser` format with `[DEFAULT]` section
- **Security**: Files validated with `0o600` permissions for API keys
- **Loading pattern**: Tools load config, fall back to command-line args, validate both

Example from `aqicheck.py`:
```python
config_path = Path.home() / ".aqi.ini"
config = configparser.ConfigParser()
config.read(config_path)
api_key = config['DEFAULT']['api_key']
```

### Error Handling & User Experience
- **Colored output**: `termcolor` for status (`green`=good, `yellow`=warning, `red`=error, `magenta`=critical)
- **stderr for errors**: `print(..., file=sys.stderr)` for all error messages
- **Exit codes**: Non-zero on failures (`sys.exit(1)`)
- **Graceful degradation**: Network errors handled with user-friendly messages, not stack traces
- **Silent success pattern**: Tools like `aqicheck.py --USG` produce **no output** unless threshold exceeded

**Silent by default examples:**
```bash
# AQI is good (35) - NO output when using threshold flag
$ aqicheck.py 94105 --USG
$

# AQI is unhealthy (165) - SHOWS output because ≥ USG threshold (101)
$ aqicheck.py 90210 --USG
AQI 90210: PM2.5=165 (Unhealthy), Ozone=45 (Good)

# Without threshold flag - ALWAYS shows output
$ aqicheck.py 94105
AQI 94105: PM2.5=35 (Good), Ozone=28 (Good)
```

## Tool-Specific Patterns

### Date Handling (`daycounter.py`)
- **Date arithmetic**: Uses `python-dateutil.relativedelta` for **accurate** year/month/day calculations (not simple day counts)
- **ISO dates only**: `YYYY-MM-DD` format enforced via `datetime.strptime("%Y-%m-%d")`
- **Human-readable mode**: `-h` flag converts to "X years, Y months, Z days" format
- **Validation**: Warns if dates >100 years in past/future, rejects invalid formats
- **Output templates**: "It is X days until Y" (countdown) vs "It has been X days since Y" (countup)

### HTTP Monitoring (`sitecheck.py`)
- **ssdeep fuzzy hashing**: Uses **context-triggered piecewise hashing** (CTPH), not MD5/SHA
- **Why fuzzy?**: Detects "how much changed" (0-100 similarity score), not just "changed vs unchanged"
- **Two-phase workflow**: 
  1. `hash <url>` → generates baseline hash
  2. `check <url> <hash>` → compares current vs baseline (returns similarity %)
- **Session handling**: Uses `requests.Session()` with custom User-Agent
- **Timeout**: Default 10s timeout on all requests
- **Real-world test**: `tests/sitecheck_test.py` uses `http://home.mcom.com/home/welcome.html` (unchanged since 1994!)

### API Integration (`aqicheck.py`)
- **Mandatory caching**: Uses `requests_cache` with **1-hour TTL** to respect API rate limits (free tier)
- **Threshold filtering**: `--MOD`, `--USG`, `--UH`, `--VUH`, `--HAZ` flags suppress output unless AQI ≥ threshold
- **Dual measurements**: Reports both **PM2.5** and **ozone** readings
- **Color ranges**: Data-driven `AQI_COLOR_RANGES` list of `(max_value, color)` tuples
- **Shell rc integration example**: `aqicheck.py 90210 --USG` in `.zshrc` → only shows when unsafe for sensitive groups

### Calendar Tools (`calendar2remind.py`, `oldcal.py`)
- **BSD calendar format**: `MM/DD<TAB>Description` (traditional Unix format)
- **Remind format**: `REM DD Mon MSG Description` (modern reminder format)
- **Bulk conversion**: `calendar2remind.py` processes entire directories
- **Naming convention**: `calendar.<name>` → `<name>-cal.rem`
- **Dual format support**: `oldcal.py` reads **both** BSD and Remind formats
- **Look-ahead**: `-A <days>` flag shows upcoming events (default: today only)
- **Default location**: `~/.remind/` directory for calendar files

## Development Workflows

### Testing
```bash
# Run all tests (discovers *_test.py in tests/)
python3 -m unittest discover -s tests -p '*_test.py'

# Test coverage
coverage erase
coverage run -m unittest discover -s tests -p '*_test.py'
coverage report
```

### CI Expectations
- GitHub Actions runs `ruff`, `black --check`, and `unittest` on pushes/PRs
- Changes should pass local checks before opening PRs:
    - `pre-commit run --all-files`
    - `python3 -m unittest discover -s tests -p '*_test.py' -v`

**Test patterns:**
- Tests named `*_test.py` (NOT `test_*.py`)
- Prefer deterministic tests using local fixtures/servers; external network tests should skip when unavailable
- Simple assertions: `assert status == 200`, `assert compare == 100`
- Test fixtures include expected ssdeep hashes for regression testing

### Copilot Prompt Assets
- Reusable prompts are in `.github/prompts/`
    - `new-tool.prompt.md`: scaffolding a new standalone CLI tool
    - `refactor-safe.prompt.md`: behavior-preserving refactors
    - `add-tests.prompt.md`: deterministic test additions
- Prefer using these prompts when opening Copilot tasks/issues for consistent outcomes

### Dependencies & Installation
- **Core deps**: `docopt`, `requests`, `termcolor`, `python-dateutil`, `requests-cache`
- **Special handling - ssdeep**: Requires **system libraries** before `pip install`
  - **Automated script**: `./install_ssdeep.sh` (handles macOS/Debian/Fedora)
  - **Manual**: macOS: `brew install ssdeep`, Debian: `apt-get install libfuzzy-dev`
- **Graceful degradation**: Tools fail with helpful messages if deps missing

### Adding New Tools Checklist
1. Create `toolname.py` with shebang + docopt usage string in module docstring
2. Implement class for core logic (e.g., `class ToolName(object):`)
3. Add `if __name__ == "__main__":` main execution block
4. Use `termcolor` for output, `sys.stderr` for errors
5. Create `tests/toolname_test.py` with real-world test cases
6. Add dependencies to `requirements.txt`
7. Document in `README.md` with usage examples and CLI output screenshot

## Project Conventions

### File Organization
- **Root level**: Executable Python scripts (main tools) - no subdirectories for tools
- **`tests/`**: Unit tests following `*_test.py` naming (NOT `test_*.py`)
- **`calendar/`**: BSD calendar data files with `calendar.*` pattern (e.g., `calendar.birthdays`)
- **`remind/`**: Output directory for Remind-format files (`*-cal.rem`)
- **`images/`**: Screenshots for README documentation
- **Example configs**: `example.*.ini` files in root (never in `~/.config/`)

### Code Style
- **Type hints everywhere**: All functions use `typing` module (`Tuple[str, str]`, `Optional[int]`, `List[str]`)
- **Docstrings with examples**: Functions include usage examples in docstrings
- **Error messages to stderr**: `print(..., file=sys.stderr)` - **never** to stdout
- **Input validation**: Always validate with specific error messages (see `parse_date()` in `daycounter.py`)
- **Data-driven color coding**: Use tuples/lists for thresholds, not hardcoded if/elif chains

Example validation pattern:
```python
def parse_date(date_string: str) -> datetime.date:
    try:
        parsed_date = datetime.datetime.strptime(date_string, "%Y-%m-%d").date()
        # Additional validation...
    except ValueError as e:
        print(f"Error: Invalid date format '{date_string}'...", file=sys.stderr)
        sys.exit(1)
```

### Integration Points
- **Silent by default**: Tools produce **no output** when thresholds not met (optimized for `.zshrc`)
- **Colored terminal output**: Assumes 256-color terminal support
- **Direct execution**: All tools are `chmod +x` with shebang - run as `./tool.py`, not `python3 tool.py`
- **No inter-dependencies**: Each tool is **completely independent** - no shared modules
- **Config in home dir**: `~/.tool.ini` for configs (NOT `.config/tool.ini`)

### Security Patterns
- **File permissions**: Config files with API keys validated to be `0o600` (user read/write only)
- **API key handling**: Never in environment variables, always in INI files
- **No proxy by default**: Proxy config commented out (see `aqicheck.py` line 60)

## Common Pitfalls

### Date Format Mistakes
```python
# ❌ WRONG - Common US format
$ daycounter.py countdown 12/25/2026 Christmas
Error: Invalid date format '12/25/2026'. Please use YYYY-MM-DD format (e.g., 2023-12-25).

# ✅ CORRECT - ISO 8601 format
$ daycounter.py countdown 2026-12-25 Christmas
It is 309 days until Christmas.
```

### Config File Permissions
```python
# ❌ WRONG - Config file too permissive
$ chmod 644 ~/.aqi.ini
$ aqicheck.py
Error: Config file /Users/user/.aqi.ini has insecure permissions (0o644). Should be 0o600.

# ✅ CORRECT - User-only read/write
$ chmod 600 ~/.aqi.ini
$ aqicheck.py
AQI 94105: PM2.5=35 (Good), Ozone=28 (Good)
```

### Missing API Keys
```python
# ❌ WRONG - Missing config file
$ aqicheck.py
Error: Config file /Users/user/.aqi.ini not found. See example.aqi.ini for format.

# ❌ WRONG - Empty/missing API key
$ aqicheck.py
Error: API key not found in config. Check [DEFAULT] section in ~/.aqi.ini
```

### Output to Wrong Stream
```python
# ❌ WRONG - Error to stdout (breaks shell rc integration)
print("Error: Invalid date format")

# ✅ CORRECT - Error to stderr
print("Error: Invalid date format", file=sys.stderr)
sys.exit(1)
```

### Hardcoded Thresholds (Anti-pattern)
```python
# ❌ WRONG - Hardcoded if/elif chains
if aqi <= 50:
    color = "green"
elif aqi <= 100:
    color = "yellow"
elif aqi <= 150:
    color = "yellow"
# ... more conditions

# ✅ CORRECT - Data-driven with tuples
AQI_COLOR_RANGES = [
    (50, "green"),
    (100, "yellow"),
    (150, "yellow"),
    (200, "red"),
    (300, "magenta"),
    (float('inf'), "magenta")
]

for max_value, color in AQI_COLOR_RANGES:
    if value <= max_value:
        return color
```

## Key Files for Understanding Context
- [README.md](README.md): Comprehensive usage examples with CLI output screenshots
- [requirements.txt](requirements.txt): Core dependencies with inline comments explaining purpose
- [tests/sitecheck_test.py](tests/sitecheck_test.py): Shows testing approach with real external dependencies
- [example.aqi.ini](example.aqi.ini): Configuration file format (3-line INI with `[DEFAULT]` section)
- [install_ssdeep.sh](install_ssdeep.sh): Platform-specific dependency installation script