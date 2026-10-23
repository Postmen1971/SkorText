/* SkorText für Android TV / NVIDIA Shield – Portierung des Enigma2-Plugins */
(function () {
"use strict";
var VERSION = "1.2";

/* ================= Texte ================= */
var TXT = {
 de: {overview:"Übersicht",results:"Ergebnisse",table:"Tabelle",liveTable:"Live-Tabelle",md:"%d. Spieltag",live:"Live",
  allLive:"Alle Live-Spiele",help:"Bedienung",settings:"Einstellungen",noLive:"Zurzeit keine Live-Spiele",ht:"HZ",ft:"Ende",
  pp:"Abg.",goal:"TOR!",club:"Verein",pl:"Pl",sp:"Sp",w:"S",d:"U",l:"N",goals:"Tore",diff:"Diff",pts:"Pkt",
  fast:["Deutschland","Türkei","Europa","LIVE"],days:["So","Mo","Di","Mi","Do","Fr","Sa"],notfound:"Seite %d nicht vorhanden",
  stand:"Stand",cDE:"DEUTSCHLAND",cTR:"TÜRKEI",cEU:"EUROPA",cNEWS:"HABERLER",openHint:"▲▼◄► wählen · OK öffnen · ZURÜCK beenden",
  home:"ZURÜCK = Übersicht",exitAgain:"Übersicht · ZURÜCK nochmal = beenden",setHint:"▲▼ wählen · ◄► ändern · ZURÜCK zurück",
  loading:"Lade Daten …",noData:"Keine Daten erreichbar.",noData2:"Internetverbindung prüfen.",noGames:"Keine Spiele gefunden.",
  noTable:"Keine Tabelle verfügbar.",source:"Daten: Sofascore (inoffiziell)",mdNow:"(aktuell)",mdBrowse:"Spieltag",
  noMore:"Kein weiterer Spieltag",newsHint:"▲▼ wählen · OK lesen · ◄► Rubrik",articleHint:"▲▼ / ◄► nächste Meldung · OK / ZURÜCK",
  resHint:"◄► Liga · OK Tabelle",tabHint:"◄► Liga · OK Ergebnisse",
  helpRows:[["◄ ►","Liga wechseln"],["OK","Ergebnisse ⇄ Tabelle"],["▲ ▼","Ergebnisse: Spieltag vor/zurück"],["▲ ▼","Tabelle: Unterseite"],
   ["ZURÜCK","Übersicht, nochmal = App beenden"],["Übersicht","▲▼◄► wählen, OK öffnet"],["500","Alle Live-Spiele"],["600","Haberler (Nachrichten)"],
   ["900","Einstellungen (Stil, Sprache …)"],["Farbtasten","falls vorhanden: DE / TR / Europa / Live"],["0–9","falls vorhanden: Seitennummer"]]},
 tr: {overview:"Genel Bakış",results:"Sonuçlar",table:"Puan Durumu",liveTable:"Canlı Puan Durumu",md:"%d. Hafta",live:"Canlı",
  allLive:"Tüm Canlı Maçlar",help:"Kullanım",settings:"Ayarlar",noLive:"Şu an canlı maç yok",ht:"İY",ft:"MS",
  pp:"Ert.",goal:"GOL!",club:"Takım",pl:"S",sp:"O",w:"G",d:"B",l:"M",goals:"Gol",diff:"Av",pts:"P",
  fast:["Almanya","Türkiye","Avrupa","CANLI"],days:["Paz","Pzt","Sal","Çar","Per","Cum","Cmt"],notfound:"Sayfa %d yok",
  stand:"Güncel",cDE:"ALMANYA",cTR:"TÜRKİYE",cEU:"AVRUPA",cNEWS:"HABERLER",openHint:"▲▼◄► seç · OK aç · GERİ çık",
  home:"GERİ = Genel Bakış",exitAgain:"Genel Bakış · tekrar GERİ = çık",setHint:"▲▼ seç · ◄► değiştir · GERİ",
  loading:"Veriler yükleniyor …",noData:"Veri alınamadı.",noData2:"İnternet bağlantısını kontrol et.",noGames:"Maç bulunamadı.",
  noTable:"Puan durumu yok.",source:"Veri: Sofascore (resmi değil)",mdNow:"(güncel)",mdBrowse:"Hafta",
  noMore:"Başka hafta yok",newsHint:"▲▼ seç · OK oku · ◄► kategori",articleHint:"▲▼ / ◄► sonraki haber · OK / GERİ",
  resHint:"◄► Lig · OK Puan",tabHint:"◄► Lig · OK Sonuçlar",
  helpRows:[["◄ ►","Lig değiştir"],["OK","Sonuçlar ⇄ Puan Durumu"],["▲ ▼","Sonuçlar: önceki/sonraki hafta"],["▲ ▼","Puan durumu: alt sayfa"],
   ["GERİ","Genel Bakış, tekrar = uygulamadan çık"],["Genel Bakış","▲▼◄► seç, OK aç"],["500","Tüm canlı maçlar"],["600","Haberler"],
   ["900","Ayarlar (görünüm, dil …)"],["Renk tuşları","varsa: DE / TR / Avrupa / Canlı"],["0–9","varsa: sayfa numarası"]]}
};
var SETTINGS = [
 ["style",["Stil / Optik","Görünüm"],[["tt","Videotext (klassisch)","Teletext (klasik)"],["modern","Modern (wie Webseite)","Modern (web sitesi gibi)"]],["Wird sofort umgeschaltet.","Hemen değişir."]],
 ["lang",["Sprache / Dil","Dil / Sprache"],[["de","Deutsch","Deutsch"],["tr","Türkçe","Türkçe"]],["Sprache der Seiten.","Sayfa dili."]],
 ["fav",["Lieblingsverein","Favori takım"],[["","– keiner –","– yok –"],["VfB Stuttgart","VfB Stuttgart","VfB Stuttgart"],["Stuttgarter Kickers","Stuttgarter Kickers","Stuttgarter Kickers"],
   ["Großaspach","SG Sonnenhof Großaspach","SG Sonnenhof Großaspach"],["Göppinger","1. Göppinger SV","1. Göppinger SV"],["Bayern München","FC Bayern München","FC Bayern München"],
   ["Dortmund","Borussia Dortmund","Borussia Dortmund"],["Galatasaray","Galatasaray","Galatasaray"],["Fenerbahçe","Fenerbahçe","Fenerbahçe"],
   ["Beşiktaş","Beşiktaş","Beşiktaş"],["Trabzonspor","Trabzonspor","Trabzonspor"],["Başakşehir","Başakşehir","Başakşehir"]],["Wird in Ergebnissen und Tabellen markiert.","Sonuç ve tabloda işaretlenir."]],
 ["startpage",["Startseite","Açılış sayfası"],[["100","100 Übersicht","100 Genel Bakış"],["500","500 Live","500 Canlı"],["200","200 1. Bundesliga","200 Bundesliga"],["300","300 Süper Lig","300 Süper Lig"]],["Seite nach dem Start.","Başlatınca açılan sayfa."]],
 ["refresh",["Aktualisierung","Güncelleme"],[["60","alle 60 s","60 sn'de bir"],["30","alle 30 s","30 sn'de bir"],["120","alle 120 s","120 sn'de bir"]],["Wie oft neue Daten geholt werden.","Verilerin çekilme sıklığı."]],
 ["rotate",["Unterseiten blättern","Alt sayfa çevirme"],[["man","Manuell (▲▼)","Manuel (▲▼)"],["10","Automatisch alle 10 s","10 sn'de bir otomatik"]],["Bei langen Seiten.","Uzun sayfalarda."]],
 ["bg",["Hintergrund","Arka plan"],[["black","Schwarz","Siyah"],["navy","Dunkelblau","Lacivert"]],["Hintergrundfarbe.","Arka plan rengi."]]
];

/* ================= Einstellungen (dauerhaft) ================= */
var CFG = {};
function prefGet(k, d) {
  try { if (window.SkorBridge && SkorBridge.pref) return SkorBridge.pref(k, d); } catch (e) {}
  try { var v = localStorage.getItem("skortext." + k); return v === null ? d : v; } catch (e) { return d; }
}
function prefSet(k, v) {
  try { if (window.SkorBridge && SkorBridge.setPref) { SkorBridge.setPref(k, v); return; } } catch (e) {}
  try { localStorage.setItem("skortext." + k, v); } catch (e) {}
}
SETTINGS.forEach(function (s) { CFG[s[0]] = prefGet(s[0], s[2][0][0]); });
function cfg(k) { return CFG[k]; }
function setCfg(k, v) { CFG[k] = v; prefSet(k, v); }
function T(k) { return TXT[cfg("lang")][k]; }
function fmt(s, n) { return s.replace("%d", n); }

/* ================= HTTP ================= */
var pending = {}, reqId = 0;
window.__skorRes = function (id, ok, status, text) {
  var p = pending[id]; delete pending[id]; if (!p) return;
  if (ok && status >= 200 && status < 300) p.res(text); else p.rej(new Error(ok ? "HTTP " + status : String(text)));
};
var SAME_ORIGIN = /sofascore\.com$/.test(location.hostname);
function httpGet(url) {
  if (SAME_ORIGIN && url.indexOf("https://api.sofascore.com/") === 0) {
    // Abruf durch den eingebauten Chrome selbst, auf demselben Weg wie die Sofascore-Webseite (www.sofascore.com/api/v1)
    return fetch(url.replace("https://api.sofascore.com", ""), {credentials: "include", headers: {"Accept": "*/*"}})
      .then(function (r) {
        if (r.ok) return r.text();
        return r.text().then(function (t) { return Promise.reject(new Error("HTTP " + r.status + " " + t.replace(/\s+/g, " ").slice(0, 70))); },
          function () { return Promise.reject(new Error("HTTP " + r.status)); });
      });
  }
  return new Promise(function (res, rej) {
    if (window.SkorBridge && SkorBridge.get) { var id = ++reqId; pending[id] = {res: res, rej: rej}; SkorBridge.get(id, url); }
    else fetch(url).then(function (r) { return r.ok ? r.text() : Promise.reject(new Error("HTTP " + r.status)); }).then(res, rej);
  });
}
function getJSON(url) { return httpGet(url).then(function (t) { return JSON.parse(t); }); }
var BASE = "https://api.sofascore.com/api/v1";
function sofa(path) { return getJSON(BASE + path); }
function niceError(e) {
  var s = String(e && e.message || e);
  if (s.indexOf("403") >= 0) return "Gesperrt (403): " + s.replace(/^.*?403\s*/, "").slice(0, 60);
  if (s.indexOf("404") >= 0) return "Daten nicht gefunden (HTTP 404)";
  if (/timeout|timed out/i.test(s)) return "Zeitüberschreitung – Internet langsam oder weg";
  if (/unknownhost|unable to resolve|dns/i.test(s)) return "Keine Internetverbindung";
  return s.slice(0, 80);
}

/* ================= Daten ================= */
var LEAGUES_DEF = [
 [200,"de",35,"1. Bundesliga","Bundesliga",""],[210,"de",44,"2. Bundesliga","2. Bundesliga",""],[220,"de",491,"3. Liga","3. Lig (Almanya)",""],
 [230,"de",1079,"Regionalliga Südwest","Regionalliga Güneybatı",""],[240,"de",493,"Regionalliga West","Regionalliga Batı",""],
 [250,"de",1085,"Regionalliga Bayern","Regionalliga Bavyera",""],[260,"de",42,"Regionalliga Nord","Regionalliga Kuzey",""],
 [270,"de",1083,"Regionalliga Nordost","Regionalliga Kuzeydoğu",""],[280,"de",32338,"Verbandsliga Württemberg","Verbandsliga Württemberg",""],
 [300,"tr",52,"Trendyol Süper Lig","Trendyol Süper Lig",""],[310,"tr",98,"Trendyol 1. Lig (2. Liga)","Trendyol 1. Lig",""],
 [320,"tr",97,"2. Lig (3. Liga)","Nesine 2. Lig",""],[330,"tr",16934,"3. Lig (4. Liga)","Nesine 3. Lig",""],
 [400,"eu",17,"Premier League","Premier Lig","ENG"],[410,"eu",8,"LaLiga","LaLiga","ESP"],[420,"eu",23,"Serie A","Serie A","ITA"],[430,"eu",34,"Ligue 1","Ligue 1","FRA"]
];
var GROUPS = {
 97: [["Beyaz Grup", /beyaz|white/], ["Kırmızı Grup", /k[ıi]rm[ıi]z[ıi]|red/]],
 16934: [["1. Grup", /(gru?p|group)\s*1\b|\b1\.\s*gru?p/], ["2. Grup", /(gru?p|group)\s*2\b|\b2\.\s*gru?p/], ["3. Grup", /(gru?p|group)\s*3\b|\b3\.\s*gru?p/]]
};
function shortGroup(name) { if (!name) return ""; return name.indexOf(",") >= 0 ? name.split(",").pop().trim() : ""; }
function zoneOf(t) {
  t = (t || "").toLowerCase(); if (!t) return null;
  if (t.indexOf("relegation") >= 0 && /playoff|play-off|qualif/.test(t)) return "y";
  if (t.indexOf("relegation") >= 0) return "r";
  if (t.indexOf("champions league") >= 0) return t.indexOf("qualif") >= 0 ? "c" : "g";
  if (t.indexOf("europa league") >= 0) return "c";
  if (t.indexOf("conference") >= 0) return "m";
  if (t.indexOf("promotion") >= 0) return /playoff|play-off/.test(t) ? "c" : "g";
  if (/playoff|play-off/.test(t)) return "c";
  return null;
}
function parseEvent(e, now) {
  now = now || Date.now() / 1000;
  var st = e.status || {}, code = st.code, hs = (e.homeScore || {}).current, as = (e.awayScore || {}).current;
  var state = {notstarted: "pre", inprogress: "in", finished: "post"}[st.type] || "pp", minute = "";
  if (hs === undefined) hs = null; if (as === undefined) as = null;
  if (state === "in") {
    if (code === 31) state = "ht";
    else {
      var cps = (e.time || {}).currentPeriodStartTimestamp;
      if (cps && (code === 6 || code === 7)) {
        var m = Math.floor((now - cps) / 60) + 1;
        if (code === 6) minute = m <= 45 ? String(m) : "45+" + (m - 45);
        else { m += 45; minute = m <= 90 ? String(m) : "90+" + (m - 90); }
      } else if ([41, 42, 33, 34].indexOf(code) >= 0) minute = "Verl";
      else if (code === 50) minute = "Elf";
      else minute = "live";
    }
  }
  var ht = e.homeTeam || {}, at = e.awayTeam || {}, tour = e.tournament || {};
  return {id: e.id, h: ht.name || "?", hsn: ht.shortName || "", a: at.name || "?", asn: at.shortName || "",
    hs: hs, as: as, state: state, min: minute, ts: e.startTimestamp || 0, group: shortGroup(tour.name),
    ut: (tour.uniqueTournament || {}).id, goal_at: 0, goal_by: null};
}

function League(d) {
  this.page = d[0]; this.c = d[1]; this.ut = d[2]; this.nameDe = d[3]; this.nameTr = d[4]; this.tag = d[5];
  this.season = null; this.tSeason = 0; this.round = null; this.tRound = 0; this.maxRound = null;
  this.events = []; this.prevEvents = []; this.prevRound = null; this.rcache = {}; this.rloading = {};
  this.tables = []; this.tLoad = 0; this.loading = false; this.error = null; this.gdefs = GROUPS[this.ut] || [];
}
League.prototype.name = function (lang) { return lang === "tr" ? this.nameTr : this.nameDe; };
League.prototype.views = function () {
  if (this.gdefs.length) return this.gdefs.map(function (g, i) { return [this.page + 2 * i, i]; }, this);
  return [[this.page, null]];
};
League.prototype.groups = function () {
  var names = this.tables.map(function (t) { return t[0]; });
  this.events.forEach(function (e) { if (names.indexOf(e.group) < 0) names.push(e.group); });
  return names.length ? names : [""];
};
League.prototype.groupIndex = function (name) {
  var low = (name || "").toLowerCase();
  for (var i = 0; i < this.gdefs.length; i++) if (this.gdefs[i][1].test(low)) return i;
  var names = this.groups(), k = names.indexOf(name);
  return k >= 0 && k < this.gdefs.length ? k : null;
};
League.prototype.inGroup = function (name, gi) { return gi === null || gi === undefined ? true : this.groupIndex(name) === gi; };
League.prototype.pageOfGroup = function (name) { var gi = this.gdefs.length ? this.groupIndex(name) : null; return gi === null ? this.page : this.page + 2 * gi; };
League.prototype.eventsOfRound = function (n) {
  if (n === this.round) return this.events;
  if (n === this.prevRound) return this.prevEvents;
  return this.rcache[n] === undefined ? null : this.rcache[n];
};
League.prototype.load = function () {
  var self = this, now = Date.now() / 1000, base;
  var p = Promise.resolve();
  if (!self.season || now - self.tSeason > 86400) {
    p = sofa("/unique-tournament/" + self.ut + "/seasons").then(function (d) {
      var ss = d.seasons || []; self.season = null;
      for (var i = 0; i < ss.length; i++) { var n = (ss[i].name || "").toLowerCase(); if (/playoff|play-off|relegation/.test(n)) continue; self.season = ss[i].id; break; }
      if (!self.season && ss.length) self.season = ss[0].id;
      self.tSeason = now;
    });
  }
  return p.then(function () {
    base = "/unique-tournament/" + self.ut + "/season/" + self.season;
    if (!self.round || now - self.tRound > 1800)
      return sofa(base + "/rounds").then(function (r) {
        self.round = (r.currentRound || {}).round || null;
        var nums = (r.rounds || []).map(function (x) { return x.round; }).filter(function (x) { return typeof x === "number"; });
        self.maxRound = nums.length ? Math.max.apply(null, nums) : null; self.tRound = now;
      }, function () { self.round = null; });
  }).then(function () {
    if (self.round) return sofa(base + "/events/round/" + self.round).then(function (d) { return d.events || []; });
    return Promise.all(["/events/last/0", "/events/next/0"].map(function (x) {
      return sofa("/unique-tournament/" + self.ut + x).then(function (d) { return d.events || []; }, function () { return []; });
    })).then(function (a) { return a[0].concat(a[1]); });
  }).then(function (evs) {
    self.events = evs.map(function (e) { return parseEvent(e, now); });
    if (self.round && self.round > 1)
      return sofa(base + "/events/round/" + (self.round - 1)).then(function (d) { return d.events || []; }, function () { return []; });
    return [];
  }).then(function (prev) {
    self.prevEvents = prev.map(function (e) { return parseEvent(e, now); });
    self.prevRound = prev.length ? self.round - 1 : null;
    return sofa(base + "/standings/total").then(function (d) { return d.standings || []; }, function () { return []; });
  }).then(function (st) {
    self.tables = st.map(function (s) {
      var rows = (s.rows || []).map(function (r) {
        var tm = r.team || {};
        return {pos: r.position || 0, tm: tm.name || "?", short: tm.shortName || "", p: r.matches || 0, w: r.wins || 0, d: r.draws || 0,
          l: r.losses || 0, gf: r.scoresFor || 0, ga: r.scoresAgainst || 0, pts: r.points || 0, zone: zoneOf((r.promotion || {}).text)};
      });
      var full = s.name || (s.tournament || {}).name || "", name = shortGroup(full);
      if (!name && st.length > 1) name = full;
      return [name, rows];
    });
    self.tLoad = Date.now() / 1000; self.error = null;
  });
};
League.prototype.loadRound = function (n) {
  var self = this;
  return sofa("/unique-tournament/" + self.ut + "/season/" + self.season + "/events/round/" + n).then(function (d) {
    self.rcache[n] = (d.events || []).map(function (e) { return parseEvent(e); });
  });
};

var STORE = {leagues: LEAGUES_DEF.map(function (d) { return new League(d); }), live: {}, tLive: 0, liveError: null, goals: [], loadingLive: false};
STORE.byUt = {}; STORE.leagues.forEach(function (l) { STORE.byUt[l.ut] = l; });
STORE.allViews = function () { var out = []; this.leagues.forEach(function (lg) { lg.views().forEach(function (v) { out.push([lg, v[0], v[1]]); }); }); return out; };
STORE.view = function (p) { var v = this.allViews(); for (var i = 0; i < v.length; i++) { if (p === v[i][1]) return [v[i][0], v[i][2], "res"]; if (p === v[i][1] + 1) return [v[i][0], v[i][2], "tab"]; } return null; };
STORE.leagueByPage = function (p) { var v = this.view(p); return v ? v[0] : null; };
STORE.liveCount = function (lg) { var n = 0; for (var k in this.live) if (!lg || this.live[k].ut === lg.ut) n++; return n; };
STORE.liveCountView = function (lg, gi) { var n = 0; for (var k in this.live) { var e = this.live[k]; if (e.ut === lg.ut && lg.inGroup(e.group, gi)) n++; } return n; };
STORE.fetchLive = function () {
  return sofa("/sport/football/events/live").then(function (d) {
    var now = Date.now() / 1000, out = {};
    (d.events || []).forEach(function (e) { var ut = ((e.tournament || {}).uniqueTournament || {}).id; if (STORE.byUt[ut]) { var pe = parseEvent(e, now); out[pe.id] = pe; } });
    return out;
  });
};
STORE.applyLive = function (nw) {
  var now = Date.now() / 1000, self = this, k;
  for (k in nw) {
    var e = nw[k], old = self.live[k];
    if (old) {
      var o = (old.hs || 0) + (old.as || 0), n = (e.hs || 0) + (e.as || 0);
      if (n > o) { e.goal_at = now; e.goal_by = (e.hs || 0) > (old.hs || 0) ? "h" : "a"; self.goals.push([now, e]); }
      else { e.goal_at = old.goal_at; e.goal_by = old.goal_by; }
    }
  }
  var ended = Object.keys(self.live).filter(function (id) { return !(id in nw); });
  self.live = nw; self.tLive = now;
  self.goals = self.goals.filter(function (g) { return now - g[0] < 60; });
  self.leagues.forEach(function (lg) {
    var changed = false, ids = {};
    lg.events.forEach(function (ev, i) { if (nw[ev.id]) lg.events[i] = nw[ev.id]; else if (ended.indexOf(String(ev.id)) >= 0) changed = true; ids[ev.id] = 1; });
    if (changed) lg.tLoad = 0;
    for (var k2 in nw) if (nw[k2].ut === lg.ut && !ids[nw[k2].id] && lg.events.length) lg.tLoad = 0;
  });
};

/* Nachrichten */
var FEEDS = [
 {page: 600, name: "Manşet", source: "TRT Haber", url: "https://www.trthaber.com/manset_articles.rss"},
 {page: 610, name: "Güncel", source: "Anadolu Ajansı", url: "https://www.aa.com.tr/tr/rss/default?cat=guncel"},
 {page: 620, name: "Dünya", source: "Anadolu Ajansı", url: "https://www.aa.com.tr/tr/rss/default?cat=dunya"},
 {page: 630, name: "Ekonomi", source: "Anadolu Ajansı", url: "https://www.aa.com.tr/tr/rss/default?cat=ekonomi"},
 {page: 640, name: "Spor", source: "Anadolu Ajansı", url: "https://www.aa.com.tr/tr/rss/default?cat=spor"}
];
FEEDS.forEach(function (f) { f.items = []; f.tLoad = 0; f.loading = false; f.error = null; });
function feedByPage(p) { for (var i = 0; i < FEEDS.length; i++) if (FEEDS[i].page === p) return FEEDS[i]; return null; }
function cleanText(s) {
  var d = document.createElement("div"); d.innerHTML = String(s || "").replace(/<[^>]+>/g, " ");
  return (d.textContent || "").replace(/\s+/g, " ").trim();
}
function parseFeed(text) {
  text = text.replace(/^﻿/, "");
  var doc = new DOMParser().parseFromString(text, "text/xml"), items = [];
  var nodes = doc.querySelectorAll("item, entry");
  if (!nodes.length) { // Notfall: abgeschnittener Feed
    var m, re = /<item>([\s\S]*?)<\/item>/g;
    while ((m = re.exec(text))) {
      var g = function (tag) { var r = new RegExp("<" + tag + "[^>]*>([\\s\\S]*?)</" + tag + ">").exec(m[1]); return r ? r[1].replace("<![CDATA[", "").replace("]]>", "") : ""; };
      items.push({title: cleanText(g("title")), desc: cleanText(g("description")), ts: Date.parse(g("pubDate")) / 1000 || 0});
    }
    return items;
  }
  Array.prototype.forEach.call(nodes, function (n) {
    var get = function (names) { for (var i = 0; i < names.length; i++) { var x = n.getElementsByTagName(names[i])[0]; if (x) return x.textContent; } return ""; };
    var t = cleanText(get(["title"]));
    if (t) items.push({title: t, desc: cleanText(get(["description", "summary"])), ts: (Date.parse(get(["pubDate", "published", "updated"])) / 1000) || 0});
  });
  return items;
}
function loadFeed(f) {
  return httpGet(f.url).then(function (t) {
    var it = parseFeed(t); it.sort(function (a, b) { return b.ts - a.ts; });
    f.items = it.slice(0, 60); f.tLoad = Date.now() / 1000; f.error = null;
  });
}

/* Wechselkurs */
var RATE = {value: null, date: "", src: "", tLoad: 0, loading: false};
function loadRate() {
  return getJSON("https://api.frankfurter.dev/v1/latest?from=EUR&to=TRY").then(function (d) {
    RATE.value = +d.rates.TRY; RATE.date = d.date || ""; RATE.src = "ezb";
  }, function () {
    return getJSON("https://open.er-api.com/v6/latest/EUR").then(function (d) {
      RATE.value = +d.rates.TRY; var dt = new Date((d.time_last_update_unix || Date.now() / 1000) * 1000);
      RATE.date = dt.getFullYear() + "-" + two(dt.getMonth() + 1) + "-" + two(dt.getDate()); RATE.src = "er";
    });
  }).then(function () { RATE.tLoad = Date.now() / 1000; });
}

/* ================= Darstellung ================= */
var PAL_TT = {w: "#f4f4f4", y: "#ffee33", c: "#33f0f0", g: "#33e36a", r: "#ff3d3d", m: "#ff4fd8", b: "#2643ff", d: "#8a8a8a", k: "#000000", fav: "#6a1260", sel: "#1d2fa8"};
var PAL_MOD = {w: "#eef2f7", y: "#ffd54a", c: "#7cc8ff", g: "#3ddc84", r: "#ff5a5f", m: "#e070ff", b: "#4c8dff", d: "#8c98aa", k: "#0b1016", fav: "#4b2c6e", sel: "#2f6bff",
  bg: "#0f151d", hdr: "#0a0f15", card: "#1b2533", zebra1: "#141c26", zebra2: "#111821"};
var COL = PAL_TT;
var PAGE_BG = {black: "#000000", navy: "#06103a"};
var COUNTRY_BG = {de: ["r", "w"], tr: ["g", "k"], eu: ["y", "k"]};
function modern() { return cfg("style") === "modern"; }
function seg(col, width, text, fg, bg, al, blink) { return [col, width, text, fg || "w", bg || null, al || "l", !!blink]; }
function fit(t, w, short) { t = t || ""; if (t.length <= w) return t; if (short && short.length <= w) return short; return t.slice(0, w); }
function two(n) { return (n < 10 ? "0" : "") + n; }
function isFav(name) { var f = cfg("fav"); return !!f && (name || "").toLowerCase().indexOf(f.toLowerCase()) >= 0; }
function trUpper(s) { return s.replace(/i/g, "İ").replace(/ı/g, "I").toUpperCase(); }
function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }

var S = {page: 100, sub: 0, entry: "", entryAt: 0, msg: "", msgUntil: 0, idx: [0, 1], setSel: 0, newsSel: 0, newsOpen: null, md: null,
  blinkOn: true, lastRot: Date.now(), openedAt: Date.now() / 1000};
var G = {rowH: 20, fs: 16, cw: 9.6, pw: 800, cols: 80};
var scr = document.getElementById("scr"), rateEl = document.getElementById("rate");
var rowEls = [];
for (var ri = 0; ri < 24; ri++) { var d = document.createElement("div"); d.className = "row"; scr.appendChild(d); rowEls.push(d); }

function layout() {
  var dw = window.innerWidth, dh = window.innerHeight, mx = Math.floor(dw * 0.03), my = Math.floor(dh * 0.035);
  G.rowH = Math.floor((dh - 2 * my) / 24); G.fs = Math.floor(G.rowH * 0.84); G.cw = G.fs * 0.602;
  G.pw = dw - 2 * mx; G.cols = Math.floor(G.pw / G.cw);
  scr.style.left = mx + "px"; scr.style.top = my + "px"; scr.style.width = G.pw + "px"; scr.style.height = (G.rowH * 24) + "px";
  rowEls.forEach(function (el, i) { el.style.top = (i * G.rowH) + "px"; el.style.height = G.rowH + "px"; });
  rateEl.style.left = (mx + G.cw) + "px"; rateEl.style.top = (my + G.rowH * 19) + "px";
  rateEl.style.width = Math.floor(G.pw * 0.47) + "px"; rateEl.style.height = (G.rowH * 2) + "px";
}
window.addEventListener("resize", function () { layout(); draw(); });

function pageType(p) {
  if (p === 100) return "idx"; if (p === 190) return "help"; if (p === 500) return "live"; if (p === 900) return "set";
  if (feedByPage(p)) return "news";
  var v = STORE.view(p); return v ? v[2] : null;
}
function allPages() {
  var pages = [100, 190]; STORE.allViews().forEach(function (v) { pages.push(v[1], v[1] + 1); });
  return pages.concat([500]).concat(FEEDS.map(function (f) { return f.page; })).concat([900]);
}
function up(s, country) {
  if (country === "tr" || cfg("lang") === "tr") { var u = trUpper(s); if (cfg("lang") !== "tr") u = u.replace(/LİGA/g, "LIGA"); return u; }
  return s.toUpperCase();
}
function message(s, secs) { S.msg = s; S.msgUntil = Date.now() + (secs || 2.2) * 1000; }

/* ---- Laden ---- */
function needLeague(lg) {
  if (lg.loading) return;
  var age = Date.now() / 1000 - lg.tLoad, limit = STORE.liveCount(lg) ? +cfg("refresh") : 600;
  if (lg.tLoad && age <= limit) return;
  lg.loading = true;
  lg.load().then(function () { lg.loading = false; draw(); }, function (e) {
    lg.loading = false; lg.error = niceError(e); lg.tLoad = Date.now() / 1000 - 600 + 20; draw();
  });
}
function needRound(lg, n) {
  if (lg.eventsOfRound(n) !== null || lg.rloading[n] || !lg.season) return;
  lg.rloading[n] = true;
  lg.loadRound(n).then(function () { delete lg.rloading[n]; draw(); }, function () { delete lg.rloading[n]; lg.rcache[n] = []; draw(); });
}
function needFeed(f) {
  if (f.loading || (f.tLoad && Date.now() / 1000 - f.tLoad < 600)) return;
  f.loading = true;
  loadFeed(f).then(function () { f.loading = false; draw(); }, function (e) { f.loading = false; f.error = niceError(e); f.tLoad = Date.now() / 1000 - 600 + 30; draw(); });
}
function needRate() {
  if (RATE.loading || (RATE.tLoad && Date.now() / 1000 - RATE.tLoad < 1800)) return;
  RATE.loading = true;
  loadRate().then(function () { RATE.loading = false; draw(); }, function () { RATE.loading = false; RATE.tLoad = Date.now() / 1000 - 1800 + 120; });
}
function fetchLive() {
  STORE.loadingLive = true;
  STORE.fetchLive().then(function (nw) { STORE.loadingLive = false; STORE.liveError = null; STORE.applyLive(nw); draw(); },
    function (e) { STORE.loadingLive = false; STORE.tLive = Date.now() / 1000; STORE.liveError = niceError(e); });
}

/* ---- Navigation ---- */
function go(p) {
  if (pageType(p) === null) { message(fmt(T("notfound"), p)); return; }
  var a = STORE.leagueByPage(S.page), b = STORE.leagueByPage(p);
  if (!a || a !== b) S.md = null;
  S.page = p; S.sub = 0; S.lastRot = Date.now(); S.newsSel = 0; S.newsOpen = null;
  var f = feedByPage(p); if (f) needFeed(f);
  if (p === 100) S.idx = [0, 1];
  var lg = STORE.leagueByPage(p); if (lg) needLeague(lg);
}
function shownRound(lg) {
  if (S.md) return S.md;
  var started = lg.events.some(function (e) { return e.state !== "pre"; });
  if (!started && lg.prevRound) return lg.prevRound;
  return lg.round;
}
function keyNumber(n) {
  if (!S.entry && n === 0) { go(100); return; }
  S.entry += String(n); S.entryAt = Date.now();
  if (S.entry.length === 3) { var p = +S.entry; S.entry = ""; go(p); }
}
function key(k) {
  if (/^[0-9]$/.test(k)) { keyNumber(+k); draw(); return; }
  S.entry = "";
  var t = pageType(S.page);
  if (t === "news" && ["back", "ok", "up", "down", "left", "right"].indexOf(k) >= 0) { newsKey(k); draw(); return; }
  if (k === "back") {
    if (S.page !== 100) { go(100); message(T("exitAgain"), 1.8); }
    else { draw(); return "exit"; }
  } else if (k === "red" || k === "green" || k === "yellow" || k === "blue") go({red: 200, green: 300, yellow: 400, blue: 500}[k]);
  else if (k === "menu") { go(900); S.setSel = 0; }
  else if (k === "info") go(190);
  else if (k === "chup" || k === "chdn") { var pages = allPages(), i = Math.max(0, pages.indexOf(S.page)); go(pages[(i + (k === "chup" ? 1 : -1) + pages.length) % pages.length]); }
  else if (k === "left" || k === "right") {
    var dd = k === "right" ? 1 : -1;
    if (t === "idx") moveIdx(dd, 0);
    else if (t === "set") changeSetting(dd);
    else if (t === "res" || t === "tab") {
      var views = STORE.allViews(), base = S.page - (t === "tab" ? 1 : 0), bases = views.map(function (v) { return v[1]; });
      var j = Math.max(0, bases.indexOf(base)); go(bases[(j + dd + bases.length) % bases.length] + (t === "tab" ? 1 : 0));
    } else if (t === "live" || t === "help") { var n = subpages().length; S.sub = (S.sub + dd + n) % Math.max(1, n); }
  } else if (k === "up" || k === "down") {
    var d2 = k === "down" ? 1 : -1;
    if (t === "idx") moveIdx(0, d2);
    else if (t === "set") S.setSel = (S.setSel + d2 + SETTINGS.length) % SETTINGS.length;
    else if (t === "res" && STORE.leagueByPage(S.page).round) {
      var lg = STORE.leagueByPage(S.page), nr = shownRound(lg) + (d2 > 0 ? -1 : 1), top = lg.maxRound || (lg.round + 40);
      if (nr >= 1 && nr <= top) { S.md = nr; S.sub = 0; needRound(lg, nr); } else message(T("noMore"), 1.5);
    } else { var ns = subpages().length; S.sub = (S.sub + d2 + ns) % Math.max(1, ns); S.lastRot = Date.now(); }
  } else if (k === "ok") {
    if (t === "idx") { var it = idxCols()[S.idx[0]][S.idx[1]]; if (it && it.page) go(it.page); }
    else if (t === "res") { go(S.page + 1); }
    else if (t === "tab") { go(S.page - 1); }
    else if (t === "set") changeSetting(1);
  }
  draw();
}
function changeSetting(d) {
  var s = SETTINGS[S.setSel], vals = s[2].map(function (o) { return o[0]; }), i = Math.max(0, vals.indexOf(cfg(s[0])));
  setCfg(s[0], vals[(i + d + vals.length) % vals.length]);
}
function newsKey(k) {
  var f = feedByPage(S.page), n = f.items.length;
  if (k === "back") { if (S.newsOpen !== null) S.newsOpen = null; else { go(100); message(T("exitAgain"), 1.8); } }
  else if (k === "ok") { S.newsOpen = (S.newsOpen === null && n) ? S.newsSel : null; }
  else if ((k === "up" || k === "down") && n) {
    var d = k === "down" ? 1 : -1;
    if (S.newsOpen !== null) { S.newsOpen = (S.newsOpen + d + n) % n; S.newsSel = S.newsOpen; } else S.newsSel = (S.newsSel + d + n) % n;
  } else if (k === "left" || k === "right") {
    var dd = k === "right" ? 1 : -1;
    if (S.newsOpen !== null && n) { S.newsOpen = (S.newsOpen + dd + n) % n; S.newsSel = S.newsOpen; }
    else { var i = FEEDS.indexOf(f); go(FEEDS[(i + dd + FEEDS.length) % FEEDS.length].page); }
  }
}
function idxCols() {
  var lang = cfg("lang");
  function views(c) {
    var out = [];
    STORE.leagues.filter(function (l) { return l.c === c; }).forEach(function (l) {
      l.views().forEach(function (v) {
        out.push({page: v[0], lbl: (l.tag ? l.tag + " " : "") + l.name(lang) + (v[1] !== null ? " · " + l.gdefs[v[1]][0] : ""), lg: l, gi: v[1]});
      });
    });
    return out;
  }
  var left = [{hdr: T("cDE"), bg: "r", fg: "w"}].concat(views("de")).concat([null, {page: 500, lbl: T("allLive"), live: true}, {page: 900, lbl: T("settings")}, {page: 190, lbl: T("help")}]);
  var right = [{hdr: T("cTR"), bg: "g", fg: "k"}].concat(views("tr")).concat([null, {hdr: T("cEU"), bg: "y", fg: "k"}]).concat(views("eu"))
    .concat([null, {hdr: T("cNEWS"), bg: "m", fg: "k"}, {page: 600, lbl: "Haberler · " + FEEDS.slice(0, 3).map(function (f) { return f.name; }).join(", ") + " …"}]);
  return [left, right];
}
function moveIdx(dc, dr) {
  var cols = idxCols(), c = S.idx[0], r = S.idx[1], ok = function (it) { return it && it.page; }, k = 0;
  if (dc) { c = (c + dc + 2) % 2; r = Math.min(r, cols[c].length - 1); while (!ok(cols[c][r]) && k++ < 40) r = (r + 1) % cols[c].length; }
  if (dr) { do { r = (r + dr + cols[c].length) % cols[c].length; } while (!ok(cols[c][r]) && k++ < 40); }
  S.idx = [c, r];
}

/* ---- Zeilen ---- */
function text(s, fg) { return [null, [seg(0, G.cols, s, fg || "w")]]; }
function blank() { return [null, []]; }
function chunk(lines, n) { n = n || 20; var out = []; for (var i = 0; i < lines.length; i += n) out.push(lines.slice(i, i + n)); return out.length ? out : [[]]; }
function dayLabel(ts) { var d = new Date(ts * 1000); return T("days")[d.getDay()] + " " + two(d.getDate()) + "." + two(d.getMonth() + 1) + "."; }
function statusSegs(e) {
  if (e.state === "pre") { var d = new Date(e.ts * 1000); return [seg(0, 6, two(d.getHours()) + ":" + two(d.getMinutes()), "w")]; }
  if (e.state === "post") return [seg(0, 6, T("ft"), "d")];
  if (e.state === "pp") return [seg(0, 6, T("pp"), "r")];
  if (e.state === "ht") return [seg(0, 6, T("ht"), "g")];
  return [seg(0, 6, (e.min || "") + (/^\d/.test(e.min || "") ? "'" : ""), "g")];
}
function resRow(e) {
  var C = G.cols, W = Math.floor((C - 17) / 2), fresh = Date.now() / 1000 - (e.goal_at || 0) < 30;
  var s = statusSegs(e);
  s.push(seg(7, W, fit(e.h, W, e.hsn), fresh && e.goal_by === "h" ? "y" : "w", null, "r"));
  if (e.state === "pre" || e.hs === null) s.push(seg(8 + W, 5, "-:-", "d", null, "c"));
  else if (fresh) s.push(seg(8 + W, 5, e.hs + ":" + e.as, "k", "y", "c", true));
  else s.push(seg(8 + W, 5, e.hs + ":" + e.as, e.state === "post" ? "w" : "y", null, "c"));
  s.push(seg(14 + W, W, fit(e.a, W, e.asn), fresh && e.goal_by === "a" ? "y" : "w"));
  if (e.state === "in" || e.state === "ht") s.push(seg(15 + 2 * W, 2, "●", "g", null, "l", true));
  return [(isFav(e.h) || isFav(e.a)) ? COL.fav : null, s];
}
function resultLines(events) {
  var out = [], last = null;
  events.slice().sort(function (a, b) {
    var la = (a.state === "in" || a.state === "ht") ? 0 : 1, lb = (b.state === "in" || b.state === "ht") ? 0 : 1;
    return la - lb || a.ts - b.ts || (a.h < b.h ? -1 : 1);
  }).forEach(function (e) {
    var live = e.state === "in" || e.state === "ht", dl = live ? "● " + up(T("live")) : dayLabel(e.ts);
    if (dl !== last) { out.push(text(dl, live ? "g" : "c")); last = dl; }
    out.push(resRow(e));
  });
  return out;
}
function tableLines(lg, rows0, gi) {
  var C = G.cols, N = C - 40, changed = false;
  var live = lg.events.filter(function (e) { return (e.state === "in" || e.state === "ht") && e.hs !== null && lg.inGroup(e.group, gi); });
  var rows = rows0.map(function (r) { var o = {}; for (var k in r) o[k] = r[k]; return o; });
  if (live.length) {
    var by = {}; rows.forEach(function (r) { by[r.tm] = r; });
    live.forEach(function (e) {
      var H = by[e.h], A = by[e.a]; if (!H || !A) return;
      [[H, e.hs, e.as], [A, e.as, e.hs]].forEach(function (x) {
        var X = x[0], gf = x[1], ga = x[2]; X.live = true;
        if (lg.round && X.p >= lg.round) return;
        X.p++; X.gf += gf; X.ga += ga; X.changed = true;
        if (gf > ga) { X.w++; X.pts += 3; } else if (gf === ga) { X.d++; X.pts += 1; } else X.l++;
      });
    });
    changed = rows.some(function (r) { return r.changed; });
    if (changed) rows.sort(function (a, b) { return b.pts - a.pts || (b.gf - b.ga) - (a.gf - a.ga) || b.gf - a.gf || (a.tm < b.tm ? -1 : 1); });
  }
  return rows.map(function (r, i) {
    var rank = changed ? i + 1 : r.pos, trend = changed ? r.pos - rank : 0, z = r.zone;
    var s = [seg(0, 3, rank + ".", z ? "k" : "w", z, "c")];
    if (trend > 0) s.push(seg(3, 1, "▲", "g")); else if (trend < 0) s.push(seg(3, 1, "▼", "r"));
    var name = fit(r.tm, N - (r.live ? 2 : 0), r.short);
    s.push(seg(5, N, name, "w"));
    if (r.live) s.push(seg(5 + name.length + 1, 1, "•", "g", null, "l", true));
    var gd = r.gf - r.ga;
    s.push(seg(C - 34, 3, String(r.p), "w", null, "r"), seg(C - 30, 3, String(r.w), "w", null, "r"), seg(C - 26, 3, String(r.d), "w", null, "r"),
      seg(C - 22, 3, String(r.l), "w", null, "r"), seg(C - 18, 7, r.gf + ":" + r.ga, "w", null, "r"),
      seg(C - 10, 5, gd > 0 ? "+" + gd : String(gd), "w", null, "r"), seg(C - 4, 4, String(r.pts), "y", null, "r"));
    return [isFav(r.tm) ? COL.fav : null, s];
  });
}
function tableHead() {
  var C = G.cols;
  return [null, [seg(0, 3, T("pl"), "c", null, "c"), seg(5, C - 40, T("club"), "c"), seg(C - 34, 3, T("sp"), "c", null, "r"), seg(C - 30, 3, T("w"), "c", null, "r"),
    seg(C - 26, 3, T("d"), "c", null, "r"), seg(C - 22, 3, T("l"), "c", null, "r"), seg(C - 18, 7, T("goals"), "c", null, "r"),
    seg(C - 10, 5, T("diff"), "c", null, "r"), seg(C - 4, 4, T("pts"), "c", null, "r")]];
}
function infoHead(left) {
  var C = G.cols, d = new Date((STORE.tLive || Date.now() / 1000) * 1000);
  return [null, [seg(0, C - 18, left, "c"), seg(C - 17, 17, T("stand") + " " + two(d.getHours()) + ":" + two(d.getMinutes()) + ":" + two(d.getSeconds()), "c", null, "r")]];
}
function statusLines(lg) {
  if (lg.loading && !lg.tLoad) return [blank(), text(T("loading"), "y")];
  if (lg.error && !lg.events.length && !lg.tables.length) return [blank(), text(T("noData"), "r"), text(T("noData2"), "c"), blank(), text(fit(lg.error, G.cols), "d")];
  return null;
}
function subpages() {
  var lang = cfg("lang"), t = pageType(S.page), subs = [], C = G.cols, lines;
  if (t === "idx") {
    var cols = idxCols(), L = cols[0], R = cols[1], half = Math.floor(C / 2), mod = modern();
    lines = [];
    for (var i = 0; i < Math.max(L.length, R.length); i++) {
      var s = [];
      [L, R].forEach(function (col, ci) {
        var it = col[i], base = ci * half; if (!it) return;
        if (it.hdr) { s.push(seg(base, half - 1, " " + it.hdr, it.fg, it.bg)); return; }
        var sel = S.idx[0] === ci && S.idx[1] === i, bg, fgp, fgn, fgl;
        if (mod) { bg = sel ? "sel" : null; fgp = sel ? "y" : "c"; fgn = sel ? "w" : (it.live ? "g" : "w"); fgl = sel ? "w" : "g"; }
        else { bg = sel ? "c" : null; fgp = sel ? "k" : "y"; fgn = sel ? "k" : (it.live ? "g" : "w"); fgl = sel ? "k" : "g"; }
        s.push(seg(base, half - 1, "", "k", bg));
        if (sel && mod) s.push(seg(base, 0.45, "", "k", "y"));
        s.push(seg(base + (mod ? 0.6 : 0), 4, String(it.page), fgp, bg));
        s.push(seg(base + (mod ? 5 : 4), half - 12, fit(it.lbl, half - 12), fgn, bg));
        var n = it.lg ? STORE.liveCountView(it.lg, it.gi) : (it.live ? STORE.liveCount() : 0);
        if (n) s.push(seg(base + half - 7, 5, "●" + n, fgl, bg, "r"));
      });
      lines.push([null, s]);
    }
    while (lines.length < 19) lines.push(blank());
    lines.push(text(T("openHint"), "c"));
    subs = [{ban: [up(T("overview")), "SkorText " + VERSION], bg: ["b", "w"], head: infoHead("LIVESCORE · " + T("source")), lines: lines}];
  } else if (t === "res" || t === "tab") {
    var v = STORE.view(S.page), lg = v[0], gi = v[1], bgc = COUNTRY_BG[lg.c], title = up(lg.name(lang), lg.c), stl = statusLines(lg);
    var parts;
    if (gi !== null) parts = [[gi, title + " · " + up(lg.gdefs[gi][0], lg.c), null]];
    else if (lg.tables.length > 1) parts = lg.tables.map(function (tb) { return [null, title + (tb[0] ? " · " + up(tb[0], lg.c) : ""), tb[0]]; });
    else parts = [[null, title, null]];
    for (var pi = 0; pi < parts.length; pi++) {
      var pgi = parts[pi][0], gt = parts[pi][1], pname = parts[pi][2];
      var match = pname !== null ? function (name) { return name === pname; } : function (name) { return lg.inGroup(name, pgi); };
      if (t === "res") {
        var rnd = lg.round ? shownRound(lg) : null;
        if (stl) lines = stl;
        else {
          var evs = rnd ? lg.eventsOfRound(rnd) : lg.events;
          if (evs === null) { needRound(lg, rnd); lines = [blank(), text(T("loading"), "y")]; }
          else { lines = resultLines(evs.filter(function (e) { return match(e.group); })); if (!lines.length) lines = [blank(), text(T("noGames"), "c")]; }
        }
        var hint = rnd ? fmt(T("md"), rnd) + (rnd === lg.round ? "  " + T("mdNow") : "") + "   ▲▼ " + T("mdBrowse") + " · " + T("resHint") : T("resHint");
        chunk(lines).forEach(function (ch) { subs.push({ban: [gt, up(T("results"))], bg: bgc, head: infoHead(hint), lines: ch}); });
      } else {
        if (stl) lines = stl;
        else {
          var tabs = lg.tables.filter(function (x) { return match(x[0]); });
          lines = tabs.length ? tableLines(lg, tabs[0][1], pgi) : [blank(), text(T("noTable"), "c")];
        }
        chunk(lines).forEach(function (ch) { subs.push({ban: [gt, up(STORE.liveCountView(lg, pgi) ? T("liveTable") : T("table"))], bg: bgc, head: tableHead(), lines: ch}); });
      }
      if (stl) break;
    }
  } else if (t === "live") {
    lines = [];
    STORE.leagues.forEach(function (lg) {
      var evs = Object.keys(STORE.live).map(function (k) { return STORE.live[k]; }).filter(function (e) { return e.ut === lg.ut; });
      if (!evs.length) return;
      var groups = []; evs.forEach(function (e) { if (groups.indexOf(e.group) < 0) groups.push(e.group); }); groups.sort();
      groups.forEach(function (g) {
        lines.push(text((lg.tag ? lg.tag + " " : "") + lg.name(lang) + (g ? " · " + g : "") + "   (" + lg.pageOfGroup(g) + ")", "y"));
        evs.filter(function (e) { return e.group === g; }).sort(function (a, b) { return a.ts - b.ts; }).forEach(function (e) { lines.push(resRow(e)); });
      });
    });
    if (!lines.length) lines = STORE.liveError && !Object.keys(STORE.live).length ? [blank(), text(T("noData"), "r"), text(T("noData2"), "c")] : [blank(), text(T("noLive"), "c")];
    chunk(lines).forEach(function (ch) { subs.push({ban: ["● " + up(T("allLive")), ""], bg: ["b", "w"], head: infoHead(dayLabel(Date.now() / 1000)), lines: ch}); });
  } else if (t === "help") {
    lines = [blank()];
    T("helpRows").forEach(function (r) { lines.push([null, [seg(1, 14, r[0], "y"), seg(16, C - 16, r[1])]]); });
    lines.push(blank()); lines.push(text("SkorText TV " + VERSION + " · " + T("source"), "d"));
    subs = [{ban: [up(T("help")), "SkorText"], bg: ["b", "w"], head: blank(), lines: lines}];
  } else if (t === "set") {
    lines = [blank()]; var half2 = Math.floor(C / 2);
    SETTINGS.forEach(function (st, i) {
      var sel = i === S.setSel, cur = st[2].filter(function (o) { return o[0] === cfg(st[0]); })[0] || st[2][0], val = lang === "tr" ? cur[2] : cur[1];
      lines.push([sel ? COL.sel : null, [seg(1, half2 - 2, lang === "tr" ? st[1][1] : st[1][0], sel ? "y" : "w"), seg(half2, half2, (sel ? "◄ " : "  ") + val + (sel ? " ►" : ""), sel ? "y" : "c")]]);
    });
    lines.push(blank()); lines.push(text(" " + SETTINGS[S.setSel][3][lang === "tr" ? 1 : 0], "g"));
    while (lines.length < 19) lines.push(blank());
    lines.push(text(T("setHint"), "c"));
    subs = [{ban: [up(T("settings")), "SkorText"], bg: ["b", "w"], head: text("MENU", "d"), lines: lines}];
  } else if (t === "news") subs = newsSubpages();
  return subs.length ? subs : [{ban: ["", ""], bg: ["b", "w"], head: blank(), lines: []}];
}
function wrap(s, w) { var out = [], line = ""; (s || "").split(/\s+/).forEach(function (word) { if (!line) line = word; else if ((line + " " + word).length <= w) line += " " + word; else { out.push(line); line = word; } }); if (line) out.push(line); return out; }
function newsSubpages() {
  var C = G.cols, f = feedByPage(S.page), title = trUpper(T("cNEWS") + " · " + f.name), lt = new Date((f.tLoad || Date.now() / 1000) * 1000);
  var head = [null, [seg(0, C - 18, f.source, "c"), seg(C - 17, 17, T("stand") + " " + two(lt.getHours()) + ":" + two(lt.getMinutes()), "c", null, "r")]];
  var lines;
  if (!f.items.length) {
    lines = (f.loading || !f.tLoad) ? [blank(), text(T("loading"), "y")] : [blank(), text(T("noData"), "r"), text(T("noData2"), "c"), blank(), text(fit(f.error || "", C), "d")];
    return [{ban: [title, ""], bg: ["m", "k"], head: head, lines: lines}];
  }
  var n = f.items.length;
  if (S.newsOpen !== null) {
    var it = f.items[S.newsOpen]; lines = [blank()];
    wrap(it.title, C - 2).slice(0, 4).forEach(function (l) { lines.push(text(" " + l, "y")); });
    if (it.ts) { var d = new Date(it.ts * 1000); lines.push(text(" " + dayLabel(it.ts) + " " + two(d.getHours()) + ":" + two(d.getMinutes()), "d")); }
    lines.push(blank());
    var room = 19 - lines.length, body = wrap(it.desc, C - 2);
    if (body.length > room) { body = body.slice(0, room); body[room - 1] = body[room - 1].slice(0, C - 4) + " …"; }
    body.forEach(function (l) { lines.push(text(" " + l, "w")); });
    while (lines.length < 19) lines.push(blank());
    lines.push(text(T("articleHint"), "c"));
    return [{ban: [title, (S.newsOpen + 1) + "/" + n], bg: ["m", "k"], head: head, lines: lines}];
  }
  var per = 18, subs = []; S.sub = Math.floor(S.newsSel / per);
  for (var st = 0; st < n; st += per) {
    lines = [];
    for (var i = st; i < Math.min(n, st + per); i++) {
      var x = f.items[i], sel = i === S.newsSel, tm = "";
      if (x.ts) { var dt = new Date(x.ts * 1000); tm = two(dt.getHours()) + ":" + two(dt.getMinutes()); }
      lines.push([sel ? COL.sel : null, [seg(0, 5, tm, sel ? "y" : "d"), seg(6, C - 6, fit(x.title, C - 6), sel ? "y" : "w")]]);
    }
    while (lines.length < 19) lines.push(blank());
    lines.push(text(T("newsHint"), "c"));
    subs.push({ban: [title, ""], bg: ["m", "k"], head: head, lines: lines});
  }
  return subs;
}
function buildRows() {
  var C = G.cols, subs = subpages(); if (S.sub >= subs.length) S.sub = 0;
  var sp = subs[S.sub], now = new Date(), rows = [];
  var pg = S.entry ? "P" + (S.entry + "---").slice(0, 3) : "P" + S.page;
  var date = T("days")[now.getDay()] + " " + two(now.getDate()) + "." + two(now.getMonth() + 1) + ".  " + two(now.getHours()) + ":" + two(now.getMinutes()) + ":" + two(now.getSeconds());
  var h = [seg(0, 5, pg, S.entry ? "y" : "w", null, "l", !!S.entry), seg(6, 9, "SkorText", "y")];
  if (S.page !== 100) h.push(seg(17, C - 40, T("home"), "c"));
  h.push(seg(C - 22, 22, date, "y", null, "r"));
  rows.push([null, h]);
  var goal = null, ns = Date.now() / 1000;
  for (var i = STORE.goals.length - 1; i >= 0; i--) if (ns - STORE.goals[i][0] < 8 && STORE.goals[i][0] > S.openedAt) { goal = STORE.goals[i][1]; break; }
  if (Date.now() < S.msgUntil) rows.push([COL.w, [seg(1, C - 2, S.msg, "k")]]);
  else if (goal) {
    var lg = STORE.byUt[goal.ut], m = goal.min + (/^\d/.test(goal.min || "") ? "'" : "");
    var txt = T("goal") + "  " + m + "  " + goal.h + " " + (goal.hs || 0) + ":" + (goal.as || 0) + " " + goal.a;
    rows.push([S.blinkOn ? COL.y : COL.k, [seg(1, C - 22, fit(txt, C - 22), S.blinkOn ? "k" : "y"), seg(C - 21, 20, fit(lg ? lg.name(cfg("lang")) : "", 20), S.blinkOn ? "k" : "y", null, "r")]]);
  } else {
    var bg = sp.bg[0], fg = sp.bg[1];
    if (modern()) { fg = bg; bg = "card"; }
    var right = sp.ban[1] + (subs.length > 1 ? "  " + (S.sub + 1) + "/" + subs.length : "");
    rows.push([COL[bg], [seg(1, C - 2 - right.length - 1, fit(sp.ban[0], C - 3 - right.length), fg), seg(C - 1 - right.length, right.length, right, fg, null, "r")]]);
  }
  rows.push(sp.head || blank());
  var body = sp.lines.slice(0, 20); while (body.length < 20) body.push(blank());
  rows = rows.concat(body);
  var F = T("fast"), q = Math.floor(C / 4);
  rows.push([null, [seg(0, q - 1, F[0], "w", "r", "c"), seg(q, q - 1, F[1], "k", "g", "c"), seg(2 * q, q - 1, F[2], "k", "y", "c"), seg(3 * q, C - 3 * q, F[3], "w", "b", "c")]]);
  return rows;
}
function draw() {
  COL = modern() ? PAL_MOD : PAL_TT;
  var rows;
  try { rows = buildRows(); } catch (e) { rows = [[null, [seg(0, G.cols, "SkorText: " + e, "r")]]]; }
  var mod = modern(), pbg = mod && cfg("bg") !== "navy" ? COL.bg : (PAGE_BG[cfg("bg")] || "#000");
  document.body.style.background = pbg;
  var font = mod ? "SkorSans" : "SkorMono";
  scr.style.fontFamily = '"' + font + '", "DejaVu Sans Mono", monospace';
  scr.style.fontSize = G.fs + "px";
  for (var i = 0; i < 24; i++) {
    var r = rows[i] || [null, []], rbg = r[0], segs = r[1], bgc = rbg !== null ? rbg : pbg, rounded = false;
    if (mod) {
      if (rbg === null && i === 0) bgc = COL.hdr;
      else if (rbg === null && i >= 3 && i <= 22 && segs.some(function (s) { return s[2]; })) { bgc = i % 2 ? COL.zebra1 : COL.zebra2; rounded = true; }
      else if (rbg !== null) rounded = true;
    }
    var el = rowEls[i];
    el.style.background = bgc; el.style.borderRadius = rounded ? Math.max(3, Math.floor(G.rowH / 4)) + "px" : "0";
    el.style.boxShadow = (mod && rbg === COL.sel) ? "inset " + Math.max(4, Math.floor(G.cw * 0.45)) + "px 0 0 " + COL.y : "none";
    var html = "";
    segs.forEach(function (s) {
      var x = Math.floor(s[0] * G.cw), w = Math.floor(s[1] * G.cw) + 2, txt = (s[6] && !S.blinkOn) ? "" : s[2];
      if (x >= G.pw) return; w = Math.min(w, G.pw - x);
      html += '<div class="sg ' + (s[5] === "r" ? "r" : s[5] === "c" ? "c" : "") + '" style="left:' + x + "px;width:" + w + "px;color:" + COL[s[3]] +
        (s[4] ? ";background:" + COL[s[4]] : "") + '">' + esc(txt) + "</div>";
    });
    el.innerHTML = html;
  }
  // Wechselkurs auf der Uebersicht
  if (S.page === 100 && !S.entry) {
    rateEl.style.display = "flex"; rateEl.style.fontFamily = scr.style.fontFamily;
    rateEl.firstChild.style.fontSize = Math.floor(G.fs * 1.3) + "px"; rateEl.lastChild.style.fontSize = G.fs + "px";
    rateEl.firstChild.style.color = COL.y; rateEl.lastChild.style.color = COL.d;
    if (RATE.value === null) { rateEl.firstChild.textContent = "1 € = … ₺"; rateEl.lastChild.textContent = ""; }
    else {
      rateEl.firstChild.textContent = "1 € = " + RATE.value.toFixed(2).replace(".", ",") + " ₺";
      var dd = RATE.date.length >= 10 ? RATE.date.slice(8, 10) + "." + RATE.date.slice(5, 7) + "." : "";
      rateEl.lastChild.textContent = (RATE.src === "ezb" ? (cfg("lang") === "tr" ? "AMB" : "EZB") : "Kurs") + " " + dd;
    }
  } else rateEl.style.display = "none";
}

/* ================= Takt ================= */
function tick() {
  S.blinkOn = !S.blinkOn;
  var now = Date.now() / 1000;
  if (S.entry && Date.now() - S.entryAt > 4000) S.entry = "";
  if (!STORE.loadingLive && now - STORE.tLive > +cfg("refresh")) fetchLive();
  var lg = STORE.leagueByPage(S.page); if (lg) needLeague(lg);
  var f = feedByPage(S.page); if (f) needFeed(f);
  needRate();
  if (cfg("rotate") === "10" && !f && pageType(S.page) !== "res" && Date.now() - S.lastRot > 10000) {
    S.lastRot = Date.now(); var n = subpages().length; if (n > 1) S.sub = (S.sub + 1) % n;
  }
  draw();
}

/* Fernbedienung: die Android-Huelle ruft skorKey(...) auf; im Browser gehen auch Tasten */
window.skorKey = function (k) { try { return key(k) || ""; } catch (e) { return ""; } };
var KB = {ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right", Enter: "ok", Escape: "back", Backspace: "back",
  r: "red", g: "green", y: "yellow", b: "blue", m: "menu", i: "info", PageUp: "chup", PageDown: "chdn"};
document.addEventListener("keydown", function (e) {
  var k = /^[0-9]$/.test(e.key) ? e.key : KB[e.key]; if (!k) return;
  e.preventDefault(); window.skorKey(k);
});

layout();
var sp0 = cfg("startpage"); S.page = /^\d+$/.test(sp0) ? +sp0 : 100;
go(S.page);
fetchLive();
draw();
setInterval(tick, 500);
try { document.fonts && document.fonts.ready.then(draw); } catch (e) {}
window.__skor = {S: S, STORE: STORE, FEEDS: FEEDS, RATE: RATE, draw: draw, key: key, parseFeed: parseFeed, parseEvent: parseEvent, G: G};
})();
