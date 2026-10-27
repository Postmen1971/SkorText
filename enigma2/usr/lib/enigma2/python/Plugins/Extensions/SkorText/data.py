# -*- coding: utf-8 -*-
# SkorText - Datenmodul (LiveScore, oeffentliche JSON-Schnittstelle)
from __future__ import absolute_import, division
import calendar
import json
import os
import time
import ssl
import gzip
import io

try:
	from urllib.request import Request, urlopen
except ImportError:  # Python 2
	from urllib2 import Request, urlopen

BASE = "https://prod-public-api.livescore.com/v1/api/app"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# Seite, Land, LiveScore-Land, LiveScore-Liga, Name deutsch, Name tuerkisch, Kuerzel
LEAGUES = [
	(200, "de", "germany", "bundesliga", u"1. Bundesliga", u"Bundesliga", u""),
	(210, "de", "germany", "2-bundesliga", u"2. Bundesliga", u"2. Bundesliga", u""),
	(220, "de", "germany", "3-liga", u"3. Liga", u"3. Lig (Almanya)", u""),
	(230, "de", "germany", "regionalliga-sudwest", u"Regionalliga Südwest", u"Regionalliga Güneybatı", u""),
	(240, "de", "germany", "regionalliga-west", u"Regionalliga West", u"Regionalliga Batı", u""),
	(250, "de", "germany", "regionalliga-bayern", u"Regionalliga Bayern", u"Regionalliga Bavyera", u""),
	(260, "de", "germany", "regionalliga-nord", u"Regionalliga Nord", u"Regionalliga Kuzey", u""),
	(270, "de", "germany", "regionalliga-nordost", u"Regionalliga Nordost", u"Regionalliga Kuzeydoğu", u""),
	(280, "de", "germany", "oberliga-baden-wurttemberg", u"Oberliga Baden-Württemberg", u"Oberliga Baden-Württemberg", u""),
	(290, "de", "fupa", "verbandsliga-wuerttemberg", u"Verbandsliga Württemberg", u"Verbandsliga Württemberg", u""),
	(295, "de", "cup:germany", "dfb-cup", u"DFB-Pokal", u"Almanya Kupası", u""),
	(300, "tr", "turkey", "super-lig", u"Trendyol Süper Lig", u"Trendyol Süper Lig", u""),
	(305, "tr", "cup:turkey", "turkiye-cup", u"Türkiye Kupası", u"Ziraat Türkiye Kupası", u""),
	(310, "tr", "turkey", "1st-lig", u"Trendyol 1. Lig (2. Liga)", u"Trendyol 1. Lig", u""),
	(320, "tr", "turkey", "2nd-lig-white-group", u"2. Lig (3. Liga) · Beyaz Grup", u"Nesine 2. Lig · Beyaz Grup", u""),
	(322, "tr", "turkey", "2nd-lig-red-group", u"2. Lig (3. Liga) · Kırmızı Grup", u"Nesine 2. Lig · Kırmızı Grup", u""),
	(400, "eu", "england", "premier-league", u"Premier League", u"Premier Lig", u"ENG"),
	(410, "eu", "spain", "laliga", u"LaLiga", u"LaLiga", u"ESP"),
	(420, "eu", "italy", "serie-a", u"Serie A", u"Serie A", u"ITA"),
	(430, "eu", "france", "ligue-1", u"Ligue 1", u"Ligue 1", u"FRA"),
	(440, "eu", "champions-league", "league-stage", u"Champions League", u"Şampiyonlar Ligi", u""),
	(450, "eu", "europa-league", "league-stage", u"Europa League", u"Avrupa Ligi", u""),
	(460, "eu", "conference-league", "league-stage", u"Conference League", u"Konferans Ligi", u""),
]

# LiveScore schreibt deutsche Vereine teils englisch / ohne Umlaute
NAME_FIX = [
	# Deutschland
	(u"FC Cologne", u"1. FC Köln"), (u"Cologne", u"Köln"), (u"Bayern Munich", u"Bayern München"), (u"Munich 1860", u"TSV 1860 München"),
	(u"Nuremberg", u"Nürnberg"), (u"Monchengladbach", u"Mönchengladbach"), (u"Dusseldorf", u"Düsseldorf"),
	(u"Furth", u"Fürth"), (u"Munster", u"Münster"), (u"Osnabruck", u"Osnabrück"), (u"Saarbrucken", u"Saarbrücken"),
	(u"Wurzburg", u"Würzburg"), (u"Gottingen", u"Göttingen"), (u"Goppingen", u"Göppingen"), (u"Lubeck", u"Lübeck"),
	(u"Grossaspach", u"Großaspach"), (u"Koln", u"Köln"), (u"Gutersloh", u"Gütersloh"), (u"Rodinghausen", u"Rödinghausen"),
	(u"Wiedenbruck", u"Wiedenbrück"), (u"Gmund", u"Gmünd"), (u"Nottingen", u"Nöttingen"), (u"Turkgucu", u"Türkgücü"),
	(u"Turkspor", u"Türkspor"), (u"Preussen", u"Preußen"), (u"Muenster", u"Münster"), (u"1860 Munich", u"TSV 1860 München"),
	(u"Luneburger", u"Lüneburger"), (u"Teutonia St. Toenis", u"Teutonia St. Tönis"), (u"Zweibrucken", u"Zweibrücken"), (u"Volklingen", u"Völklingen"),
	# Tuerkei
	(u"Bodoe/Glimt", u"Bodø/Glimt"), (u"Slavia Prague", u"SK Slavia Prag"), (u"Sparta Prague", u"AC Sparta Prag"),
	(u"Atletico Madrid", u"Atlético Madrid"), (u"Ferencvaros", u"Ferencváros"), (u"Viktoria Plzen", u"Viktoria Pilsen"),
	(u"Lech Poznan", u"Lech Posen"), (u"Lillestroem", u"Lillestrøm"), (u"Mjaellby", u"Mjällby"), (u"FC Nordsjaelland", u"FC Nordsjælland"),
	(u"FC Copenhagen", u"FC Kopenhagen"), (u"FC Salzburg", u"RB Salzburg"), (u"Union St.Gilloise", u"Union Saint-Gilloise"),
	(u"Turkiye", u"Türkiye"), (u"Besiktas", u"Beşiktaş"), (u"Fenerbahce", u"Fenerbahçe"), (u"Basaksehir", u"Başakşehir"), (u"Kasimpasa", u"Kasımpaşa"),
	(u"Eyupspor", u"Eyüpspor"), (u"Goztepe", u"Göztepe"), (u"Caykur", u"Çaykur"), (u"Genclerbirligi", u"Gençlerbirliği"),
	(u"Karagumruk", u"Karagümrük"), (u"Igdir", u"Iğdır"), (u"Corum", u"Çorum"), (u"Bandirmaspor", u"Bandırmaspor"),
	(u"Umraniyespor", u"Ümraniyespor"), (u"Keciorengucu", u"Keçiörengücü"), (u"Istanbulspor", u"İstanbulspor"),
	(u"Sariyer", u"Sarıyer"), (u"Sanliurfaspor", u"Şanlıurfaspor"), (u"Arnavutkoy", u"Arnavutköy"), (u"Mus Spor", u"Muşspor"),
	(u"Musspor", u"Muşspor"), (u"Elazigspor", u"Elazığspor"), (u"Corluspor", u"Çorluspor"), (u"Genclik", u"Gençlik"),
	(u"Kirklarelispor", u"Kırklarelispor"), (u"Inegolspor", u"İnegölspor"), (u"Altinordu", u"Altınordu"), (u"Usakspor", u"Uşakspor"),
	(u"Kahramanmaras", u"Kahramanmaraş"), (u"Istiklalspor", u"İstiklalspor"), (u"Yildirimspor", u"Yıldırımspor"),
	(u"Aliaga", u"Aliağa"), (u"Karsiyaka", u"Karşıyaka"), (u"Mugla", u"Muğla"), (u"Duzce", u"Düzce"), (u"Guzide", u"Güzide"),
	(u"Erzincanspor", u"Erzincanspor"), (u"Bucaspor", u"Bucaspor"), (u"Kucukcekmece", u"Küçükçekmece"), (u"Beyoglu", u"Beyoğlu"),
	(u"Carsi", u"Çarşı"), (u"Iskenderun", u"İskenderun"), (u"Tuzla", u"Tuzla"), (u"Sile", u"Şile"), (u"Ergene", u"Ergene"),
	(u"Bursa Yildirim", u"Bursa Yıldırım"), (u"Igdir FK", u"Iğdır FK"), (u"Sakarya", u"Sakarya"), (u"Eskisehir", u"Eskişehir"),
	(u"Kutahya", u"Kütahya"), (u"Balikesir", u"Balıkesir"), (u"Canakkale", u"Çanakkale"), (u"Diyarbakir", u"Diyarbakır"),
	(u"Kirsehir", u"Kırşehir"), (u"Nevsehir", u"Nevşehir"), (u"Nigde", u"Niğde"), (u"Kirikkale", u"Kırıkkale"),
	(u"Inegol", u"İnegöl"), (u"gucu", u"gücü"), (u"Ayvalik", u"Ayvalık"), (u"Kulubu", u"Kulübü"), (u"Yesilyurt", u"Yeşilyurt"),
	(u"Sumerbey", u"Sümerbey"), (u"Mazidagi", u"Mazıdağı"), (u"Bingol", u"Bingöl"), (u"Universitesi", u"Üniversitesi"), (u"Dernegi", u"Derneği"), (u"Agri ", u"Ağrı "), (u"Mardin", u"Mardin"), (u"Akcaabat", u"Akçaabat"), (u"Carsamba", u"Çarşamba"), (u"Sebat", u"Sebat"),
]

