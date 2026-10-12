#!/usr/bin/env python
from __future__ import annotations

import os

# URLs der Datenquellen
JSON_URL = (
    "https://www.speierlinghof.de/cmft_cache/"
    "cmft-cache-document-1817490367348609024-de.json"
)

# Kategorienamen im OpenMensa-Feed
CATEGORY_DEFAULT = "Hauptgericht"
CATEGORY_VEGETARIAN = "Vegetarisch"

# Einträge außerhalb dieses Fensters (in Tagen) werden ausgefiltert.
DATE_WINDOW_DAYS = 31

# Wochentage in der Reihenfolge, wie sie im JSON-Payload vorkommen.
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday")

# Schlüsselwörter, die einen geschlossenen Tag signalisieren.
CLOSURE_KEYWORDS = ("geschlossen", "feiertag", "brückentag", "brueckentag", "ruhetag")

# Pfade zu statischen Dateien.
BASE_DIR = os.path.dirname(__file__)
META_JSON = os.path.join(BASE_DIR, "canteenDict.json")
META_XSLT = os.path.join(BASE_DIR, "../meta.xsl")
