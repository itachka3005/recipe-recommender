import re

from bs4 import Tag

DURATION = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
TRAILING_DASH = " —–-"


class ParseError(Exception):
    """Page does not contain a valid recipe."""


def parse_duration(value: str | None) -> int | None:
    if not value:
        return None
    match = DURATION.match(value.strip())
    if not match or not any(match.groups()):
        return None
    days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return days * 1440 + hours * 60 + minutes + round(seconds / 60)


def first_number(value: str | None) -> float | None:
    if not value:
        return None
    match = NUMBER.search(value)
    return float(match.group(0).replace(",", ".")) if match else None


def collapse_spaces(text: str) -> str:
    return " ".join(text.split())


def prop_value(el: Tag) -> str:
    for attr in ("content", "datetime"):
        value = el.get(attr)
        if value:
            return collapse_spaces(str(value))
    return collapse_spaces(el.get_text(" ", strip=True))


def clean_ingredient(text: str) -> str:
    return text.rstrip(TRAILING_DASH).strip()


def own_props(scope: Tag, name: str) -> list[Tag]:
    result = []
    for el in scope.find_all(attrs={"itemprop": name}):
        if el.find_parent(attrs={"itemscope": True}) is scope:
            result.append(el)
    return result