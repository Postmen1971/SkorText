# SkorText – Übergabe für einen neuen Chat

Stand: 22.11.2026 · aktuelle Version **3.18** (Android-App und GigaBlue-Plugin haben dieselbe Nummer)

## 1. Was ist SkorText?

Fußball-Ergebnisse, Tabellen und Nachrichten im Videotext-Stil (Seitennummern wie im Teletext), in zwei Ausführungen:

| | GigaBlue (Enigma2-Plugin) | Android-App |
|---|---|---|
| Gerät | GigaBlue bei den Eltern, Image Team Blue 7.3/7.6 (Python 3) | NVIDIA Shield (Fernbedienung) + Android-Tablet (Touch); auch im Aze-IPTV-Player eingebettet |
| Datei | `skortext.ipk` (Paket `enigma2-plugin-extensions-skortext`) | `skortext.apk` (`de.skortext.tv`) |
| Start | Plugin-Menü oder TEXT-Taste lang (nach GUI-Neustart) | App-Symbol |
| Stil | Videotext klassisch / modern, Zeilen abwechselnd weiß/cyan | gleich |

## 2. Wo liegt alles?

- **GitHub:** https://github.com/Postmen1971/SkorText (öffentlich)
  - `enigma2/usr/lib/enigma2/python/Plugins/Extensions/SkorText/` – Plugin: `plugin.py` (Oberfläche, Tasten, Seiten), `data.py` (alle Datenquellen), `texts.py` (Texte DE/TR, Einstellungen, Nationen), `news.py` (RSS-Nachrichten), `liveonsat.py` (TV-Sender je Spiel), `fonts/`
  - `enigma2/CONTROL/` – `control` + `postinst` für das ipk
  - `app/src/main/assets/www/app.js` – die komplette Android-Oberfläche (JavaScript, gleiche Logik wie das Plugin)
  - `app/src/main/java/de/skortext/tv/MainActivity.java` – Android-Hülle: Fernbedienung, Datenabruf ohne Browser-Sperren (`SkorBridge.get`), Einstellungen, Update-Installation, Schwarzbild-Schutz
  - `app/src/main/java/de/skortext/tv/ApkProvider.java` – stellt die geladene Update-APK dem Installer bereit
  - `app/skortext.keystore` – **Signaturschlüssel der App** (siehe Abschnitt 8)
  - `feed/make_feed.py`, `feed/liveonsat.py` – erzeugen den TV-Sender-Feed
  - `samples/` – gespeicherte Beispielantworten der Quellen (für Tests)
- **Workflows** (`.github/workflows/`):
  - `build.yml` – bei **jedem Push auf main**: baut APK + ipk, prüft gleiche Versionsnummer, erstellt Release `v1.0.N` mit `skortext.apk`, `skortext.ipk`, `version.json`
  - `liveonsat-feed.yml` – alle 30 min: Sender je Spiel von liveonsat.com → JSON im Zweig `feed`
  - `probe.yml` – Testlauf („Sofascore-Test“) zum Ausprobieren von Quellen von GitHub aus; schreibt `probe-result.txt` + `samples/`. Den Anfang (requests/H/OUT/print_) beim Umbauen nicht löschen.
- **Downloads (immer neueste Version):**
  - Android: https://github.com/Postmen1971/SkorText/releases/latest/download/skortext.apk
  - Downloader-Code: **5694507** (aftv.news/5694507)
  - GigaBlue: https://github.com/Postmen1971/SkorText/releases/latest/download/skortext.ipk
  - Versionsdatei: …/latest/download/version.json → `{"app": "3.16", "plugin": "3.16"}`

## 2b. Sprachen (seit 3.18)

Deutsch und Türkisch stehen wie bisher direkt in `app.js` (TXT) bzw. `texts.py`. **Englisch, Französisch, Spanisch, Italienisch, Schwedisch, Dänisch, Norwegisch** kommen aus einer gemeinsamen Datei:

