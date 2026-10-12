#!/usr/bin/env python
from __future__ import annotations

import json
import os
import sys
import urllib.parse
from typing import Any

import requests

try:
    from version import __version__, useragentcomment, useragentname
    from util import meta_from_xsl, xml_str_param
except ModuleNotFoundError:
    include = os.path.dirname(__file__)
    sys.path.insert(0, include)
    from version import __version__, useragentcomment, useragentname
    from util import meta_from_xsl, xml_str_param


class BaseParser:
    """Shared metadata, URL, and HTTP-session behavior for canteen parsers."""

    canteen_json: str
    meta_xslt: str

    def __init__(self, url_template: str, timeout: int = 30) -> None:
        with open(self.canteen_json, encoding="utf-8") as canteen_file:
            self.canteens: dict[str, dict[str, Any]] = json.load(canteen_file)

        self.url_template = url_template
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            "User-Agent": (
                f"{useragentname}/{__version__} "
                f"({useragentcomment}) "
                f"{requests.utils.default_user_agent()}"
            ),
        })

    def meta(self, canteen_reference: str) -> str:
        if not self._has_canteen(canteen_reference):
            return "Unknown canteen"

        canteen = self.canteens[canteen_reference]
        data = {
            "name": xml_str_param(canteen["name"]),
            "address": xml_str_param(canteen["address"]),
            "city": xml_str_param(canteen["city"]),
            "latitude": xml_str_param(canteen["latitude"]),
            "longitude": xml_str_param(canteen["longitude"]),
            "feed": self._feed_url("feed", canteen_reference),
            "feed_today": self._feed_url("today", canteen_reference),
            "source": xml_str_param(canteen["source"]),
        }

        if "phone" in canteen:
            data["phone"] = xml_str_param(canteen["phone"])
        if "times" in canteen:
            data["times"] = canteen["times"]

        return meta_from_xsl(self.meta_xslt, data)

    def json(self) -> str:
        return json.dumps(
            {
                reference: self.url_template.format(
                    metaOrFeed="meta",
                    mensaReference=urllib.parse.quote(reference),
                )
                for reference in self.canteens
            },
            indent=2,
        )

    def _has_canteen(self, canteen_reference: str) -> bool:
        return canteen_reference in self.canteens

    def _feed_url(self, feed_name: str, canteen_reference: str) -> Any:
        return xml_str_param(
            self.url_template.format(
                metaOrFeed=feed_name,
                mensaReference=urllib.parse.quote(canteen_reference),
            )
        )
