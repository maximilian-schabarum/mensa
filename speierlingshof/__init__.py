#!/usr/bin/env python
from __future__ import annotations

import datetime as dt
import json
import logging
import os
import sys
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

try:
    from version import __version__, useragentname, useragentcomment
    from util import meta_from_xsl, xml_str_param
except ModuleNotFoundError:
    include = os.path.relpath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, include)
    from version import __version__, useragentname, useragentcomment
    from util import meta_from_xsl, xml_str_param

try:
    from .config import JSON_URL, META_JSON, META_XSLT, VERPFLEGUNG_URL
    from .helpers import (
        build_feed_xml,
        empty_feed,
        filter_by_date_window,
        parse_json_menu,
        parse_pdf_menu,
    )
except ImportError:
    from config import JSON_URL, META_JSON, META_XSLT, VERPFLEGUNG_URL
    from helpers import (
        build_feed_xml,
        empty_feed,
        filter_by_date_window,
        parse_json_menu,
        parse_pdf_menu,
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
        if canteenReference not in self.canteens:
            return empty_feed(canteenReference)
        return build_feed_xml(self._load_days(), include_weekend_closure=False)

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

        data = {
            "name": xml_str_param(mensa["name"]),
            "address": xml_str_param(mensa["address"]),
            "city": xml_str_param(mensa["city"]),
            "latitude": xml_str_param(mensa["latitude"]),
            "longitude": xml_str_param(mensa["longitude"]),
            "feed": feed_url,
            "feed_today": feed_url,
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
            if filteredDays:
                return filteredDays
        except Exception:
            logging.debug("JSON-Abruf fehlgeschlagen, versuche PDF-Fallback", exc_info=True)

        try:
            pdfDays = self._fetch_pdf_menu()
            return filter_by_date_window(pdfDays, today)
        except Exception:
            logging.debug("PDF-Fallback fehlgeschlagen", exc_info=True)
            return []

    def _fetch_json_menu(self) -> list[dict[str, Any]]:
        response = self.session.get(JSON_URL, timeout=self.timeout)
        response.raise_for_status()
        days = parse_json_menu(response.json())
        return days

    def _fetch_pdf_menu(self) -> list[dict[str, Any]]:
        pdfUrl = self._find_pdf_url()
        lines  = self._download_pdf_as_lines(pdfUrl)
        return parse_pdf_menu(lines)

    def _find_pdf_url(self) -> str:
        response = self.session.get(VERPFLEGUNG_URL, timeout=self.timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        node = soup.select_one("footer [title='Download Speiseplan']")
        if node and node.get("href"):
            return requests.compat.urljoin(VERPFLEGUNG_URL, str(node["href"]))

        for anchor in soup.find_all("a", href=True):
            linkText = (anchor.get_text(" ") or "").casefold()
            href     = str(anchor["href"])
            if "speiseplan" in linkText or href.casefold().endswith(".pdf"):
                return requests.compat.urljoin(VERPFLEGUNG_URL, href)

        raise ValueError("PDF-Link nicht gefunden.")

    def _download_pdf_as_lines(self, pdfUrl: str) -> list[str]:
        response = self.session.get(pdfUrl, timeout=self.timeout)
        response.raise_for_status()

        tmpPath: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(response.content)
                tmp.flush()  
                tmpPath = Path(tmp.name)

            reader = PdfReader(str(tmpPath))
            text   = "\n".join(page.extract_text() or "" for page in reader.pages)
        finally:
            if tmpPath and tmpPath.exists():
                tmpPath.unlink(missing_ok=True)

        return [line.strip() for line in text.splitlines()]


def getParser(urlTemplate: str) -> Parser:
    """Erstelle einen Parser mit dem angegebenen URL-Template."""
    return Parser(urlTemplate)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    p = Parser("http://localhost/{metaOrFeed}/speierlingshof_{mensaReference}.xml")
    for ref in p.canteens:
        print(p.meta(ref))
        print(p.feed(ref))
