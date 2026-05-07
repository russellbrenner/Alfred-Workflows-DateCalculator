# Date Calculator — Alfred 5.x Refactor Plan

## Current State Diagnosis

### Critical blockers for Alfred 5.x

1. **Python 2 syntax**: `from __future__ import unicode_literals`, old `%` and `.format()` string formatting, backtick ``repr`` syntax in vendored `dateutil/tz.py` line 78 (removed in Python 3.0+).
2. **Vendored dependencies are Python 2-era**: The workflow bundles ancient copies of `arrow` (pre-1.0), `python-dateutil` (backtick repr), `parsedatetime`, `pypeg2`, `isoweek`, `humanfriendly`, and `deanishe/alfred-workflow`. None are compatible with Python 3.12 (macOS 14/15 system Python).
3. **Alfred 3 references**: `info.plist` contains `tell application "Alfred 3"` AppleScript, workflow object versions at v1/v2 (current is v3+), no JSON Script Filter output — the deanishe `Workflow` class emits XML by default.
4. **No test suite**: Zero tests. No CI. No way to verify correctness of date arithmetic after refactoring.
5. **`.pyc` files checked in**: `humanfriendly.pyc`, `utils.pyc`, `date_format_mappings.pyc`, `pyparsing.pyc` — stale bytecode, should never be in a repo.
6. **Monolithic structure**: All code in the workflow root. No `src/` layout, no package structure, no `__init__.py`, no separation of concerns between domain logic and Alfred plumbing.

### What works (don't break it)

- Date arithmetic: `dcalc 25.12.14 - 18.01.14`, `dcalc now + 6d`, compound operations
- Format options: `y`, `m`, `w`, `d`, `h`, `M`, `s`, `long`, `ymwd`
- Time arithmetic: `dcalc time + 6h 8M`, `dcalc 14:35 + 6h`
- Date-time combined: `dcalc 21.06.14@14:20 - 23.01.12@09:21 long`
- Week numbers: `dcalc today wn`, `dcalc wn 2015 5 sun`
- Special dates: `easter`, `passover`, `pancake day`, `lent`, `mlk`, `mom/mum/mutter`, `start/end bst`, `start/end year`, `next month`
- Day-of-week navigation: `next mon`, `prev fri`, etc.
- Exclusions: `exclude weekdays`, `exclude mon to fri`, specific date exclusions
- Natural language parsing: `dcalc "4 hours 8 minutes after 4pm"`
- User-defined anniversaries/macros: `christmas`, `alfred`, custom via `dcalcset list`
- Date format settings: 15 format variants (UK, US, ISO, wordy)
- Time format settings: 24-hour, 12-hour, Military
- Date-time separator settings: `@`, `T`, `at`, `on`, `arrow`
- Abbreviations: `<` yesterday, `*` today, `>` tomorrow, `&` time, `#` now
- Formatters: `wn` (week number), `wd` (weekday), `wdi` (weekday ISO), `iso`, `sign` (zodiac)

## Technology Decision

**Python 3** — the only sensible choice for Alfred workflows. Alfred's Script Filter objects natively run `/usr/bin/python3` (or the language of your choice), and JSON output is the native Alfred 5.x protocol. Alternatives considered:

- **Rust**: Fast startup, single binary, but loses the pypeg2 PEG parser (no mature Rust equivalent for the grammar DSL), and the dateutil/rrule exclusion logic is heavily Python-specific. Rewriting the grammar + exclusion engine in Rust would be 3x the effort.
- **Node.js**: Viable (good date libraries, JSON native), but again the PyPEG2 grammar is the core parser and has no direct JS equivalent. The exclusion logic using `dateutil.rrule` is a direct mapping to iCalendar recurrence rules.
- **Go**: Same issue — no PEG parser DSL that matches pypeg2's class-based grammar definitions.

Python keeps the domain logic intact. The refactor is about **modernising the runtime, not rewriting the algorithm**.

## Architecture