- `app/src/main/assets/www/sprachen.js` (`var SKOR_SPRACHEN = {…}` – reines JSON nach dem `=`), von `index.html` vor `app.js` geladen
- GigaBlue: `SkorText/sprachen.json` – wird beim Bauen von `tools/sprachen_json.py` aus der JS-Datei erzeugt (ohne die Touch-Texte `t_…`); nach Änderungen auch von Hand ausführen
- Aufbau je Sprache: `txt` (gleiche Schlüssel wie TXT; `e2_…` = abweichender Text fürs Plugin mit EXIT/MENU-Tasten, `e2_helpRows` = Plugin-Hilfe; `days` ab Montag – die App dreht sie auf Sonntag zuerst), `tx` (Übersetzung nach dem **deutschen Originaltext**: Einstellungen, Runden, Gruppen, Meldungen, Ligennamen), `nations` (nach dem englischen Namen der Datenquellen)
- Rückfall: Sprache → Englisch → Deutsch. Code-Helfer: `tx(de, tr)` / `txIn(lang, de, tr)` in app.js, `tx(de, tr, lang)` / `text_for(lang, key)` in texts.py. Türkische Ligen heißen in den weiteren Sprachen offiziell (Trendyol Süper Lig …), deutsche Ligen wie im Deutschen.
- Nachrichten (600 ff.) bleiben türkisch oder deutsch (Einstellung „Nachrichten“).
- Neue Sprache: in `sprachen.js` unter `order`, `names` und einem eigenen Block ergänzen – sonst nichts.

## 3. Seiten

| Seite | Inhalt |
|---|---|
| 100 | Übersicht (eine Seite; links DE + Weiteres, rechts TR, Europa, Länderspiele, Ranglisten) |
| 110 | Mein Verein |
| 150 | Tor-Ticker (nur GigaBlue) |
| 190 | Bedienung (über Einstellungen erreichbar) |
| 200–295 | Bundesliga, 2. BL, 3. Liga, Regionalligen (SW, West, Bayern, Nord, Nordost), Oberliga BW, Verbandsliga Württemberg (290), DFB-Pokal (295) |
| 300–322 | Süper Lig, Türkiye Kupası (305), 1. Lig, 2. Lig Beyaz (320) / Kırmızı (322) |
| 400–460 | England, Spanien, Italien, Frankreich, Champions League, Europa League, Conference League |
| 470 | Länderspiele Europa – schaltet automatisch zwischen EM-Quali, WM-Quali (UEFA) und Nations League; jede Gruppe eine Unterseite: letzter Spieltag, Tabelle, nächste Spiele |
| 480 / 482 / 484 | FIFA-Weltrangliste, UEFA-Länderkoeffizient, UEFA-Vereinskoeffizient |
| 500 | Live (alle laufenden Spiele) |
| 510 | Heute |
| 520 | Heute im TV – Sender je Spiel (liveonsat), OK klappt alle Sender eines Spiels auf |
| 600–660 | Nachrichten. Türkisch: 600 Manşet (TRT), 610 Güncel, 620 Dünya, 630 Ekonomi, 640 Spor (AA), 650 Kahramanmaraş (haberler.com), 660 Maraş Yerel (Maraş Manşet). Deutsch: 600 Schlagzeilen, 610 Inland, 620 Welt, 630 Wirtschaft (tagesschau), 640 Sport (sportschau), 650 Fußball (kicker) |
| 700–810 | Weitere Ligen (Standard aus): NED, POR, BEL, SCO, AUT, SUI, GRE, ENG Championship, ESP LaLiga 2, ITA Serie B, FRA Ligue 2, DEN |
| 990 | ARD Text – Online-Videotext von ard-text.de (`ardtext.py` / `ardParse` in app.js). Ziffern = ARD-Seite, ▲▼/Rot/Grün blättern, ◄► Unterseiten (`&sub=N`), Gelb/Blau = ARD-Farbtasten, OK neu laden, Tippen auf Seitennummer (Tablet) |
| 900 | Einstellungen: Stil, Sprache, Lieblingsverein, Startseite, Aktualisierung, Unterseiten, Hintergrund, Auto-Update, Nachrichten TR/DE, „Ligen auswählen“ (→ 910), Bedienung (→ 190), Update suchen; unten der Downloader-Code |
| 910 | Ligen-Auswahl: Haken = auf der Übersicht eingeblendet (ausgeblendet = auch nicht in Heute/Live) |

Bedienung: OK schaltet Ergebnis ⇄ Tabelle (keine Torschützen). ▲▼ blättert Spieltage. ◄► wechselt Liga bzw. Gruppe. Zurück zur Übersicht springt an die letzte Position. Kein Frauenfußball, kein Euro→TRY-Kurs.

## 4. Datenquellen (alle ohne API-Schlüssel)

