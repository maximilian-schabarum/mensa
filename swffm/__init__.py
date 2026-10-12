import logging
import os
import sys
import datetime as dt

try:
    from parser_base import BaseParser
except ModuleNotFoundError:
    include = os.path.relpath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, include)
    from parser_base import BaseParser

try:
    from .config import CANTEEN_JSON, META_XSLT
    from .helpers import build_feed_xml, empty_feed
except ImportError:
    from config import CANTEEN_JSON, META_XSLT
    from helpers import build_feed_xml, empty_feed


class Parser(BaseParser):
    canteen_json = CANTEEN_JSON
    meta_xslt = META_XSLT

    def __init__(self, url_template: str, timeout: int = 30) -> None:
        super().__init__(url_template, timeout)

    def feed(self, ref: str) -> str:
        return self._fetch_feed(ref)

    def feed_today(self, ref: str) -> str:
        return self._fetch_feed(ref, only_day=dt.date.today().isoformat())

    def _fetch_feed(self, ref: str, only_day: str | None = None) -> str:
        if not self._has_canteen(ref):
            return empty_feed(ref)

        source_url = self.canteens[ref]['source']
        response = self.session.get(source_url, timeout=self.timeout)
        response.raise_for_status()
        return build_feed_xml(response.content, only_day=only_day)


def getParser(url_template: str) -> Parser:
    return Parser(url_template)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    p = Parser('http://localhost/{metaOrFeed}/swffm_{mensaReference}.xml')
    print(p.feed('mensa-casino'))