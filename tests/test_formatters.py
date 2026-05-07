from datetime import datetime

from src.core.formatters import iso_format, week_day, week_day_in_isoformat, week_number, zodiac_sign


def test_week_number_week_day_and_iso_formatters():
    dt = datetime(2014, 12, 25, 13, 45, 30)
    assert week_number(dt) == "52"
    assert week_day(dt) == "THU"
    assert week_day_in_isoformat(dt) == "4"
    assert iso_format(dt) == "2014-12-25T13:45:30"


def test_zodiac_sign_boundaries_use_legacy_bisect_logic():
    # Legacy bisect semantics switch on the day after each listed boundary.
    assert zodiac_sign(datetime(2024, 1, 1)) == "Capricorn"
    assert zodiac_sign(datetime(2024, 1, 20)) == "Capricorn"
    assert zodiac_sign(datetime(2024, 1, 21)) == "Aquarius"
    assert zodiac_sign(datetime(2024, 2, 19)) == "Pisces"
    assert zodiac_sign(datetime(2024, 3, 21)) == "Aries"
    assert zodiac_sign(datetime(2024, 4, 21)) == "Taurus"
    assert zodiac_sign(datetime(2024, 5, 22)) == "Gemini"
    assert zodiac_sign(datetime(2024, 6, 22)) == "Cancer"
    assert zodiac_sign(datetime(2024, 7, 23)) == "Leo"
    assert zodiac_sign(datetime(2024, 8, 24)) == "Virgo"
    assert zodiac_sign(datetime(2024, 9, 24)) == "Libra"
    assert zodiac_sign(datetime(2024, 10, 24)) == "Scorpio"
    assert zodiac_sign(datetime(2024, 11, 23)) == "Sagittarius"
    assert zodiac_sign(datetime(2024, 12, 23)) == "Capricorn"
