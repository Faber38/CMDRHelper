# Gemeinsame lokale Märkte und Mining

## Fachliche Korrektur und Schema

Marktstände sind gemeinsames lokales Wissen der Installation. MarketID identifiziert
den Markt; FID bleibt die Herkunft der Beobachtung, kein Zugriffsfilter. Kaufen,
Verkaufen, Empfehlungen und Mining verwenden denselben aktuellen vollständigen
Stand. Ein leerer neuer Stand verdrängt daher auch ältere Preise anderer FIDs.

Die kleinste saubere persistente Änderung ist MarketStore-Schema **2**:
`current_markets` hat den Primärschlüssel `market_id` statt `(fid, market_id)`.
Seine Fremdschlüssel sichern weiterhin die tatsächliche Beobachter-FID. Alters-/
Systemindizes beginnen nicht mehr mit FID. Die übrigen Tabellen und die historischen
Beobachtungen behalten ihre Herkunft. Die App-Version bleibt unverändert;
`cmdrhelper.db` bleibt Schema **20**.

Schreibzugriffe ersetzen den aktuellen Zeiger nur durch einen neueren Zeitstempel;
bei identischer Zeit gewinnt deterministisch die lexikographisch kleinere FID,
unabhängig von der Import-/Ankunftsreihenfolge. Beide Beobachtungen bleiben erhalten.
Widersprüchliche Wiederholungen derselben FID/MarketID/Zeit bleiben ein Fehler.

Ein schreibend geöffneter Schema-1-Store wird in einer Transaktion aktualisiert:
aktuelle Zeigertabelle/Indizes neu aufbauen, neuesten gültigen Stand pro MarketID
per SQL bestimmen, Revision und Schema-Version erhöhen. Keine Beobachtungen oder
Warenlisten werden dafür gelöscht oder vollständig nach Python geladen. Fehler
rollen den gesamten Upgrade zurück; read-only Leser führen keine Migration aus.
Importierte zukünftige Zeitstempel bleiben zur verlustfreien Dokumentation als
Beobachtung erhalten, sind aber kein gültiger aktueller Stand und verdrängen
keine tatsächlich gültige Beobachtung.

## APIs, JSON und Aufbewahrung

Aktuelle APIs ohne FID-Zugriffsparameter:

- `get_current(market_id, max_age)`
- `get_current_headers(market_ids, max_age)`
- `query_current_candidates(commodity=None, ...)`
- `best_sell_prices(commodities, scope='current', max_age=..., min_demand=1)`

Ergebnisse tragen weiterhin die Beobachter-FID. Historische Detail-/Verlaufs-APIs
können weiter nach Beobachter-FID filtern; kein aktueller Handels-/Mining-Leser
verwendet diese Herkunftsfilter. Schiff, Cargo und Aufenthaltskontext bleiben
commanderbezogen. Der aktuell angedockte Commander muss einen Stationsmarkt jedoch
nicht selbst beobachtet haben, um einen gültigen gemeinsamen Stand zu verwenden.

Die JSON-Migration importiert alle FID-Beobachtungen, prüft die vollständigen
Payloads und erwartet getrennte Anzahlen für Beobachtungen und gemeinsame aktuelle
Märkte. Bei gleicher MarketID entscheidet `observed_at`, nicht die Listenreihenfolge.
Schema-1-Upgrade und JSON-Migration lassen die Original-JSON unverändert. Der
bisherige frühe JSON-Lesefallback bildet ebenfalls gemeinsame Gewinner je MarketID;
nach Aktivierung bleibt jeder JSON-Rückfall gesperrt.

Cleanup schützt den neuesten gemeinsamen Stand pro MarketID dauerhaft. Nur
zusätzliche Beobachtungen außerhalb von 30 Tagen werden gelöscht. Jüngere
Beobachtungen verschiedener FIDs bleiben in der Historie sichtbar. Die globale
Speicherstatuszahl zählt die eindeutigen lokal gespeicherten Stationen über die
`stations`-Primärschlüssel, einschließlich erhaltener reiner Herkunftsdaten.

## Mining: Datenweg und Darstellung

Vorher: fester Katalog, feste Referenzpreise, rekonstruierter Commanderbestand.
Nachher zusätzlich: eine Spalte **Eigener Verkaufspreis / t** mit dem besten
lokal beobachteten `commander_sell_price`. Der Tooltip enthält System, Station,
Beobachtungszeit, Alter, Nachfrage und das ausgewählte Handels-Alterslimit.
Unverändert bleiben Referenzpreis, Wertklasse, Bestände, Carrier-Merkwerte und
bestehende Suchaktionen. Marktangebot/Nachfrage werden niemals als Bestand benutzt.

Ein Hintergrundworker ruft `best_sell_prices()` einmal für die 57 Katalogidentitäten
auf. Intern sind das 57 indexgestützte Identitätsauflösungen und 57 gezielte
Bestpreisabfragen in einer konsistenten Lesetransaktion, keine vollständigen
Stations-/Warenlisten in Python. Höchstens ein Ergebnis je Ware wird zurückgegeben.
Es gilt der bestehende Wert `trade/max_age_hours`, einschließlich exakter Grenze;
„Kein Limit“ ist explizit unbegrenzt. Historie wird nicht als aktuelle Quelle gelesen.
Positiver Preis und positive Nachfrage sind Voraussetzung. Nachfrage 0 liefert
keinen nutzbaren Bestpreis. Unbekannte Nachfrage lässt das bestehende
Beobachtungsschema nicht zu; sie wird nicht erfunden.

