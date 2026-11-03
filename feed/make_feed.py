# -*- coding: utf-8 -*-
"""Erzeugt liveonsat.json (Spiele der nächsten 7 Tage mit europäischen Sendern) für Browser-Seiten wie das
Galvanik-Tool und die SkorText-App. Läuft alle 30 Minuten als GitHub-Action und landet im Zweig „feed“:
https://raw.githubusercontent.com/Postmen1971/SkorText/feed/liveonsat.json

Schonend: heute + morgen bei jedem Lauf, die Tage danach nur alle 3 Stunden (sonst bleiben die alten Einträge).
Aufruf: make_feed.py NEUE_DATEI [ALTE_DATEI]
"""
import datetime
import json
import os
import sys

import liveonsat

DAYS = 7


def fetch_day(d):
    q = "?start_dd={0}&start_mm={1}&start_yyyy={2}&end_dd={0}&end_mm={1}&end_yyyy={2}".format(d.day, d.month, d.year)
    for base in liveonsat.URLS:
        try:
            return liveonsat.parse(liveonsat._fetch(base + q))
        except Exception as e:
            print("Fehler", d, base, e)
    return None


out_path = sys.argv[1]
old_path = sys.argv[2] if len(sys.argv) > 2 else ""
now = datetime.datetime.utcnow()
today = now.date()

by_date = {}
if old_path and os.path.exists(old_path):
    try:
        for f in json.load(open(old_path)).get("fixtures", []):
            if f.get("date") and f["date"] >= today.isoformat():
                by_date.setdefault(f["date"], []).append(f)
    except Exception as e:
        print("alte Datei unlesbar:", e)

full = not by_date or (now.hour % 3 == 0 and now.minute < 30)
for i in range(DAYS if full else 2):
    d = today + datetime.timedelta(days=i)
    fx = fetch_day(d)
    if not fx:
        continue  # nicht erreichbar: alte Einträge dieses Tages behalten
    day = []
    for f in fx:
        ch = liveonsat.european_sorted(f["channels"])
        if ch:
            day.append({"date": d.isoformat(), "home": f["home"], "away": f["away"], "channels": ch[:80]})
    by_date[d.isoformat()] = day
    print(d, "Spiele mit Sendern:", len(day))

fixtures = [f for k in sorted(by_date) for f in by_date[k]]
if not fixtures:
    sys.exit("liveonsat: nichts erkannt – alte Datei bleibt stehen")
data = {"updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "source": "liveonsat.com", "fixtures": fixtures}
with open(out_path, "w") as fh:
    json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
