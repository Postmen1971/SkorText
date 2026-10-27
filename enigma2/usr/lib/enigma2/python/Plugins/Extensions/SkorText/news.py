# -*- coding: utf-8 -*-
# SkorText - Tuerkische Nachrichten (RSS/Atom)
from __future__ import absolute_import
import re
import time
import calendar
from email.utils import parsedate_tz, mktime_tz
import xml.etree.ElementTree as ET

try:
	from html import unescape as _unescape
except ImportError:  # Python 2
	from HTMLParser import HTMLParser
	_unescape = HTMLParser().unescape

from .data import Request, urlopen, _ctx, UA

# Seite, Rubrik, Quelle, Feed
FEEDS = [
	(600, u"Manşet", u"TRT Haber", "https://www.trthaber.com/manset_articles.rss"),
	(610, u"Güncel", u"Anadolu Ajansı", "https://www.aa.com.tr/tr/rss/default?cat=guncel"),
	(620, u"Dünya", u"Anadolu Ajansı", "https://www.aa.com.tr/tr/rss/default?cat=dunya"),
	(630, u"Ekonomi", u"Anadolu Ajansı", "https://www.aa.com.tr/tr/rss/default?cat=ekonomi"),
	(640, u"Spor", u"Anadolu Ajansı", "https://www.aa.com.tr/tr/rss/default?cat=spor"),
]


def clean(s):
	if not s:
		return u""
	if not isinstance(s, type(u"")):
		s = s.decode("utf-8", "replace")
	s = re.sub(r"(?s)<[^>]+>", u" ", s)
	s = _unescape(s)
	return re.sub(r"\s+", u" ", s).strip()


def parse_date(s):
	if not s:
		return 0
	s = s.strip()
	try:
		t = parsedate_tz(s)
		if t:
			return mktime_tz(t)
	except Exception:
		pass
	m = re.match(r"(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d)(?::(\d\d))?(?:\.\d+)?(Z|[+-]\d\d:?\d\d)?", s)
	if m:
		y, mo, d, h, mi, se, tz = m.groups()
		ts = calendar.timegm((int(y), int(mo), int(d), int(h), int(mi), int(se or 0), 0, 0, 0))
		if tz and tz != "Z":
			sign = 1 if tz[0] == "+" else -1
			tz = tz[1:].replace(":", "")
			ts -= sign * (int(tz[:2]) * 3600 + int(tz[2:4]) * 60)
		return ts
	return 0


def _local(tag):
	return tag.split("}")[-1] if "}" in tag else tag


def parse_feed(raw):
	if raw[:3] == b"\xef\xbb\xbf":
		raw = raw[3:]
	items = []
	try:
		root = ET.fromstring(raw)
		for el in root.iter():
			name = _local(el.tag)
			if name not in ("item", "entry"):
				continue
			it = {"title": u"", "desc": u"", "ts": 0}
			for ch in el:
				n = _local(ch.tag)
				txt = ch.text or u""
				if n == "title":
					it["title"] = clean(txt)
				elif n in ("description", "summary") and not it["desc"]:
					it["desc"] = clean(txt)
				elif n in ("pubDate", "published", "updated") and not it["ts"]:
					it["ts"] = parse_date(txt)
			if it["title"]:
				items.append(it)
	except Exception:
		# Notfall: abgeschnittene oder fehlerhafte Feeds per Muster lesen
		text = raw.decode("utf-8", "replace")
		for blk in re.findall(r"(?s)<item>(.*?)</item>", text):
			def g(tag):
				m = re.search(r"(?s)<%s[^>]*>(.*?)</%s>" % (tag, tag), blk)
				v = m.group(1) if m else u""
				return v.replace(u"<![CDATA[", u"").replace(u"]]>", u"")
			if g("title"):
				items.append({"title": clean(g("title")), "desc": clean(g("description")), "ts": parse_date(g("pubDate"))})
	return items


class Feed(object):
	def __init__(self, row):
		self.page, self.name, self.source, self.url = row
		self.items = []
		self.t_load = 0
		self.loading = False
		self.error = None

	def load(self):
		req = Request(self.url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
		last = None
		for verify in (True, False):
			ctx = _ctx(verify)
			try:
				resp = urlopen(req, timeout=12, context=ctx) if ctx is not None else urlopen(req, timeout=12)
				items = parse_feed(resp.read())
				items.sort(key=lambda x: -x["ts"])
				self.items = items[:60]
				self.t_load = time.time()
				self.error = None
				return self
			except Exception as e:
				last = e
				if "CERTIFICATE" not in str(e).upper() and "SSL" not in str(e).upper():
					break
		raise last


FEED_LIST = [Feed(r) for r in FEEDS]


def feed_by_page(p):
	for f in FEED_LIST:
		if f.page == p:
			return f
	return None
