# -*- coding: utf-8 -*-
# SkorText - Live-Ergebnisse und Tabellen im Videotext-Stil fuer Enigma2 (GigaBlue / Team Blue)
from __future__ import absolute_import, division
import os
import sys
import time

from enigma import (eListboxPythonMultiContent, gFont, getDesktop, eTimer, addFont, eActionMap,
	RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import NumberActionMap
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Components.Label import Label
from Components.config import config, ConfigSubsection, ConfigSelection, configfile
from Plugins.Plugin import PluginDescriptor
from twisted.internet import threads

from .data import STORE, RATE, log, nice_error, RANKINGS, ranking_by_page, FupaLeague, fupa_today, NAT, get_url_json, fetch_bytes
from .texts import TXT, SETTINGS, tr_upper, nation, FAV_LEAGUES
from .news import FEED_LIST, feed_by_page

PY2 = sys.version_info[0] == 2
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION = "3.8.0"


def E(s):
	"""Text fuer Enigma (Python 2 braucht UTF-8-Bytes)."""
	if PY2 and isinstance(s, unicode):  # noqa: F821
		return s.encode("utf-8")
	return s


def U(s):
	if PY2 and isinstance(s, str):
		return s.decode("utf-8")
	return s


for _file, _alias in (("DejaVuSansMono-Bold.ttf", "SkorMono"), ("DejaVuSansCondensed-Bold.ttf", "SkorSans")):
	try:
		addFont(os.path.join(PLUGIN_DIR, "fonts", _file), _alias, 100, False)
	except Exception:
		pass

# ---------------- Einstellungen ----------------
config.plugins.SkorText = ConfigSubsection()
for _k, _lbl, _opts, _info in SETTINGS:
	setattr(config.plugins.SkorText, _k, ConfigSelection(default=E(_opts[0][0]), choices=[(E(o[0]), E(o[1])) for o in _opts]))


def cfg(key):
	return U(getattr(config.plugins.SkorText, key).value)


def set_cfg(key, val):
	c = getattr(config.plugins.SkorText, key)
	c.value = E(val)
	c.save()
	try:
		configfile.save()
	except Exception:
		pass


def T(key):
	return TXT[cfg("lang")][key]


def mk_timer(owner, cb):
	t = eTimer()
	try:
		owner._conns.append(t.timeout.connect(cb))
	except AttributeError:
		t.callback.append(cb)
	return t


PAL_TT = {"w": 0xF4F4F4, "y": 0xFFEE33, "c": 0x33F0F0, "g": 0x33E36A, "r": 0xFF3D3D, "m": 0xFF4FD8,
	"b": 0x2643FF, "d": 0x8A8A8A, "k": 0x000000, "fav": 0x6A1260, "sel": 0x1D2FA8}
# Moderner Stil: dunkles Schiefergrau, Karten, kraeftiger blauer Auswahlbalken mit gelber Kante
PAL_MOD = {"w": 0xEEF2F7, "y": 0xFFD54A, "c": 0x7CC8FF, "g": 0x3DDC84, "r": 0xFF5A5F, "m": 0xE070FF,
	"b": 0x4C8DFF, "d": 0x8C98AA, "k": 0x0B1016, "fav": 0x4B2C6E, "sel": 0x2F6BFF,
	"bg": 0x0F151D, "hdr": 0x0A0F15, "card": 0x1B2533, "zebra1": 0x141C26, "zebra2": 0x111821}
COL = dict(PAL_TT)


def modern():
	return cfg("style") == "modern"


def apply_palette():
	COL.clear()
	COL.update(PAL_MOD if modern() else PAL_TT)
PAGE_BG = {"black": 0x000000, "navy": 0x06103A, "mix": 0x98000000}
ALIGN = {"l": RT_HALIGN_LEFT, "r": RT_HALIGN_RIGHT, "c": RT_HALIGN_CENTER}
COUNTRY_BG = {"de": ("r", "w"), "tr": ("g", "k"), "eu": ("y", "k"), "nat": ("c", "k")}
FAV_CODES = {200: u"BL", 230: u"RL", 280: u"OL", 290: u"VL", 295: u"DFB", 300: u"SL", 305: u"TK", 440: u"CL", 450: u"EL", 460: u"ECL"}
SRC_TAG = {"espn": u" · ESPN", "tff": u" · TFF", "fupa": u" · FuPa"}
IDX_ROWS = 20
UPD_BASE = "https://github.com/postmen1971/skortext/releases/latest/download/"
UPD = {"msg": u"", "busy": False, "checked": 0}


def newer_version(a, b):
	def parts(v):
		out = []
		for x in (v or u"0").split("."):
			try:
				out.append(int(x))
			except ValueError:
				out.append(0)
		return out
	x, y = parts(a), parts(b)
	n = max(len(x), len(y))
	return x + [0] * (n - len(x)) > y + [0] * (n - len(y))  # Zeilen der Uebersicht


def seg(col, width, text, fg="w", bg=None, al="l", blink=False):
	return (col, width, text, fg, bg, al, blink)


def fit(text, width, short=u""):
	if len(text) <= width:
		return text
	if short and len(short) <= width:
		return short
	return text[:width]


def is_fav(name):
	f = cfg("fav")
	return bool(f) and f.lower() in (name or u"").lower()


def is_fav_first(name):
	"""Lieblingsverein, aber nicht seine zweite Mannschaft / Jugend."""
	if not is_fav(name):
		return False
	import re
	return not re.search(r"\b(II|U ?2\d|U ?19|U ?17)\b", name or u"")


def dn(name):
	"""Anzeigename (Laendernamen auf Deutsch/Tuerkisch)."""
	return nation(name, cfg("lang"))


def two(n):
	return u"%02d" % n


# =====================================================================
class SkorText(Screen):
	instance = None

	def __init__(self, session):
		dw = getDesktop(0).size().width()
		dh = getDesktop(0).size().height()
		mx, my = int(dw * 0.03), int(dh * 0.035)
		self.rowH = int((dh - 2 * my) / 24)
		self.fs = int(self.rowH * 0.84)
		self.cw = self.fs * 0.602
		self.pw = dw - 2 * mx
		self.cols = int(self.pw / self.cw)
		self.skin = ('<screen name="SkorText" position="0,0" size="%d,%d" flags="wfNoBorder" backgroundColor="#ff000000">'
			'<widget name="tt" position="%d,%d" size="%d,%d" backgroundColor="#ff000000" transparent="1" scrollbarMode="showNever" />'
			'<widget name="rate" position="%d,%d" size="%d,%d" font="SkorMono;%d" foregroundColor="#ffee33" backgroundColor="#ff000000" transparent="1" valign="center" zPosition="2" />'
			'<widget name="ratesub" position="%d,%d" size="%d,%d" font="SkorMono;%d" foregroundColor="#8a8a8a" backgroundColor="#ff000000" transparent="1" valign="center" halign="right" zPosition="2" />'
			'</screen>') % (dw, dh, mx, my, self.pw, self.rowH * 24,
			mx + int(self.cw), my + self.rowH * 20, int(self.pw * 0.36), self.rowH * 2, int(self.fs * 1.3),
			mx + int(self.pw * 0.30), my + self.rowH * 20, int(self.pw * 0.18), self.rowH * 2, self.fs)
		Screen.__init__(self, session)
		self._conns = []
		self["tt"] = MenuList([], enableWrapAround=False, content=eListboxPythonMultiContent)
		self["tt"].l.setFont(0, gFont("SkorMono", self.fs))
		self["tt"].l.setItemHeight(self.rowH)
		self["rate"] = Label("")
		self["ratesub"] = Label("")

		A = lambda k: (lambda: self.key(k))
		self["actions"] = NumberActionMap(["OkCancelActions", "DirectionActions", "ColorActions", "MenuActions",
			"NumberActions", "InfobarTeletextActions", "EPGSelectActions", "ChannelSelectBaseActions", "HelpActions"], {
			"ok": A("ok"), "cancel": A("exit"), "up": A("up"), "down": A("down"), "left": A("left"), "right": A("right"),
			"red": A("red"), "green": A("green"), "yellow": A("yellow"), "blue": A("blue"), "menu": A("menu"),
			"startTeletext": A("text"), "info": A("info"), "displayHelp": A("info"),
			"nextBouquet": A("chup"), "prevBouquet": A("chdn"),
			"1": self.keyNumber, "2": self.keyNumber, "3": self.keyNumber, "4": self.keyNumber, "5": self.keyNumber,
			"6": self.keyNumber, "7": self.keyNumber, "8": self.keyNumber, "9": self.keyNumber, "0": self.keyNumber,
		}, -2)

		sp = cfg("startpage")
		self.page = int(sp) if sp.isdigit() else 100
		self.sub = 0
		self.entry = u""
		self.entry_at = 0
		self.msg = u""
		self.msg_until = 0
		self.idx = [0, 1]
		self.set_sel = 0
		self.tick_sel = 0
		self.news_sel = 0
		self.news_open = None
		self.md = None   # angezeigter Spieltag (None = automatisch)
		self.det = False  # Ergebnisse mit Torschuetzen
		self.day_off = 0  # Seite 510: Tag relativ zu heute
		self.nl_pick = False
		self.mix = False
		self.blink_on = True
		self.last_rot = time.time()
		self.opened_at = time.time()
		self.closed = False
		self.timer = mk_timer(self, self.tick)
		self.onLayoutFinish.append(self.start)
		self.onClose.append(self.cleanup)
		SkorText.instance = self

	# ---------- Ablauf ----------
	def apply_style(self):
		apply_palette()
		font = "SkorSans" if modern() else "SkorMono"
		self["tt"].l.setFont(0, gFont(font, self.fs))
		try:
			self["rate"].instance.setFont(gFont(font, int(self.fs * 1.3)))
			self["ratesub"].instance.setFont(gFont(font, self.fs))
		except Exception:
			pass

	def start(self):
		try:
			self["tt"].instance.setSelectionEnable(0)
		except Exception:
			pass
		self.apply_style()
		self.go(self.page, quiet=True)
		self.fetch_live()
		self.draw()
		self.timer.start(500, False)
		if cfg("autoupd") != "off" and time.time() - UPD["checked"] > 6 * 3600:
			UPD["checked"] = time.time()
			self.check_update(False)

	def cleanup(self):
		self.closed = True
		self.timer.stop()
		SkorText.instance = None

	def tick(self):
		self.blink_on = not self.blink_on
		now = time.time()
		if self.entry and now - self.entry_at > 4:
			self.entry = u""
		ref = int(cfg("refresh"))
		if not STORE.loading_live and now - STORE.t_live > ref:
			self.fetch_live()
		lg = STORE.league_by_page(self.page)
		if lg:
			self.need_league(lg)
			if self.det:
				self.need_details(lg)
		t = self.page_type(self.page)
		if t == "fav":
			for l in self.fav_leagues():
				self.need_league(l)
		elif t == "nl":
			self.need_nat()
		elif t == "day":
			self.need_day()
		elif t == "rank":
			self.need_rank(ranking_by_page(self.page))
		fd = feed_by_page(self.page)
		if fd:
			self.need_feed(fd)
		if cfg("rotate") == "10" and not fd and not (t == "res" and not self.det) and now - self.last_rot > 10:
			self.last_rot = now
			n = len(self.subpages())
			if n > 1:
				self.sub = (self.sub + 1) % n
		self.draw()

	def fetch_live(self):
		STORE.loading_live = True
		d = threads.deferToThread(STORE.fetch_live)

		def ok(new):
			STORE.loading_live = False
			STORE.live_error = None
			STORE.apply_live(new)
			if not self.closed:
				self.draw()

		def err(f):
			STORE.loading_live = False
			STORE.t_live = time.time()
			STORE.live_error = nice_error(f.value)
			log("Live-Daten: %r" % f.value)
		d.addCallbacks(ok, err)

	def need_league(self, lg):
		if lg.loading:
			return
		age = time.time() - lg.t_load
		limit = int(cfg("refresh")) if (STORE.live_count(lg) or lg.live_count()) else 600
		if lg.t_load == 0 or age > limit:
			if lg.error and age < 20:
				return
			lg.loading = True
			d = threads.deferToThread(lg.load)

			def ok(_):
				lg.loading = False
				if not self.closed:
					self.draw()

			def err(f):
				lg.loading = False
				lg.error = nice_error(f.value)
				log("Liga %d (%s): %r" % (lg.page, lg.ut, f.value))
				lg.t_load = time.time() - 600 + 20  # in 20 s neuer Versuch
				if not self.closed:
					self.draw()
			d.addCallbacks(ok, err)

	def fav_leagues(self):
		return [l for l in (STORE.league_by_page(p) for p in FAV_LEAGUES.get(cfg("fav"), [])) if l is not None]

	def run_bg(self, fn, done, fail):
		d = threads.deferToThread(fn)

		def ok(r):
			try:
				done(r)
			finally:
				if not self.closed:
					self.draw()

		def err(f):
			try:
				fail(f)
			finally:
				if not self.closed:
					self.draw()
		d.addCallbacks(ok, err)

	def need_details(self, lg):
		rnd = self.shown_round(lg) if lg.round else None
		evs = lg.events_of_round(rnd) if rnd else lg.events
		ref = int(cfg("refresh"))
		busy = len(STORE.details.loading)
		for e in evs or []:
			if busy >= 4:
				break
			if STORE.details.needs(e, ref):
				busy += 1
				STORE.details.loading.add(e["id"])

				def done(_r, eid=e["id"]):
					STORE.details.loading.discard(eid)

				def fail(f, eid=e["id"]):
					STORE.details.loading.discard(eid)
					STORE.details.cache[eid] = {"t": time.time(), "list": [], "final": False}
					log("Details %s: %r" % (eid, f.value))
				self.run_bg(lambda ev=e: STORE.details.load(ev), done, fail)

	def day_key(self):
		return time.strftime("%Y%m%d", time.localtime(time.time() + self.day_off * 86400))

	def need_day(self):
		ymd = self.day_key()
		d = STORE.days.get(ymd)
		if d is not None and d.get("loading"):
			return
		if d is not None and "list" in d:
			live = any(e["state"] in ("in", "ht") for _lg, evs in d["list"] for e in evs)
			if time.time() - d["t"] < (int(cfg("refresh")) if live else 300):
				return
		if d is not None and d.get("error") and time.time() - d["t"] < 30:
			return
		STORE.days.setdefault(ymd, {"t": 0})["loading"] = True

		def done(_r):
			STORE.days[ymd]["loading"] = False
			STORE.days[ymd].pop("error", None)

		def fail(f):
			x = STORE.days.setdefault(ymd, {})
			x.update(loading=False, t=time.time(), error=nice_error(f.value))
			log("Tag %s: %r" % (ymd, f.value))
		self.run_bg(lambda: STORE.fetch_day(ymd), done, fail)

	def need_nat(self):
		if NAT.loading:
			return
		live = any(e["state"] in ("in", "ht") for lg in NAT.groups for e in lg.events)
		age = time.time() - NAT.t_load
		if NAT.t_load and age < (int(cfg("refresh")) if live else 600):
			return
		if NAT.error and age < 30:
			return
		NAT.loading = True

		def done(_r):
			NAT.loading = False

		def fail(f):
			NAT.loading = False
			NAT.error = nice_error(f.value)
			NAT.t_load = time.time()
			log("Laenderspiele: %r" % f.value)
		self.run_bg(NAT.load, done, fail)

	def need_rank(self, rk):
		if rk is None or rk.loading:
			return
		if rk.t_load and time.time() - rk.t_load < 6 * 3600 and not rk.error:
			return
		if rk.error and time.time() - rk.t_load < 60:
			return
		rk.loading = True

		def done(_r):
			rk.loading = False

		def fail(f):
			rk.loading = False
			rk.error = nice_error(f.value)
			rk.t_load = time.time()
			log("Rangliste %d: %r" % (rk.page, f.value))
		self.run_bg(rk.load, done, fail)

	# ---------- Update ueber GitHub ----------
	def check_update(self, manual):
		if UPD["busy"]:
			return
		UPD["busy"] = True
		if manual:
			UPD["msg"] = u"…"

		def done(v):
			UPD["busy"] = False
			new = (v or {}).get("plugin") or u""
			if not newer_version(new, VERSION):
				UPD["msg"] = (T("updNone") + u" (%s)" % VERSION) if manual else u""
				if manual:
					self.message(UPD["msg"], 3)
				return
			UPD["msg"] = u""
			self.session.openWithCallback(lambda yes: yes and self.install_update(new), MessageBox,
				E(T("updAsk") % (new, VERSION)), MessageBox.TYPE_YESNO)

		def fail(f):
			UPD["busy"] = False
			log("Update-Pruefung: %r" % f.value)
			if manual:
				UPD["msg"] = T("updErr")
				self.message(UPD["msg"], 3)
		self.run_bg(lambda: get_url_json(UPD_BASE + "version.json", timeout=20), done, fail)

	def install_update(self, new):
		UPD["msg"] = T("updLoad") % new
		self.message(UPD["msg"], 30)
		self.draw()

		def work():
			import subprocess
			raw = fetch_bytes(UPD_BASE + "skortext.ipk", timeout=60)
			with open("/tmp/skortext-update.ipk", "wb") as fh:
				fh.write(raw)
			pr = subprocess.Popen(["opkg", "install", "--force-reinstall", "/tmp/skortext-update.ipk"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			out = pr.communicate()[0]
			log("Update %s: opkg rc=%s %r" % (new, pr.returncode, out[-300:]))
			if pr.returncode != 0:
				raise Exception("opkg %s" % pr.returncode)
			return new

		def done(_r):
			UPD["msg"] = u""
			self.msg_until = 0
			from Screens.Standby import TryQuitMainloop
			self.session.openWithCallback(lambda yes: yes and self.session.open(TryQuitMainloop, 3), MessageBox,
				E(T("updDone") % new), MessageBox.TYPE_YESNO)

		def fail(f):
			UPD["msg"] = T("updErr")
			self.message(UPD["msg"], 4)
			log("Update: %r" % f.value)
		self.run_bg(work, done, fail)

	def need_rate(self):
		if RATE.loading or (RATE.t_load and time.time() - RATE.t_load < 1800):
			return
		RATE.loading = True
		d = threads.deferToThread(RATE.load)

		def ok(_):
			RATE.loading = False
			if not self.closed:
				self.draw()

		def err(f):
			log("Wechselkurs: %r" % f.value)
			RATE.loading = False
			RATE.t_load = time.time() - 1800 + 120  # in 2 Minuten neuer Versuch
		d.addCallbacks(ok, err)

	def draw_rate(self):
		if self.page != 100 or self.entry or self.idx[1] >= IDX_ROWS:
			self["rate"].setText("")
			self["ratesub"].setText("")
			return
		if RATE.value is None:
			self["rate"].setText(E(u"1 € = … ₺"))
			self["ratesub"].setText("")
			return
		v = (u"%.2f" % RATE.value).replace(u".", u",")
		self["rate"].setText(E(u"1 € = %s ₺" % v))
		dd = RATE.date[8:10] + u"." + RATE.date[5:7] + u"." if len(RATE.date) >= 10 else u""
		src = (u"AMB" if cfg("lang") == "tr" else u"EZB") if RATE.src == u"ezb" else u"Kurs"
		self["ratesub"].setText(E(src + u" " + dd))

	def shown_round(self, lg):
		if self.md:
			return self.md
		started = any(e["state"] != "pre" for e in lg.events)
		if not started and lg.prev_round:
			return lg.prev_round
		return lg.round

	def need_round(self, lg, n):
		if lg.events_of_round(n) is not None or n in lg.rloading or not lg.season:
			return
		lg.rloading.add(n)
		d = threads.deferToThread(lg.load_round, n)

		def ok(_):
			lg.rloading.discard(n)
			if not self.closed:
				self.draw()

		def err(f):
			lg.rloading.discard(n)
			log("Spieltag %d Liga %d: %r" % (n, lg.page, f.value))
			lg.rcache[n] = []
			if not self.closed:
				self.draw()
		d.addCallbacks(ok, err)

	def need_feed(self, fd):
		if fd.loading:
			return
		age = time.time() - fd.t_load
		if fd.t_load and age < 600:
			return
		fd.loading = True
		d = threads.deferToThread(fd.load)

		def ok(_):
			fd.loading = False
			if not self.closed:
				self.draw()

		def err(f):
			fd.loading = False
			fd.error = nice_error(f.value)
			log("Nachrichten %d: %r" % (fd.page, f.value))
			fd.t_load = time.time() - 600 + 30
			if not self.closed:
				self.draw()
		d.addCallbacks(ok, err)

	# ---------- Seiten ----------
	def page_type(self, p):
		if p == 100:
			return "idx"
		if p == 150:
			return "tick"
		if p == 190:
			return "help"
		if p == 500:
			return "live"
		if p == 900:
			return "set"
		if p == 110:
			return "fav"
		if p == 470:
			return "nl"
		if p == 510:
			return "day"
		if ranking_by_page(p):
			return "rank"
		if feed_by_page(p):
			return "news"
		v = STORE.view(p)
		if v:
			return v[2]
		return None

	def all_pages(self):
		pages = [100, 110, 150, 190, 470]
		for lg, base, gi in STORE.all_views():
			pages += [base, base + 1]
		return sorted(pages + [500, 510] + [r.page for r in RANKINGS] + [f.page for f in FEED_LIST] + [900])

	def go(self, p, quiet=False):
		if self.page_type(p) is None:
			self.message(T("notfound") % p)
			return
		if STORE.league_by_page(self.page) is None or STORE.league_by_page(self.page) is not STORE.league_by_page(p):
			self.md = None  # andere Liga: wieder beim aktuellen Spieltag beginnen
		old = self.page
		if p == 510 and old != 510:
			self.day_off = 0
		self.det = False
		self.page = p
		self.sub = 0
		self.last_rot = time.time()
		self.news_sel = 0
		self.news_open = None
		fd = feed_by_page(p)
		if fd:
			self.need_feed(fd)
		if p == 100:
			self.idx_mark(old)
		if p == 150:
			vals = [o[0] for o in SETTINGS[3][2]]
			self.tick_sel = vals.index(cfg("alarm")) if cfg("alarm") in vals else 0
		lg = STORE.league_by_page(p)
		if lg:
			self.need_league(lg)
		t = self.page_type(p)
		if t == "fav":
			for l in self.fav_leagues():
				self.need_league(l)
		elif t == "nl":
			self.need_nat()
			if old != 470:
				self.nl_pick = True  # mit der Gruppe der deutschen Mannschaft beginnen
		elif t == "day":
			self.need_day()
		elif t == "rank":
			self.need_rank(ranking_by_page(p))

	def message(self, s, secs=2.2):
		self.msg = s
		self.msg_until = time.time() + secs

	def up(self, s, country=None):
		if country == "tr" or cfg("lang") == "tr":
			u = tr_upper(s)
			if cfg("lang") != "tr":
				u = u.replace(u"LİGA", u"LIGA")  # deutsches Wort in Klammern, z. B. "(2. Liga)"
			return u
		return s.upper()

	# ---------- Tasten ----------
	def keyNumber(self, n):
		if not self.entry and n == 0:
			self.go(100)
			self.draw()
			return
		self.entry += u"%d" % n
		self.entry_at = time.time()
		if len(self.entry) == 3:
			p = int(self.entry)
			self.entry = u""
			self.go(p)
		self.draw()

	def key(self, k):
		self.entry = u""
		t = self.page_type(self.page)
		if t == "news" and k in ("exit", "ok", "up", "down", "left", "right"):
			self.news_key(k)
			self.draw()
			return
		if k == "exit":
			if self.page != 100:
				self.go(100)
				self.message(T("exitAgain"), 1.8)
			else:
				self.close()
				return
		elif k in ("red", "green", "yellow", "blue"):
			self.go({"red": 200, "green": 300, "yellow": 400, "blue": 500}[k])
		elif k == "menu":
			self.go(900)
			self.set_sel = 0
		elif k == "info":
			self.go(190)
		elif k == "text":
			self.mix = not self.mix
			self.message(T("mixOn") if self.is_mix() else T("mixOff"), 1.5)
		elif k in ("chup", "chdn"):
			pages = self.all_pages()
			i = pages.index(self.page) if self.page in pages else 0
			self.go(pages[(i + (1 if k == "chup" else -1)) % len(pages)])
		elif k in ("left", "right"):
			d = 1 if k == "right" else -1
			if t == "idx":
				self.move_idx(d, 0)
			elif t == "set":
				if self.set_sel == len(SETTINGS):
					self.go(190)
					self.draw()
					return
				if self.set_sel > len(SETTINGS):
					self.check_update(True)
					self.draw()
					return
				key, lbl, opts, info = SETTINGS[self.set_sel]
				vals = [o[0] for o in opts]
				i = vals.index(cfg(key)) if cfg(key) in vals else 0
				set_cfg(key, vals[(i + d) % len(vals)])
				if key == "style":
					self.apply_style()
			elif t in ("res", "tab"):
				views = STORE.all_views()
				base = self.page - (1 if t == "tab" else 0)
				bases = [v[1] for v in views]
				i = bases.index(base) if base in bases else 0
				det = self.det
				self.go(bases[(i + d) % len(bases)] + (1 if t == "tab" else 0))
				nl = STORE.league_by_page(self.page)
				self.det = det and t == "res" and not isinstance(nl, FupaLeague)
			elif t == "nl":
				n = len(self.subpages())
				self.sub = (self.sub + d) % max(1, n)
			elif t == "day":
				self.day_off = max(-7, min(7, self.day_off + d))
				self.sub = 0
				self.need_day()
			elif t == "rank":
				pages = [r.page for r in RANKINGS]
				self.go(pages[(pages.index(self.page) + d) % len(pages)])
		elif k in ("up", "down"):
			d = 1 if k == "down" else -1
			if t == "idx":
				self.move_idx(0, d)
			elif t == "set":
				self.set_sel = (self.set_sel + d) % (len(SETTINGS) + 2)
			elif t == "tick":
				self.tick_sel = (self.tick_sel + d) % len(SETTINGS[3][2])
			elif t == "res" and STORE.league_by_page(self.page).round and not self.det:
				lg = STORE.league_by_page(self.page)
				n = self.shown_round(lg) + (-1 if d > 0 else 1)  # ▼ = zurueck, ▲ = vor
				top = lg.max_round or (lg.round + 40)
				if 1 <= n <= top:
					self.md = n
					self.sub = 0
					self.need_round(lg, n)
				else:
					self.message(T("noMore"), 1.5)
			else:
				n = len(self.subpages())
				self.sub = (self.sub + d) % max(1, n)
				self.last_rot = time.time()
		elif k == "ok":
			if t == "idx":
				it = self.idx_cols()[self.idx[0]][self.idx[1]]
				if it and "page" in it:
					self.go(it["page"])
			elif t == "res":
				self.go(self.page + 1)
			elif t == "tab":
				self.go(self.page - 1)
			elif t == "set":
				if self.set_sel == len(SETTINGS):
					self.go(190)
					self.draw()
					return
				if self.set_sel > len(SETTINGS):
					self.check_update(True)
					self.draw()
					return
				key, lbl, opts, info = SETTINGS[self.set_sel]
				vals = [o[0] for o in opts]
				i = vals.index(cfg(key)) if cfg(key) in vals else 0
				set_cfg(key, vals[(i + 1) % len(vals)])
				if key == "style":
					self.apply_style()
			elif t == "tick":
				val = SETTINGS[3][2][self.tick_sel][0]
				set_cfg("alarm", val)
				if val != "off":
					self.close()
					return
				self.message(T("tkOffMsg"), 1.8)
		self.draw()

	def news_key(self, k):
		fd = feed_by_page(self.page)
		n = len(fd.items)
		if k == "exit":
			if self.news_open is not None:
				self.news_open = None
			else:
				self.go(100)
				self.message(T("exitAgain"), 1.8)
		elif k == "ok":
			if self.news_open is None and n:
				self.news_open = self.news_sel
			else:
				self.news_open = None
		elif k in ("up", "down") and n:
			d = 1 if k == "down" else -1
			if self.news_open is not None:
				self.news_open = (self.news_open + d) % n
				self.news_sel = self.news_open
			else:
				self.news_sel = (self.news_sel + d) % n
		elif k in ("left", "right"):
			if self.news_open is not None and n:
				d = 1 if k == "right" else -1
				self.news_open = (self.news_open + d) % n
				self.news_sel = self.news_open
			else:
				i = FEED_LIST.index(fd)
				self.go(FEED_LIST[(i + (1 if k == "right" else -1)) % len(FEED_LIST)].page)

	def is_mix(self):
		return (cfg("bg") == "mix") != self.mix

	# ---------- Uebersicht ----------
	def idx_cols(self):
		lang = cfg("lang")
		de = [l for l in STORE.leagues if l.c == "de"]
		tr = [l for l in STORE.leagues if l.c == "tr"]
		eu = [l for l in STORE.leagues if l.c == "eu"]
		nat = [l for l in STORE.leagues if l.c == "nat"]
		def views(ls):
			out = []
			for l in ls:
				for base, gi in l.views():
					lbl = (l.tag + u" " if l.tag else u"") + l.name(lang) + ((u" · " + l.gdefs[gi][0]) if gi is not None else u"")
					out.append({"page": base, "lbl": lbl, "lg": l, "gi": gi})
			return out
		tick = T("ticker") + u" · " + (T("tkOff") if cfg("alarm") == "off" else T("tkOn"))
		left = [{"hdr": T("cDE"), "bg": "r", "fg": "w"}] + views(de) + [None,
			{"hdr": T("cMORE"), "bg": "m", "fg": "k"},
			{"page": 110, "lbl": T("fav") + ((u" · " + cfg("fav")) if cfg("fav") else u"")}, {"page": 510, "lbl": T("today")},
			{"page": 500, "lbl": T("allLive"), "live": True},
			{"page": 600, "lbl": u"Haberler · " + u", ".join(f.name for f in FEED_LIST[:3]) + u" …"},
			{"page": 150, "lbl": tick}, {"page": 900, "lbl": T("settings")}]
		right = [{"hdr": T("cTR"), "bg": "g", "fg": "k"}] + views(tr) + [
			{"hdr": T("cEU"), "bg": "y", "fg": "k"}] + views(eu) + [
			{"hdr": T("cNAT"), "bg": "c", "fg": "k"}, {"page": 470, "lbl": NAT.title(lang) if NAT.groups else T("natEU")},
			{"hdr": T("cRANK"), "bg": "b", "fg": "w"},
			{"page": 480, "lbl": T("rkFifa")}, {"page": 482, "lbl": T("rkUefa")}, {"page": 484, "lbl": T("rkClub")}]
		n = max(len(left), len(right), IDX_ROWS)
		left += [None] * (n - len(left))
		right += [None] * (n - len(right))
		return [left, right]

	def idx_mark(self, old):
		"""In der Uebersicht dort stehen bleiben, wo man zuletzt hineingegangen ist."""
		lg = STORE.league_by_page(old)
		target = lg.page if lg else (600 if 600 <= old < 700 else old)
		try:
			for ci, col in enumerate(self.idx_cols()):
				for ri, it in enumerate(col):
					if it is not None and it.get("page") == target:
						self.idx = [ci, ri]
						return
			cols = self.idx_cols()
			c, r = self.idx
			if not (c < len(cols) and r < len(cols[c]) and cols[c][r] is not None and "page" in cols[c][r]):
				self.idx = [0, 1]
		except Exception:
			self.idx = [0, 1]

	def move_idx(self, dc, dr):
		cols = self.idx_cols()
		c, r = self.idx
		ok = lambda it: it is not None and "page" in it
		if dc:
			c = (c + dc) % 2
			r = min(r, len(cols[c]) - 1)
			k = 0
			while not ok(cols[c][r]) and k < 40:
				r = (r + 1) % len(cols[c])
				k += 1
		if dr:
			k = 0
			while True:
				r = (r + dr) % len(cols[c])
				k += 1
				if ok(cols[c][r]) or k > 40:
					break
		self.idx = [c, r]

	# ---------- Zeilen bauen ----------
	def status_segs(self, e, col):
		st = e["state"]
		if st == "pre" and e.get("nodate"):
			return [seg(col, 6, u"", "w")]
		if st == "pre":
			lt = time.localtime(e["ts"])
			return [seg(col, 6, two(lt.tm_hour) + u":" + two(lt.tm_min), "w")]
		if st == "post":
			return [seg(col, 6, T("ft"), "d")]
		if st == "pp":
			return [seg(col, 6, T("pp"), "r")]
		if st == "ht":
			return [seg(col, 6, T("ht"), "g")]
		return [seg(col, 6, (e["min"] or u"") + (u"'" if e["min"] and e["min"][0].isdigit() else u""), "g")]

	def res_row(self, e):
		C = self.cols
		W = (C - 17) // 2
		fresh = time.time() - e.get("goal_at", 0) < 30
		s = self.status_segs(e, 0)
		hcol = "y" if fresh and e.get("goal_by") == "h" else "w"
		acol = "y" if fresh and e.get("goal_by") == "a" else "w"
		s.append(seg(7, W, fit(dn(e["h"]), W, e["hs_name"]), hcol, al="r"))
		if e["state"] == "pre" or e["hs"] is None:
			s.append(seg(8 + W, 5, u"-:-", "d", al="c"))
		elif fresh:
			s.append(seg(8 + W, 5, u"%d:%d" % (e["hs"], e["as"]), "k", "y", "c", blink=True))
		else:
			s.append(seg(8 + W, 5, u"%d:%d" % (e["hs"], e["as"]), "w" if e["state"] == "post" else "y", al="c"))
		s.append(seg(14 + W, W, fit(dn(e["a"]), W, e["as_name"]), acol))
		if e["state"] in ("in", "ht"):
			s.append(seg(15 + 2 * W, 2, u"●", "g", blink=True))
		bg = COL["fav"] if (is_fav(e["h"]) or is_fav(e["a"])) else None
		return (bg, s)

	def zebra(self, row, i):
		"""Jede zweite Zeile tuerkis statt weiss - besser lesbar (wie im echten Videotext)."""
		if i % 2 == 0:
			return row
		bg, segs = row
		return (bg, [tuple(s[:3]) + (("c" if s[3] == "w" else s[3]),) + tuple(s[4:]) for s in segs])

	def day_label(self, ts):
		lt = time.localtime(ts)
		return u"%s %s.%s." % (T("days")[lt.tm_wday], two(lt.tm_mday), two(lt.tm_mon))

	def result_lines(self, events):
		out = []
		last = None
		n = 0
		for e in sorted(events, key=lambda x: (0 if x["state"] in ("in", "ht") else 1, x["ts"], x["h"])):
			live = e["state"] in ("in", "ht")
			dl = (u"● " + self.up(T("live"))) if live else (self.day_label(e["ts"]) if not e.get("nodate") else u"")
			if dl != last:
				out.append((None, [seg(0, self.cols, dl, "g" if live else "c")]))
				last = dl
			out.append(self.zebra(self.res_row(e), n))
			n += 1
		return out

	def table_lines(self, lg, rows, gi):
		C = self.cols
		N = C - 40
		live = [e for e in lg.events if e["state"] in ("in", "ht") and e["hs"] is not None and lg.in_group(e["group"], gi)]
		rows = [dict(r) for r in rows]
		changed = False
		if live:
			by = dict((r["tm"], r) for r in rows)
			for e in live:
				H, A = by.get(e["h"]), by.get(e["a"])
				if not H or not A:
					continue
				for X, gf, ga in ((H, e["hs"], e["as"]), (A, e["as"], e["hs"])):
					X["live"] = True
					if lg.round and X["p"] >= lg.round:
						continue  # die Datenquelle hat das laufende Spiel schon eingerechnet
					X["p"] += 1
					X["gf"] += gf
					X["ga"] += ga
					X["changed"] = True
					if gf > ga:
						X["w"] += 1
						X["pts"] += 3
					elif gf == ga:
						X["d"] += 1
						X["pts"] += 1
					else:
						X["l"] += 1
			changed = any(r.get("changed") for r in rows)
			if changed:
				rows.sort(key=lambda r: (-r["pts"], -(r["gf"] - r["ga"]), -r["gf"], r["tm"]))
		out = []
		for i, r in enumerate(rows):
			rank = i + 1 if changed else r["pos"]
			trend = (r["pos"] - rank) if changed else 0
			z = r["zone"]
			s = [seg(0, 3, u"%d." % rank, "k" if z else "w", z, "c")]
			if trend > 0:
				s.append(seg(3, 1, u"▲", "g"))
			elif trend < 0:
				s.append(seg(3, 1, u"▼", "r"))
			name = fit(dn(r["tm"]), N - (2 if r.get("live") else 0), r["short"])
			s.append(seg(5, N, name, "w"))
			if r.get("live"):
				s.append(seg(5 + len(name) + 1, 1, u"•", "g", blink=True))
			gd = r["gf"] - r["ga"]
			s += [seg(C - 34, 3, u"%d" % r["p"], al="r"), seg(C - 30, 3, u"%d" % r["w"], al="r"),
				seg(C - 26, 3, u"%d" % r["d"], al="r"), seg(C - 22, 3, u"%d" % r["l"], al="r"),
				seg(C - 18, 7, u"%d:%d" % (r["gf"], r["ga"]), al="r"),
				seg(C - 10, 5, (u"+%d" % gd) if gd > 0 else u"%d" % gd, al="r"),
				seg(C - 4, 4, u"%d" % r["pts"], "y", al="r")]
			out.append(self.zebra((COL["fav"] if is_fav(r["tm"]) else None, s), i))
		return out

	def table_head(self):
		C = self.cols
		return (None, [seg(0, 3, T("pl"), "c", al="c"), seg(5, C - 40, T("club"), "c"),
			seg(C - 34, 3, T("sp"), "c", al="r"), seg(C - 30, 3, T("w"), "c", al="r"),
			seg(C - 26, 3, T("d"), "c", al="r"), seg(C - 22, 3, T("l"), "c", al="r"),
			seg(C - 18, 7, T("goals"), "c", al="r"), seg(C - 10, 5, T("diff"), "c", al="r"),
			seg(C - 4, 4, T("pts"), "c", al="r")])

	def info_head(self, left):
		C = self.cols
		lt = time.localtime(STORE.t_live or time.time())
		right = T("stand") + u" " + two(lt.tm_hour) + u":" + two(lt.tm_min) + u":" + two(lt.tm_sec)
		return (None, [seg(0, C - 18, left, "c"), seg(C - 17, 17, right, "c", al="r")])

	def text(self, s, fg="w"):
		return (None, [seg(0, self.cols, s, fg)])

	def chunk(self, lines, n=20):
		out = [lines[i:i + n] for i in range(0, len(lines), n)]
		return out or [[]]

	def status_lines(self, lg):
		if lg.loading and not lg.t_load:
			return [self.text(u""), self.text(T("loading"), "y")]
		if lg.error and not lg.events and not lg.tables:
			return [self.text(u""), self.text(T("noData"), "r"), self.text(T("noData2"), "c"),
				self.text(u""), self.text(fit(lg.error, self.cols), "d")]
		return None

	def subpages(self):
		lang = cfg("lang")
		t = self.page_type(self.page)
		subs = []
		C = self.cols
		if t == "idx":
			L, R = self.idx_cols()
			half = C // 2
			lines = []
			win = self.idx[1] // IDX_ROWS
			nwin = (max(len(L), len(R)) + IDX_ROWS - 1) // IDX_ROWS
			for i in range(win * IDX_ROWS, min(max(len(L), len(R)), (win + 1) * IDX_ROWS)):
				s = []
				for ci, col in enumerate((L, R)):
					it = col[i] if i < len(col) else None
					base = ci * half
					if it is None:
						continue
					if "hdr" in it:
						s.append(seg(base, half - 1, u" " + it["hdr"], it["fg"], it["bg"]))
						continue
					sel = self.idx == [ci, i]
					if modern():
						bg = "sel" if sel else None
						fgp, fgn, fgl = ("y", "w", "w") if sel else ("c", "g" if it.get("live") else "w", "g")
					else:
						bg = "c" if sel else None
						fgp, fgn, fgl = ("k", "k", "k") if sel else ("y", "g" if it.get("live") else "w", "g")
					s.append(seg(base, half - 1, u"", "k", bg))
					if sel and modern():
						s.append(seg(base, 0.45, u"", "k", "y"))  # gelbe Kante = hier stehst du
					s.append(seg(base + (0.6 if modern() else 0), 4, u"%d" % it["page"], fgp, bg))
					s.append(seg(base + (5 if modern() else 4), half - 12, fit(it["lbl"], half - 12), fgn, bg))
					n = STORE.live_count_view(it["lg"], it["gi"]) if "lg" in it else (STORE.live_count() if it.get("live") else 0)
					if n:
						s.append(seg(base + half - 7, 5, u"●%d" % n, fgl, bg, "r"))
				lines.append((None, s))
			while len(lines) < IDX_ROWS:
				lines.append(self.text(u""))
			lines.append(self.text(T("openHint") + u"   · " + T("source"), "c"))
			right = u"SkorText " + VERSION + ((u"  %d/%d" % (win + 1, nwin)) if nwin > 1 else u"")
			# keine Info-Zeile: die Uebersicht beginnt direkt unter dem Titel
			subs = [{"ban": (self.up(T("overview")), right), "bg": ("b", "w"),
				"head": lines[0], "lines": lines[1:]}]
		elif t in ("res", "tab"):
			lg, gi, _k = STORE.view(self.page)
			bgc = COUNTRY_BG[lg.c]
			title = self.up(lg.name(lang), lg.c)
			stl = self.status_lines(lg)
			if gi is not None:
				parts = [(gi, title + u" · " + self.up(lg.gdefs[gi][0], lg.c))]
			elif len(lg.tables) > 1:  # Liga mit mehreren Tabellen ohne eigene Seiten
				parts = [(None, title + ((u" · " + self.up(n, lg.c)) if n else u""), n) for n, _r in lg.tables]
			else:
				parts = [(None, title)]
			for part in parts:
				pgi, gt = part[0], part[1]
				pname = part[2] if len(part) > 2 else None
				match = (lambda name: name == pname) if pname is not None else (lambda name: lg.in_group(name, pgi))
				if t == "res":
					right = self.up(T("results")) + SRC_TAG.get(getattr(lg, "source", ""), u"")
					rnd = self.shown_round(lg) if lg.round else None
					if stl is not None:
						lines = stl
					else:
						evs = lg.events_of_round(rnd) if rnd else lg.events
						if evs is None:
							self.need_round(lg, rnd)
							lines = [self.text(u""), self.text(T("loading"), "y")]
						else:
							cur = [e for e in evs if match(e["group"])]
							lines = self.result_lines(cur) or [self.text(u""), self.text(T("noGames"), "c")]
					hint = u""
					if rnd:
						lbl = lg.round_label(rnd, lang) or (T("md") % rnd)
						hint = lbl + (u"  " + T("mdNow") if rnd == lg.round else u"") + u"   ▲▼ " + T("mdBrowse")
					if self.det and stl is None:
						right = self.up(T("scorers"))
						hint = (lbl if rnd else u"") + u"   " + T("detHint")
						evs = lg.events_of_round(rnd) if rnd else lg.events
						blocks = self.det_blocks([e for e in (evs or []) if match(e["group"])])
						head = self.info_head(hint)
						for ch in self.chunk_blocks(blocks):
							subs.append({"ban": (gt, right), "bg": bgc, "head": head, "lines": ch})
						continue
					head = self.info_head(hint)
					for ch in self.chunk(lines):
						subs.append({"ban": (gt, right), "bg": bgc, "head": head, "lines": ch})
				else:
					right = self.up(T("liveTable") if STORE.live_count_view(lg, pgi) else T("table")) + SRC_TAG.get(getattr(lg, "source", ""), u"")
					if stl is not None:
						lines = stl
					else:
						tabs = [x[1] for x in lg.tables if match(x[0])]
						lines = self.table_lines(lg, tabs[0], pgi) if tabs else [self.text(u""), self.text(T("noTable"), "c")]
					for ch in self.chunk(lines):
						subs.append({"ban": (gt, right), "bg": bgc, "head": self.table_head(), "lines": ch})
				if stl is not None:
					break
		elif t == "live":
			lines = []
			for lg in STORE.leagues:
				evs = [e for e in STORE.live.values() if e["ut"] == lg.ut]
				if not evs:
					continue
				groups = sorted(set(e["group"] for e in evs))
				for g in groups:
					hdr = (lg.tag + u" " if lg.tag else u"") + lg.name(lang) + ((u" · " + g) if g else u"") + u"   (%d)" % lg.page_of_group(g)
					lines.append(self.text(hdr, "y"))
					for zi, e in enumerate(sorted([x for x in evs if x["group"] == g], key=lambda x: x["ts"])):
						lines.append(self.zebra(self.res_row(e), zi))
			if not lines:
				if STORE.live_error and not STORE.live:
					lines = [self.text(u""), self.text(T("noData"), "r"), self.text(T("noData2"), "c")]
				else:
					lines = [self.text(u""), self.text(T("noLive"), "c")]
			for ch in self.chunk(lines):
				subs.append({"ban": (u"● " + self.up(T("allLive")), u""), "bg": ("b", "w"),
					"head": self.info_head(self.day_label(time.time())), "lines": ch})
		elif t == "news":
			subs = self.news_subpages()
		elif t == "help":
			lines = [self.text(u"")]
			for k, v in T("helpRows"):
				lines.append((None, [seg(1, 14, k, "y"), seg(16, C - 16, v)]))
			lines.append(self.text(u""))
			lines.append(self.text(u"SkorText " + VERSION + u" · " + T("source"), "d"))
			subs = [{"ban": (self.up(T("help")), u"SkorText"), "bg": ("b", "w"), "head": self.text(u""), "lines": ch} for ch in self.chunk(lines)]
		elif t == "fav":
			subs = self.fav_subpages()
		elif t == "nl":
			subs = self.nl_subpages()
		elif t == "day":
			subs = self.day_subpages()
		elif t == "rank":
			subs = self.rank_subpages()
		elif t == "set":
			lines = [self.text(u"")]
			half = C // 2
			for i, (key, lbl, opts, info) in enumerate(SETTINGS):
				sel = i == self.set_sel
				cur = [o for o in opts if o[0] == cfg(key)]
				cur = cur[0] if cur else opts[0]
				val = cur[2] if lang == "tr" else cur[1]
				lines.append((COL["sel"] if sel else None, [seg(1, half - 2, lbl[1] if lang == "tr" else lbl[0], "y" if sel else "w"),
					seg(half, half, (u"◄ " if sel else u"  ") + val + (u" ►" if sel else u""), "y" if sel else "c")]))
			sel = self.set_sel == len(SETTINGS)
			lines.append((COL["sel"] if sel else None, [seg(1, half - 2, T("help"), "y" if sel else "w"),
				seg(half, half, (u"► " if sel else u"  ") + T("helpOpen"), "y" if sel else "c")]))
			us = self.set_sel > len(SETTINGS)
			lines.append((COL["sel"] if us else None, [seg(1, half - 2, T("updRow"), "y" if us else "w"),
				seg(half, half, (u"► " if us else u"  ") + (UPD["msg"] or T("updOpen")), "y" if us else "c")]))
			lines.append(self.text(u""))
			inf = SETTINGS[self.set_sel][3] if not (sel or us) else ((T("helpInfo"),) * 2 if sel else ((T("updInfo") + u" " + VERSION),) * 2)
			lines.append(self.text(u" " + (inf[1] if lang == "tr" else inf[0]), "g"))
			while len(lines) < 19:
				lines.append(self.text(u""))
			lines.append(self.text(T("setHint"), "c"))
			subs = [{"ban": (self.up(T("settings")), u"SkorText"), "bg": ("b", "w"), "head": self.text(u"MENU", "d"), "lines": lines}]
		elif t == "tick":
			key, lbl, opts, info = SETTINGS[3]
			on = cfg("alarm") != "off"
			cur = [o for o in opts if o[0] == cfg("alarm")][0]
			st = [seg(1, 12, T("ticker") + u":", "w"), seg(13, 8, u" " + (T("tkOn") if on else T("tkOff")) + u" ", "k" if on else "w", "g" if on else "r")]
			if on:
				st.append(seg(23, C - 24, cur[2] if lang == "tr" else cur[1], "g"))
			lines = [self.text(u""), (None, st), self.text(u""),
				self.text(u" " + T("tk1"), "c"), self.text(u" " + T("tk2"), "c"), self.text(u" " + T("tk3"), "c"), self.text(u"")]
			for i, o in enumerate(opts):
				sel = i == self.tick_sel
				act = o[0] == cfg("alarm")
				lines.append((COL["sel"] if sel else None, [seg(1, C - 2, (u"► " if sel else u"  ") + (u"● " if act else u"○ ") + (o[2] if lang == "tr" else o[1]),
					"y" if sel else ("g" if act else "w"))]))
			while len(lines) < 19:
				lines.append(self.text(u""))
			lines.append(self.text(T("tkHint"), "c"))
			subs = [{"ban": (u"150 " + self.up(T("ticker")), u"SkorText"), "bg": ("b", "w"), "head": self.text(u"●", "y"), "lines": lines}]
		return subs or [{"ban": (u"", u""), "bg": ("b", "w"), "head": self.text(u""), "lines": []}]

	# ---------- Torschuetzen ----------
	def det_items(self, inc, side):
		out = []
		for x in inc:
			if x["side"] != side:
				continue
			m = x["min"] + u"."
			if x["type"] in ("goal", "pen", "og"):
				extra = {"pen": u" (" + T("pen") + u")", "og": u" (" + T("og") + u")"}.get(x["type"], u"")
				out.append((m + u" " + x["name"] + extra, "c"))
			elif x["type"] == "red":
				out.append((u"■ " + m + u" " + x["name"], "r"))
			elif x["type"] == "yr":
				out.append((u"■ " + m + u" " + x["name"], "y"))
		return out

	def pack(self, items, width):
		"""Eintraege zeilenweise auf die Breite verteilen."""
		lines, cur, ln = [], [], 0
		for txt, col in items:
			txt = fit(txt, width)
			add = len(txt) + (2 if cur else 0)
			if cur and ln + add > width:
				lines.append(cur)
				cur, ln = [], 0
				add = len(txt)
			cur.append((txt, col))
			ln += add
		if cur:
			lines.append(cur)
		return lines

	def det_blocks(self, events):
		C = self.cols
		W = (C - 17) // 2
		blocks = []
		for e in sorted(events, key=lambda x: (0 if x["state"] in ("in", "ht") else 1, x["ts"], x["h"])):
			bl = [self.res_row(e)]
			if e["state"] != "pre":
				inc = STORE.details.get(e)
				if inc is None:
					bl.append((None, [seg(7, W, u"…", "d", al="r")]))
				else:
					hl = self.pack(self.det_items(inc, 1), W)
					al = self.pack(self.det_items(inc, 2), W)
					for i in range(max(len(hl), len(al))):
						s = []
						if i < len(hl):
							tot = sum(len(t) for t, c in hl[i]) + 2 * (len(hl[i]) - 1)
							x = 7 + W - tot
							for j, (txt, col) in enumerate(hl[i]):
								s.append(seg(x, len(txt) + (1 if j < len(hl[i]) - 1 else 0), txt + (u"," if j < len(hl[i]) - 1 else u""), col))
								x += len(txt) + 2
						if i < len(al):
							x = 14 + W
							for j, (txt, col) in enumerate(al[i]):
								s.append(seg(x, len(txt) + 1, txt + (u"," if j < len(al[i]) - 1 else u""), col))
								x += len(txt) + 2
						bl.append((None, s))
			blocks.append(bl)
		if not blocks:
			blocks = [[self.text(u""), self.text(T("noGames"), "c")]]
		return blocks

	def chunk_blocks(self, blocks, n=20):
		pages, cur = [], []
		for bl in blocks:
			if cur and len(cur) + len(bl) > n:
				pages.append(cur)
				cur = []
			cur = cur + bl[:n]
		if cur:
			pages.append(cur)
		return pages or [[]]

	# ---------- Mein Verein ----------
	def fav_row(self, e, lg):
		C = self.cols
		W = (C - 22) // 2
		lt = time.localtime(e["ts"])
		live = e["state"] in ("in", "ht")
		s = self.status_segs(e, 0) if live else [seg(0, 6, two(lt.tm_mday) + u"." + two(lt.tm_mon) + u".", "d")]
		s.append(seg(7, W, fit(dn(e["h"]), W, e["hs_name"]), "y" if is_fav(e["h"]) else "w", al="r"))
		if e["state"] == "pre":
			s.append(seg(8 + W, 5, two(lt.tm_hour) + u":" + two(lt.tm_min), "c", al="c"))
		elif e["hs"] is None:
			s.append(seg(8 + W, 5, T("pp") if e["state"] == "pp" else u"-:-", "r" if e["state"] == "pp" else "d", al="c"))
		else:
			s.append(seg(8 + W, 5, u"%d:%d" % (e["hs"], e["as"]), "y" if live else "w", al="c"))
		s.append(seg(14 + W, W, fit(dn(e["a"]), W, e["as_name"]), "y" if is_fav(e["a"]) else "w"))
		s.append(seg(C - 4, 4, FAV_CODES.get(lg.page, u""), "d", al="r"))
		return (None, s)

	def fav_subpages(self):
		C = self.cols
		lang = cfg("lang")
		fav = cfg("fav")
		ban = (self.up(T("fav")) + ((u" · " + self.up(fav)) if fav else u""), u"")
		head = self.info_head(u"")
		if not fav:
			return [{"ban": ban, "bg": ("m", "k"), "head": head, "lines": [self.text(u""), self.text(T("noFav"), "y"), self.text(T("noFav2"), "c")]}]
		lgs = self.fav_leagues()
		lines = []
		seen = set()
		evs = []
		for lg in lgs:
			for e in lg.all_events:
				if e["id"] in seen:
					continue
				if is_fav_first(e["h"]) or is_fav_first(e["a"]):
					seen.add(e["id"])
					evs.append((e, lg))
			for _n, rows in lg.tables:
				for r in rows:
					if is_fav_first(r["tm"]):
						txt = u"%s %d · %d %s · %d %s" % (T("place"), r["pos"], r["p"], T("sp"), r["pts"], T("pts"))
						lines.append((None, [seg(1, C - 30, fit(lg.name(lang) + ((u" · " + _n) if _n else u""), C - 31), "c"), seg(C - 29, 29, txt, "y", al="r")]))
		if not evs and any(lg.loading or not lg.t_load for lg in lgs):
			return [{"ban": ban, "bg": ("m", "k"), "head": head, "lines": [self.text(u""), self.text(T("loading"), "y")]}]
		now = time.time()
		live = [x for x in evs if x[0]["state"] in ("in", "ht")]
		past = sorted([x for x in evs if x[0]["state"] in ("post", "pp") and x[0]["ts"] <= now], key=lambda x: x[0]["ts"])[-5:]
		nxt = sorted([x for x in evs if x[0]["state"] == "pre" or (x[0]["state"] == "pp" and x[0]["ts"] > now)], key=lambda x: x[0]["ts"])[:5]
		if live:
			lines.append(self.text(u""))
			lines.append(self.text(u"● " + self.up(T("live")), "g"))
			lines += [self.fav_row(e, lg) for e, lg in live]
		lines.append(self.text(u""))
		lines.append(self.text(self.up(T("last")), "c"))
		lines += [self.zebra(self.fav_row(e, lg), i) for i, (e, lg) in enumerate(past)] or [self.text(u"  –", "d")]
		lines.append(self.text(u""))
		lines.append(self.text(self.up(T("next")), "c"))
		lines += [self.zebra(self.fav_row(e, lg), i) for i, (e, lg) in enumerate(nxt)] or [self.text(u"  –", "d")]
		return [{"ban": ban, "bg": ("m", "k"), "head": head, "lines": ch} for ch in self.chunk(lines)]

	# ---------- Nations League ----------
	def nl_subpages(self):
		lang = cfg("lang")
		subs = []
		grs = [lg for lg in NAT.groups if not (lg.error and not lg.all_events)]
		if self.nl_pick and grs and all(lg.t_load or lg.error for lg in grs):
			self.nl_pick = False
			for i, lg in enumerate(grs):
				if any(r["tm"] == u"Germany" for _n, rows in lg.tables for r in rows):
					self.sub = i
		for lg in grs:
			title = self.up(lg.name(lang))
			if lg.error and not lg.all_events:
				continue  # Gruppe gibt es in dieser Saison nicht
			lines = []
			if not lg.all_events and not lg.tables:
				lines = [self.text(u""), self.text(T("loading"), "y")]
			else:
				done = [e for e in lg.all_events if e["state"] in ("post", "in", "ht")]
				last_r = max([e["round"] for e in done if e["round"]] or [0])
				last = [e for e in lg.all_events if e["round"] == last_r and e["state"] != "pre"] if last_r else []
				nxt = [e for e in lg.all_events if e["state"] == "pre"]
				next_r = min([e["round"] for e in nxt if e["round"]] or [0])
				nxt = [e for e in nxt if e["round"] == next_r] if next_r else nxt[:2]
				if last:
					lines.append(self.text(self.up(T("md") % last_r), "c"))
					lines += [self.zebra(self.res_row(e), i) for i, e in enumerate(sorted(last, key=lambda x: (x["ts"], x["h"])))]
					lines.append(self.text(u""))
				if lg.tables:
					lines.append(self.table_head())
					lines += self.table_lines(lg, lg.tables[0][1], None)
					lines.append(self.text(u""))
				if nxt:
					lines.append(self.text(self.up(T("next")) + ((u" · " + T("md") % next_r) if next_r else u""), "c"))
					lines += [self.zebra(self.fav_row(e, lg), i) for i, e in enumerate(sorted(nxt, key=lambda x: (x["ts"], x["h"])))]
			subs.append({"ban": (title, u""), "bg": ("c", "k"), "head": self.info_head(T("nlHint")), "lines": lines[:20]})
		if not subs:
			msg = [self.text(u""), self.text(T("loading"), "y")]
			if NAT.error and not NAT.loading:
				msg = [self.text(u""), self.text(T("noData"), "r"), self.text(fit(NAT.error, self.cols), "d")]
			subs = [{"ban": (self.up(NAT.title(lang)), u""), "bg": ("c", "k"), "head": self.text(u""), "lines": msg}]
		return subs

	# ---------- Heute ----------
	def day_subpages(self):
		lang = cfg("lang")
		ymd = self.day_key()
		t0 = time.time() + self.day_off * 86400
		name = {0: T("today"), -1: T("yesterday"), 1: T("tomorrow")}.get(self.day_off)
		title = self.up(name + u" · " + self.day_label(t0)) if name else self.up(self.day_label(t0))
		d = STORE.days.get(ymd) or {}
		head = self.info_head(T("dayHint"))
		if "list" not in d:
			if d.get("error"):
				lines = [self.text(u""), self.text(T("noData"), "r"), self.text(T("noData2"), "c"), self.text(u""), self.text(fit(d["error"], self.cols), "d")]
			else:
				lines = [self.text(u""), self.text(T("loading"), "y")]
			return [{"ban": (title, u""), "bg": ("b", "w"), "head": head, "lines": lines}]
		blocks = []
		for lg, evs in d["list"]:
			live = {}
			for e in evs:
				live[e["id"]] = STORE.live.get(e["id"], e)
			bl = [self.text((lg.tag + u" " if lg.tag else u"") + lg.name(lang) + u"   (%d)" % lg.page, "y")]
			bl += [self.zebra(self.res_row(live[e["id"]]), i) for i, e in enumerate(evs)]
			blocks.append(bl)
		if not blocks:
			blocks = [[self.text(u""), self.text(T("noMatches"), "c")]]
		return [{"ban": (title, u""), "bg": ("b", "w"), "head": head, "lines": ch} for ch in self.chunk_blocks(blocks)]

	# ---------- Ranglisten ----------
	def rank_subpages(self):
		C = self.cols
		lang = cfg("lang")
		rk = ranking_by_page(self.page)
		title = self.up({"fifa": T("rkFifa"), "uefa": T("rkUefa"), "club": T("rkClub")}[rk.kind])
		ban = (title, u"")
		hd = (None, [seg(0, 4, T("pl"), "c", al="r"), seg(6, C - 30, T("club") if rk.kind == "club" else T("nation"), "c"),
			seg(C - 23, 10, T("points"), "c", al="r"), seg(C - 11, 10, (u"+/-" if rk.kind == "fifa" else (T("season") if rk.kind == "uefa" else T("nation"))), "c", al="r")])
		if not rk.rows:
			if rk.error:
				lines = [self.text(u""), self.text(T("noData"), "r"), self.text(fit(rk.error, C), "d")]
			else:
				lines = [self.text(u""), self.text(T("loading"), "y")]
			return [{"ban": ban, "bg": ("b", "w"), "head": hd, "lines": lines}]
		lines = []
		for i, r in enumerate(rk.rows[:80 if rk.kind == "club" else 60]):
			mine = r["code"] in ("GER", "TUR") if rk.kind != "club" else is_fav(r["name"])
			s = [seg(0, 4, u"%d." % r["pos"], "w", al="r"), seg(6, C - 30, fit(dn(r["name"]), C - 31), "w"),
				seg(C - 23, 10, (u"%.2f" % r["pts"]) if rk.kind == "fifa" else (u"%.3f" % r["pts"]), "y", al="r")]
			if rk.kind == "fifa":
				dlt = (r["prev"] - r["pos"]) if r["prev"] else 0
				s.append(seg(C - 11, 10, (u"▲%d" % dlt) if dlt > 0 else ((u"▼%d" % -dlt) if dlt < 0 else u"="), "g" if dlt > 0 else ("r" if dlt < 0 else "d"), al="r"))
			elif rk.kind == "uefa":
				s.append(seg(C - 11, 10, (u"%.3f" % r["season"]) if r.get("season") is not None else u"", "w", al="r"))
			else:
				s.append(seg(C - 11, 10, r["code"], "w" if r["code"] not in ("GER", "TUR") else "y", al="r"))
			if rk.kind != "club" and r["code"] in ("GER", "TUR"):
				mine = True
			row = (COL["fav"] if mine else None, s)
			lines.append(self.zebra(row, i))
		subs = []
		for ch in self.chunk(lines):
			subs.append({"ban": (title, T("asOf") + u" " + rk.date if rk.date else u""), "bg": ("b", "w"), "head": hd, "lines": ch})
		return subs

	def news_subpages(self):
		import textwrap
		C = self.cols
		fd = feed_by_page(self.page)
		title = tr_upper(T("cNEWS") + u" · " + fd.name)
		lt = time.localtime(fd.t_load or time.time())
		head = (None, [seg(0, C - 18, fd.source, "c"), seg(C - 17, 17, T("stand") + u" " + two(lt.tm_hour) + u":" + two(lt.tm_min), "c", al="r")])
		ban = {"bg": ("m", "k"), "head": head}
		if not fd.items:
			if fd.loading or not fd.t_load:
				lines = [self.text(u""), self.text(T("loading"), "y")]
			else:
				lines = [self.text(u""), self.text(T("noData"), "r"), self.text(T("noData2"), "c"),
					self.text(u""), self.text(fit(fd.error or u"", C), "d")]
			return [dict(ban, ban=(title, u""), lines=lines)]
		n = len(fd.items)
		if self.news_open is not None:
			it = fd.items[self.news_open]
			lines = [self.text(u"")]
			for ln in textwrap.wrap(it["title"], C - 2)[:4]:
				lines.append(self.text(u" " + ln, "y"))
			if it["ts"]:
				lt = time.localtime(it["ts"])
				lines.append(self.text(u" " + self.day_label(it["ts"]) + u" " + two(lt.tm_hour) + u":" + two(lt.tm_min), "d"))
			lines.append(self.text(u""))
			room = 19 - len(lines)
			body = textwrap.wrap(it["desc"] or u"", C - 2)
			if len(body) > room:
				body = body[:room]
				body[-1] = body[-1][:C - 4] + u" …"
			for ln in body:
				lines.append(self.text(u" " + ln, "w"))
			while len(lines) < 19:
				lines.append(self.text(u""))
			lines.append(self.text(T("articleHint"), "c"))
			return [dict(ban, ban=(title, u"%d/%d" % (self.news_open + 1, n)), lines=lines)]
		per = 18
		self.sub = self.news_sel // per
		subs = []
		for start in range(0, n, per):
			lines = []
			for i in range(start, min(n, start + per)):
				it = fd.items[i]
				sel = i == self.news_sel
				tm = u""
				if it["ts"]:
					lt = time.localtime(it["ts"])
					tm = two(lt.tm_hour) + u":" + two(lt.tm_min)
				lines.append((COL["sel"] if sel else None, [seg(0, 5, tm, "y" if sel else "d"),
					seg(6, C - 6, fit(it["title"], C - 6), "y" if sel else "w")]))
			while len(lines) < 19:
				lines.append(self.text(u""))
			lines.append(self.text(T("newsHint"), "c"))
			subs.append(dict(ban, ban=(title, u""), lines=lines))
		return subs

	# ---------- Zeichnen ----------
	def build_rows(self):
		C = self.cols
		subs = self.subpages()
		if self.sub >= len(subs):
			self.sub = 0
		sp = subs[self.sub]
		now = time.time()
		lt = time.localtime(now)
		rows = []
		pg = (u"P" + (self.entry + u"---")[:3]) if self.entry else (u"P%d" % self.page)
		date = u"%s %s.%s.  %s:%s:%s" % (T("days")[lt.tm_wday], two(lt.tm_mday), two(lt.tm_mon), two(lt.tm_hour), two(lt.tm_min), two(lt.tm_sec))
		h = [seg(0, 5, pg, "y" if self.entry else "w", blink=bool(self.entry)), seg(6, 9, u"SkorText", "y")]
		if self.page != 100:
			h.append(seg(17, C - 40, T("home"), "c"))
		h.append(seg(C - 22, 22, date, "y", al="r"))
		rows.append((None, h))
		goal = None
		for ts, e in reversed(STORE.goals):
			if now - ts < 8 and ts > self.opened_at:
				goal = e
				break
		if now < self.msg_until:
			rows.append((COL["w"], [seg(1, C - 2, self.msg, "k")]))
		elif goal:
			lg = STORE.by_ut.get(goal["ut"])
			m = goal["min"] + (u"'" if goal["min"] and goal["min"][0].isdigit() else u"")
			txt = u"%s  %s  %s %d:%d %s" % (T("goal"), m, goal["h"], goal["hs"] or 0, goal["as"] or 0, goal["a"])
			rows.append((COL["y"] if self.blink_on else COL["k"], [seg(1, C - 22, fit(txt, C - 22), "k" if self.blink_on else "y"),
				seg(C - 21, 20, fit(lg.name(cfg("lang")) if lg else u"", 20), "k" if self.blink_on else "y", al="r")]))
		else:
			bg, fg = sp["bg"]
			if modern():
				fg = bg  # Landesfarbe als Schriftfarbe auf dunkler Karte
				bg = "card"
			right = sp["ban"][1] + ((u"  %d/%d" % (self.sub + 1, len(subs))) if len(subs) > 1 else u"")
			rows.append((COL[bg], [seg(1, C - 2 - len(right) - 1, fit(sp["ban"][0], C - 3 - len(right)), fg), seg(C - 1 - len(right), len(right), right, fg, al="r")]))
		rows.append(sp["head"])
		body = list(sp["lines"][:20])
		while len(body) < 20:
			body.append((None, []))
		rows += body
		F = T("fast")
		q = C // 4
		rows.append((None, [seg(0, q - 1, F[0], "w", "r", "c"), seg(q, q - 1, F[1], "k", "g", "c"),
			seg(2 * q, q - 1, F[2], "k", "y", "c"), seg(3 * q, C - 3 * q, F[3], "w", "b", "c")]))
		return rows

	def draw(self):
		if self.closed:
			return
		try:
			rows = self.build_rows()
		except Exception as e:
			log("Seite %d: %r" % (self.page, e))
			rows = [(None, [seg(0, self.cols, u"SkorText: " + U(str(e)), "r")])]
		pbg = PAGE_BG.get(cfg("bg"), 0)
		if self.mix:
			pbg = PAGE_BG["black"] if cfg("bg") == "mix" else PAGE_BG["mix"]
		mod = modern()
		if mod and not self.mix and cfg("bg") != "mix":
			pbg = COL["bg"]
		entries = []
		for i, (rbg, segs) in enumerate(rows):
			bgc = rbg if rbg is not None else pbg
			rounded = False
			if mod:
				if rbg is None and i == 0:
					bgc = COL["hdr"] if pbg == COL["bg"] else pbg
				elif rbg is None and 3 <= i <= 22 and any(sg[2] for sg in segs) and pbg == COL["bg"]:
					bgc = COL["zebra1"] if i % 2 else COL["zebra2"]
					rounded = True
				elif rbg is not None:
					rounded = True
			bkw = dict(pos=(0, 0), size=(self.pw, self.rowH), font=0, text="", backcolor=bgc, backcolor_sel=bgc)
			if rounded:
				bkw["corner_radius"] = max(3, self.rowH // 4)
			try:
				first = MultiContentEntryText(**bkw)
			except TypeError:  # aelteres Enigma ohne runde Ecken
				bkw.pop("corner_radius", None)
				first = MultiContentEntryText(**bkw)
			ent = [None, first]
			if mod and rbg is not None and rbg == COL["sel"]:
				ent.append(MultiContentEntryText(pos=(0, 0), size=(max(4, int(self.cw * 0.45)), self.rowH), font=0, text="",
					backcolor=COL["y"], backcolor_sel=COL["y"]))
			for col, width, txt, fg, bg, al, blink in segs:
				if blink and not self.blink_on:
					txt = u""
				x = int(col * self.cw)
				w = int(width * self.cw) + 2
				if x >= self.pw:
					continue
				w = min(w, self.pw - x)
				kw = dict(pos=(x, 0), size=(w, self.rowH), font=0, flags=ALIGN[al] | RT_VALIGN_CENTER,
					text=E(txt), color=COL[fg], color_sel=COL[fg])
				if bg:
					kw["backcolor"] = COL[bg]
					kw["backcolor_sel"] = COL[bg]
				ent.append(MultiContentEntryText(**kw))
			entries.append(ent)
		self["tt"].setList(entries)
		pass


# =====================================================================
class SkorGoalPopup(Screen):
	def __init__(self, session):
		dw = getDesktop(0).size().width()
		dh = getDesktop(0).size().height()
		fs = int(dh / 30)
		w, h = int(dw * 0.56), int(fs * 2.9)
		x, y = int(dw * 0.04), dh - h - int(dh * 0.07)
		self.skin = ('<screen name="SkorGoalPopup" position="%d,%d" size="%d,%d" flags="wfNoBorder" backgroundColor="#000000">'
			'<eLabel position="0,0" size="%d,%d" backgroundColor="#ffee33" />'
			'<widget name="main" position="%d,%d" size="%d,%d" font="SkorMono;%d" foregroundColor="#f4f4f4" backgroundColor="#000000" transparent="1" valign="center" />'
			'<widget name="sub" position="%d,%d" size="%d,%d" font="SkorMono;%d" foregroundColor="#33f0f0" backgroundColor="#000000" transparent="1" valign="center" />'
			'</screen>') % (x, y, w, h, int(fs * 0.45), h,
			int(fs * 0.9), int(fs * 0.2), w - fs, int(fs * 1.4), fs,
			int(fs * 0.9), int(fs * 1.65), w - fs, int(fs * 1.05), int(fs * 0.75))
		Screen.__init__(self, session)
		self["main"] = Label("")
		self["sub"] = Label("")

	def set(self, main, sub):
		self["main"].setText(E(main))
		self["sub"].setText(E(sub))


class Background(object):
	"""Starttaste abfangen + Tor-Ticker im Fernsehbild."""
	KEYS = {"text_long": 388, "help": 138, "blue_long": 401}

	def __init__(self, session):
		self.session = session
		self._conns = []
		self.capturing = None
		self.long_timer = mk_timer(self, self.long_fired)
		self.poll_timer = mk_timer(self, self.poll)
		self.hide_timer = mk_timer(self, self.hide_popup)
		self.popup = None
		self.seen_until = time.time()
		self.busy = False
		self.fupa_scores = {}
		self.keylog = 0
		try:
			eActionMap.getInstance().bindAction("", -0x7FFFFFFF, self.key_handler)
			log("Hintergrund aktiv (Version %s), Starttaste: %s" % (VERSION, cfg("startkey")))
		except Exception as e:
			log("Tastenhaken fehlgeschlagen: %r" % e)
		self.poll_timer.start(15000, True)

	# ---- Starttaste ----
	def on_tv(self):
		try:
			from Screens.InfoBar import InfoBar
			return InfoBar.instance is not None and self.session.current_dialog is InfoBar.instance
		except Exception:
			return False

	def key_handler(self, key, flag):
		try:
			mode = cfg("startkey")
			if self.keylog < 60 and flag in (0, 3):
				self.keylog += 1
				log("Taste %d Flag %d TV=%s" % (key, flag, self.on_tv()))
			if self.capturing is not None:
				if key == self.capturing:
					if flag == 1:
						if self.long_timer.isActive():
							self.long_timer.stop()
							self.short_press(self.capturing)
						self.capturing = None
					return 1
				return 0
			want = self.KEYS.get(mode)
			if want is None or key != want or flag != 0 or not self.on_tv():
				return 0
			self.capturing = key
			if mode == "help":
				self.open_plugin()
			else:
				self.long_timer.start(700, True)
			return 1
		except Exception as e:
			log("Tastenabfrage: %r" % e)
			self.capturing = None
			return 0

	def long_fired(self):
		self.open_plugin()

	def short_press(self, key):
		try:
			from Screens.InfoBar import InfoBar
			ib = InfoBar.instance
			if key == 388 and hasattr(ib, "startTeletext"):
				ib.startTeletext()
			elif key == 401 and hasattr(ib, "showExtensionSelection"):
				ib.showExtensionSelection()
		except Exception:
			pass

	def open_plugin(self):
		if SkorText.instance is None:
			self.hide_popup()
			self.session.open(SkorText)

	# ---- Tor-Ticker ----
	def poll(self):
		ref = int(cfg("refresh"))
		if cfg("alarm") == "off" or SkorText.instance is not None or self.busy:
			self.seen_until = time.time()
			self.poll_timer.start(ref * 1000, True)
			return
		self.busy = True
		d = threads.deferToThread(STORE.fetch_live)

		def ok(new):
			self.busy = False
			try:
				STORE.apply_live(new)
				self.check_goals()
			except Exception as e:
				log("Tor-Ticker: %r" % e)
			self.poll_fupa()
			self.poll_timer.start(ref * 1000, True)

		def err(f):
			self.busy = False
			log("Tor-Ticker Live-Daten: %r" % f.value)
			self.poll_timer.start(ref * 1000, True)
		d.addCallbacks(ok, err)

	def poll_fupa(self):
		"""Amateurliga des Lieblingsvereins (FuPa) - nur tagsueber und nur wenn gewuenscht."""
		if cfg("alarm") not in ("fav", "all") or not cfg("fav"):
			return
		lt = time.localtime()
		if not 10 <= lt.tm_hour < 22:
			return
		lgs = [STORE.league_by_page(pg) for pg in FAV_LEAGUES.get(cfg("fav"), [])]
		lgs = [l for l in lgs if isinstance(l, FupaLeague)]
		if not lgs:
			return
		lg = lgs[0]
		d = threads.deferToThread(fupa_today, lg)

		def ok(evs):
			now = time.time()
			for e in evs:
				if not (is_fav(e["h"]) or is_fav(e["a"])) or e["hs"] is None:
					continue
				old = self.fupa_scores.get(e["id"])
				self.fupa_scores[e["id"]] = (e["hs"], e["as"])
				if old is not None and (e["hs"] + e["as"]) > (old[0] + old[1]):
					e["goal_at"] = now
					e["goal_by"] = "h" if e["hs"] > old[0] else "a"
					STORE.goals.append((now, e))
			self.check_goals()

		def err(f):
			log("Tor-Ticker FuPa: %r" % f.value)
		d.addCallbacks(ok, err)

	def wanted(self, e):
		a = cfg("alarm")
		if a == "all":
			return True
		if a == "top":
			return e["ut"] in ("germany/bundesliga", "turkey/super-lig")
		if a == "fav":
			return is_fav(e["h"]) or is_fav(e["a"])
		return False

	def check_goals(self):
		new = [g for g in STORE.goals if g[0] > self.seen_until]
		self.seen_until = time.time()
		new = [g for g in new if self.wanted(g[1])]
		if not new or not self.on_tv():
			return
		e = new[-1][1]
		lg = STORE.by_ut.get(e["ut"])
		m = e["min"] + (u"'" if e["min"] and e["min"][0].isdigit() else u"")
		main = u"%s %s  %s %d:%d %s" % (TXT[cfg("lang")]["goal"], m, e["h"], e["hs"] or 0, e["as"] or 0, e["a"])
		sub = (lg.name(cfg("lang")) if lg else u"") + u" · " + (u"TEXT uzun → Detay" if cfg("lang") == "tr" else u"TEXT lang → Details")
		if self.popup is None:
			self.popup = self.session.instantiateDialog(SkorGoalPopup)
		self.popup.set(main, sub)
		self.popup.show()
		self.hide_timer.start(8000, True)

	def hide_popup(self):
		if self.popup is not None:
			self.popup.hide()


BG = None


def main(session, **kwargs):
	session.open(SkorText)


def sessionstart(reason, session=None, **kwargs):
	global BG
	if reason == 0 and session is not None and BG is None:
		BG = Background(session)


def Plugins(**kwargs):
	desc = "Live-Ergebnisse & Tabellen (DE / TR / Europa)"
	return [
		PluginDescriptor(name="SkorText", description=desc, where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main),
		PluginDescriptor(name="SkorText - Live-Ergebnisse", description=desc, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main),
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart),
	]
