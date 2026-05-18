import datetime as dt

from speierlingshof.helpers import parse_date


def test_parse_date_prefers_four_digit_year() -> None:
    assert parse_date("Montag 18.05.2026") == dt.date(2026, 5, 18)


def test_parse_date_two_digit_year_still_supported() -> None:
    assert parse_date("Montag 18.05.26") == dt.date(2026, 5, 18)
