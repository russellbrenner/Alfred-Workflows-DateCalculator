# Date Calculator — Alfred Workflow

A date and time calculator for [Alfred](https://www.alfredapp.com/) (Powerpack required).

Modernised for Alfred 5.x / Python 3.10+. Originally created by MuppetGate Media.

## Installation

1. Download the latest `.alfredworkflow` from [Releases](../../releases)
2. Double-click to install into Alfred

## Usage

### Main Calculator

Type `dcalc` followed by your expression:

| Expression | Example | Description |
|------------|---------|-------------|
| Date subtraction | `dcalc 25.12.14 - 18.01.14` | Days between dates |
| With format | `dcalc 25.12.14 - 18.01.14 long` | Full breakdown |
| Add time | `dcalc now + 6d` | Add days/weeks/months |
| Combined | `dcalc 18.12.12 + 5y 9d 3w` | Multiple operations |
| Week number | `dcalc today wn` | Current week number |
| From week | `dcalc wn 2015 5 sun` | Date for week 5, Sunday |
| Day of week | `dcalc next mon` | Next Monday's date |
| Time calc | `dcalc time + 6h 8M` | Add hours/minutes |
| Date+time | `dcalc 21.06.14@14:20 - 23.01.12@09:21 long` | Combined |
| Natural language | `dcalc "4 hours after 4pm"` | Human-readable |
| Special dates | `dcalc easter`, `dcalc christmas` | Named dates |

### Format Options

Append to subtraction results: `y`, `m`, `w`, `d`, `h`, `M`, `s`, `long`, or combinations like `ymwd`.

### Abbreviations

| Symbol | Meaning |
|--------|---------|
| `<` | yesterday |
| `*` | today |
| `>` | tomorrow |
| `&` | time |
| `#` | now |

### Settings

| Command | Purpose |
|---------|---------|
| `dcalcset date format` | Choose date format (UK, US, ISO, etc.) |
| `dcalcset time format` | Choose time format (24-hour, 12-hour, Military) |
| `dcalcset date and time format` | Choose date+time separator (@, T, at, on) |
| `dcalcshow date format` | Show current date format |
| `dcalcshow time format` | Show current time format |

### Anniversaries

| Command | Purpose |
|---------|---------|
| `dcalcset list` | Manage anniversaries |
| `dcalcset list add name date` | Add a named anniversary |
| `dcalcset list edit name date` | Edit an anniversary |
| `dcalcset list delete name` | Remove an anniversary |
| `dcalcshow list` | Show anniversary list |

Use anniversaries in calculations: `dcalc christmas`, `dcalc today - christmas`.

## Date Formats Supported

- UK: `dd-mm-yy`, `dd-mm-yyyy`, `dd/mm/yy`, `dd/mm/yyyy`, `dd.mm.yy`, `dd.mm.yyyy`
- US: `mm-dd-yy`, `mm-dd-yyyy`, `mm/dd/yy`, `mm/dd/yyyy`, `mm.dd.yy`, `mm.dd.yyyy`
- International: `yyyy-mm-dd`
- ISO: `yyyymmdd`
- Wordy: `dd mmm yyyy`

## Special Dates

`easter`, `passover`, `pancake day`, `lent`, `mlk` (Martin Luther King Day), `mom`/`mum`/`mutter` (Mother's Day), `start bst`, `end bst`, `start year`, `end year`, `next month`, `christmas`, `alfred`.

## Development

### Setup

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Test

```bash
pytest tests/ -v
```

### Build

```bash
make build          # Build workflow bundle
make pack           # Create .alfredworkflow file
```

## License

MIT License — Copyright (c) 2014 MuppetGate Media

See [LICENSE](LICENSE) for full text.

## Credits

Original workflow by MuppetGate Media. Modernised for Alfred 5.x and Python 3.

Original dependencies:
- [Alfred-Workflow](http://www.deanishe.net/alfred-workflow/) by Dean Jackson
- [python-dateutil](https://labix.org/python-dateutil) by Gustavo Niemeyer
- [PyPEG](http://fdik.org/pyPEG/) by Volker Birk
- [ParseDateTime](https://github.com/bear/parsedatetime) by Mike Taylor
- [HumanFriendly](https://humanfriendly.readthedocs.io/en/latest) by Peter Odding