def fix_name(n):
	n = (n or u"").replace(u"i\u0307", u"i").strip()
	for a, b in NAME_FIX:
		if a != b and a in n and b not in n:
			n = n.replace(a, b)
	return n


LOGFILE = "/tmp/skortext.log"


def log(msg):
	"""Fehler-Logbuch fuer die Fehlersuche (max. ca. 200 KB)."""
	try:
		if os.path.exists(LOGFILE) and os.path.getsize(LOGFILE) > 200000:
			os.remove(LOGFILE)
		with open(LOGFILE, "a") as f:
			f.write("%s %s\n" % (time.strftime("%d.%m. %H:%M:%S"), msg))
	except Exception:
		pass


def nice_error(err):
	s = str(err)
	if "403" in s:
		return u"Datenquelle sperrt den Zugriff (HTTP 403) – neuer Versuch in 5 Min."
	if "404" in s or "410" in s:
		return u"Liga bei der Datenquelle nicht gefunden"
	if "timed out" in s.lower() or "timeout" in s.lower():
		return u"Zeitüberschreitung – Internet langsam oder weg"
	if "name or service" in s.lower() or "nodename" in s.lower() or "errno -2" in s.lower() or "errno -3" in s.lower():
		return u"Keine Internetverbindung (DNS)"
	if "certificate" in s.lower() or "ssl" in s.lower():
		return u"SSL-Fehler – Uhrzeit des Receivers prüfen"
	return s[:80]


def _ctx(verify):
	try:
		if verify:
			return ssl.create_default_context()
		return ssl._create_unverified_context()
	except Exception:
		return None


LS_HOSTS = ["https://prod-public-api.livescore.com", "https://prod-cdn-public-api.livescore.com"]
LS_STATE = {"i": 0, "pause": 0}


def get_url_json(url, timeout=15):
	"""Wie fetch_json; LiveScore hat zwei Server - sperrt einer (403), wird der andere genommen,
	sperren beide, wird 5 Minuten pausiert statt weiter anzufragen."""
	import re
	m = re.match(r"^https://prod-(?:cdn-)?public-api\.livescore\.com(/.*)$", url)
	if not m:
		return fetch_json(url, timeout)
	if time.time() < LS_STATE["pause"]:
		raise Exception("HTTP Error 403: Pause")
	path = m.group(1)
	first = LS_STATE["i"]
	try:
		return fetch_json(LS_HOSTS[first] + path, timeout)
	except Exception as e:
		if "403" not in str(e):
			raise
	other = (first + 1) % len(LS_HOSTS)
	try:
		d = fetch_json(LS_HOSTS[other] + path, timeout)
		LS_STATE["i"] = other
		return d
	except Exception as e:
		if "403" in str(e):
			LS_STATE["pause"] = time.time() + 300
		raise


def fetch_bytes(url, timeout=30):
	req = Request(url, headers={"User-Agent": UA})
	last = None
	for verify in (True, False):
		ctx = _ctx(verify)
		try:
			resp = urlopen(req, timeout=timeout, context=ctx) if ctx is not None else urlopen(req, timeout=timeout)
			return resp.read()
		except Exception as e:
			last = e
			if "CERTIFICATE" not in str(e).upper() and "SSL" not in str(e).upper():
				break
	raise last


def fetch_json(url, timeout=15):
	req = Request(url, headers={"User-Agent": UA, "Accept": "application/json", "Accept-Encoding": "gzip"})
	last = None
	for verify in (True, False):  # manche Receiver haben veraltete Zertifikate
		ctx = _ctx(verify)
		try:
			resp = urlopen(req, timeout=timeout, context=ctx) if ctx is not None else urlopen(req, timeout=timeout)
			raw = resp.read()
			if raw[:2] == b"\x1f\x8b":
				raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
			return json.loads(raw.decode("utf-8"))
		except Exception as e:
			last = e
			if "CERTIFICATE" not in str(e).upper() and "SSL" not in str(e).upper():
				break
	raise last


