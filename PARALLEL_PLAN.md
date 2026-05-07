# Date Calculator — Parallel Refactor Plan

## Wave 0: Contracts (mira, 15 min)

Create the skeleton that all subagents implement against:

```
src/
  __init__.py
  core/
    __init__.py
    mappings.py        # TypedDict dataclasses for all lookup tables
    settings.py        # Settings dataclass + load/save interface
    parser.py          # Command dataclasses + DateParser interface
    engine.py          # Pure function signatures
    functions.py       # DATE_FUNCTION_MAP interface
    formatters.py      # DATE_FORMATTERS_MAP interface
  alfred/
    __init__.py
    feedback.py        # Feedback + Item dataclasses
    io.py              # read_args, write_feedback interfaces
tests/
  __init__.py
  conftest.py          # fixtures: frozen_now, default_settings
pyproject.toml
Makefile
.gitignore (updated)
```

Each file has: correct imports, type signatures, docstrings, and `raise NotImplementedError` bodies. This is the **contract** — subagents implement the bodies.

---

## Wave 1: Foundation (3 subagents, parallel, ~30 min)

Disjoint files — zero collision risk.

### Agent 1A: Mappings
**Files:** `src/core/mappings.py`
**Contract:** All lookup tables from `date_format_mappings.py`, ported to Python 3:
- `DATE_MAPPINGS`, `TIME_MAPPINGS`, `DATE_TIME_MAPPINGS` as TypedDicts
- `TIME_CALCULATION`, `VALID_FORMAT_OPTIONS`, `VALID_WORD_FORMAT_OPTIONS`
- `DEFAULT_DATE_FORMAT`, `DEFAULT_TIME_FORMAT`, `DEFAULT_DATE_TIME_FORMAT`
- `DEFAULT_ANNIVERSARIES`, `DEFAULT_WORKFLOW_SETTINGS`
- `MAX_LOOKAHEAD_ATTEMPTS`, `WN_FUNCTION_REGEX`
- Remove all Python 2 cruft (`__future__`, `unicode_literals`)

### Agent 1B: Settings
**Files:** `src/core/settings.py`
**Contract:** 
- `Settings` dataclass with all fields
- `load_settings(workflow_data_dir) -> Settings` — reads JSON from `$ALFRED_WORKFLOW_DATA/settings.json`, applies defaults
- `save_settings(settings, workflow_data_dir)` — writes JSON
- `migrate_settings(old_plist_path) -> Settings` — reads old deanishe plist format if it exists, converts to new format
- Uses `ALFRED_WORKFLOW_DATA` env var, falls back to `~/.local/share/alfred-date-calc/`

### Agent 1C: Alfred I/O
**Files:** `src/alfred/feedback.py`, `src/alfred/io.py`
**Contract:**
- `Item` dataclass: `title`, `subtitle`, `arg`, `valid`, `uid`, `icon`, `icontype`, `autocomplete`, `mods` (dict), `variables` (dict)
- `Feedback` class: `items: list[Item]`, `add_item()`, `to_json() -> str` (valid Alfred 5.x JSON)
- `read_args() -> list[str]` — parses sys.argv, handles Alfred's `{query}` escaping
- `write_feedback(fb: Feedback) -> None` — prints JSON to stdout
- `write_output(text: str) -> None` — prints plain text for action scripts
- Icon constants: `ICON_INFO`, `ICON_WARNING`, `ICON_ERROR` → path strings

**Tests:** Agent 1C also writes `tests/test_feedback.py` — validates JSON structure against Alfred spec.

---

## Wave 2: Parser + Core (2 subagents, parallel, ~45 min)

These agents depend on Wave 1 contracts existing. They work on disjoint files.

### Agent 2A: Parser
**Files:** `src/core/parser.py`
**Contract:** Port the PyPEG2 grammar from `date_parser.py` + `macros_parser.py`:
- Command dataclasses: `TimespanCommand`, `SubtractionCommand`, `ExclusionCommand`, `AnniversaryCommand`
- `DateParser` class: `__init__(settings)`, `parse_command(string) -> Command`
- PyPEG2 grammar: `Operator`, `TimeSpans`, `Operand`, `DateTime`, `DateFormat`, `Format`, `ExclusionKeyword`, `ExclusionRange`, `ExclusionType`, `ExclusionCommands`, `Commands`
- `MacrosParser(DateParser)` subclass: `parse_command(string) -> AnniversaryCommand`
- All regex patterns from `mappings.py`
- Type hints on everything

**Tests:** Agent 2A also writes `tests/test_parser.py` — every command variant, edge cases, malformed input.

### Agent 2B: Engine + Functions + Formatters
**Files:** `src/core/engine.py`, `src/core/functions.py`, `src/core/formatters.py`
**Contract:**

