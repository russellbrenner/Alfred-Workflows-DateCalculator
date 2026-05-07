# Migration Guide — v2.x to v3.0

## What Changed

This is a complete rewrite of the Date Calculator workflow for Alfred 5.x and Python 3.10+. The original workflow was written for Alfred 2/3 with Python 2.7 and bundled dependencies.

### Breaking Changes

- **Bundle ID preserved**: `muppet.gate.net.DateCalculator` — settings and data should carry over
- **All keywords unchanged**: `dcalc`, `dcalcset ...`, `dcalcshow ...`, `date`, `dcalchelp`
- **Settings migration**: Your existing date format, time format, and anniversary settings will be automatically migrated on first run
- **Settings storage**: Old settings stored via Alfred-Workflow library; new settings stored as JSON in `$ALFRED_WORKFLOW_DATA/settings.json`

### Removed

- The `exclude` feature for date calculations was kept but may have edge-case differences
- Natural language parsing (`"4 hours after 4pm"`) now uses `dateutil.parser` instead of `parsedatetime` — results should be equivalent for common expressions

### Added

- Python 3.10+ compatibility
- Alfred 5.x JSON Script Filter output
- Modern dependency management via pip
- 56 automated tests
- Cleaner code structure with typed dataclasses

### Installation

1. Download the new `.alfredworkflow` file
2. Double-click to install — Alfred will replace the old version
3. Your settings (date format, time format, anniversaries) should be automatically migrated

### If Something Goes Wrong

- **Settings not migrated**: Your old settings are in `~/Library/Application Support/Alfred/Workflow Data/muppet.gate.net.DateCalculator/settings.json`. The new workflow reads this on first run.
- **Workflow not working**: Check Alfred's debugger (click the bug icon in Alfred Preferences) for error output.
- **Missing dependencies**: The workflow bundles all dependencies — no manual installation needed.

## For Developers

The source code is available at [GitHub](https://github.com/russellbrenner/Alfred-Workflows-DateCalculator).

### Project Structure

```
src/
  dcalc.py              # Main calculator entry point
  anniversary_list.py   # Anniversary list Script Filter
  set_anniversary.py    # Anniversary add/edit/delete
  date_format_list.py   # Date format selection
  set_date_format.py    # Set date format
  time_format_list.py   # Time format selection
  set_time_format.py    # Set time format
  date_time_format_list.py  # Date-time format selection
  set_date_time_format.py   # Set date-time format
  show_date_format.py   # Show current date format
  show_time_format.py   # Show current time format
  core/
    mappings.py         # Lookup tables (date/time formats, etc.)
    settings.py         # Settings management
    parser.py           # PyPEG2 grammar for parsing commands
    engine.py           # Date arithmetic and formatting
    functions.py        # Special date functions (easter, passover, etc.)
    formatters.py       # Output formatters (week number, zodiac, etc.)
  alfred/
    feedback.py         # Alfred JSON output builder
    io.py               # I/O helpers
tests/                  # 56 tests
```

### Build

```bash
make pack    # Creates DateCalculator.alfredworkflow
```
