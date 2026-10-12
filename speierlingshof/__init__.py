#!/usr/bin/env python
from __future__ import annotations

import datetime as dt
import logging
import os
import sys

try:
    from parser_base import BaseParser
except ModuleNotFoundError:
    include = os.path.relpath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, include)
    from parser_base import BaseParser

try:
    from .config import JSON_URL, META_JSON, META_XSLT
    from .helpers import (
        build_feed_xml,
        empty_feed,
        filter_by_date_window,
        parse_json_menu,
    )
except ImportError:
    from config import JSON_URL, META_JSON, META_XSLT
    from helpers import (
        build_feed_xml,
        empty_feed,
        filter_by_date_window,
        parse_json_menu,
    )


class Parser(BaseParser):
    canteen_json = META_JSON
    meta_xslt = META_XSLT

    def __init__(self, url_template: str, timeout: int = 25) -> None:
        super().__init__(url_template, timeout)

    def feed(self, canteen_reference: str) -> str:
        return self._build_feed(canteen_reference)

    def _build_feed(self, canteen_reference: str) -> str:
        if not self._has_canteen(canteen_reference):
            return empty_feed(canteen_reference)
        return build_feed_xml(self._load_days(), include_weekend_closure=False)

    def feed_today(self, canteen_reference: str) -> str:
        return self._build_feed(canteen_reference)

    def _load_days(self) -> list[dict[str, Any]]:
        today = dt.date.today()

        try:
            jsonDays = self._fetch_json_menu()
            filteredDays = filter_by_date_window(jsonDays, today)
            logging.debug(
                "Speierlingshof JSON verwendet: parsed=%d filtered=%d today=%s",
                len(jsonDays),
                len(filteredDays),
                today,
            )
            return filteredDays
        except Exception:
            logging.warning(
                "Speierlingshof JSON-Abruf/Parsing fehlgeschlagen",
                exc_info=True,
            )
            return []

    def _fetch_json_menu(self) -> list[dict[str, Any]]:
        response = self.session.get(JSON_URL, timeout=self.timeout)
        response.raise_for_status()
        return parse_json_menu(response.json())


def getParser(url_template: str) -> Parser:
    """Erstelle einen Parser mit dem angegebenen URL-Template."""
    return Parser(url_template)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    p = Parser("http://localhost/{metaOrFeed}/speierlingshof_{mensaReference}.xml")
    for ref in p.canteens:
        print(p.meta(ref))
        print(p.feed(ref))