def get_url_text(url, timeout=20, enc="utf-8"):
	req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json,*/*", "Accept-Encoding": "gzip"})
	last = None
	for verify in (True, False):
		ctx = _ctx(verify)
		try:
			resp = urlopen(req, timeout=timeout, context=ctx) if ctx is not None else urlopen(req, timeout=timeout)
			raw = resp.read()
			if raw[:2] == b"\x1f\x8b":
				raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
			return raw.decode(enc, "replace")
		except Exception as e:
			last = e
			if "CERTIFICATE" not in str(e).upper() and "SSL" not in str(e).upper():
				break
	raise last


def season_start(now=None):
	"""Beginn der laufenden Saison (1. Juli) als Unix-Zeit."""
	lt = time.localtime(now or time.time())
	y = lt.tm_year if lt.tm_mon >= 7 else lt.tm_year - 1
	return calendar.timegm((y, 7, 1, 0, 0, 0, 0, 0, 0))


def esd_ts(v):
	"""LiveScore-Zeit (JJJJMMTThhmmss, UTC) -> Unix-Zeit."""
	try:
		s = str(v)
		return calendar.timegm((int(s[0:4]), int(s[4:6]), int(s[6:8]), int(s[8:10]), int(s[10:12]), int(s[12:14] or 0), 0, 0, 0))
	except Exception:
		return 0


def to_int(v):
	try:
		return int(v)
	except Exception:
		return None


def parse_event(e, key):
	eps = (e.get("Eps") or u"").strip()
	minute = u""
	if eps in ("NS", ""):
		state = "pre"
	elif eps in ("FT", "AET", "AP", "Pen.", "FT Pen", "After Pen.", "Awarded"):
		state = "post"
	elif eps == "HT":
		state = "ht"
	elif eps in ("Postp.", "Canc.", "Aband.", "Int.", "Susp.", "Delayed", "Postponed", "Cancelled"):
		state = "pp"
	else:
		state = "in"
		if eps.endswith("'"):
			minute = eps[:-1]
		elif eps in ("ET", "AET", "BET"):
			minute = u"Verl"
		elif "Pen" in eps:
			minute = u"Elf"
		else:
			minute = eps[:5]
	t1 = (e.get("T1") or [{}])[0]
	t2 = (e.get("T2") or [{}])[0]
	hs, as_ = to_int(e.get("Tr1")), to_int(e.get("Tr2"))
	if state == "pre":
		hs = as_ = None
	h, a = fix_name(t1.get("Nm") or u"?"), fix_name(t2.get("Nm") or u"?")
	return {
		"id": e.get("Eid"),
		"h": h, "hs_name": t1.get("Abr") or u"",
		"a": a, "as_name": t2.get("Abr") or u"",
		"hs": hs, "as": as_, "state": state, "min": minute,
		"ts": esd_ts(e.get("Esd")), "round": to_int(e.get("ErnInf")),
		"group": u"", "ut": key,
	}


def parse_table(stage):
	lt = stage.get("LeagueTable") or {}
	tabs = (lt.get("L") or [{}])[0].get("Tables") or []
	tab = None
	for t in tabs:
		if t.get("LTT") == 1:
			tab = t
			break
	if tab is None and tabs:
		tab = tabs[0]
	if not tab:
		return []
	teams = tab.get("team") or []
	n = len(teams)
	rows = []
	for r in teams:
		rows.append({
			"pos": r.get("rnk") or 0, "tm": fix_name(r.get("Tnm") or u"?"), "short": u"",
			"p": r.get("pld") or 0, "w": r.get("win") or 0, "d": r.get("drw") or 0, "l": r.get("lst") or 0,
			"gf": r.get("gf") or 0, "ga": r.get("ga") or 0, "pts": r.get("pts") or 0,
			"phr": (r.get("phr") or [None])[0], "zone": None,
		})
	# Farbzonen aus den Markierungen ableiten (oben gruen/tuerkis/lila, unten rot/gelb)
	top = []
	bottom = []
	for r in rows:
		if r["phr"] is None:
			continue
		if r["pos"] <= n / 2.0:
			if r["phr"] not in top:
				top.append(r["phr"])
		elif r["phr"] not in bottom:
			bottom.append(r["phr"])
	for r in rows:
		if r["phr"] is None:
			continue
		if r["phr"] in top:
			r["zone"] = ("g", "c", "m", "c")[min(top.index(r["phr"]), 3)]
		else:
			i = len(bottom) - 1 - bottom.index(r["phr"])
			r["zone"] = ("r", "y", "y")[min(i, 2)]
	return [(u"", rows)]


def infer_rounds(evs):
	"""Spiele ohne Spieltagsnummer (z. B. "Beyaz") per Datum dem Spieltag zuordnen."""
	if not evs or all(e["round"] is not None for e in evs):
		return
	buckets = []
	last_ts = None
	for e in evs:  # evs nach Zeit sortiert
		if last_ts is None or e["ts"] - last_ts > 60 * 3600:
			buckets.append([])
		buckets[-1].append(e)
		last_ts = e["ts"]
	prev = 0
	for b in buckets:
		nums = [e["round"] for e in b if e["round"] is not None]
		if nums:
			r = max(set(nums), key=nums.count)
		else:
			r = prev + 1
		for e in b:
			if e["round"] is None:
				e["round"] = r
		prev = max(prev, r)


# ---------------- Ersatzquelle ESPN (wenn LiveScore sperrt) ----------------
ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer"
ESPN_TAB = "https://site.api.espn.com/apis/v2/sports/soccer"
ESPN_CODES = {200: "ger.1", 210: "ger.2", 295: "ger.dfb_pokal", 300: "tur.1", 400: "eng.1", 410: "esp.1", 420: "ita.1",
	430: "fra.1", 440: "uefa.champions", 450: "uefa.europa", 460: "uefa.europa.conf"}
FUPA_SLUGS = {200: "bundesliga", 210: "2-bundesliga", 220: "3-liga", 230: "regionalliga-suedwest", 240: "regionalliga-west",
	250: "regionalliga-bayern", 260: "regionalliga-nord", 270: "regionalliga-nordost", 280: "oberliga-baden-wuerttemberg"}
ESPN_NAMES = [(u"Bayern Munich", u"Bayern München"), (u"1. FC Union Berlin", u"Union Berlin"), (u"Borussia Monchengladbach", u"Borussia M'gladbach"),
	(u"1. FC Cologne", u"1. FC Köln"), (u"FC Cologne", u"1. FC Köln"), (u"FC Augsburg", u"Augsburg"), (u"VfL Wolfsburg", u"Wolfsburg"),
	(u"1. FC Heidenheim 1846", u"FC Heidenheim"), (u"TSG Hoffenheim", u"Hoffenheim"), (u"SC Freiburg", u"Freiburg")]


def espn_ts(v):
	import re
	m = re.match(r"(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d)(?::(\d\d))?", v or u"")
	if not m:
		return 0
	g = [int(x or 0) for x in m.groups()]
	return calendar.timegm((g[0], g[1], g[2], g[3], g[4], g[5], 0, 0, 0))


def espn_name(n):
	n = n or u"?"
	for a, b in ESPN_NAMES:
		if n == a:
			return b
	return fix_name(n)


def parse_espn_event(ev, key):
	st = (ev.get("status") or {}).get("type") or {}
	state = {"pre": "pre", "in": "in", "post": "post"}.get(st.get("state"), "pre")
	nm = st.get("name") or u""
	minute = u""
	if "HALFTIME" in nm:
		state = "ht"
	elif "POSTPONED" in nm or "CANCELED" in nm or "SUSPENDED" in nm:
		state = "pp"
	elif state == "in":
		minute = ((ev.get("status") or {}).get("displayClock") or u"").split(u"'")[0]
	comp = (ev.get("competitions") or [{}])[0]
	home = away = {}
	for c in comp.get("competitors") or []:
		if c.get("homeAway") == "home":
			home = c
		else:
			away = c
	hs, as_ = to_int(home.get("score")), to_int(away.get("score"))
	if state == "pre":
		hs = as_ = None
	ht, at = home.get("team") or {}, away.get("team") or {}
	return {"id": "espn%s" % ev.get("id"), "h": espn_name(ht.get("displayName")), "hs_name": ht.get("shortDisplayName") or u"",
		"a": espn_name(at.get("displayName")), "as_name": at.get("shortDisplayName") or u"", "hs": hs, "as": as_,
		"state": state, "min": minute, "ts": espn_ts(ev.get("date")), "round": None, "group": u"", "ut": key}


def espn_zone(note):
	d = ((note or {}).get("description") or u"").lower()
	if not d:
		return None
	if "relegation" in d and ("play" in d or "qualif" in d):
		return "y"
	if "relegation" in d:
		return "r"
	if "champions league" in d or "round of 16" in d or "promotion" in d:
		return "g"
	if "europa league" in d or "play" in d:
		return "c"
	if "conference" in d:
		return "m"
	return "c"


class League(object):
	def __init__(self, row):
		self.page, self.c, self.ccd, self.scd, self.name_de, self.name_tr, self.tag = row
		self.ut = "%s/%s" % (self.ccd, self.scd)
		self.season = True          # bei LiveScore nicht noetig
		self.round = None
		self.max_round = None
		self.all_events = []
		self.events = []
		self.prev_events = []
		self.prev_round = None
		self.rcache = {}
		self.rloading = set()
		self.tables = []
		self.t_load = 0
		self.loading = False
		self.error = None
		self.gdefs = []

	def name(self, lang):
		return self.name_tr if lang == "tr" else self.name_de

	def views(self):
		if self.c == "nlg":
			return []  # Gruppen der Nations League stehen gemeinsam auf Seite 470
		return [(self.page, None)]

	def groups(self):
		return [u""]

	def group_index(self, name):
		return None

	def group_name(self, gi):
		return u""

	def in_group(self, name, gi):
		return True

	def page_of_group(self, name):
		return self.page

	def load(self):
		"""Blockierend - laeuft in einem Hintergrund-Thread. LiveScore, bei Sperre Ersatzquelle ESPN."""
		try:
			r = self.load_ls()
			self.source = "ls"
			return r
		except Exception as e:
			err = str(e)
			if self.c == "nlg" or "404" in err or "410" in err:
				raise
			for src, ok, fn in (("espn", self.page in ESPN_CODES, self.load_espn),
					("fupa", self.page in FUPA_SLUGS, lambda: fupa_load(self, FUPA_SLUGS[self.page])),
					("tff", self.page in TFF_PAGES, lambda: tff_load(self))):
				if not ok:
					continue
				try:
					r = fn()
					self.source = src
					log("Liga %d: LiveScore nicht erreichbar (%s), Ersatz %s" % (self.page, err[:40], src))
					return r
				except Exception as e2:
					log("Liga %d: Ersatz %s: %r" % (self.page, src, e2))
			raise

	def load_espn(self):
		code = ESPN_CODES[self.page]
		now = time.time()
		old = dict((e["id"], e) for e in self.all_events) if getattr(self, "source", "") == "espn" else {}
		full = not old or now - getattr(self, "t_espn_full", 0) > 1800
		days = range(-6, 7) if full else [0]  # bei laufenden Spielen nur heute neu holen
		evs = dict(old)
		for dd in days:
			ymd = time.strftime("%Y%m%d", time.localtime(now + dd * 86400))
			try:
				d = fetch_json("%s/%s/scoreboard?dates=%s" % (ESPN, code, ymd), timeout=20)
			except Exception:
				continue
			for ev in d.get("events") or []:
				pe = parse_espn_event(ev, self.ut)
				evs[pe["id"]] = pe
		if not evs:
			raise Exception("HTTP Error 403 (LiveScore gesperrt, ESPN ohne Daten)")
		rows = []
		try:
			t = fetch_json("%s/%s/standings" % (ESPN_TAB, code), timeout=20)
			for ch in t.get("children") or [t]:
				for en in ((ch.get("standings") or {}).get("entries")) or []:
					st = dict((x.get("name"), x.get("value")) for x in en.get("stats") or [])
					tm = en.get("team") or {}
					rows.append({"pos": int(st.get("rank") or 0), "tm": espn_name(tm.get("displayName")), "short": tm.get("shortDisplayName") or u"",
						"p": int(st.get("gamesPlayed") or 0), "w": int(st.get("wins") or 0), "d": int(st.get("ties") or 0), "l": int(st.get("losses") or 0),
						"gf": int(st.get("pointsFor") or 0), "ga": int(st.get("pointsAgainst") or 0), "pts": int(st.get("points") or 0),
						"phr": None, "zone": espn_zone(en.get("note"))})
		except Exception:
			rows = [r for _n, rr in self.tables for r in rr] if old else []
		rows.sort(key=lambda r: r["pos"])
		# Spieltage nach Datum bilden; Nummer aus der Zahl der gespielten Spiele ableiten
		lst = sorted(evs.values(), key=lambda x: x["ts"])
		buckets, last = [], None
		for e in lst:
			if last is None or e["ts"] - last > 60 * 3600:
				buckets.append([])
			buckets[-1].append(e)
			last = e["ts"]
		played = max([r["p"] for r in rows] or [0])
		idx = max([i for i, b in enumerate(buckets) if any(e["state"] == "post" for e in b)] or [0])
		base = (played or (idx + 1)) - idx
		for i, b in enumerate(buckets):
			for e in b:
				e["round"] = max(1, base + i)
		self.rnames = {}
		self.set_events(lst, infer=False)
		self.tables = [(u"", rows)] if rows else []
		self.source = "espn"
		if full:
			self.t_espn_full = now
		self.t_load = time.time()
		self.error = None
		return self

	def load_ls(self):
		d = get_url_json("%s/stage/soccer/%s/%s/0?MD=1" % (BASE, self.ccd, self.scd))
		stages = d.get("Stages") or []
		if not stages:
			raise Exception("404 keine Daten")
		st = stages[0]
		evs = [parse_event(e, self.ut) for e in (st.get("Events") or [])]
		self.set_events(evs)
		self.tables = parse_table(st)
		if self.scd == "league-stage":
			# Europapokal-Ligaphase: 1-8 Achtelfinale, 9-24 Playoffs, ab 25 raus
			for _n, rows in self.tables:
				if all(r["zone"] is None for r in rows):
					for r in rows:
						r["zone"] = "g" if r["pos"] <= 8 else ("c" if r["pos"] <= 24 else None)
		self.t_load = time.time()
		self.error = None
		return self

	def round_label(self, n, lang):
		return None  # normaler Spieltag

	def set_events(self, evs, infer=True):
		evs.sort(key=lambda x: x["ts"])
		if infer:
			infer_rounds(evs)
		self.all_events = evs
		rounds = sorted(set(e["round"] for e in evs if e["round"] is not None))
		self.max_round = rounds[-1] if rounds else None
		# aktueller Spieltag = erster Spieltag mit noch nicht beendeten Spielen
		cur = None
		for e in evs:
			if e["round"] is not None and e["state"] in ("pre", "in", "ht"):
				cur = e["round"]
				break
		if cur is None and rounds:
			cur = rounds[-1]
		self.round = cur
		self.events = self.events_of_round(cur) if cur else list(evs[-10:])
		self.prev_round = cur - 1 if cur and cur > 1 else None
		self.prev_events = self.events_of_round(self.prev_round) if self.prev_round else []

	def events_of_round(self, n):
		if n is None:
			return []
		return [e for e in self.all_events if e["round"] == n]

	def load_round(self, n):
		return n  # alle Spieltage sind schon geladen

	def live_count(self):
		return len([e for e in self.events if e["state"] in ("in", "ht")])


FUPA = "https://api.fupa.net/v1"


def iso_ts(v):
	"""FuPa-Zeit 2026-08-15T14:00:00+02:00 -> Unix-Zeit."""
	try:
		s = str(v)
		t = calendar.timegm((int(s[0:4]), int(s[5:7]), int(s[8:10]), int(s[11:13]), int(s[14:16]), int(s[17:19] or 0), 0, 0, 0))
		tz = s[19:]
		if len(tz) >= 6 and tz[0] in "+-":
			off = int(tz[1:3]) * 3600 + int(tz[4:6]) * 60
			t = t - off if tz[0] == "+" else t + off
		return t
	except Exception:
		return 0


def fupa_season(now=None):
	lt = time.localtime(now or time.time())
	y = lt.tm_year if lt.tm_mon >= 7 else lt.tm_year - 1
	return "%d-%02d" % (y, (y + 1) % 100)


def fupa_name(t):
	n = (t or {}).get("name") or {}
	return (n.get("full") or n.get("middle") or u"?").strip(), (n.get("short") or u"").strip()


def parse_fupa_match(m, key):
	sec = (m.get("section") or u"").upper()
	hs, as_ = m.get("homeGoal"), m.get("awayGoal")
	minute = u""
	if sec == "PRE":
		state = "pre"
		hs = as_ = None
	elif sec == "POST":
		state = "post" if hs is not None else "pp"
	else:
		state = "in"
		minute = u"live"
	h, hsn = fupa_name(m.get("homeTeam"))
	a, asn = fupa_name(m.get("awayTeam"))
	return {
		"id": "fupa%s" % m.get("id"),
		"h": h, "hs_name": hsn, "a": a, "as_name": asn,
		"hs": hs, "as": as_, "state": state, "min": minute,
		"ts": iso_ts(m.get("kickoff")), "round": ((m.get("round") or {}).get("number")),
		"group": u"", "ut": key,
	}


class FupaLeague(League):
	"""Amateurligen von FuPa (z. B. Verbandsliga Wuerttemberg mit dem 1. Göppinger SV)."""

	def __init__(self, row):
		League.__init__(self, row)
		self.t_full = 0

	def load(self):
		return fupa_load(self, self.scd)


def fupa_load(self, slug):
	"""Liga von FuPa laden (eigene Amateurliga oder Ersatz fuer 3. Liga / Regionalligen)."""
	if True:
		season = fupa_season()
		base = "%s/competitions/%s/seasons/%s/matches" % (FUPA, slug, season)
		now = time.time()
		if not self.all_events or now - getattr(self, "t_full", 0) > 3 * 3600 or getattr(self, "source", "fupa") != "fupa":
			raw = []
			for page in range(1, 6):
				part = get_url_json("%s?limit=100&page=%d" % (base, page), timeout=20)
				raw += part or []
				if not part or len(part) < 100:
					break
			evs = [parse_fupa_match(m, self.ut) for m in raw]
			self.t_full = now
		else:
			# nur die Tage rund um heute neu holen und einsortieren
			f = time.strftime("%Y-%m-%d", time.localtime(now - 4 * 86400))
			t = time.strftime("%Y-%m-%d", time.localtime(now + 8 * 86400))
			fresh = dict((e["id"], e) for e in (parse_fupa_match(m, self.ut) for m in (get_url_json("%s?from=%s&to=%s" % (base, f, t)) or [])))
			evs = [fresh.pop(e["id"], e) for e in self.all_events] + list(fresh.values())
		self.set_events(evs)
		d = get_url_json("%s/standings?competition=%s&season=%s" % (FUPA, slug, season))
		rows = []
		for r in (d or {}).get("standings") or []:
			tm, short = fupa_name(r.get("team"))
			mark = r.get("mark") or u""
			zone = {"up1": "g", "up2": "c", "down1": "y", "down2": "r"}.get(mark)
			if zone is None and mark.startswith("up"):
				zone = "c"
			elif zone is None and mark.startswith("down"):
				zone = "r"
			rows.append({"pos": r.get("rank") or 0, "tm": tm, "short": short,
				"p": r.get("matches") or 0, "w": r.get("wins") or 0, "d": r.get("draws") or 0, "l": r.get("defeats") or 0,
				"gf": r.get("ownGoals") or 0, "ga": r.get("againstGoals") or 0, "pts": r.get("points") or 0,
				"phr": None, "zone": zone})
		self.tables = [(u"", rows)] if rows else []
		self.rnames = {}
		self.t_load = time.time()
		self.error = None
		return self



# ---------------- Ersatzquelle TFF (tuerkische Ligen) ----------------
TFF_PAGES = {300: (198, None), 310: (142, None), 320: (976, u"Beyaz"), 322: (976, u"Kırmızı"), 305: (598, u"cup")}
TR_MONTHS = {u"Ocak": 1, u"Şubat": 2, u"Mart": 3, u"Nisan": 4, u"Mayıs": 5, u"Haziran": 6, u"Temmuz": 7, u"Ağustos": 8,
	u"Eylül": 9, u"Ekim": 10, u"Kasım": 11, u"Aralık": 12}


def tff_round_key(name):
	"""TFF-Rundenname -> Schluessel fuer round_text ('3.Tur Maçları' -> 'Round 3')."""
	import re
	n = (name or u"").replace(u"Maçları", u"").strip()
	m = re.match(r"(\d+)\s*\.?\s*Tur", n)
	if m:
		return u"Round %s" % m.group(1)
	low = n.lower()
	for k, v in ((u"son 16", u"Round of 16"), (u"son 32", u"Round of 32"), (u"çeyrek", u"Quarter-finals"), (u"yarı", u"Semi-finals"),
			(u"final", u"Final"), (u"grup", u"Group"), (u"eleme", u"Qualification"), (u"play", u"Play-offs")):
		if k in low:
			return v
	return n or u"Round"


def parse_tff_cup(html, key):
	import re
	evs = []
	cur = u""
	for m in re.finditer(r'kupaMaclari_ctl(\d+)_lbl(Grup|Tarih|Takim1|Skor|Takim2)"[^>]*>([^<]*)<', html):
		pass
	rows = {}
	order = []
	for m in re.finditer(r'kupaMaclari_ctl(\d+)_(lblGrup|lblTarih|lblTakim1|lblSkor|lblTakim2)"[^>]*>([^<]*)<', html):
		n, fld, val = m.group(1), m.group(2), m.group(3).strip()
		if n not in rows:
			rows[n] = {}
			order.append(n)
		rows[n][fld] = val
	for n in order:
		r = rows[n]
		if r.get("lblGrup"):
			cur = r["lblGrup"]
		if not r.get("lblTakim1"):
			continue
		ts = 0
		dm = re.match(r"(\d+)\s+(\S+)\s+(\d{4})\s*(\d+)?:?(\d+)?", r.get("lblTarih", u""))
		if dm and dm.group(2) in TR_MONTHS:
			ts = calendar.timegm((int(dm.group(3)), TR_MONTHS[dm.group(2)], int(dm.group(1)), int(dm.group(4) or 0), int(dm.group(5) or 0), 0, 0, 0, 0)) - 3 * 3600
		sc = re.match(r"\s*(\d+)\s*-\s*(\d+)", r.get("lblSkor", u""))
		evs.append({"id": "tffk" + n + r["lblTakim1"][:6], "h": tff_name(r["lblTakim1"]), "hs_name": u"", "a": tff_name(r.get("lblTakim2", u"?")), "as_name": u"",
			"hs": int(sc.group(1)) if sc else None, "as": int(sc.group(2)) if sc else None, "state": "post" if sc else "pre",
			"min": u"", "ts": ts, "nodate": not ts, "round": None, "rkey": tff_round_key(cur), "group": u"", "ut": key})
	return evs


def tff_cup_load(self):
	html = get_url_text(TFF % TFF_PAGES[self.page][0], timeout=30, enc="cp1254")
	evs = parse_tff_cup(html, self.ut)
	if not evs:
		raise Exception("TFF-Pokal: keine Daten")
	keys = []
	for e in sorted(evs, key=lambda x: x["ts"] or 9e9):
		if e["rkey"] not in keys:
			keys.append(e["rkey"])
	self.rnames = {}
	for i, k in enumerate(keys):
		self.rnames[i + 1] = k
	for e in evs:
		e["round"] = keys.index(e["rkey"]) + 1
	now = time.time()
	for e in evs:
		if e["state"] == "pre" and e["ts"] and e["ts"] < now - 3 * 3600:
			e["state"] = "pp"
	self.set_events(evs, infer=False)
	self.tables = []
	self.t_load = time.time()
	self.error = None
	return self
TFF = "https://www.tff.org/Default.aspx?pageID=%d"


def tr_title(w):
	low = {u"I": u"ı", u"İ": u"i"}
	out = []
	for word in w.split():
		if word.isdigit() or word in (u"FK", u"SK", u"SMS", u"GMG", u"AŞ", u"BB", u"TFF"):
			out.append(word)
			continue
		rest = u"".join(low.get(c, c.lower()) for c in word[1:])
		out.append(word[0] + rest)
	return u" ".join(out)


def tff_name(n):
	import re
	n = re.sub(r"\s+", u" ", n or u"").strip()
	n = n.replace(u" FUTBOL KULÜBÜ", u" FK").replace(u" FUTBOL SK", u" SK").replace(u" FUTBOL A.Ş.", u"")
	n = re.sub(r"\s+(A\.Ş\.|SPOR KULÜBÜ|KULÜBÜ)$", u"", n)
	return tr_title(n)


def parse_tff(html, key, group=None):
	import re
	rows = []
	for m in re.finditer(r'lnkTakim"[^>]*>(\d+)\.([^<]+)</a>(.*?)</tr>', html, re.S):
		nums = [int(x) for x in re.findall(r'<span[^>]*>(-?\d+)</span>', m.group(3))]
		if len(nums) >= 8:
			o, g, b, mm, a, y, _av, p = nums[:8]
			rows.append({"pos": int(m.group(1)), "tm": tff_name(m.group(2)), "short": u"", "p": o, "w": g, "d": b, "l": mm,
				"gf": a, "ga": y, "pts": p, "phr": None, "zone": None})
	dates = {}
	for m in re.finditer(r'lblTarih">([\d.]+)</span>(?:&nbsp;|\s)*<span[^>]*lbl?Saat">([\d:]*)</span>.*?macId=(\d+)', html, re.S):
		try:
			dd, mo, yy = [int(x) for x in m.group(1).split(".")]
			hh, mi = ([int(x) for x in m.group(2).split(":")] + [0, 0])[:2] if m.group(2) else (0, 0)
			dates[m.group(3)] = calendar.timegm((yy, mo, dd, hh, mi, 0, 0, 0, 0)) - 3 * 3600  # Istanbul = UTC+3
		except Exception:
			pass
	start = html.find(u"Fikstür Listesi")
	if group:
		g = html.find(u"<br/>%s Grup<br/>" % group)
		start = g if g >= 0 else start
	end = len(html)
	if group:
		nxt = html.find(u"Panel1", start + 200)
		end = nxt if nxt > 0 else end
	sec = html[start:end] if start >= 0 else u""
	evs = []
	weeks = list(re.finditer(r'(\d+)\.Hafta</td>', sec))
	rx = re.compile(r'kulupId=\d+">([^<]+)</a></td>\s*<td[^>]*><a href="[^"]*macId=(\d+)">([^<]*)</a></td>\s*<td[^>]*><a href="[^"]*kulupId=\d+">([^<]+)</a>', re.S)
	for i, w in enumerate(weeks):
		blk = sec[w.end(): weeks[i + 1].start() if i + 1 < len(weeks) else len(sec)]
		for m in rx.finditer(blk):
			sc = re.match(r"\s*(\d+)\s*-\s*(\d+)\s*$", m.group(3))
			mid = m.group(2)
			ts = dates.get(mid, 0)
			evs.append({"id": "tff" + mid, "h": tff_name(m.group(1)), "hs_name": u"", "a": tff_name(m.group(4)), "as_name": u"",
				"hs": int(sc.group(1)) if sc else None, "as": int(sc.group(2)) if sc else None,
				"state": "post" if sc else "pre", "min": u"", "ts": ts, "nodate": not ts, "round": int(w.group(1)), "group": u"", "ut": key})
	return evs, rows


def tff_load(self):
	import re
	pid, group = TFF_PAGES[self.page]
	if group == "cup":
		return tff_cup_load(self)
	html = get_url_text(TFF % pid, timeout=30, enc="cp1254")
	if group:
		m = re.search(r'grupID=(\d+)#hmac"[^>]*>\s*%s' % group, html)
		if m:
			html = get_url_text((TFF % pid) + "&grupID=" + m.group(1), timeout=30, enc="cp1254")
	evs, rows = parse_tff(html, self.ut, group)
	if not evs and not rows:
		raise Exception("TFF: keine Daten")
	m = re.search(r"haftaNoActive><a href=[^>]*hafta=(\d+)", html)
	active = int(m.group(1)) if m else None
	if not active:
		dated = [e["round"] for e in evs if e["ts"]]
		active = min(dated) if dated else None
	if active:  # Spiele frueherer Wochen ohne Ergebnis = abgesagt/verlegt
		for e in evs:
			if e["state"] == "pre" and e["round"] < active:
				e["state"] = "pp"
	# Spiele ohne Datum zeitlich hinter/vor die datierten sortieren
	cur = None
	for e in evs:
		if e["state"] == "pre":
			cur = e["round"] if cur is None else min(cur, e["round"])
	now = time.time()
	for e in evs:
		if not e["ts"]:
			e["ts"] = now + ((e["round"] - (cur or e["round"])) * 7 * 86400) - (3600 if e["state"] == "post" else 0)
	self.rnames = {}
	self.set_events(evs, infer=False)
	self.tables = [(u"", rows)] if rows else []
	self.t_load = time.time()
	self.error = None
	return self


# ---------------- Pokale ----------------
ROUND_NAMES = [
	(r"^round of 16", (u"Achtelfinale", u"Son 16 Turu")),
	(r"^round of 32", (u"Sechzehntelfinale", u"Son 32 Turu")),
	(r"^round (\d+)", (u"%s. Runde", u"%s. Tur")),
	(r"^1st round", (u"1. Runde", u"1. Tur")),
	(r"^quarter", (u"Viertelfinale", u"Çeyrek Final")),
	(r"^semi", (u"Halbfinale", u"Yarı Final")),
	(r"^final stage", (u"Endrunde", u"Final Aşaması")),
	(r"^final", (u"Finale", u"Final")),
	(r"^qualification", (u"Qualifikation", u"Ön Eleme")),
	(r"^group", (u"Gruppenphase", u"Grup Aşaması")),
	(r"^play", (u"Play-offs", u"Play-off")),
]


def round_text(key, lang):
	import re
	k = key.lower().strip()
	sub = u""
	if u"|" in k:
		k, sub = k.split(u"|", 1)
	for rx, (de, tr) in ROUND_NAMES:
		m = re.match(rx, k)
		if m:
			t = tr if lang == "tr" else de
			if u"%s" in t:
				t = t % m.group(1)
			if sub:
				t += u" · " + ((u"%s. Tur" if lang == "tr" else u"%s. Runde") % sub)
			return t
	return key


class CupLeague(League):
	"""Pokal (DFB-Pokal, Türkiye Kupası): bei LiveScore ist jede Runde eine eigene Stufe."""

	def __init__(self, row):
		League.__init__(self, row)
		self.country = self.ccd.split(":", 1)[1]
		self.prefix = self.scd
		self.ut = "cup/%s/%s" % (self.country, self.prefix)
		self.keys = set()
		self.rnames = {}

	def matches_stage(self, ccd, scd):
		return ccd == self.country and (scd or u"").startswith(self.prefix) and u"women" not in scd

	def round_label(self, n, lang):
		k = self.rnames.get(n)
		return round_text(k, lang) if k else None

	def load_ls(self):
		cat = get_url_json("%s/category/soccer/%s/0?MD=1" % (BASE, self.country), timeout=25)
		start = season_start()
		cands = [st for st in (cat.get("Stages") or []) if self.matches_stage(st.get("Ccd"), st.get("Scd"))
			and any(esd_ts(e.get("Esd")) >= start for e in (st.get("Events") or []))]
		groups = {}     # Rundenname -> Spiele
		tables = []
		keys = set()
		for c in cands:
			try:
				d = get_url_json("%s/stage/soccer/%s/%s/0?MD=1" % (BASE, self.country, c.get("Scd")), timeout=20)
				st = (d.get("Stages") or [c])[0]
			except Exception:
				st = c
			evs = [parse_event(e, self.ut) for e in (st.get("Events") or [])]
			evs = [e for e in evs if e["ts"] >= start]
			if not evs:
				continue
			keys.add(u"%s/%s" % (st.get("Ccd") or self.country, st.get("Scd")))
			raw = (st.get("Snm") or u"").replace(u";", u":")
			name = raw.split(u":")[-1].strip() or raw
			if name.lower().startswith(u"group"):
				for _n, rows in parse_table(st):
					tables.append((u"Gruppe " + name.split()[-1], rows))
				name = u"Group"
			nums = set(e["round"] for e in evs if e["round"] is not None)
			for e in evs:
				k = name
				if name.lower().startswith(u"qualification") and len(nums) > 1 and e["round"] is not None:
					k = u"%s|%d" % (name, e["round"])
				groups.setdefault(k, []).append(e)
		order = sorted(groups.keys(), key=lambda k: min(e["ts"] for e in groups[k]))
		allev = []
		self.rnames = {}
		for i, k in enumerate(order):
			self.rnames[i + 1] = k
			for e in groups[k]:
				e["round"] = i + 1
				allev.append(e)
		self.keys = keys
		self.set_events(allev, infer=False)
		self.tables = tables
		self.t_load = time.time()
		self.error = None
		return self


# ---------------- Spieldetails (Tore, Platzverweise) ----------------
INC_TYPES = {36: "goal", 37: "pen", 39: "og", 44: "yr", 45: "red"}


def parse_incidents(d):
	out = []
	incs = (d or {}).get("Incs") or {}
	for per in sorted(incs.keys(), key=lambda x: to_int(x) or 0):
		for it in incs[per] or []:
			for x in [it] + list(it.get("Incs") or []):
				typ = INC_TYPES.get(x.get("IT"))
				if not typ:
					continue
				mn = to_int(x.get("Min")) or 0
				ex = to_int(x.get("MinEx")) or 0
				name = x.get("Ln") or x.get("Snm") or x.get("Pn") or u"?"
				out.append({"side": to_int(x.get("Nm")) or 1, "min": (u"%d+%d" % (mn, ex)) if ex else u"%d" % mn,
					"sort": mn * 100 + ex, "type": typ, "name": name})
	out.sort(key=lambda x: x["sort"])
	return out


class Details(object):
	def __init__(self):
		self.cache = {}     # Spiel-ID -> {"t":..., "list": [...], "final": bool}
		self.loading = set()

	def get(self, e):
		c = self.cache.get(e["id"])
		return c["list"] if c else None

	def needs(self, e, ref):
		if e["state"] == "pre" or str(e["id"]).startswith("fupa") or e["id"] in self.loading:
			return False
		c = self.cache.get(e["id"])
		if c is None:
			return True
		if c["final"]:
			return False
		return time.time() - c["t"] > ref

	def load(self, e):
		d = get_url_json("%s/incidents/soccer/%s?locale=en" % (BASE, e["id"]))
		lst = parse_incidents(d)
		self.cache[e["id"]] = {"t": time.time(), "list": lst, "final": e["state"] == "post"}
		return lst


# ---------------- Ranglisten ----------------
def uefa_season_year(now=None):
	lt = time.localtime(now or time.time())
	return lt.tm_year + 1 if lt.tm_mon >= 7 else lt.tm_year


class Ranking(object):
	def __init__(self, page, kind):
		self.page = page
		self.kind = kind
		self.rows = []
		self.date = u""
		self.t_load = 0
		self.loading = False
		self.error = None

	def load(self):
		import re
		if self.kind == "fifa":
			html = get_url_text("https://inside.fifa.com/fifa-world-ranking/men", timeout=25)
			m = re.search(r'"id":"(FRS_Male_Football_\d+)"', html)
			if not m:
				raise Exception("FIFA-Rangliste: Datum nicht gefunden")
			md = re.search(r'"lastUpdateDate":"(\d{4})-(\d\d)-(\d\d)', html)
			self.date = (u"%s.%s.%s" % (md.group(3), md.group(2), md.group(1))) if md else u""
			d = get_url_json("https://api.fifa.com/api/v3/fifarankings/rankings/rankingsbyschedule?rankingScheduleId=%s&language=en" % m.group(1), timeout=25)
			rows = []
			for r in d.get("Results") or []:
				nm = (r.get("TeamName") or [{}])[0].get("Description") or u"?"
				rows.append({"pos": r.get("Rank") or 0, "prev": r.get("PrevRank") or 0, "name": nm, "code": r.get("IdCountry") or u"",
					"pts": float(r.get("TotalPoints") or 0), "extra": u""})
			rows.sort(key=lambda x: x["pos"])
		else:
			typ = "MEN_ASSOCIATION" if self.kind == "uefa" else "MEN_CLUB"
			d = get_url_json("https://comp.uefa.com/v2/coefficients?coefficientRange=OVERALL&coefficientType=%s&language=EN&page=1&pagesize=%d&seasonYear=%d"
				% (typ, 60 if self.kind == "uefa" else 80, uefa_season_year()), timeout=25)
			data = d.get("data") or {}
			lu = data.get("lastUpdateDate") or u""
			self.date = (u"%s.%s.%s" % (lu[8:10], lu[5:7], lu[0:4])) if len(lu) >= 10 else u""
			rows = []
			for m in data.get("members") or []:
				mem = m.get("member") or {}
				ov = m.get("overallRanking") or {}
				cur = [x for x in (m.get("seasonRankings") or []) if x.get("seasonYear") == uefa_season_year()]
				rows.append({"pos": ov.get("position") or 0, "prev": 0, "name": fix_name((mem.get("displayOfficialName") if self.kind == "club" else mem.get("displayName")) or mem.get("countryName") or u"?"),
					"code": mem.get("countryCode") or u"", "pts": float(ov.get("totalValue") or ov.get("totalPoints") or 0),
					"season": float(cur[0].get("totalValue") or cur[0].get("totalPoints") or 0) if cur else None, "trend": ov.get("trend") or u""})
			rows.sort(key=lambda x: x["pos"])
		self.rows = rows
		self.t_load = time.time()
		self.error = None
		return self


RANKINGS = [Ranking(480, "fifa"), Ranking(482, "uefa"), Ranking(484, "club")]


def ranking_by_page(p):
	for r in RANKINGS:
		if r.page == p:
			return r
	return None


# ---------------- Europaeische Laenderspiele (Seite 470) ----------------
# Es wird automatisch der Wettbewerb gezeigt, der gerade laeuft:
# EM-Qualifikation, WM-Qualifikation (UEFA) oder Nations League.
NAT_TITLES = {"euro": (u"EM-Qualifikation", u"EURO Elemeleri"), "wc": (u"WM-Qualifikation", u"Dünya Kupası Elemeleri"),
	"nl": (u"Nations League", u"Uluslar Ligi")}


def nat_stage_name(snm, lang):
	"""'League A: Group 2' -> 'Liga A · Gruppe 2', 'UEFA Qualification: 1st Round: Group C' -> 'Gruppe C'."""
	import re
	parts = [p.strip() for p in (snm or u"").replace(u";", u":").split(u":") if p.strip()]
	out = []
	for p in parts:
		m = re.match(r"(?i)^league ([a-d])$", p)
		if m:
			out.append((u"%s Ligi" if lang == "tr" else u"Liga %s") % m.group(1).upper())
			continue
		m = re.match(r"(?i)^group ([a-z0-9]+)", p)
		if m:
			g = m.group(1).upper()
			out.append((u"%s. Grup" % g if g.isdigit() else u"Grup %s" % g) if lang == "tr" else u"Gruppe %s" % g)
			continue
		if re.search(r"(?i)play-?off", p):
			out.append(u"Play-off")
		elif re.search(r"(?i)final", p):
			out.append(u"Final" if lang == "tr" else u"Finale")
		elif re.search(r"(?i)semi", p):
			out.append(u"Yarı Final" if lang == "tr" else u"Halbfinale")
		elif re.search(r"(?i)quarter", p):
			out.append(u"Çeyrek Final" if lang == "tr" else u"Viertelfinale")
	return u" · ".join(out) or snm


class NatLeague(League):
	"""Eine Gruppe des gerade laufenden Laenderspiel-Wettbewerbs."""

	def __init__(self, ccd, scd, snm, kind):
		League.__init__(self, (470, "nlg", ccd, scd, u"", u"", u""))
		self.snm = snm
		self.kind = kind

	def name(self, lang):
		t = NAT_TITLES[self.kind]
		return (t[1] if lang == "tr" else t[0]) + u" · " + nat_stage_name(self.snm, lang)

	def load(self):
		if getattr(self, "source", "") == "uefa":
			NAT.load_uefa()
			return self
		return League.load(self)


# Ersatzquelle UEFA (match.uefa.com / standings.uefa.com), wenn LiveScore gesperrt ist
UEFA_MATCH = "https://match.uefa.com/v5/matches"
UEFA_STAND = "https://standings.uefa.com/v1/standings"
UEFA_STATE = {"FINISHED": "post", "UPCOMING": "pre", "LIVE": "in", "POSTPONED": "pp", "CANCELLED": "pp", "ABANDONED": "pp"}


def uefa_day(ts):
	return time.strftime("%Y-%m-%d", time.gmtime(ts))


def uefa_matches(cid, season, q):
	return get_url_json("%s?competitionId=%s&seasonYear=%s&%s" % (UEFA_MATCH, cid, season, q), timeout=40) or []


def uefa_stage_name(grp):
	md = (grp or {}).get("metaData") or {}
	gn = md.get("groupName") or u""
	lg = (((grp or {}).get("league") or {}).get("metaData") or {}).get("leagueName") or u""
	import re
	m = re.match(r"(?i)^group ([a-d])(\d+)$", gn)
	if lg and m:
		return u"%s: Group %s" % (lg, m.group(2))
	return (lg + u": " + gn) if lg else gn


def parse_uefa_match(m, key):
	st = m.get("status") or u""
	state = UEFA_STATE.get(st, "pre")
	ph = (m.get("phase") or u"").upper()
	if state == "in" and "HALF_TIME" in ph:
		state = "ht"
	sc = ((m.get("score") or {}).get("total")) or {}
	hs, as_ = sc.get("home"), sc.get("away")
	if state == "pre":
		hs = as_ = None
	minute = u""
	if state == "in":
		mi = m.get("minute") or {}
		minute = u"%s" % (mi.get("normal") or u"")
	ht, at = m.get("homeTeam") or {}, m.get("awayTeam") or {}
	md = m.get("matchday") or {}
	return {"id": "uefa%s" % m.get("id"), "h": fix_name(ht.get("internationalName") or u"?"), "hs_name": u"",
		"a": fix_name(at.get("internationalName") or u"?"), "as_name": u"", "hs": hs, "as": as_,
		"state": state, "min": minute, "ts": espn_ts(((m.get("kickOffTime") or {}).get("dateTime")) or u""),
		"round": to_int(md.get("sequenceNumber")), "group": u"", "ut": key,
		"gid": u"%s" % ((m.get("group") or {}).get("id") or u"")}


class NatComp(object):
	def __init__(self):
		self.kind = "nl"
		self.groups = []
		self.t_disc = 0
		self.t_load = 0
		self.loading = False
		self.error = None

	def title(self, lang):
		t = NAT_TITLES[self.kind]
		return t[1] if lang == "tr" else t[0]

	def candidates(self):
		y = time.localtime().tm_year
		out = []
		for yy in range(y, y + 6):
			if yy % 4 == 0:
				out.append(("euro", "euro-%d-qualification" % yy))
		out.append(("wc", "world-cup-qualification"))
		out.append(("nl", "uefa-nations-league"))
		return out

	def uefa_candidates(self):
		y = time.localtime().tm_year
		out = []
		for yy in range(y, y + 6):
			if yy % 4 == 0:
				out.append(("euro", 3, yy))
		for yy in range(y, y + 5):
			if yy % 4 == 2:
				out.append(("wc", 17, yy))
		out.append(("nl", 2014, y + 1))
		out.append(("nl", 2014, y))
		return out

	def discover_uefa(self):
		"""Ersatz: aktiven Wettbewerb und Gruppen bei der UEFA suchen."""
		now = time.time()
		found = None
		for kind, cid, season in self.uefa_candidates():
			try:
				near = uefa_matches(cid, season, "fromDate=%s&toDate=%s&limit=1&offset=0&order=ASC" % (uefa_day(now - 21 * 86400), uefa_day(now + 120 * 86400)))
			except Exception as e:
				log("UEFA %s/%s: %r" % (cid, season, e))
				continue
			grp = [m for m in near if (m.get("group") or {}).get("id")]
			if grp:
				found = (kind, cid, season)
				break
		if not found:
			return False
		kind, cid, season = found
		st = get_url_json("%s?competitionId=%s&seasonYear=%s" % (UEFA_STAND, cid, season), timeout=40) or []
		groups = []
		for g in st:
			grp = g.get("group") or {}
			if not grp.get("id") or not g.get("items"):
				continue
			lg = NatLeague("uefa-%s" % cid, u"g%s" % grp.get("id"), uefa_stage_name(grp), kind)
			lg.source = "uefa"
			lg.gid = u"%s" % grp.get("id")
			lg.order = (to_int((grp.get("league") or {}).get("order")) or 0, to_int(grp.get("order")) or 0)
			groups.append(lg)
		if not groups:
			return False
		groups.sort(key=lambda x: x.order)
		self.kind = kind
		self.uefa = (cid, season)
		self.groups = groups
		self.t_disc = now
		self.t_uefa_full = 0
		self.uefa_stand = st
		log("Laenderspiele: LiveScore nicht erreichbar, UEFA %s/%s mit %d Gruppen" % (cid, season, len(groups)))
		return True

	def load_uefa(self):
		cid, season = self.uefa
		now = time.time()
		byg = dict((lg.gid, lg) for lg in self.groups)
		full = now - getattr(self, "t_uefa_full", 0) > 1800
		if full:
			evs = uefa_matches(cid, season, "toDate=%s&limit=80&offset=0&order=DESC" % uefa_day(now))
			evs += uefa_matches(cid, season, "fromDate=%s&limit=80&offset=0&order=ASC" % uefa_day(now + 86400))
			if now - self.t_disc > 60:
				self.uefa_stand = get_url_json("%s?competitionId=%s&seasonYear=%s" % (UEFA_STAND, cid, season), timeout=40) or self.uefa_stand
		else:
			# nur heutige Spiele neu (laufende Partien)
			evs = uefa_matches(cid, season, "fromDate=%s&toDate=%s&limit=80&offset=0&order=ASC" % (uefa_day(now), uefa_day(now)))
		per = {}
		for m in evs:
			pe = parse_uefa_match(m, u"")
			if pe["gid"] in byg:
				pe["ut"] = byg[pe["gid"]].ut
				per.setdefault(pe["gid"], {})[pe["id"]] = pe
		tabs = {}
		for g in self.uefa_stand or []:
			gid = u"%s" % ((g.get("group") or {}).get("id") or u"")
			rows = []
			for it in g.get("items") or []:
				tm = it.get("team") or {}
				rows.append({"pos": to_int(it.get("rank")) or 0, "tm": fix_name(tm.get("internationalName") or u"?"), "short": u"",
					"p": to_int(it.get("played")) or 0, "w": to_int(it.get("won")) or 0, "d": to_int(it.get("drawn")) or 0,
					"l": to_int(it.get("lost")) or 0, "gf": to_int(it.get("goalsFor")) or 0, "ga": to_int(it.get("goalsAgainst")) or 0,
					"pts": to_int(it.get("points")) or 0, "phr": None, "zone": None})
			rows.sort(key=lambda r: r["pos"])
			tabs[gid] = rows
		for gid, lg in byg.items():
			old = {} if full else dict((e["id"], e) for e in lg.all_events)
			old.update(per.get(gid, {}))
			lg.rnames = {}
			lg.set_events(list(old.values()), infer=False)
			if tabs.get(gid):
				lg.tables = [(u"", tabs[gid])]
			lg.t_load = now
			lg.error = None
		if full:
			self.t_uefa_full = now

	def discover(self):
		now = time.time()
		found = []
		for kind, ccd in self.candidates():
			try:
				cat = get_url_json("%s/category/soccer/%s/0?MD=1" % (BASE, ccd), timeout=25)
			except Exception:
				continue
			stages = []
			for st in cat.get("Stages") or []:
				scd = st.get("Scd") or u""
				if kind == "wc" and u"uefa" not in scd:
					continue  # nur die europaeischen Gruppen
				ts = [esd_ts(e.get("Esd")) for e in (st.get("Events") or [])]
				ts = [t for t in ts if abs(t - now) < 270 * 86400]
				if ts:
					stages.append((scd, st.get("Snm") or scd, min(ts), max(ts)))
			if not stages:
				continue
			near = min(min(abs(a - now), abs(b - now)) for _s, _n, a, b in stages)
			active = any(a - 21 * 86400 <= now <= b + 120 * 86400 or now <= a <= now + 120 * 86400 for _s, _n, a, b in stages)
			found.append((0 if active else 1, kind, ccd, stages, near))
		if not found:
			return False
		prio = {"euro": 0, "wc": 1, "nl": 2}
		found.sort(key=lambda f: (f[0], prio[f[1]] if f[0] == 0 else f[4]))
		_a, kind, ccd, stages, _n = found[0]
		stages.sort(key=lambda x: (u"group" not in x[0], x[0]))  # erst die Gruppen
		self.kind = kind
		self.groups = [NatLeague(ccd, scd, snm, kind) for scd, snm, _x, _y in stages]
		self.t_disc = now
		return True

	def load(self):
		if not self.groups or time.time() - self.t_disc > 6 * 3600:
			if not self.discover() and not self.discover_uefa() and not self.groups:
				raise Exception("Keine Länderspiele gefunden")
			STORE.set_nat(self.groups)
		if self.groups and getattr(self.groups[0], "source", "") == "uefa":
			self.load_uefa()
		else:
			for lg in list(self.groups):
				try:
					lg.load()
				except Exception as e:
					lg.error = nice_error(e)
			if self.groups and all(lg.error and not lg.all_events for lg in self.groups) and self.discover_uefa():
				STORE.set_nat(self.groups)
				self.load_uefa()
		self.t_load = time.time()
		self.error = None
		return self


NAT = NatComp()


def fupa_today(lg):
	"""Blockierend - heutige Spiele einer FuPa-Liga (fuer den Tor-Ticker)."""
	base = "%s/competitions/%s/seasons/%s/matches" % (FUPA, lg.scd, fupa_season())
	day = time.strftime("%Y-%m-%d")
	return [parse_fupa_match(m, lg.ut) for m in (get_url_json("%s?from=%s&to=%s" % (base, day, day)) or [])]


class DataStore(object):
	def __init__(self):
		self.leagues = [(FupaLeague(r) if r[2] == "fupa" else (CupLeague(r) if r[2].startswith("cup:") else League(r))) for r in LEAGUES]
		self.details = Details()
		self.days = {}       # Datum JJJJMMTT -> {"t":..., "list": [(liga, [spiele])], "loading": bool}
		self.by_ut = dict((l.ut, l) for l in self.leagues)
		self.live = {}       # id -> event
		self.t_live = 0
		self.live_error = None
		self.goals = []      # [(zeit, event)]
		self.loading_live = False

	def all_views(self):
		return [(lg, lg.page, None) for lg in self.leagues if lg.c != "nlg"]

	def nl_groups(self):
		return [lg for lg in self.leagues if lg.c == "nlg"]

	def set_nat(self, groups):
		"""Gruppen des aktuellen Laenderspiel-Wettbewerbs eintragen (fuer Live, Heute)."""
		self.leagues = [lg for lg in self.leagues if lg.c != "nlg"] + list(groups)
		self.by_ut = dict((l.ut, l) for l in self.leagues)

	def view(self, p):
		for lg in self.leagues:
			if lg.c == "nlg":
				continue
			if p == lg.page:
				return (lg, None, "res")
			if p == lg.page + 1:
				return (lg, None, "tab")
		return None

	def league_by_page(self, p):
		v = self.view(p)
		return v[0] if v else None

	def live_count_view(self, lg, gi):
		return len([e for e in self.live.values() if e["ut"] == lg.ut])

	def league_of_stage(self, ccd, scd):
		lg = self.by_ut.get("%s/%s" % (ccd, scd))
		if lg is not None:
			return lg
		for l in self.leagues:
			if isinstance(l, CupLeague) and l.matches_stage(ccd, scd):
				return l
		return None

	def espn_day(self, ymd, only_live=False):
		"""Ersatz: Spiele eines Tages von ESPN (fuer 500 / 510, wenn LiveScore sperrt)."""
		out = []
		for page, code in sorted(ESPN_CODES.items()):
			lg = self.league_by_page(page)
			if lg is None:
				continue
			try:
				d = fetch_json("%s/%s/scoreboard?dates=%s" % (ESPN, code, ymd), timeout=15)
			except Exception:
				continue
			evs = [parse_espn_event(ev, lg.ut) for ev in d.get("events") or []]
			if only_live:
				evs = [e for e in evs if e["state"] in ("in", "ht")]
			if evs:
				out.append((lg, evs))
		return out

	def fupa_day(self, ymd):
		"""Ersatz: Spiele eines Tages von FuPa fuer 3. Liga, Regionalligen, Oberliga."""
		out = []
		day = u"%s-%s-%s" % (ymd[0:4], ymd[4:6], ymd[6:8])
		for page, slug in sorted(FUPA_SLUGS.items()):
			if page in ESPN_CODES:
				continue
			lg = self.league_by_page(page)
			if lg is None:
				continue
			try:
				lst = fetch_json("%s/competitions/%s/seasons/%s/matches?from=%s&to=%s" % (FUPA, slug, fupa_season(), day, day), timeout=15)
			except Exception:
				continue
			evs = [parse_fupa_match(m, lg.ut) for m in lst or []]
			if evs:
				out.append((lg, evs))
		return out

	def fetch_live(self):
		"""Blockierend - liefert neue Live-Liste (fuer Thread)."""
		try:
			return self.fetch_live_ls()
		except Exception as e:
			if "404" in str(e) or "410" in str(e):
				raise
			out = {}
			for lg, evs in self.espn_day(time.strftime("%Y%m%d"), only_live=True):
				for pe in evs:
					out[pe["id"]] = pe
			for lg in self.leagues:  # schon geladene Ligen (FuPa/TFF-Ersatz) mit laufenden Spielen
				for pe in lg.events:
					if pe["state"] in ("in", "ht"):
						out.setdefault(pe["id"], pe)
			self.live_src = "espn"
			return out

	def fetch_live_ls(self):
		d = get_url_json("%s/live/soccer/0?MD=1" % BASE)
		self.live_src = "ls"
		out = {}
		for st in d.get("Stages") or []:
			lg = self.league_of_stage(st.get("Ccd"), st.get("Scd"))
			if lg is None:
				continue
			for e in st.get("Events") or []:
				pe = parse_event(e, lg.ut)
				if pe["state"] in ("in", "ht"):
					out[pe["id"]] = pe
		return out

	def fetch_day(self, ymd):
		"""Blockierend - alle Spiele eines Tages aus unseren Wettbewerben."""
		try:
			d = get_url_json("%s/date/soccer/%s/0?MD=1" % (BASE, ymd), timeout=30)
		except Exception as e:
			if "404" in str(e) or "410" in str(e):
				raise
			by = dict((lg.page, evs) for lg, evs in self.espn_day(ymd) + self.fupa_day(ymd))
			d = {"Stages": []}
		else:
			by = {}
		for st in d.get("Stages") or []:
			lg = self.league_of_stage(st.get("Ccd"), st.get("Scd"))
			if lg is None:
				continue
			for e in st.get("Events") or []:
				pe = parse_event(e, lg.ut)
				by.setdefault(lg.page, []).append(pe)
		y, m, dd = int(ymd[0:4]), int(ymd[4:6]), int(ymd[6:8])
		t0 = time.mktime((y, m, dd, 0, 0, 0, 0, 0, -1))
		for lg in self.leagues:  # Amateurligen (FuPa) und Ersatzdaten (TFF) aus den schon geladenen Ligen
			if (isinstance(lg, FupaLeague) or (getattr(lg, "source", "") == "tff" and lg.page not in by)) and lg.all_events:
				evs = [e for e in lg.all_events if t0 <= e["ts"] < t0 + 86400 and not e.get("nodate")]
				if evs:
					by[lg.page] = evs
		out = []
		for lg in self.leagues:
			if lg.page in by:
				out.append((lg, sorted(by[lg.page], key=lambda x: (x["ts"], x["h"]))))
		self.days[ymd] = {"t": time.time(), "list": out}
		return out

	def apply_live(self, new):
		"""Im Hauptthread: Live-Daten uebernehmen und Tore erkennen."""
		now = time.time()
		for eid, e in new.items():
			old = self.live.get(eid)
			if old is not None:
				o = (old["hs"] or 0) + (old["as"] or 0)
				n = (e["hs"] or 0) + (e["as"] or 0)
				if n > o:
					e["goal_at"] = now
					e["goal_by"] = "h" if (e["hs"] or 0) > (old["hs"] or 0) else "a"
					self.goals.append((now, e))
				else:
					e["goal_at"] = old.get("goal_at", 0)
					e["goal_by"] = old.get("goal_by")
		ended = [eid for eid in self.live if eid not in new]
		self.live = new
		self.t_live = now
		self.goals = [g for g in self.goals if now - g[0] < 60]
		for lg in self.leagues:
			changed = False
			for lst in (lg.all_events, lg.events):
				for i, ev in enumerate(lst):
					if ev["id"] in new:
						ne = dict(new[ev["id"]])
						ne["round"] = ev.get("round")
						lst[i] = ne
					elif ev["id"] in ended:
						changed = True
			if changed:
				lg.t_load = 0  # Endstand/Tabelle bald neu laden

	def live_count(self, lg=None):
		if lg is None:
			return len(self.live)
		return len([e for e in self.live.values() if e["ut"] == lg.ut])


class Rate(object):
	"""Wechselkurs 1 EUR -> TRY (EZB-Referenzkurs, Ersatzquelle open.er-api.com)."""
	def __init__(self):
		self.value = None
		self.date = u""
		self.src = u""
		self.t_load = 0
		self.loading = False

	def load(self):
		try:
			d = get_url_json("https://api.frankfurter.dev/v1/latest?from=EUR&to=TRY")
			self.value = float(d["rates"]["TRY"])
			self.date = d.get("date") or u""
			self.src = u"ezb"
		except Exception:
			d = get_url_json("https://open.er-api.com/v6/latest/EUR")
			self.value = float(d["rates"]["TRY"])
			ts = d.get("time_last_update_unix") or time.time()
			self.date = time.strftime("%Y-%m-%d", time.localtime(ts))
			self.src = u"er"
		self.t_load = time.time()
		return self


STORE = DataStore()
RATE = Rate()
