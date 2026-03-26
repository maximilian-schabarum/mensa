import json
import logging
import os
import sys
import urllib.parse
import datetime as dt

import requests

try:
    from version import __version__, useragentname, useragentcomment
    from util import meta_from_xsl, xml_escape, xml_str_param
except ModuleNotFoundError:
    include = os.path.relpath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, include)
    from version import __version__, useragentname, useragentcomment
    from util import meta_from_xsl, xml_escape, xml_str_param

try:
    from .config import CANTEEN_JSON, META_XSLT
    from .helpers import build_feed_xml, empty_feed
except ImportError:
    from config import CANTEEN_JSON, META_XSLT
    from helpers import build_feed_xml, empty_feed


class Parser:
    canteen_json = CANTEEN_JSON
    meta_xslt = META_XSLT

    def __init__(self, url_template):
        with open(self.canteen_json, 'r', encoding='utf8') as f:
            self.canteens = json.load(f)

        self.url_template = url_template
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': f'{useragentname}/{__version__} ({useragentcomment}) {requests.utils.default_user_agent()}',
            'Accept-Encoding': 'utf-8',
        }

    def feed(self, ref):
        if ref not in self.canteens:
            return empty_feed(ref)

        source_url = self.canteens[ref]['source']
        resp = self.session.get(source_url, timeout=30)
        resp.raise_for_status()
        return build_feed_xml(resp.content)

    def feed_today(self, ref):
        if ref not in self.canteens:
            return empty_feed(ref)

        source_url = self.canteens[ref]['source']
        resp = self.session.get(source_url, timeout=30)
        resp.raise_for_status()
        return build_feed_xml(resp.content, only_day=dt.date.today().isoformat())

    def meta(self, ref):
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
            mensa['phone'] = xml_str_param(mensa['phone'])

        if 'times' in mensa:
            data['times'] = mensa['times']

        return meta_from_xsl(self.meta_xslt, data)

    def json(self):
        tmp = {}
        for reference in self.canteens:
            tmp[reference] = self.url_template.format(
                metaOrFeed='meta', mensaReference=urllib.parse.quote(reference)
            )
        return json.dumps(tmp, indent=2)


def getParser(url_template):
    return Parser(url_template)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    p = Parser('http://localhost/{metaOrFeed}/swffm_{mensaReference}.xml')
    print(p.feed('mensa-casino'))