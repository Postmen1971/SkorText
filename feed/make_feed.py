# -*- coding: utf-8 -*-
"""Erzeugt liveonsat.json (Spiele von heute mit europäischen Sendern) für Browser-Seiten wie das Galvanik-Tool.
Läuft alle 30 Minuten als GitHub-Action und landet im Zweig „feed“:
https://raw.githubusercontent.com/Postmen1971/SkorText/feed/liveonsat.json
"""
import datetime
import json
import sys

import liveonsat

fx = liveonsat.today()
out = []
for f in fx:
    ch = liveonsat.european_sorted(f["channels"])
    if ch:
        out.append({"home": f["home"], "away": f["away"], "channels": ch[:25]})
print("Spiele mit Sendern:", len(out))
if not out:
    sys.exit("liveonsat: nichts erkannt – alte Datei bleibt stehen")
data = {"updated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "source": "liveonsat.com", "fixtures": out}
with open(sys.argv[1] if len(sys.argv) > 1 else "liveonsat.json", "w") as fh:
    json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
