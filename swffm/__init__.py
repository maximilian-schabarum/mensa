import json
import logging
import os
import sys
import urllib.parse
import datetime as dt
from typing import Any

import requests

try:
    from version import __version__, useragentname, useragentcomment
    from util import meta_from_xsl, xml_str_param
except ModuleNotFoundError:
    include = os.path.relpath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, include)
    from version import __version__, useragentname, useragentcomment
    from util import meta_from_xsl, xml_str_param

try:
    from .config import CANTEEN_JSON, META_XSLT
    from .helpers import build_feed_xml, empty_feed
except ImportError:
    from config import CANTEEN_JSON, META_XSLT
    from helpers import build_feed_xml, empty_feed


class Parser:
    canteen_json = CANTEEN_JSON
    meta_xslt = META_XSLT

    def __init__(self, url_template: str) -> None:
        with open(self.canteen_json, 'r', encoding='utf8') as f:
            self.canteens: dict[str, dict[str, Any]] = json.load(f)

        self.url_template = url_template
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': f'{useragentname}/{__version__} ({useragentcomment}) {requests.utils.default_user_agent()}',
            'Accept-Encoding': 'utf-8',
        }

    def feed(self, ref: str) -> str:
        return self._fetch_feed(ref)

    def feed_today(self, ref: str) -> str:
        return self._fetch_feed(ref, only_day=dt.date.today().isoformat())

    def _fetch_feed(self, ref: str, only_day: str | None = None) -> str:
        if ref not in self.canteens:
            return empty_feed(ref)

        source_url = self.canteens[ref]['source']
        resp = self.session.get(source_url, timeout=30)
        resp.raise_for_status()
        return build_feed_xml(resp.content, only_day=only_day)

    def meta(self, ref: str) -> str:
        if ref not in self.canteens:
            return 'Unknown canteen'

        mensa = self.canteens[ref]

        data = {
            'name': xml_str_param(mensa['name']),
            'address': xml_str_param(mensa['address']),
            'city': xml_str_param(mensa['city']),
            'latitude': xml_str_param(mensa['latitude']),
            'longitude': xml_str_param(mensa['longitude']),
            'feed': xml_str_param(self.url_template.format(metaOrFeed='feed', mensaReference=urllib.parse.quote(ref))),
            'feed_today': xml_str_param(self.url_template.format(metaOrFeed='today', mensaReference=urllib.parse.quote(ref))),
            'source': xml_str_param(mensa['source']),
        }

        if 'phone' in mensa:
            data['phone'] = xml_str_param(mensa['phone'])

        if 'times' in mensa:
            data['times'] = mensa['times']

        return meta_from_xsl(self.meta_xslt, data)

    def json(self) -> str:
        return json.dumps(
            {
                reference: self.url_template.format(
                    metaOrFeed='meta',
                    mensaReference=urllib.parse.quote(reference),
                )
                for reference in self.canteens
            },
            indent=2,
        )


def getParser(url_template: str) -> Parser:
    return Parser(url_template)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    p = Parser('http://localhost/{metaOrFeed}/swffm_{mensaReference}.xml')
    print(p.feed('mensa-casino'))