Kein Commanderwechsel schränkt diesen gemeinsamen Preisbestand ein. Es wird
insbesondere keine Commander-FID aus der Commander-DB nachgeladen. Fehlende DB
liefert „—“, ein Lesefehler zusätzlich einen sichtbaren Hinweis und Logeintrag;
Referenzen und Bestände bleiben nutzbar. Es gibt keinen Spansh-/JSON-Ersatzpfad.

Der Controller bündelt Änderungen, verwirft überholte Generationen, liest nur bei
sichtbarem Mining-Reiter und bricht überholte Abfragen kooperativ ab. Gemeinsame
Commit-, Commander- und Altersfilteränderungen aktualisieren die Zusatzpreise.
Ein Ablauf-Timer entfernt zu alte Ergebnisse; die GUI prüft das Alter nochmals
vor Darstellung. Tooltip-Alter wird ohne SQL aktualisiert. Sämtliche DB-Arbeit
und Verbindungsöffnung bleiben im Worker. Bestehende Spaltenlayouts werden unter
Beibehaltung ihrer Breiten/Reihenfolge um die neue Spalte erweitert.

## Performance und Prüfung

`tools/benchmark_mining_market.py` erzeugt ausschließlich temporäre synthetische
Daten: 57 Waren, vier Beobachter-FIDs, zusätzliche ältere Beobachtungen derselben
MarketIDs. Je Stationszahl ein frischer Prozess; warme Abfragen siebenmal,
GUI-Aktualisierung 30-mal. Netzwerkzugriffe sind gesperrt. Query-Trace: **114 SELECTs
pro Batch**, maximal **57 zurückgegebene Preise**; vollständige Payload-Lader sind
während der Prüfung gesperrt.

| Stationen | Batch Median / Maximum | GUI Median | Python-Peak |
|---:|---:|---:|---:|
| 100 | 1.48 / 2.55 ms | 0.76 ms | 73.9 KiB |
| 1000 | 1.49 / 2.58 ms | 0.76 ms | 80.6 KiB |
| 5000 | 1.67 / 2.53 ms | 0.84 ms | 80.7 KiB |

Ende-zu-Ende inklusive 100-ms-Debounce und Zeichnen: etwa 158–161 ms bei Refresh,
182–190 ms beim ersten Anzeigen. Maximaler Abstand eines 5-ms-GUI-Timers beim
Refresh: 28–31 ms; beim ersten Zeichnen mit Layout/Fonts: 57–60 ms. Diese
Offscreen-Qt-Zeichenkosten sind getrennt von den oben gemessenen DB-/Rendercallbacks.
Ein gezielt blockierter Worker-Test bestätigt weiterhin laufende GUI-Timer und
verwirft Ergebnisse eines inzwischen überholten Altersfilters.

Neue Tests decken gemeinsame aktuelle Märkte, Herkunftshistorie, spätere/ältere
Beobachtungen, deterministische Gleichstände, neueste leere Stände, Schema-1-Upgrade
und Rollback, alle FIDs in der JSON-Migration, Cleanup, zukünftige Imports,
Kaufen/Verkaufen/Empfehlungen/Mining über Commander hinweg sowie Mining-Altersgrenzen,
Null-/unbekannte Nachfrage, fehlende/fehlerhafte DB, Batchgrenze, unveränderte
Referenzen/Bestände und bestehende Spaltenlayouts ab.

## Dateien

Store/Migration/Writer, gemeinsamer Cache-/Handelslesepfad und Empfehlungen;
neu `mining_market.py` und `mining_market_controller.py`; Mining-Tabelle und
Handels-Alterssignal; zwölf Mining-i18n-Ergänzungen; gemeinsame Markt-/Mining-Tests,
angepasste bisherige API-/FID-Tests und Benchmarkskripte.

Der zusätzlich beauftragte Empfehlungshinweis ist ausschließlich Darstellung:
`ui/recommendations_view.py`, `ui/styles.py`, je zwölf i18n-/Handelshilfekataloge
und der Layouttest in `test_recommendations_view.py`. `<small>` verwendet eine
relative Schriftstufe ohne feste Punktgröße. Rahmen und Text sind im Dark-/Light-
Stylesheet gelb/orange; der Hinweis steht nur über den Empfehlungsfiltern.
Cargo-, Such-, Checkbox- und Merklogik werden durch ihn nicht geändert.

## Abschlussprüfung

Gemeinsame Regression nach allen Änderungen: **832 Tests, 831 bestanden,
1 optionaler Test mit externer Referenzdatenbank bewusst übersprungen**.
Enthalten sind Store/Migration/Writer, Handel/Empfehlungen/Merkziele/Cargo,
Mining/Materialien/Commanderansicht, Startup und lokalisierte Hilfen.
Netzwerkverbindungen wurden im Testprozess gesperrt, App-Daten und Einstellungen
isoliert; sämtliche Markt-/Journalfixtures sind temporär und synthetisch.

Der Hinweis-Layouttest prüft 12 Sprachen × Dark/Light × 10/18/24 pt × schmal/breit,
relative Schrift ohne feste Punktgröße, Höhe/Umbruch und korrekte Platzierung.
Die ergänzte Prüfung der Sichtbarkeit nur im Empfehlungsreiter bestand ebenfalls.
Dark 10 pt/breit und Light 24 pt/schmal wurden zusätzlich anhand gerenderter
Qt-Aufnahmen visuell geprüft. Keine Such-/Cargo-/Merklogikänderung durch den Hinweis.

`git diff --check`: sauber. Kein Commit, Push, Tag oder Release.
