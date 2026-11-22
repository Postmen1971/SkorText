#!/usr/bin/env python3
"""Gemeinsame Sprachdatei der Android-App (www/sprachen.js) als sprachen.json fürs GigaBlue-Plugin ablegen.

Wird beim Bauen aufgerufen (build.yml); nach Änderungen an sprachen.js auch von Hand: python3 tools/sprachen_json.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "app", "src", "main", "assets", "www", "sprachen.js")
DST = os.path.join(ROOT, "enigma2", "usr", "lib", "enigma2", "python", "Plugins", "Extensions", "SkorText", "sprachen.json")

text = open(SRC, encoding="utf-8").read()
start = text.index("=", text.index("var SKOR_SPRACHEN")) + 1
end = text.rindex("}") + 1
data = json.loads(text[start:end])
# Plugin braucht die Touch-/App-Texte nicht – kleiner halten
for l in data.get("order", []):
    txt = data[l].get("txt", {})
    for k in [k for k in txt if k.startswith("t_")]:
        del txt[k]
with open(DST, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
print("sprachen.json: %d Sprachen, %d Bytes" % (len(data.get("order", [])), os.path.getsize(DST)))
sys.exit(0)