`engine.py`:
- `execute_command(command, settings, now_fn=datetime.now) -> str` — main dispatcher
- `do_timespans(command, settings, now_fn) -> str`
- `do_subtraction(command, settings, now_fn) -> str`
- `do_formats(command, settings, now_fn) -> str`
- `delta_arithmetic(date_time, operand_list) -> datetime`
- `exclusion_check(start, end, command, settings) -> datetime`
- `calculate_rrule_exclusions(start, end, exclusions) -> int`
- `normalised_days(command, date1, date2) -> str`
- `calculate_time_interval(interval, start, end) -> tuple[int, datetime]`
- `pluralize(count, singular, plural) -> str` — tiny vendored function (replaces `humanfriendly`)
- `valid_command_format(format_str) -> bool`
- All exception classes: `FormatError`, `IncompatibleFunctionError`, etc.

`functions.py`:
- `DATE_FUNCTION_MAP` — all date functions (current_date, now, yesterday, tomorrow, weekday, next_easter, etc.)
- `EXCLUSION_MAP` — all exclusion rules (weekdays, weekends, individual days, etc.)
- `DAYS_OF_WEEK_ABBREVIATIONS`
- All helper functions: `next_passover`, `bst`, `around_easter`, `mothers_day_us`, `martin_luther_king_day`
- **Critical:** All functions accept `now_fn` parameter for testability (injectable time)

`formatters.py`:
- `DATE_FORMATTERS_MAP` — `week_number`, `week_day`, `week_day_in_isoformat`, `iso_format`, `zodiac_sign`
- `DAYS_OF_WEEK` mapping

**Tests:** Agent 2B also writes:
- `tests/test_engine.py` — date arithmetic, exclusions, formatting, edge cases
- `tests/test_functions.py` — easter, passover, BST, MLK day, day-of-week navigation
- `tests/test_formatters.py` — all formatter functions, zodiac boundaries

---

## Wave 3: Entry Points + Integration (3 subagents, parallel, ~30 min)

All Wave 1 + 2 modules exist. These agents wire them together.

### Agent 3A: Main Entry Points
**Files:** `src/dcalc.py`, `src/anniversary_list.py`, `src/set_anniversary.py`
**Contract:** Thin scripts with zero domain logic:
- `dcalc.py`: load settings → parse → execute → write feedback JSON
- `anniversary_list.py`: load settings → list anniversaries → write feedback JSON
- `set_anniversary.py`: load settings → parse → add/edit/delete → print output
- All use `#!/usr/bin/env python3` shebang
- All import from `src.core.*` and `src.alfred.*`

### Agent 3B: Settings Entry Points
**Files:** `src/date_format_list.py`, `src/set_date_format.py`, `src/time_format_list.py`, `src/set_time_format.py`, `src/date_time_format_list.py`, `src/set_date_time_format.py`, `src/show_date_format.py`, `src/show_time_format.py`
**Contract:** Same pattern — load, read/write settings, output.

### Agent 3C: Integration Tests + info.plist
**Files:** `tests/test_integration.py`, `tests/test_runtime.py`, `info.plist`
**Contract:**
- `test_integration.py`: full pipeline tests — input → parser → engine → feedback JSON, validate structure
- `test_runtime.py`: subprocess tests — spawn actual entry points, capture stdout, validate JSON, cross-validate against expected values
- `info.plist`: Alfred 5.x compatible — all objects v3+, JSON Script Filters (`"type": "json"`), `alfredfiltersresults: true`, `python3` language, bundle ID reference instead of "Alfred 3"

---

## Wave 4: Integration Review (1 subagent, ~15 min)

### Agent 4A: Final Review + Build
**Contract:**
- Run `make test` — all tests passing, coverage >= 95%
- Run `make lint` — ruff clean
- Review all files for consistency (import paths, naming, style)
- Verify `info.plist` object connections are correct
- Create `Makefile` build target if not complete
- Produce `.alfredworkflow` via `make pack`
- Write `MIGRATION.md` — notes for users upgrading from old version

---

## Review Gates (per subagent skill)

Each subagent dispatch includes two review steps:

1. **Spec Compliance Review** — does the implementation match the contract? (file existence, function signatures, behaviour)
2. **Code Quality Review** — is the code clean, tested, correct? (error handling, edge cases, naming, test coverage)

If either review fails → fix subagent → re-review. Only proceed when both PASS.

After each wave, I (mira) merge the branch and run `make test` as a gate before starting the next wave.

---

## Parallelism Summary

| Wave | Agents | Files | Wall Time | Dependencies |
|------|--------|-------|-----------|-------------|
| 0 | mira (1) | Skeleton + contracts | 15 min | None |
| 1 | 3 parallel | mappings, settings, alfred/ | 30 min | Wave 0 |
| 2 | 2 parallel | parser, engine+functions+formatters | 45 min | Wave 0, 1 |
| 3 | 3 parallel | entry points, integration tests, info.plist | 30 min | Waves 0-2 |
| 4 | 1 | final review + build | 15 min | Waves 0-3 |
| **Total** | | | **~2.25 hours** | |

vs. sequential estimate of 20-27 hours. The compression comes from:
- Agents work in parallel (not serial)
- Subagents have focused context (no plan-reading, no accumulated state)
- Review gates catch issues per-task (not at the end)
- Contracts defined upfront (no waiting for dependencies to be implemented)