```
src/
  __init__.py
  core/
    __init__.py
    settings.py          # Settings model + defaults + migration
    parser.py            # PyPEG2 grammar → Command dataclasses
    engine.py            # Date arithmetic, exclusions, formatting
    functions.py         # DATE_FUNCTION_MAP (easter, passover, etc.)
    formatters.py        # DATE_FORMATTERS_MAP (wn, wd, iso, sign)
    mappings.py          # All lookup tables (DATE_MAPPINGS, etc.)
  alfred/
    __init__.py
    feedback.py          # JSON Script Filter output (Alfred 5.x spec)
    io.py                # stdin/stdout, argument handling
tests/
  __init__.py
  test_parser.py         # PyPEG2 grammar → all command variants
  test_engine.py         # Date arithmetic, exclusions, formatting
  test_functions.py      # Special date functions (easter, passover, etc.)
  test_formatters.py     # wn, wd, iso, sign
  test_settings.py       # Settings migration, defaults
  test_integration.py    # Full end-to-end via Alfred feedback JSON
  conftest.py            # Pytest fixtures (now=freeze, settings fixture)
info.plist               # Alfred 5.x: all objects v3+, JSON Script Filters
icon.png
README.md
pyproject.toml           # Modern Python project metadata
Makefile                 # dev: test, lint, build, pack
```

## Refactor Phases

### Phase 1: Foundation

**Goal**: Modern Python project structure, dependency management, settings migration.

1. Create `pyproject.toml` with:
   - `python-dateutil>=2.9` (modern, Python 3 compatible, has `rrule`)
   - `arrow>=1.3` (modern API, replaces vendored arrow)
   - `pypeg2>=2.15` (still the best PEG parser for this grammar)
   - `pytest>=8`, `pytest-cov`, `freezegun` (testing)
   - `ruff` (linting + formatting, replaces flake8/black/isort)

2. Create `src/core/mappings.py` — port all lookup tables from `date_format_mappings.py`:
   - `DATE_MAPPINGS`, `TIME_MAPPINGS`, `DATE_TIME_MAPPINGS`
   - `TIME_CALCULATION`, `VALID_FORMAT_OPTIONS`
   - `DEFAULT_*` constants, `MAX_LOOKAHEAD_ATTEMPTS`
   - `WN_FUNCTION_REGEX`
   - Use `dataclasses` or `TypedDict` for structured mappings instead of raw dicts

3. Create `src/core/settings.py`:
   - Settings dataclass with defaults
   - Migration logic (replaces `versioning.py`)
   - JSON file storage (replaces deanishe `Workflow.settings` which uses plist)
   - Alfred workflow data directory: `$ALFRED_WORKFLOW_DATA`

### Phase 2: Parser

**Goal**: Modern PyPEG2 grammar with type-safe command dataclasses.

1. Create `src/core/parser.py`:
   - Define `@dataclass` types for all command variants:
     - `TimespanCommand(dateTime, operandList, dateFormat?)`
     - `SubtractionCommand(dateTime1, operandList1?, dateTime2, operandList2?, format)`
     - `ExclusionCommand(dateTime, operandList?, exclusionCommands)`
   - Port the PyPEG2 grammar from `date_parser.py`:
     - `Operator`, `TimeSpans`, `Operand`, `OperandList`
     - `DateTime`, `DateFormat`, `Format`
     - `ExclusionKeyword`, `ExclusionRange`, `ExclusionType`, `ExclusionCommands`
     - `Commands` (the union of all valid command patterns)
   - Add `MacrosParser` subclass for anniversary add/edit/delete commands

2. Key changes from original:
   - Use `dataclass` instead of dynamic `hasattr()` checks
   - Replace `str` subclass grammar classes with proper named types
   - Add type hints throughout
   - Replace `re.compile()` regexes in `__init__` with module-level constants

### Phase 3: Engine

**Goal**: Pure functions for date arithmetic, exclusions, formatting.

