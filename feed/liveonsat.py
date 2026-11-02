# -*- coding: utf-8 -*-
"""
liveonsat.py – Sender je Fußballspiel von liveonsat.com auslesen
(gleiche Logik wie in Aze-IPTV-Player, data/LiveOnSat.kt). Läuft mit Python 3, ohne Zusatzpakete
(auch auf Enigma2 / GigaBlue).

Ablauf:
  1. Seite „2day.php“ laden (wie ein Browser, mit Datum von heute)
  2. HTML in Textzeilen zerlegen
  3. Zeile „Mannschaft A v Mannschaft B“  → neues Spiel
     folgende kurze Zeilen                 → Sender dieses Spiels
     (Uhrzeiten, Satelliten-/Frequenz-/Verschlüsselungs-Angaben werden aussortiert)

Benutzung:
    from liveonsat import today, for_match, european_sorted
    spiele = today()                      # [{"home":..., "away":..., "channels":[...]}, ...]
    sender = for_match("Galatasaray", "Fenerbahce", spiele)
    print(european_sorted(sender))

Bitte schonend abrufen: Ergebnis zwischenspeichern, höchstens alle 15–30 Minuten neu laden.
"""
import datetime
import html as _html
import re
import unicodedata
import urllib.request

URLS = ["https://liveonsat.com/2day.php", "https://www.liveonsat.com/2day.php"]
UA = ("Mozilla/5.0 (Linux; Android 11; SHIELD Android TV) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def _fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(12 * 1024 * 1024).decode("utf-8", "replace")


# ---------- Zerlegen ----------
_SCRIPTS = re.compile(r"(?is)<(script|style)[^>]*>.*?</\1>")
# versteckte Tooltips (Satellit, Frequenz …) entfernen
_HANDLER_ATTRS = re.compile(r"""(?is)\s(on\w+|title|data-[\w-]+)\s*=\s*("[^"]*"|'[^']*')""")
_BLOCK_TAGS = re.compile(r"(?i)<\s*(br|/div|/p|/tr|/td|/li|/h\d|/a|/span|/table)[^>]*>")
_ANY_TAG = re.compile(r"<[^>]+>")
_MATCH_LINE = re.compile(r"^(.{2,60}?)\s+v\.?s?\.?\s+(.{2,60})$", re.I)
_TIME_LINE = re.compile(r"(?i)^(st|ko|kick[- ]?off)?\s*:?\s*\d{1,2}[:.]\d{2}.*$")
_HEADER_WORDS = re.compile(r"(?i)\b(week|round|matchday|spieltag|group|stage|qualif|play-?off|final|semi|quarter)\b")
_SAT_NAMES = re.compile(
    r"(?i)^(thor|astra|hot ?bird|eutelsat|t[uü]rksat|badr|nilesat|arabsat|hispasat|amos|express|yamal|yahsat|eshail|es'hail|"
    r"intelsat|hellas ?sat|abs|galaxy|ses|telstar|apstar|asiasat|measat|thaicom|nss|bulgariasat|azerspace|belintersat|kazsat|"
    r"sirius|sky ?brasil|chinasat|optus|\* ?iptv)\b")
_ENCRYPTION = {
    "conax", "irdeto", "nagravision", "nagra", "viaccess", "videoguard", "hd videoguard", "powervu", "biss", "biss-1", "biss-2",
    "free", "fta", "mediaguard", "cryptoworks", "verimatrix", "tandberg", "dre-crypt", "drecrypt", "betacrypt", "seca", "hd",
    "satellite", "pos", "freq", "symbol", "encryption", "sat", "frequency", "dvb-s", "dvb-s2", "live", "ku", "c-band",
}
_SAT_POS = re.compile(r"^\d{1,3}([.,]\d)?\s*°?\s*[ewEW]\b")
_TECH_LINE = re.compile(r"^\d[\d\s.,/:-]*([HVLRhvlr]\b.*)?$")
_FREQ = re.compile(r"\d{4,5}\s*[HV]\b")


def _is_channel(line):
    if line.lower() in _ENCRYPTION:
        return False
    if "°" in line or _SAT_POS.search(line) or _TECH_LINE.match(line) or _SAT_NAMES.search(line) or _FREQ.search(line):
        return False
    return any(c.isalpha() for c in line)


def parse(page):
    text = _SCRIPTS.sub(" ", page)
    text = _HANDLER_ATTRS.sub(" ", text)
    text = _BLOCK_TAGS.sub("\n", text)
    text = _ANY_TAG.sub(" ", text)
    text = _html.unescape(text)
    lines = [re.sub(r"\s+", " ", l).strip() for l in text.splitlines()]
    lines = [l for l in lines if l]

    out, home, away, chans = [], None, None, []

    def flush():
        if home and away and chans:
            out.append({"home": home, "away": away, "channels": list(dict.fromkeys(chans))})

    for l in lines:
        m = _MATCH_LINE.fullmatch(l)
        if m and "http" not in l:
            flush()
            chans = []
            home, away = m.group(1).strip(), m.group(2).strip()
            continue
        if home is None:
            continue
        if _TIME_LINE.fullmatch(l) or len(l) > 50 or len(l) < 2 or _HEADER_WORDS.search(l):
            continue
        if _is_channel(l) and len(chans) < 400:
            chans.append(l)
    flush()
    return out


# ---------- Laden ----------
def today():
    """Spiele mit Sendern von heute. liveonsat rechnet in britischer Zeit – darum zusätzlich mit heutigem Datum laden."""
    d = datetime.date.today()
    dated = "?start_dd={0}&start_mm={1}&start_yyyy={2}&end_dd={0}&end_mm={1}&end_yyyy={2}".format(d.day, d.month, d.year)
    result, pages = {}, 0
    for u in [URLS[0] + dated, URLS[0], URLS[1] + dated, URLS[1]]:
        if pages >= 2:
            break
        try:
            page = _fetch(u)
        except Exception:
            continue
        pages += 1
        for f in parse(page):
            result.setdefault(norm(f["home"]) + "|" + norm(f["away"]), f)
    return list(result.values())


# ---------- Spiel finden ----------
def norm(s):
    s = s.lower().replace("ı", "i").replace("ß", "ss")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


_NOISE = {"fc", "sc", "sk", "fk", "cf", "ac", "as", "sv", "vfb", "vfl", "tsg", "afc", "club", "de", "the", "1"}


def tokens(team):
    return [t for t in re.split(r"[^a-z0-9]+", norm(team)) if len(t) >= 3 and t not in _NOISE]


_YOUTH = re.compile(r"(?i)\b(u-?\d{2}|women|woman|frauen|kadin|ladies|reserves|ii)\b|\(w\)")


def for_match(home, away, fixtures):
    """Sender für ein Spiel (Zuordnung über die Mannschaftsnamen, Jugend-/Frauenspiele nicht verwechseln)."""
    t1, t2 = tokens(home), tokens(away)
    youth = bool(_YOUTH.search(home + " " + away))
    for f in fixtures:
        if not youth and _YOUTH.search(f["home"] + " " + f["away"]):
            continue
        h, a = norm(f["home"]), norm(f["away"])
        if (any(t in h for t in t1) and any(t in a for t in t2)) or (any(t in a for t in t1) and any(t in h for t in t2)):
            return f["channels"]
    return []


_NON_EUROPE = re.compile(
    r"(?i)\b(usa|us|canada|mena|arabia|arab|africa|asia|japan|india|malaysia|indonesia|thailand|vietnam|philippines|china|korea|"
    r"brasil|brazil|argentina|mexico|latam|latin|caribbean|persiana|iran|astro|azam|supersport|kenya|nigeria|ghana|australia|"
    r"new zealand|nz|singapore|hong kong|taiwan|peacock|fubo|espn\+|paramount\+|sling|kayo|optus|stan sport|bangladesh|pakistan|"
    r"israel|iraq|kurdistan|afghanistan|ethiopia|tanzania|uganda|zambia|mongolia|cambodia|myanmar|nepal|sri lanka|"
    r"chile|colombia|peru|ecuador|venezuela|uruguay|paraguay|bolivia|costa rica|honduras|guatemala|panama|el salvador)\b")
_PRIORITY = ("deutsch", "germany", "german", "türkiye", "turkiye", "turkey", "turkish", "austria", "österreich", "schweiz", "swiss")


def european_sorted(channels):
    """Nur europäische Sender, deutsche/türkische zuerst."""
    eu = [c for c in channels if not _NON_EUROPE.search(c)]
    return sorted(eu, key=lambda c: 0 if any(p in c.lower() for p in _PRIORITY) else 1)


if __name__ == "__main__":
    for f in today()[:20]:
        print(f["home"], "–", f["away"], ":", ", ".join(european_sorted(f["channels"])[:6]))
