#!/usr/bin/env python
from __future__ import annotations

import datetime as dt
import os
import re
import sys
from typing import Any

try:
    from .config import (
        CATEGORY_DEFAULT,
        CATEGORY_VEGETARIAN,
        CLOSURE_KEYWORDS,
        DATE_WINDOW_DAYS,
        MAX_STALE_DATE_DAYS,
        RE_MEAT_OR_FISH,
        RE_VEGETARIAN,
        WEEKDAYS,
    )
except ImportError:
    from config import (
        CATEGORY_DEFAULT,
        CATEGORY_VEGETARIAN,
        CLOSURE_KEYWORDS,
        DATE_WINDOW_DAYS,
        MAX_STALE_DATE_DAYS,
        RE_MEAT_OR_FISH,
        RE_VEGETARIAN,
        WEEKDAYS,
    )

try:
    from util import StyledLazyBuilder, xml_escape, weekdays_map
except ModuleNotFoundError:
    include = os.path.relpath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, include)
    from util import StyledLazyBuilder, xml_escape, weekdays_map

def parse_json_menu(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse die JSON-Nutzdaten in eine Liste von Tagesdatensätzen."""
    days: list[dict[str, Any]] = []

    for block in payload.get("cmftData", {}).get("content", []):
        if block.get("contentElementTyp") != "weeklyMenu":
            continue

        for week in block.get("weeklyMenu", []):
            for weekday in WEEKDAYS:
                day_data = week.get(weekday, {})
                date_label = day_data.get(f"{weekday}AdditionalTitle")
                if not date_label:
                    continue

                date = parse_date(str(date_label))
                if date is None:
                    continue

                if is_closure_text(str(date_label)):
                    days.append({"date": date, "source": "JSON", "meals": [], "closed": True})
                    continue

                meals = build_meals_from_json(day_data.get(f"{weekday}FoodOffer", []))
                closed = meals is None
                days.append({
                    "date": date,
                    "source": "JSON",
                    "meals": [] if closed else meals,
                    "closed": closed,
                })

    days.sort(key=lambda d: d["date"])
    return days


def build_meals_from_json(food_offers: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    """Baue Meals aus JSON-FoodOffer-Einträgen oder gib None für geschlossene Tage zurück."""
    meals: list[dict[str, Any]] = []
    for offer in food_offers:
        for meal in offer.get("meal", []):
            title = clean_title(str(meal.get("title", "")))
            if not title:
                continue
            if is_closure_text(title):
                return None
            is_vegetarian = is_vegetarian_category(str(meal.get("category", "")))
            notes = extract_nutrition_notes(meal.get("nutritions", []))
            meals.append(
                {
                    "title": title,
                    "category": CATEGORY_VEGETARIAN if is_vegetarian else CATEGORY_DEFAULT,
                    "notes": notes,
                }
            )
    return meals


def parse_pdf_menu(lines: list[str]) -> list[dict[str, Any]]:
    """Parse PDF-Textzeilen in Tagesdatensätze."""
    days: list[dict[str, Any]] = []
    current_day: dict[str, Any] | None = None
    skip_next_line = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if skip_next_line:
            date = parse_date(line)
            if date is not None:
                current_day = {"date": date, "source": "PDF", "meals": []}
                days.append(current_day)
                skip_next_line = False
            continue

        if re.search(r"Suppe\s*[–-]", line):
            skip_next_line = True
            continue

        date = parse_date(line)
        if date is not None:
            current_day = {"date": date, "source": "PDF", "meals": []}
            days.append(current_day)
            continue

        if current_day is not None:
            if is_closure_text(line):
                current_day["closed"] = True
                continue
            meal = classify_pdf_line(line)
            if meal:
                current_day["meals"].append(meal)

    days.sort(key=lambda d: d["date"])
    return days


def parse_date(text: str) -> dt.date | None:
    """Parse TT.MM.JJ oder TT.MM.JJJJ aus einem Text."""
    match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{2}|\d{4})", text)
    if not match:
        return None
    day, month, year_raw = int(match.group(1)), int(match.group(2)), int(match.group(3))
    year = 2000 + year_raw if year_raw < 100 else year_raw
    try:
        return dt.date(year, month, day)
    except ValueError:
        return None


def is_closure_text(text: str) -> bool:
    """Erkenne Hinweise auf geschlossene Tage wie Feiertag oder Brückentag."""
    lower = text.casefold()
    return any(keyword in lower for keyword in CLOSURE_KEYWORDS)


def is_vegetarian_category(category: str) -> bool:
    """Mappe bekannte JSON-Kategorien auf vegetarisch oder nicht."""
    key = re.sub(r"[^a-z]", "", category.casefold())
    return key in ("vegetariandishes", "soupwithoutmeat")


def looks_vegetarian(title: str) -> bool:
    """Heuristik für PDF-Gerichte ohne strukturierte Kategorieangabe."""
    if RE_MEAT_OR_FISH.search(title):
        return False
    return bool(RE_VEGETARIAN.search(title))


def classify_pdf_line(title: str) -> dict[str, Any] | None:
    """Klassifiziere eine einzelne PDF-Zeile als Gericht oder ignoriere sie."""
    title = clean_title(title)

    ignored_words = (
        "brueckentag",
        "geschlossen",
        "nitritpoekelsalz",
        "montag",
        "dienstag",
        "mittwoch",
        "donnerstag",
        "freitag",
        "samstag",
        "sonntag",
    )
    if any(word in title.casefold() for word in ignored_words):
        return None

    category = CATEGORY_VEGETARIAN if looks_vegetarian(title) else CATEGORY_DEFAULT
    if not title.endswith("*"):
        title = f"{title}*"

    return {"title": title, "category": category, "notes": []}


def clean_title(title: str) -> str:
    """Entferne Zusatzziffern und normalize Leerzeichen."""
    cleaned = re.sub(r"\(\s*\d+(?:\s*,\s*\d+)*\s*\)", "", title)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip(" -\t\r\n")


def extract_nutrition_notes(nutritions: Any) -> list[str]:
    """Extrahiere Notiztexte aus dem JSON-Feld nutritions."""
    if not isinstance(nutritions, list):
        return []

    notes: list[str] = []
    for item in nutritions:
        value = str(item.get("title", "") if isinstance(item, dict) else item).strip()
        if value:
            notes.append(value)
    return notes


def filter_by_date_window(
    days: list[dict[str, Any]],
    reference_date: dt.date,
    window_days: int = DATE_WINDOW_DAYS,
) -> list[dict[str, Any]]:
    """Behalte nur Tage innerhalb des konfigurierten Datumsfensters."""
    return sorted(
        (day for day in days if abs((day["date"] - reference_date).days) <= window_days),
        key=lambda day: day["date"],
    )


def realign_stale_dates(
    days: list[dict[str, Any]],
    today: dt.date,
    max_stale_days: int = MAX_STALE_DATE_DAYS,
) -> list[dict[str, Any]]:
    """Mappe veraltete Wochen auf die aktuelle Kalenderwoche um."""
    if not days:
        return days
    if any(abs((day["date"] - today).days) <= max_stale_days for day in days):
        return days

    week_start = today - dt.timedelta(days=today.weekday())
    realigned = []
    for day in days:
        copy = day.copy()
        copy["date"] = week_start + dt.timedelta(days=day["date"].weekday())
        realigned.append(copy)

    realigned.sort(key=lambda day: day["date"])
    return realigned


def build_feed_xml(days: list[dict[str, Any]], include_weekend_closure: bool = True) -> str:
    """Erzeuge den OpenMensa-XML-Feed aus Tagesdatensätzen."""
    builder = StyledLazyBuilder()

    for day in days:
        if day.get("closed"):
            builder.setDayClosed(day["date"])
            continue
        for meal in day["meals"]:
            title = meal["title"].strip()
            if title:
                builder.addMeal(day["date"], meal["category"], title, notes=meal["notes"])

    if days and include_weekend_closure:
        first_date = min(d["date"] for d in days)
        last_date = max(d["date"] for d in days)
        week_start = first_date - dt.timedelta(days=first_date.weekday())
        week_end = last_date + dt.timedelta(days=6 - last_date.weekday())
        current = week_start
        while current <= week_end:
            if current.weekday() in (5, 6):
                builder.setDayClosed(current)
            current += dt.timedelta(days=1)

    return builder.toXMLFeed()


def empty_feed(canteen_reference: str) -> str:
    """Erzeuge einen leeren Feed für unbekannte Mensa-Referenzen."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<openmensa xmlns="http://openmensa.org/open-mensa-v2" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'version="2.1" xsi:schemaLocation="http://openmensa.org/open-mensa-v2 '
        f'http://openmensa.org/open-mensa-v2.xsd">'
        f'<!-- Unbekannte Mensa: {xml_escape(canteen_reference)} -->'
        "</openmensa>"
    )
