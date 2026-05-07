"""Date function map — specialised date calculations.

DATE_FUNCTION_MAP maps keyword strings to functions that return (datetime, format).
EXCLUSION_MAP maps exclusion keywords to excluded day sets and rrule generators.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from math import floor

from dateutil.relativedelta import FR, MO, SA, SU, TH, TU, WE, relativedelta
from dateutil.rrule import DAILY, YEARLY, rrule

from src.core.mappings import DATE_MAPPINGS, DATE_TIME_MAPPINGS, TIME_MAPPINGS
from src.core.settings import Settings

DAYS_OF_WEEK_ABBREVIATIONS: dict[str, str] = {
    "mon": "monday",
    "tue": "tuesday",
    "wed": "wednesday",
    "thu": "thursday",
    "fri": "friday",
    "sat": "saturday",
    "sun": "sunday",
}

DAY_MAP = {
    "mon": relativedelta(days=+1, weekday=MO(+1)),
    "tue": relativedelta(days=+1, weekday=TU(+1)),
    "wed": relativedelta(days=+1, weekday=WE(+1)),
    "thu": relativedelta(days=+1, weekday=TH(+1)),
    "fri": relativedelta(days=+1, weekday=FR(+1)),
    "sat": relativedelta(days=+1, weekday=SA(+1)),
    "sun": relativedelta(days=+1, weekday=SU(+1)),
    "prev mon": relativedelta(days=-1, weekday=MO(-1)),
    "prev tue": relativedelta(days=-1, weekday=TU(-1)),
    "prev wed": relativedelta(days=-1, weekday=WE(-1)),
    "prev thu": relativedelta(days=-1, weekday=TH(-1)),
    "prev fri": relativedelta(days=-1, weekday=FR(-1)),
    "prev sat": relativedelta(days=-1, weekday=SA(-1)),
    "prev sun": relativedelta(days=-1, weekday=SU(-1)),
}

DateFunction = Callable[[Settings], tuple[datetime, str]]


def get_date_format(settings: Settings) -> str:
    return DATE_MAPPINGS[settings.date_format]["date_format"]


def get_time_format(settings: Settings) -> str:
    return TIME_MAPPINGS[settings.time_format]["time_format"]


def get_full_format(settings: Settings) -> str:
    return DATE_TIME_MAPPINGS[settings.date_time_format]["date-time-format"](get_date_format(settings), get_time_format(settings))


def get_date_format_regex(settings: Settings) -> str:
    return DATE_MAPPINGS[settings.date_format]["regex"]


def get_time_format_regex(settings: Settings) -> str:
    return TIME_MAPPINGS[settings.time_format]["regex"]


def get_full_format_regex(settings: Settings) -> str:
    return DATE_TIME_MAPPINGS[settings.date_time_format]["date-time-format"](get_date_format_regex(settings), get_time_format_regex(settings))


def get_time_preprocessor(settings: Settings) -> Callable[[str], str]:
    return TIME_MAPPINGS[settings.time_format]["pre_process"]


def _get_current_date() -> datetime:
    return datetime.combine(datetime.today(), datetime.max.time())


def _get_current_time() -> datetime:
    return datetime.combine(datetime.today(), datetime.now().time())


def current_date(settings: Settings) -> tuple[datetime, str]:
    return _get_current_date(), get_date_format(settings)


def current_time(settings: Settings) -> tuple[datetime, str]:
    return _get_current_time(), get_time_format(settings)


def now(settings: Settings) -> tuple[datetime, str]:
    return datetime.now(), get_full_format(settings)


def yesterday(settings: Settings) -> tuple[datetime, str]:
    return _get_current_date() - timedelta(days=1), get_date_format(settings)


def tomorrow(settings: Settings) -> tuple[datetime, str]:
    return _get_current_date() + timedelta(days=1), get_date_format(settings)


def weekday(day_of_week_str: str) -> DateFunction:
    def _weekday(settings: Settings) -> tuple[datetime, str]:
        return _get_current_date() + DAY_MAP[day_of_week_str.lower()], get_date_format(settings)

    return _weekday


def next_easter(settings: Settings) -> tuple[datetime, str]:
    easter_rule = rrule(freq=YEARLY, byeaster=0)
    return easter_rule.after(_get_current_date(), inc=False), get_date_format(settings)


def start_of_year(settings: Settings) -> tuple[datetime, str]:
    return datetime(year=_get_current_date().year, day=1, month=1), get_date_format(settings)


def end_of_year(settings: Settings) -> tuple[datetime, str]:
    return datetime(year=_get_current_date().year, day=31, month=12), get_date_format(settings)


def next_month(settings: Settings) -> tuple[datetime, str]:
    current = _get_current_date()
    result = (current.replace(day=1) + relativedelta(months=+1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return result, get_date_format(settings)


def next_passover(settings: Settings) -> tuple[datetime, str]:
    def rosh_hashanah(year: int) -> int:
        g = year % 19 + 1
        r = 12 * g % 19
        v = floor(year / 100.0) - floor(year / 400.0) - 2
        v += 765433.0 * r / 492480
        v += (year % 4) / 4.0
        v -= (313.0 * year + 89081) / 98496
        n = int(v)
        f = v - n
        dow = (datetime(year, 8, 31).weekday() + n) % 7
        if dow in (2, 4, 6) or dow == 0 and f >= 23269.0 / 25920 and r > 11:
            n += 1
        elif dow == 1 and f >= 1367.0 / 2160 and r > 6:
            n += 2
        return n

    def calc_passover_year(year: int) -> datetime:
        return datetime(year, 3, 21) + timedelta(rosh_hashanah(year))

    passover_date = calc_passover_year(_get_current_date().year)
    if passover_date >= _get_current_date():
        return passover_date, get_date_format(settings)
    return calc_passover_year(_get_current_date().year + 1), get_date_format(settings)


def bst(month_number: int) -> DateFunction:
    def _bst(settings: Settings) -> tuple[datetime, str]:
        bst_rule = rrule(freq=YEARLY, bymonth=month_number, byweekday=SU(-1))
        return bst_rule.after(_get_current_date(), inc=False), get_date_format(settings)

    return _bst


def around_easter(days: int) -> DateFunction:
    def _easter_offset(settings: Settings) -> tuple[datetime, str]:
        easters = list(rrule(freq=YEARLY, byeaster=0, count=2))
        offset_date = easters[0] + timedelta(days=days)
        if _get_current_date() > offset_date:
            offset_date = easters[1] + timedelta(days=days)
        return offset_date, get_date_format(settings)

    return _easter_offset


def mothers_day_us(settings: Settings) -> tuple[datetime, str]:
    mothers_day_rule = rrule(freq=YEARLY, bymonth=5, byweekday=SU(2))
    return mothers_day_rule.after(_get_current_date()), get_date_format(settings)


def martin_luther_king_day(settings: Settings) -> tuple[datetime, str]:
    mlk_day_rule = rrule(freq=YEARLY, bymonth=1, byweekday=MO(3))
    return mlk_day_rule.after(_get_current_date()), get_date_format(settings)


DATE_FUNCTION_MAP: dict[str, DateFunction] = {
    "date": current_date,
    "today": current_date,
    "*": current_date,
    "time": current_time,
    "&": current_time,
    "now": now,
    "#": now,
    "yesterday": yesterday,
    "<": yesterday,
    "tomorrow": tomorrow,
    ">": tomorrow,
    "easter": next_easter,
    "next mon": weekday("mon"),
    "next tue": weekday("tue"),
    "next wed": weekday("wed"),
    "next thu": weekday("thu"),
    "next fri": weekday("fri"),
    "next sat": weekday("sat"),
    "next sun": weekday("sun"),
    "prev mon": weekday("prev mon"),
    "prev tue": weekday("prev tue"),
    "prev wed": weekday("prev wed"),
    "prev thu": weekday("prev thu"),
    "prev fri": weekday("prev fri"),
    "prev sat": weekday("prev sat"),
    "prev sun": weekday("prev sun"),
    "start bst": bst(3),
    "end bst": bst(10),
    "start year": start_of_year,
    "end year": end_of_year,
    "next month": next_month,
    "passover": next_passover,
    "pancake day": around_easter(-47),
    "lent": around_easter(-46),
    "mlk": martin_luther_king_day,
    "mum": around_easter(-21),
    "mom": mothers_day_us,
    "mutter": mothers_day_us,
}


def _rule(*weekdays: object) -> Callable[[datetime, datetime], object]:
    return lambda start, end: rrule(freq=DAILY, dtstart=start, until=end, byweekday=weekdays)


EXCLUSION_MAP: dict[str, dict[str, object]] = {
    "weekdays": {"days": {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}, "rule": _rule(MO, TU, WE, TH, FR)},
    "wkdy": {"days": {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}, "rule": _rule(MO, TU, WE, TH, FR)},
    "weekends": {"days": {"Saturday", "Sunday"}, "rule": _rule(SA, SU)},
    "wknd": {"days": {"Saturday", "Sunday"}, "rule": _rule(SA, SU)},
    "mondays": {"days": {"Monday"}, "rule": _rule(MO)},
    "mon": {"days": {"Monday"}, "rule": _rule(MO)},
    "tuesdays": {"days": {"Tuesday"}, "rule": _rule(TU)},
    "tue": {"days": {"Tuesday"}, "rule": _rule(TU)},
    "wednesdays": {"days": {"Wednesday"}, "rule": _rule(WE)},
    "wed": {"days": {"Wednesday"}, "rule": _rule(WE)},
    "thursdays": {"days": {"Thursday"}, "rule": _rule(TH)},
    "thu": {"days": {"Thursday"}, "rule": _rule(TH)},
    "fridays": {"days": {"Friday"}, "rule": _rule(FR)},
    "fri": {"days": {"Friday"}, "rule": _rule(FR)},
    "saturdays": {"days": {"Saturday"}, "rule": _rule(SA)},
    "sat": {"days": {"Saturday"}, "rule": _rule(SA)},
    "sundays": {"days": {"Sunday"}, "rule": _rule(SU)},
    "sun": {"days": {"Sunday"}, "rule": _rule(SU)},
    "all except weekdays": {"days": {"Saturday", "Sunday"}, "rule": _rule(SA, SU)},
    "xwkdy": {"days": {"Saturday", "Sunday"}, "rule": _rule(SA, SU)},
    "all except weekends": {"days": {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}, "rule": _rule(MO, TU, WE, TH, FR)},
    "xwknd": {"days": {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}, "rule": _rule(MO, TU, WE, TH, FR)},
    "all except mondays": {"days": {"Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}, "rule": _rule(TU, WE, TH, FR, SA, SU)},
    "xmon": {"days": {"Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}, "rule": _rule(TU, WE, TH, FR, SA, SU)},
    "all except tuesdays": {"days": {"Monday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}, "rule": _rule(MO, WE, TH, FR, SA, SU)},
    "xtue": {"days": {"Monday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}, "rule": _rule(MO, WE, TH, FR, SA, SU)},
    "all except wednesdays": {"days": {"Monday", "Tuesday", "Thursday", "Friday", "Saturday", "Sunday"}, "rule": _rule(MO, TU, TH, FR, SA, SU)},
    "xwed": {"days": {"Monday", "Tuesday", "Thursday", "Friday", "Saturday", "Sunday"}, "rule": _rule(MO, TU, TH, FR, SA, SU)},
    "all except thursdays": {"days": {"Monday", "Tuesday", "Wednesday", "Friday", "Saturday", "Sunday"}, "rule": _rule(MO, TU, WE, FR, SA, SU)},
    "xthu": {"days": {"Monday", "Tuesday", "Wednesday", "Friday", "Saturday", "Sunday"}, "rule": _rule(MO, TU, WE, FR, SA, SU)},
    "all except fridays": {"days": {"Monday", "Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"}, "rule": _rule(MO, TU, WE, TH, SA, SU)},
    "xfri": {"days": {"Monday", "Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"}, "rule": _rule(MO, TU, WE, TH, SA, SU)},
    "all except saturdays": {"days": {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"}, "rule": _rule(MO, TU, WE, TH, FR, SU)},
    "exsat": {"days": {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"}, "rule": _rule(MO, TU, WE, TH, FR, SU)},
    "xsat": {"days": {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"}, "rule": _rule(MO, TU, WE, TH, FR, SU)},
    "all except sundays": {"days": {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"}, "rule": _rule(MO, TU, WE, TH, FR, SA)},
    "exsun": {"days": {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"}, "rule": _rule(MO, TU, WE, TH, FR, SA)},
    "xsun": {"days": {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"}, "rule": _rule(MO, TU, WE, TH, FR, SA)},
}
