# -*- coding: utf-8 -*-
"""ARD Text (ard-text.de) als Online-Videotext in SkorText anzeigen.

Die klassische Webseite liefert jede Tafel als 23 Zeilen mit Farben (fg/bg) und
Mosaik-Grafiken (kleine Bilder g1<farbe><hex>.gif).  Daraus werden Zeilen mit
(spalte, breite, text, vordergrund, hintergrund) im 40-Spalten-Raster.
"""
from __future__ import unicode_literals

import re
import time

try:
	from html import unescape as _unescape
except ImportError:  # Python 2
	from HTMLParser import HTMLParser
	_unescape = HTMLParser().unescape

ARD_URL = "https://www.ard-text.de/index.php?page=%s"
ARD_COLS = 40
ARD_ROWS = 23
# Farbnamen der ARD-Seite -> SkorText-Farben
ARD_COL = {"w": "w", "g": "g", "bl": "b", "c": "c", "y": "y", "r": "r", "m": "m", "b": "k"}

_SPAN = re.compile(r"<span class='fg(\w+) bg(\w+)' style='width:(\d+)px;'><nobr>(.*?)</nobr></span>", re.S)
_ROW = re.compile(r"<div>(<span.*?)</div>", re.S)
_IMG = re.compile(r"<img src='[^']*?g\d[a-z]+([0-9a-f]{2})\.gif'>")
_TAG = re.compile(r"<[^>]+>")
_LINK = re.compile(r"(?<!\d)([1-8]\d\d)(?!\d)")


def find_links(rows):
	"""Seitennummern (100-899) auf der Tafel: [(zeile, spalte, nummer)] - zum Ansteuern ohne Zifferntasten."""
	out = []
	for ri, r in enumerate(rows):
		line = u"".join(s[2] for s in r)
		for m in _LINK.finditer(line):
			out.append((ri, m.start(), int(m.group(1))))
	return out


def mosaic(code):
	"""Videotext-Mosaikzeichen (2x3 Bloecke) grob als Blockzeichen darstellen."""
	b = code & 0x5f
	tl, tr, ml, mr, bl, br = b & 1, b & 2, b & 4, b & 8, b & 16, b & 64
	n = sum(1 for x in (tl, tr, ml, mr, bl, br) if x)
	if n == 0:
		return u" "
	if n >= 5:
		return u"█"
	top, bot = bool(tl or tr), bool(bl or br)
	left = not (tr or mr or br)
	right = not (tl or ml or bl)
	if left:
		return u"▌"
	if right:
		return u"▐"
	if top and not bot:
		return u"▀"
	if bot and not top:
		return u"▄"
	return u"█" if n >= 3 else (u"▀" if (tl or tr) else u"▄")


def _text(inner):
	inner = _IMG.sub(lambda m: u"\x00%s\x00" % m.group(1), inner)
	inner = _TAG.sub(u"", inner)
	inner = _unescape(inner.replace(u"&nbsp;", u" "))
	inner = re.sub(u"\x00([0-9a-f]{2})\x00", lambda m: mosaic(int(m.group(1), 16)), inner)
	return inner.replace(u"\xa0", u" ")


def parse(html):
	"""-> {"page", "sub", "nsub", "rows": [[(col, w, text, fg, bg)]], "fast": {farbe: seite}}"""
	out = {"page": None, "sub": 1, "nsub": 1, "rows": [], "fast": {}}
	m = re.search(r'class="hiddenpagenumber"[^>]*>(\d{3})<', html)
	if m:
		out["page"] = int(m.group(1))
	m = re.search(r'subpageCounter">\s*(\d+)\s*/\s*(\d+)\s*<', html)
	if m:
		out["sub"], out["nsub"] = int(m.group(1)), max(1, int(m.group(2)))
	for col in ("red", "green", "yellow", "blue"):
		m = re.search(r'class="field %s"[^>]*href="[^"]*page=(\d{3})' % col, html)
		if m:
			out["fast"][col] = int(m.group(1))
	i = html.find("<div id='page_1'>")
	if i < 0:
		return out
	j = html.find('<div class="row', i)
	chunk = html[i:j if j > i else i + 200000]
	for rm in _ROW.finditer(chunk):
		segs, col = [], 0
		for sm in _SPAN.finditer(rm.group(1)):
			fg, bg, px, inner = sm.group(1), sm.group(2), int(sm.group(3)), sm.group(4)
			w = px // 10
			if w <= 0:
				continue
			txt = _text(inner)
			txt = (txt + u" " * w)[:w]
			segs.append((col, w, txt, ARD_COL.get(fg, "w"), ARD_COL.get(bg, "k")))
			col += w
		out["rows"].append(segs)
		if len(out["rows"]) >= ARD_ROWS:
			break
	out["links"] = find_links(out["rows"])
	return out


class ArdText(object):
	"""Merkt sich die aktuelle Tafel und haelt einen kleinen Zwischenspeicher."""

	def __init__(self):
		self.page = 100
		self.sub = 1
		self.data = None
		self.loading = False
		self.error = None
		self.t_load = 0
		self.cache = {}
		self.want = 100
		self.sel = 0       # markierte Seitennummer (Index in data["links"])
		self.hist = []     # zuvor angesehene Seiten (fuer ZURUECK)

	def url(self, page, sub=1, direction=None):
		q = u"%d" % page
		if sub and sub > 1:
			q += u"&sub=%d" % sub
		if direction:
			q += u"&dir=%s" % direction
		return ARD_URL % q

	def load(self, fetch_text, page, sub=1, direction=None):
		"""Holt eine Tafel (fetch_text = Funktion url -> html). Gibt das Ergebnis zurueck."""
		key = (page, sub, direction)
		hit = self.cache.get(key)
		if hit and time.time() - hit[0] < 60:
			d = hit[1]
		else:
			d = parse(fetch_text(self.url(page, sub, direction)))
			if not d["rows"]:
				raise Exception("Seite %d nicht gefunden" % page)
			self.cache[key] = (time.time(), d)
			if len(self.cache) > 40:
				for k in sorted(self.cache, key=lambda x: self.cache[x][0])[:10]:
					self.cache.pop(k, None)
		new = (d["page"] or page, d["sub"])
		if self.data is None or new != (self.page, self.sub):
			self.sel = 0   # neue Tafel: erste Seitennummer markieren
		self.page, self.sub = new
		self.data = d
		self.t_load = time.time()
		self.error = None
		return d


ARD = ArdText()
