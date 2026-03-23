#!/usr/bin/env python
from __future__ import annotations

import os
import re

# URLs der Datenquellen
JSON_URL = (
    "https://www.speierlinghof.de/cmft_cache/"
    "cmft-cache-document-1817490367348609024-de.json"
)
VERPFLEGUNG_URL = "https://www.uni-speyer.de/service/soziales/verpflegung"

# Kategorienamen im OpenMensa-Feed
CATEGORY_DEFAULT = "Hauptgericht"
CATEGORY_VEGETARIAN = "Vegetarisch"

# Tage die älter als dieser Schwellwert sind, gelten als veraltet und werden
# auf die aktuelle Woche remappt.
MAX_STALE_DATE_DAYS = 92

# Einträge außerhalb dieses Fensters (in Tagen) werden ausgefiltert.
DATE_WINDOW_DAYS = 31

# Wochentage in der Reihenfolge, wie sie im JSON-Payload vorkommen.
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday")

# Schlüsselwörter, die einen geschlossenen Tag signalisieren.
CLOSURE_KEYWORDS = ("geschlossen", "feiertag", "brückentag", "brueckentag", "ruhetag")

# Pfade zu statischen Dateien.
BASE_DIR = os.path.dirname(__file__)
META_JSON = os.path.join(BASE_DIR, "canteenDict.json")
META_TEMPLATE_FILE = os.path.join(BASE_DIR, "metaTemplate.xml")

# Kompilierte Regex-Muster für PDF-basierte Vegetarisch-Erkennung.
RE_MEAT_OR_FISH = re.compile(
    r"schnitzel|hack(?:braten|fleisch|bällchen)?"
    r"|gulasch|sauerbraten|roulade"
    r"|fleisch"
    r"|rind(?:er(?:braten|filet|steak|gulasch|roulade|fleisch)?)?"
    r"|schwein(?:e(?:braten|fleisch|schnitzel|kotelett|haxe|filet)?)?"
    r"|pute(?:n(?:brust|braten|schnitzel|filet)?)?"
    r"|ente(?:n(?:braten|keule|brust)?)?"
    r"|kalb(?:s(?:braten|schnitzel|filet|leber)?)?"
    r"|lamm(?:(?:keule|rücken|kotelett|fleisch))?"
    r"|h[äa]hnchen|h[üu]hn(?:chen|er)?"
    r"|huhn|gefl[üu]gel|truthahn"
    r"|wurst|currywurst|bratwurst|leberwurst|blutwurst|bockwurst|weißwurst|weisswurst"
    r"|schinken|speck|salami|kassler|gyros"
    r"|boulette|frikadelle|bulette"
    r"|cordon.?bleu|fricass[eé]e?|cevapcici"
    r"|fisch|lachs|thunfisch|forelle|hering|sardine|garnelen?|meeresfrüchte|meeresfruchte"
    r"|bolognese|leberkäse|leberkaese",
    re.IGNORECASE,
)

RE_VEGETARIAN = re.compile(
    r"vegetarisch|vegan"
    r"|gem[üu]se"
    r"|tofu|seitan|tempeh"
    r"|linsen|kichererbsen?"
    r"|spinat|zucchini|pilze?|champignon"
    r"|brokkoli|blumenkohl|erbsen|rote.?bete|rüben|rübe"
    r"|quark|apfel|kartoffel|spargel|puffer"
    r"|auflauf|lasagne|caprese"
    r"|kürbis|paprika(?:gemüse|ragout|topf)"
    r"|käsespätzle|k[äa]sesp[äa]tzle",
    re.IGNORECASE,
)
