#!/usr/bin/env python
from __future__ import annotations

import datetime as dt
import os
import re
import sys

from lxml import html

try:
    from .config import (
        CATEGORY_MAIN,
        CATEGORY_VEGETARIAN,
        DAY_PATTERN,
        IGNORED_NOTE_TITLES,
        MONTHS,
        NOTE_MAP,
        ROLES,
        TAG_NOTE_MAP,
        VEGETARIAN_TITLES,
    )
except ImportError:
    from config import (
        CATEGORY_MAIN,
        CATEGORY_VEGETARIAN,
        DAY_PATTERN,
        IGNORED_NOTE_TITLES,
        MONTHS,
        NOTE_MAP,
        ROLES,
        TAG_NOTE_MAP,
        VEGETARIAN_TITLES,
    )

try:
    from util import StyledLazyBuilder, xml_escape
except ModuleNotFoundError:
    include = os.path.relpath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, include)
    from util import StyledLazyBuilder, xml_escape


def parse_day(heading: str) -> str | None:
    clean = ' '.join(heading.replace('\xa0', ' ').split())
    clean = clean.replace('März', 'Maerz')
    match = DAY_PATTERN.search(clean)
    if not match:
        return None

    day = int(match.group(2))
    month_name = match.group(3).lower()
    month = MONTHS.get(month_name)
    if month is None:
        return None

    today = dt.date.today()
    year = today.year
    candidate = dt.date(year, month, day)

    if month == 12 and today.month == 1 and day > 20:
        candidate = dt.date(year - 1, month, day)
    elif month == 1 and today.month == 12 and day < 15:
        candidate = dt.date(year + 1, month, day)

    return candidate.isoformat()


def clean_text(txt: str | None) -> str:
    clean = re.sub(r'\s+', ' ', txt or '').strip()
    return clean.replace('Ausverkauft! ', '').strip()


def extract_notes_from_name(name: str) -> tuple[str, list[str]]:
    notes = []
    meal_name = name
    for allergen in re.findall(r'\(([^\)]*)\)', name):
        allergen = allergen.strip()
        if allergen:
            notes.append(allergen)
    meal_name = re.sub(r'\s*\([^\)]*\)', '', meal_name)
    return meal_name.strip(), notes


def expand_notes(raw_notes: list[str]) -> list[str]:
    expanded = []
    for raw_note in raw_notes:
        if not raw_note:
            continue
        parts = [part.strip() for part in raw_note.split(',') if part.strip()]
        if not parts:
            parts = [raw_note.strip()]
        for part in parts:
            expanded.append(NOTE_MAP.get(part, part))
    return expanded


def normalize_tag_note(tag: str | None) -> str | None:
    if not tag:
        return None
    normalized = tag.lower()
    if normalized == 'vegetarisch':
        return None
    return TAG_NOTE_MAP.get(normalized, tag)


def format_price(price_text: str, surcharge: float = 0.0) -> str | None:
    if not price_text:
        return None

    clean = price_text.replace('€', '').replace('EUR', '').replace('Nährwerte', '').strip()
    clean = clean.replace('.', '').replace(',', '.')
    try:
        value = float(clean) + surcharge
    except ValueError:
        return None
    return f'{value:.2f}'


def get_category(tags: list[str]) -> str:
    for tag in tags:
        if tag.lower() in VEGETARIAN_TITLES:
            return CATEGORY_VEGETARIAN
    return CATEGORY_MAIN


def extract_tags(main_div) -> list[str]:
    tags = []
    for title in main_div.xpath('.//img/@title'):
        clean_title = clean_text(title)
        if not clean_title or clean_title in IGNORED_NOTE_TITLES:
            continue
        tags.append(clean_title)
    return tags


def build_feed_xml(page_content: bytes | str, only_day: str | None = None) -> str:
    doc = html.fromstring(page_content)
    panels = doc.xpath(
        "//div[contains(concat(' ', normalize-space(@class), ' '), ' panel ') "
        "and contains(concat(' ', normalize-space(@class), ' '), ' speiseplan ')]"
    )

    builder = StyledLazyBuilder()

    for panel in panels:
        heading = ' '.join(panel.xpath(".//div[contains(@class,'panel-heading')]//text()"))
        day = parse_day(heading)
        if not day:
            continue
        if only_day and day != only_day:
            continue

        for row in panel.xpath('.//tr'):
            main_divs = row.xpath('./td[1]/div[1]')
            if not main_divs:
                continue
            main_div = main_divs[0]

            name_parts = main_div.xpath(".//strong[contains(@class,'menu_name')]//text()")
            if not name_parts:
                continue

            base_name = clean_text(' '.join(name_parts))
            extras = clean_text(' '.join(main_div.xpath('./p//text()')))
            full_name = f'{base_name} {extras}'.strip() if extras else base_name
            full_name, notes = extract_notes_from_name(full_name)
            if not full_name:
                continue

            tags = extract_tags(main_div)
            category = get_category(tags)

            price = clean_text(' '.join(row.xpath('./td[2]//text()')))
            student_price = format_price(price)
            other_price = format_price(price, surcharge=1.6)
            prices = (student_price, other_price) if student_price else ()

            clean_notes = []
            seen = set()
            tag_notes = [normalize_tag_note(tag) for tag in tags]
            for note in tag_notes + expand_notes(notes):
                if note and note.lower() not in seen:
                    seen.add(note.lower())
                    clean_notes.append(note)

            builder.addMeal(day, category, full_name, clean_notes, prices, ROLES)

    return builder.toXMLFeed()


def empty_feed(canteen_reference: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<openmensa xmlns="http://openmensa.org/open-mensa-v2" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'version="2.1" xsi:schemaLocation="http://openmensa.org/open-mensa-v2 '
        f'http://openmensa.org/open-mensa-v2.xsd"><!-- Unknown canteen: {xml_escape(canteen_reference)} --></openmensa>'
    )