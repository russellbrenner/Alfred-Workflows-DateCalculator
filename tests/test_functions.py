from freezegun import freeze_time

from src.core.functions import DATE_FUNCTION_MAP, EXCLUSION_MAP
from src.core.settings import Settings

EXPECTED_DATE_KEYS = {
    "date",
    "today",
    "*",
    "time",
    "&",
    "now",
    "#",
    "yesterday",
    "<",
    "tomorrow",
    ">",
    "easter",
    "next mon",
    "next tue",
    "next wed",
    "next thu",
    "next fri",
    "next sat",
    "next sun",
    "prev mon",
    "prev tue",
    "prev wed",
    "prev thu",
    "prev fri",
    "prev sat",
    "prev sun",
    "start bst",
    "end bst",
    "start year",
    "end year",
    "next month",
    "passover",
    "pancake day",
    "lent",
    "mlk",
    "mum",
    "mom",
    "mutter",
}

EXPECTED_EXCLUSION_KEYS = {
    "weekdays",
    "wkdy",
    "weekends",
    "wknd",
    "mondays",
    "mon",
    "tuesdays",
    "tue",
    "wednesdays",
    "wed",
    "thursdays",
    "thu",
    "fridays",
    "fri",
    "saturdays",
    "sat",
    "sundays",
    "sun",
    "all except weekdays",
    "xwkdy",
    "all except weekends",
    "xwknd",
    "all except mondays",
    "xmon",
    "all except tuesdays",
    "xtue",
    "all except wednesdays",
    "xwed",
    "all except thursdays",
    "xthu",
    "all except fridays",
    "xfri",
    "all except saturdays",
    "exsat",
    "xsat",
    "all except sundays",
    "exsun",
    "xsun",
}


def test_date_function_map_has_legacy_keys():
    assert set(DATE_FUNCTION_MAP) == EXPECTED_DATE_KEYS


def test_exclusion_map_has_expected_keys_and_days():
    assert EXPECTED_EXCLUSION_KEYS.issubset(EXCLUSION_MAP)
    assert EXCLUSION_MAP["weekdays"]["days"] == {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}
    assert EXCLUSION_MAP["wknd"]["days"] == {"Saturday", "Sunday"}
    assert EXCLUSION_MAP["xmon"]["days"] == {"Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}


def test_fixed_special_dates_from_known_current_date():
    settings = Settings()
    with freeze_time("2014-01-01 12:00:00"):
        easter, _ = DATE_FUNCTION_MAP["easter"](settings)
        mlk, _ = DATE_FUNCTION_MAP["mlk"](settings)
        mom, _ = DATE_FUNCTION_MAP["mom"](settings)
        start_bst, _ = DATE_FUNCTION_MAP["start bst"](settings)
        end_bst, _ = DATE_FUNCTION_MAP["end bst"](settings)

    assert easter.date().isoformat() == "2014-04-20"
    assert mlk.date().isoformat() == "2014-01-20"
    assert mom.date().isoformat() == "2014-05-11"
    assert start_bst.date().isoformat() == "2014-03-30"
    assert end_bst.date().isoformat() == "2014-10-26"
