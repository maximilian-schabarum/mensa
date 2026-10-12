#!/usr/bin/env python
from __future__ import annotations

import datetime as dt
import json
import logging
import os
import sys
import urllib.parse
from typing import Any

import requests

try:
    from version import __version__, useragentname, useragentcomment
    from util import meta_from_xsl, xml_str_param
except ModuleNotFoundError:
    include = os.path.relpath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, include)
    from version import __version__, useragentname, useragentcomment
    from util import meta_from_xsl, xml_str_param

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


class Parser:
    def __init__(self, urlTemplate: str, timeout: int = 25) -> None:
        with open(META_JSON, encoding="utf-8") as f:
            self.canteens: dict[str, Any] = json.load(f)

        self.urlTemplate = urlTemplate
        self.timeout     = timeout
        self.session     = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                f"{useragentname}/{__version__} "
                f"({useragentcomment}) "
                f"{requests.utils.default_user_agent()}"
            ),
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
        })

    def feed(self, canteenReference: str) -> str:
        return self._build_feed(canteenReference)

    def _build_feed(self, canteenReference: str) -> str:
        if canteenReference not in self.canteens:
            return empty_feed(canteenReference)
        return build_feed_xml(self._load_days(), include_weekend_closure=False)

    def feed_today(self, canteenReference: str) -> str:
        return self._build_feed(canteenReference)

    def meta(self, canteenReference: str) -> str:
        if canteenReference not in self.canteens:
            return 'Unknown canteen'

        mensa = self.canteens[canteenReference]
        feed_url = xml_str_param(
            self.urlTemplate.format(
                metaOrFeed="feed",
                mensaReference=urllib.parse.quote(canteenReference),
            )
        )
        feed_today_url = xml_str_param(
            self.urlTemplate.format(
                metaOrFeed="today",
                mensaReference=urllib.parse.quote(canteenReference),
            )
        )

        data = {
            "name": xml_str_param(mensa["name"]),
            "address": xml_str_param(mensa["address"]),
            "city": xml_str_param(mensa["city"]),
            "latitude": xml_str_param(mensa["latitude"]),
            "longitude": xml_str_param(mensa["longitude"]),
            "feed": feed_url,
            "feed_today": feed_today_url,
            "source": xml_str_param(mensa["source"]),
        }

        if "phone" in mensa:
            data["phone"] = xml_str_param(mensa["phone"])

        if "times" in mensa:
            data["times"] = mensa["times"]

        return meta_from_xsl(META_XSLT, data)

    def json(self) -> str:
        return json.dumps(
            {
                ref: self.urlTemplate.format(
                    metaOrFeed="meta",
                    mensaReference=urllib.parse.quote(ref),
                )
                for ref in self.canteens
            },
            indent=2,
        )

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


def getParser(urlTemplate: str) -> Parser:
    """Erstelle einen Parser mit dem angegebenen URL-Template."""
    return Parser(urlTemplate)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    p = Parser("http://localhost/{metaOrFeed}/speierlingshof_{mensaReference}.xml")
    for ref in p.canteens:
        print(p.meta(ref))
        print(p.feed(ref))