1. **LiveScore** (Hauptquelle; zwei Server prod-public-api / prod-cdn-public-api; bei HTTP 403 5 min Pause)
2. Ersatz, wenn LiveScore gesperrt ist (bei Aziz' Anschluss oft der Fall):
   - **ESPN** – Bundesliga, 2. BL, DFB-Pokal, Süper Lig, ENG/ESP/ITA/FRA, CL/EL/ECL und die 12 weiteren Ligen. Spieltage blättern über den ESPN-Saisonkalender (bei LaLiga fehlen die ersten 2 Spieltage).
   - **FuPa** – 3. Liga, Regionalligen, Oberliga BW, Verbandsliga Württemberg
   - **TFF** (tff.org, HTML, cp1254) – türkische Ligen und Türkiye Kupası
   - **UEFA** (match.uefa.com / standings.uefa.com) – Länderspiele (Nations League = Wettbewerb 2014, WM-Quali = 17; EM-Quali = 3 ist nur geraten)
   - 500/510 fallen auf ESPN/FuPa zurück
3. Ranglisten: FIFA (inside.fifa.com + api.fifa.com), UEFA-Koeffizienten (comp.uefa.com)
4. TV-Sender: liveonsat.com über den eigenen Feed (Zweig `feed`)
5. Nachrichten: RSS (TRT, AA, haberler.com, marasmanset.com, tagesschau, sportschau, kicker)

## 5. Updates

- Beide Apps prüfen beim Start `version.json` (Einstellung „Auto-Update“), manuell über Einstellungen → „Update suchen“.
- Android lädt die APK und öffnet den Installer (einmalig „Unbekannte Apps installieren“ für SkorText erlauben). Im Aze-IPTV-Player kommt SkorText mit dem Player-Update.
- GigaBlue lädt `skortext.ipk`, installiert mit `opkg install --force-reinstall` und bietet den GUI-Neustart an.
- **Neue Version veröffentlichen:** `VERSION` in `plugin.py` **und** in `app.js` gleich hochzählen → auf main pushen → Build erzeugt das Release automatisch.

## 6. Testen (Arbeitsweise bisher)

- Plugin: Testmatrix mit echten Enigma2-Bausteinen (Team Blue 7.3/7.6, Python 3.11–3.13), Bildschirmfotos per Render-Skript
- App: Playwright-Simulation mit nachgebauter SkorBridge und Beispieldaten
- Echte Quellen: über `probe.yml` von GitHub aus (aus der Claude-Umgebung sind die Seiten gesperrt)
- Commits als „Claude <noreply@anthropic.com>“

## 7. Offen / Ideen

- **Auf echten Geräten noch nicht bestätigt:** das Update von selbst (Box + Shield), dass der Schwarzbild-Fix auf der Shield hilft (seit 3.9.1), Türkiye-Kupası über TFF
- EM-Quali über UEFA (Wettbewerbsnummer 3 geraten) – prüfen, sobald die EM-2028-Quali läuft (ab März 2027)
- LaLiga über ESPN: Spieltag 1–2 fehlen
- Übersicht läuft über, wenn viele Zusatzligen eingeblendet sind (dann zweite Übersichtsseite)
- `build.yml` baut bei **jedem** Push ein Release (auch bei Probe-Commits) – ggf. auf Änderungen in `app/` und `enigma2/` beschränken
- ARD Text ist seit 3.16 eingebaut (Seite 990). Möglich wären noch ZDFtext, ORF, SRF. TRT bietet keinen Online-Videotext an.
- Übersicht hat mit 990 eine Zeile zu viel (zweite Übersichtsseite), bis man über 910 etwas ausblendet.
- Reserve-Quellen aus dem Galvanik-Tool (TheSportsDB, OpenLigaDB, football-data.org über Cloudflare-Worker) sind **nicht** eingebaut. football-data.org bräuchte einen eigenen kostenlosen API-Schlüssel.

## 8. Schlüssel

- **App-Signatur:** `app/skortext.keystore` (PKCS12, Alias `skortext`, Passwort `skortext` – steht in `app/build.gradle`).
  - SHA-256-Fingerabdruck: `DC:7F:D1:8A:69:05:35:1C:EB:6B:34:BF:34:19:43:70:0D:43:AA:12:BB:23:FE:5A:32:6C:A7:CE:B9:BC:FF:E6`
  - Android nimmt Updates nur an, wenn sie mit **diesem** Schlüssel signiert sind. Geht er verloren, muss die App auf allen Geräten deinstalliert und neu installiert werden (Einstellungen weg). Deshalb zusätzlich eine Sicherungskopie aufbewahren.
- Sonst gibt es keine API-Schlüssel oder Passwörter; alle Quellen sind frei abrufbar. GitHub-Zugriff läuft über das eigene Konto (Postmen1971).