1. Create `src/core/engine.py`:
   - `delta_arithmetic(date_time, operand_list) → datetime` — pure function
   - `exclusion_check(start, end, command, settings) → datetime`
   - `calculate_rrule_exclusions(start, end, exclusions) → int`
   - `normalised_days(command, date1, date2) → str` — the subtraction result
   - `calculate_time_interval(interval, start, end) → (count, remainder)`
   - `pluralize(count, singular, plural) → str` — from `humanfriendly` (we'll vendor a tiny version)

2. Create `src/core/functions.py`:
   - Port `DATE_FUNCTION_MAP` and `EXCLUSION_MAP` from `date_functions.py`
   - Replace `_get_current_date()` / `_get_current_time()` with injectable `now` function for testability
   - Keep all the dateutil.rrule logic (easter, passover, BST, MLK day, etc.)
   - Use `datetime.datetime` and `datetime.timedelta` from stdlib + dateutil

3. Create `src/core/formatters.py`:
   - Port `DATE_FORMATTERS_MAP` from `date_formatters.py`
   - `week_number`, `week_day`, `week_day_in_isoformat`, `iso_format`, `zodiac_sign`

### Phase 4: Alfred I/O

**Goal**: JSON Script Filter output per Alfred 5.x spec.

1. Create `src/alfred/feedback.py`:
   - `Feedback` class that builds `{"items": [...]}` JSON
   - `Item` dataclass: `title`, `subtitle`, `arg`, `valid`, `uid`, `icon`, `autocomplete`, `mods` (cmd/ctrl/shift/alt/fn)
   - `to_json()` method returning properly formatted JSON
   - Support for `variables` (Alfred 5.x workflow variables)
   - `skipknowledge` option for ordering

2. Create `src/alfred/io.py`:
   - `read_args()` — sys.argv parsing
   - `write_feedback(feedback)` — stdout JSON
   - `write_output(text)` — for non-Script-Filter actions
   - Settings file I/O using `$ALFRED_WORKFLOW_DATA` env var

### Phase 5: Entry Points

**Goal**: Thin scripts that wire Alfred objects to the core engine.

Each entry point is a minimal script (no logic, just wiring):

| Script | Purpose |
|--------|---------|
| `src/dcalc.py` | Main calculator — Script Filter input |
| `src/anniversary_list.py` | List anniversaries — Script Filter |
| `src/set_anniversary.py` | Add/edit/delete anniversary — action script |
| `src/date_format_list.py` | List date formats — Script Filter |
| `src/set_date_format.py` | Set date format — action script |
| `src/time_format_list.py` | List time formats — Script Filter |
| `src/set_time_format.py` | Set time format — action script |
| `src/date_time_format_list.py` | List date-time formats — Script Filter |
| `src/set_date_time_format.py` | Set date-time format — action script |
| `src/show_date_format.py` | Show current date format — action |
| `src/show_time_format.py` | Show current time format — action |

Each entry point:
```python
#!/usr/bin/env python3
"""dcalc — Date Calculator main entry point."""
from alfred.io import read_args, write_feedback
from alfred.feedback import Feedback, Item
from core.settings import load_settings
from core.parser import DateParser
from core.engine import execute_command

def main():
    settings = load_settings()
    args = read_args()
    parser = DateParser(settings)
    command = parser.parse_command(args[0])
    result = execute_command(command, settings)
    feedback = Feedback()
    if result.startswith("Invalid"):
        feedback.add_item(title=". . .", subtitle=result, valid=False, icon="icon-error")
    else:
        feedback.add_item(title=result, subtitle="Copy to clipboard", valid=True, arg=result)
    write_feedback(feedback)

if __name__ == "__main__":
    main()
```

### Phase 6: info.plist

**Goal**: Alfred 5.x compatible workflow definition.

Changes needed:
- Update `version` keys: Script Filter v3 (was v2), Run Script v3 (was v2), Keyword v1→v1 (ok), Notification v1→v1 (ok), Clipboard v2→v3, Large Type v2→v3
- Replace `python date_calculator.py "{query}"` with `python3 dcalc.py "{query}"` (or use the `script` + `type: "alfred.workflow.action.script"` with `language: "python3"`)
- Replace `tell application "Alfred 3"` with `tell application id "com.runningwithcrab.alfred"` (bundle ID)
- Enable `alfredfiltersresults: true` on all Script Filters (Alfred-side fuzzy matching)
- Set `argumenttype: 1` (required argument) or `2` (optional) correctly
- Add `type: "json"` to Script Filter config for JSON output
- Update `bundleid` to a modern format (keep backwards compat if desired)
- Add `variables` for workflow-scoped settings if needed

### Phase 7: Tests

**Goal**: 100% test coverage with machine-led runtime validation.

#### Unit tests (no Alfred dependency)

- `test_parser.py`:
  - Every command variant: timespan, subtraction, exclusion, natural language
  - Edge cases: malformed input, missing components, ambiguous formats
  - All macros: `now`, `today`, `tomorrow`, `yesterday`, `easter`, `passover`, etc.
  - All abbreviations: `<`, `*`, `>`, `&`, `#`
  - Week number commands: `wn`, `wn 2015 5`, `wn 2015 5 sun`
  - Anniversary macros and user-defined names
  - Exclusion variants: `exclude weekdays`, `exclude mon`, range exclusions
  - Natural language: `"4 hours 8 minutes after 4pm"`, `"next wednesday"`

- `test_engine.py`:
  - Date arithmetic: `+6d`, `-3w`, `+5y 9d 3w - 2d`
  - Subtraction: `date1 - date2`, with and without format options
  - Exclusion logic: weekdays excluded, specific dates excluded, range exclusions
  - Normalised output: `long` format, `ymwd`, `wd`, etc.
  - `calculate_time_interval` for each interval type
  - Edge cases: leap years, month boundaries, year boundaries
  - Time arithmetic: hours, minutes, day rollover

- `test_functions.py`:
  - Easter calculation (verify against known dates for 2024-2030)
  - Passover calculation (verify against known dates)
  - BST start/end dates
  - MLK day, Mother's day, Pancake day
  - Day-of-week navigation (next mon, prev fri, etc.)
  - Year start/end, next month

- `test_formatters.py`:
  - Week number, week day, week day ISO, ISO format, zodiac sign
  - All zodiac sign boundaries

- `test_settings.py`:
  - Default settings
  - Migration from old settings (missing keys)
  - Date/time format mapping lookups
  - Anniversary CRUD

#### Integration tests (Alfred JSON output)

- `test_integration.py`:
  - Full pipeline: input → parser → engine → feedback JSON
  - Validate JSON structure matches Alfred 5.x spec
  - Test valid/invalid item states
  - Test modifier key configurations
  - Test all entry points with representative inputs

#### Runtime tests (machine-led)

- `test_runtime.py`:
  - Spawn the actual entry point scripts as subprocesses
  - Feed them arguments via `sys.argv` simulation
  - Capture stdout and validate it's valid JSON
  - Validate the JSON structure contains `items` array
  - Cross-validate output against expected values from unit tests
  - This is the "real" test — the scripts actually run and produce Alfred-compatible output

#### Coverage

- Target: 100% line coverage, 95%+ branch coverage
- Use `pytest-cov` with `--cov=src --cov-report=term-missing`
- CI gate: fail if coverage drops below threshold

### Phase 8: Build & Packaging

**Goal**: Reproducible build from source to `.alfredworkflow`.

1. `Makefile` targets:
   - `make test` — run pytest with coverage
   - `make lint` — ruff check + format
   - `make typecheck` — mypy (if type hints added)
   - `make build` — build the workflow bundle
   - `make pack` — create `.alfredworkflow` zip

2. Build process:
   - Create a build directory
   - Copy entry point scripts to root
   - Copy `src/` as package directories
   - Install dependencies via `pip install -t build/lib/`
   - Copy `info.plist`, `icon.png`, `README.md`
   - Clean up: remove `__pycache__`, `.pyc`, test files
   - Zip into `.alfredworkflow` (which is just a `.zip` renamed)

3. CI (optional, via GitHub Actions):
   - On push: lint + test + coverage
   - On tag: build + attach `.alfredworkflow` artifact

## Best Practices Applied

### Python
- **pyproject.toml** as single source of truth (no setup.py)
- **src/ layout** for clean import paths
- **Type hints** on all public functions and dataclasses
- **ruff** for linting + formatting (single tool, fast)
- **pytest** with fixtures for test isolation
- **dataclasses** for all structured data (commands, settings, items)
- **Pure functions** for all domain logic (testable, no side effects)
- **Dependency injection** for `now` / `settings` in functions (testability)
- **No vendored deps** — install from PyPI via pip (or vendor via `pip install -t`)

### Alfred 5.x
- **JSON Script Filter output** (Alfred's recommended format)
- **Object version 3+** on all workflow objects
- **alfredfiltersresults: true** for client-side fuzzy matching
- **Workflow variables** for state sharing between objects
- **Bundle ID reference** instead of "Alfred 3" in AppleScript
- **python3** language in all Script Filter / Run Script objects
- **Proper icon paths** relative to workflow root

### Testing
- **100% coverage** target on all `src/core/` modules
- **Machine-led runtime tests** — subprocess execution of actual scripts
- **Freeze time** with `freezegun` for deterministic date tests
- **Parametrised tests** for all input variants
- **Integration tests** validating JSON output structure
- **CI gate** on coverage threshold

### Remediation → Review Cycles

Each phase follows this cycle:

1. **Write code** → implement the phase
2. **Run tests** → `make test`, verify coverage
3. **Self-review** → `make lint`, check for regressions
4. **Integration test** → build the workflow, load into Alfred, manual smoke test
5. **Commit** → with descriptive message + Co-Authored-By trailer
6. **Next phase**

Phases are ordered by dependency: Foundation → Parser → Engine → Alfred I/O → Entry Points → info.plist → Tests → Build. Tests are written concurrently with code (TDD where possible), not as an afterthought.

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| PyPEG2 grammar incompatibility with Python 3.12 | Pin `pypeg2>=2.15.2` (last release, Python 3 compatible). If broken, switch to `lark` parser (more modern, actively maintained). |
| dateutil.rrule behaviour changes between versions | Pin `python-dateutil>=2.9,<3.0`. Write exhaustive tests for every rrule usage. |
| Alfred 5.x JSON format drift | Tests validate JSON structure against Alfred's documented spec. Manual smoke test before release. |
| Settings migration from old deanishe format | Read old plist settings on first run, convert to JSON, write new format. Keep backwards compat for one version. |
| Performance degradation | Python 3 is generally faster than Python 2. Bundle only what's needed. Profile if Script Filter takes >200ms. |
| Vendored deps still needed for offline | Use `pip install -t build/lib/` to vendor at build time. Don't check vendored deps into git. |

## Estimated Effort

| Phase | Effort | Dependencies |
|-------|--------|-------------|
| 1. Foundation | 1-2 hours | None |
| 2. Parser | 3-4 hours | Phase 1 |
| 3. Engine | 4-5 hours | Phase 1, 2 |
| 4. Alfred I/O | 1-2 hours | Phase 1 |
| 5. Entry Points | 2-3 hours | Phase 2, 3, 4 |
| 6. info.plist | 1 hour | Phase 5 |
| 7. Tests | 6-8 hours | All above (concurrent) |
| 8. Build | 1-2 hours | Phase 6, 7 |
| **Total** | **~20-27 hours** | |

Tests should be written alongside each phase, not deferred. The runtime tests (Phase 7) require all entry points to exist, so they come last.

## Success Criteria

1. All existing functionality works identically (verified by tests)
2. 100% line coverage on `src/core/`
3. Workflow loads and runs in Alfred 5.x without errors
4. Script Filter returns valid JSON matching Alfred 5.x spec
5. `make test` passes with zero failures
6. `make lint` passes with zero violations
7. `.alfredworkflow` builds successfully via `make pack`
8. No vendored dependencies in the git repo
9. Python 3.10+ compatible (minimum Alfred 5.x system Python)
10. Clean `info.plist` with all objects at current versions
