from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def run_script(script: str, *args: str, data_dir: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["ALFRED_WORKFLOW_DATA"] = str(data_dir)
    return subprocess.run(
        [sys.executable, str(SRC / script), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


def test_dcalc_subtraction_returns_alfred_json(tmp_path: Path) -> None:
    result = run_script("dcalc.py", "25.12.14 - 18.01.14", data_dir=tmp_path)

    payload = json.loads(result.stdout)
    assert "items" in payload
    assert payload["items"]
    assert payload["items"][0]["valid"] is True


def test_date_format_list_returns_items(tmp_path: Path) -> None:
    result = run_script("date_format_list.py", data_dir=tmp_path)

    payload = json.loads(result.stdout)
    assert len(payload["items"]) > 0


def test_set_and_show_date_format(tmp_path: Path) -> None:
    set_result = run_script("set_date_format.py", "yyyy-mm-dd", data_dir=tmp_path)
    show_result = run_script("show_date_format.py", data_dir=tmp_path)

    assert set_result.stdout.strip() == "Date format set to yyyy-mm-dd"
    assert show_result.stdout.strip() == "Date format is yyyy-mm-dd"


def test_set_and_show_time_format(tmp_path: Path) -> None:
    set_result = run_script("set_time_format.py", "12-hour", data_dir=tmp_path)
    show_result = run_script("show_time_format.py", data_dir=tmp_path)

    assert set_result.stdout.strip() == "Time format set to 12-hour"
    assert show_result.stdout.strip() == "Time format is 12-hour"


def test_set_anniversary_and_list(tmp_path: Path) -> None:
    run_script("set_date_format.py", "dd.mm.yyyy", data_dir=tmp_path)
    add_result = run_script("set_anniversary.py", "add birthday 25.12.1990", data_dir=tmp_path)
    list_result = run_script("anniversary_list.py", "birthday", data_dir=tmp_path)

    assert add_result.stdout.strip() == "birthday added"
    payload = json.loads(list_result.stdout)
    assert payload["items"]
    assert payload["items"][0]["arg"] == "birthday"
    assert payload["items"][0]["title"].startswith("birthday ➤")
