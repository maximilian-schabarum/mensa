#!/usr/bin/env python
from __future__ import annotations

import os
import re

BASE_DIR = os.path.dirname(__file__)
CANTEEN_JSON = os.path.join(BASE_DIR, 'canteenDict.json')
META_XSLT = os.path.join(BASE_DIR, '../meta.xsl')

ROLES = ('student', 'other')

CATEGORY_MAIN = 'Hauptgericht'
CATEGORY_VEGETARIAN = 'Vegetarisch'

DAY_PATTERN = re.compile(
    r'^(Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag),?\s*(\d{1,2})\.\s*([A-Za-zÄÖÜäöü]+)',
    flags=re.IGNORECASE,
)

MONTHS = {
    'januar': 1,
    'februar': 2,
    'maerz': 3,
    'märz': 3,
    'april': 4,
    'mai': 5,
    'juni': 6,
    'juli': 7,
    'august': 8,
    'september': 9,
    'oktober': 10,
    'november': 11,
    'dezember': 12,
}

IGNORED_NOTE_TITLES = {'CO2', 'Stern', 'Tier', 'Wald', 'Wasser'}
VEGETARIAN_TITLES = {'vegetarisch', 'vegan'}

TAG_NOTE_MAP = {
    'vegan': 'vegan',
    'mensavital': 'mensaVital',
    'msc': 'MSC',
    'msc-fisch': 'MSC',
    'rind': 'Rind',
    'schwein': 'Schwein',
    'geflügel': 'Geflügel',
    'gefluegel': 'Geflügel',
    'lamm': 'Lamm',
    'wild': 'Wild',
    'alkohol': 'Alkohol',
}

NOTE_MAP = {
    '1': 'mit Farbstoff',
    '2': 'konserviert',
    '3': 'mit Antioxidationsmittel',
    '4': 'mit Geschmacksverstaerker',
    '5': 'geschwefelt',
    '6': 'geschwaerzt',
    '7': 'gewachst',
    '8': 'mit Phosphat',
    '9': 'mit Suessungsmitteln',
    '10': 'enthaelt eine Phenylalaninquelle',
    'A': 'Glutenhaltige Getreide',
    'A1': 'Weizen',
    'A2': 'Roggen',
    'A3': 'Gerste',
    'A4': 'Hafer',
    'A5': 'Dinkel',
    'A6': 'Kamut',
    'B': 'Krebstiere und Krebserzeugnisse',
    'C': 'Eier und Eiererzeugnisse',
    'D': 'Fisch und Fischerzeugnisse',
    'E': 'Erdnuesse und Erdnusserzeugnisse',
    'F': 'Soja und Sojaerzeugnisse',
    'G': 'Milch und Milcherzeugnisse',
    'H': 'Schalenfruechte und Nuesse',
    'H1': 'Mandeln',
    'H2': 'Haselnuesse',
    'H3': 'Walnuesse',
    'H4': 'Cashewnuesse',
    'H5': 'Pecannuesse',
    'H6': 'Paranuesse',
    'H7': 'Pistazien',
    'H8': 'Macadamianuesse',
    'I': 'Sellerie und Sellerieerzeugnisse',
    'J': 'Senf und Senferzeugnisse',
    'K': 'Sesam und Sesamerzeugnisse',
    'L': 'Schwefeldioxid / Sulfit',
    'M': 'Lupine und Lupinenerzeugnisse',
    'N': 'Weichtiere und Weichtiererzeugnisse',
}