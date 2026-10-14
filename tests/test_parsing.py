import pytest

from src.scraper.parsing import first_number, parse_duration


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("PT30M", 30),
        ("PT1H30M", 90),
        ("P1D", 1440),
        ("P1DT2H", 1560),
        ("PT45S", 1),
        ("PT", None),
        ("", None),
        (None, None),
        ("30 минут", None),
    ],
)
def test_parse_duration(value, expected):
    assert parse_duration(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("238 ккал", 238.0),
        ("1,5 кг", 1.5),
        ("8", 8.0),
        ("по вкусу", None),
        (None, None),
    ],
)
def test_first_number(value, expected):
    assert first_number(value) == expected