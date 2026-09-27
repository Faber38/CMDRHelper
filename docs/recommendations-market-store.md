# v3.8: Empfehlungen lesen MarketStore

Aktueller Folgestand: [gemeinsame lokale Märkte, Schema 2 und Mining](shared-markets-mining.md).
Die früheren Phasenmessungen und FID-Verträge unten sind historische Dokumentation;
für aktuelle Lese-APIs, Migration und Aufbewahrung gilt der verlinkte Folgestand.

Stand: 26.09.2026. Version unverändert, Commander-Schema 20 und MarketStore-Schema 1.
Mining bleibt unverändert. Der nachfolgende [Übergangsabschluss](market-transition.md)
stellt auch die Statusanzeige um.

## Datenweg

RecommendationsView übergibt nur den aktuellen Stationsheader, Suchparameter und
Store-Pfade. Kein cache.all(), kein cache.get(), keine Koordinaten-/Markt-DB-Abfrage
in der GUI-Vorbereitung oder in Fortschrittscallbacks. Der Worker wartet bei Bedarf
auf die Aktivierung, öffnet eigene read-only Verbindungen und lädt den vollständigen
Ausgangsmarkt genau einmal. Die Liste kaufbarer Waren wird einmal gebildet.

RecommendationStoreSession liest pro Ware höchstens 500 Kandidaten je Seite.
Dabei werden nur aktuelle Header und die benötigte Ware gelesen, keine vollständigen
Zielmarkt-Snapshots. Revision, FID, Altersgrenze und vollständige Snapshots bleiben
verbindlich. Koordinaten werden im Worker aufgelöst und je System wiederverwendet.
Revisionsänderungen/Abbruch liefern keine unbemerkt inkonsistente Ergebnismischung.

Je Ware bleiben höchstens 101 geeignete lokale Alternativen im Suchlauf gespeichert:
Die reguläre Spansh-Abfrage liefert höchstens 100 Märkte und kann daher höchstens
100 lokale Alternativen verdrängen. Ein Provider, der dieses Limit überschreitet,
löst eine erneute begrenzte Streaming-Auswertung aus. Spansh-MarketIDs werden zusätzlich
stapelweise ohne Preis-/Bestandsfilter abgefragt: Auch fehlende Waren und Nullpreise
im neuesten lokalen Snapshot müssen ältere Community-Angebote verdrängen können.
Die vorhandenen Merge-, Mengen-, Gewinn-, Standort- und Sortierfunktionen entscheiden.
Caches werden bei überschrittener Altersgrenze invalidiert. Wiederverwendete lokale
Angebote erhalten den aktuellen Abrufzeitpunkt; Spansh behält seinen Abrufzeitpunkt.

Der Store erhält optionale Filter market_ids/min_sell_price. Ein Eintrag je aktuellem
FID/MarketID in store_meta bewahrt die ursprüngliche Commodity-Reihenfolge, damit
stabile Ranggleichheiten dieselbe Reihenfolge wie im bisherigen Cache behalten.
Snapshot-Deduplizierung bleibt kanonisch; historische Payloads und Schema bleiben
unverändert. Ältere DBs ohne diese Metadaten behalten zunächst ihre bisherige
kanonische Reihenfolge, bis ein neuer aktueller Stand geschrieben wird.

## GUI und Übergang

Worker-Fortschritt/Diagnostik werden auf 100 ms gebündelt; der erste Providerstart
wird sofort gemeldet. GUI-Callbacks prüfen nur kleinen Kontext und aktualisieren
Fortschritt. Tabellenänderungen werden separat mit einem 100-ms-Timer zusammengefasst.
Der Abschluss übernimmt das endgültige Ergebnis und zeichnet es bei Bedarf einmal.
Keine Fortschrittsmeldung startet eine erneute Marktprojektion oder DB-Abfrage.
Merkliste, Mehrfachauswahl, Cargo-Restkapazität, Clipboard und Stationskörper bleiben
im bestehenden UI. Gemeinsame manuelle Merkliste-Aktionen sind kein Teil des Suchworkers.

Nach erfolgreicher SQLite-Aktivierung liefert der produktive Schreibworker nur noch
Stationsheader an den Übergangscache; dessen alte vollständige JSON-Projektion wird
freigegeben. Änderungen bleiben COMMIT-bestätigt. Legacy-Modus und Cache-Lesecode
bleiben für Übergang/Tests vorhanden; all() verweigert bewusst einen vermeintlich
vollständigen Preisbestand, wenn nur Header installiert sind.

Die Original-JSON bleibt unverändert als Migrationsquelle und Lesefallback vor
erfolgreicher Aktivierung erhalten. Nach Aktivierung ist ausschließlich MarketStore
maßgeblich; die Statusanzeige misst DB + WAL + SHM. Der Writer unterstützt keine
vollständige Warenprojektion mehr. Mining bleibt unverändert.

## Prüfung

294 unterschiedliche Tests aus den Empfehlungs-, MarketStore-, Migrations-, Handels-,
Alters-, Status-, Merkliste-, Clipboard-, Stationskörper- und kombinierten UI-Suiten
bestanden. Der abschließende gezielte Wiederholungslauf bestand mit 69 Tests.
Neue Tests vergleichen komplette synthetische Empfehlungsergebnisse einschließlich
Quellen, Reihenfolge, Mengen, Preise und Gewinne; sie prüfen FID, Altersgrenzen,
entfernte/fehlende Waren, Nullpreise/Bestände, Spansh-Überlagerungen, Ranggleichheiten,
101. lokalen Kandidaten, Ursprung genau einmal, buyable genau einmal, Query-Reuse,
Callback-Begrenzung und Header-Projektion ohne Zielmarkt-Payloads.
GUI-Regression: all(), get(), DB-Konstruktion und refresh() dürfen während des
Fortschrittscallbacks nicht aufgerufen werden.

## Reproduzierbare synthetische Messung

`QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 venv/bin/python tools/benchmark_recommendation_store.py`

Je Größe drei Wiederholungen in getrennten Prozessen, temporäre Datenbanken,
350 Waren je Station, davon 35 am Ausgangsmarkt kaufbar. Alle Ziele liegen im selben
bekannten System; keine produktive Koordinaten-DB, keine Netzwerkabfrage.
Spansh ist gemockt (keine Treffer); Quellenkonflikte werden in den A/B-Tests geprüft.
Neue Messung verwendet echte RecommendationsView, QThreadPool und Qt-Callbacks.
Der 10-ms-Qt-Timer läuft bis nach abschließender Tabellenanzeige/Zeichnen.

Der alte Vergleich rekonstruiert Cache-Vorbereitung und die zwei vollständigen
get()-Kopien je Fortschritt; komplette alte Berechnung wird nur bis 100 Stationen
ausgeführt. Das ist kein identischer vollständiger alter Qt-App-Lauf. Bei größeren
Beständen nutzt die separate A/B-Referenz die alte Fachlogik mit den 35 relevanten
Waren, außerhalb der Messzeit. Kein künstlich verlangsamter PC wurde simuliert.

Alle Zeitpaare: Median / Maximum in ms. „Gemischt“ erlaubt den gemockten Provider.

| Stationen / Warenzeilen | GUI alt | GUI neu | Ursprung | Kandidatenabfragen | Worker | Bis Ergebnisübergabe |
|---|---|---|---|---|---|---|
| 10 / 3500 | 16.39 / 17.58 | 1.20 / 1.68 | 1.97 / 1.98 | 4.69 / 4.81 | 14.74 / 15.20 | 15.73 / 16.49 |
| 100 / 35000 | 164.06 / 166.07 | 1.34 / 1.44 | 1.65 / 1.93 | 34.57 / 36.43 | 81.89 / 85.51 | 83.30 / 86.69 |
| 500 / 175000 | 953.73 / 969.73 | 1.24 / 1.28 | 1.71 / 1.73 | 195.22 / 199.30 | 346.21 / 349.89 | 347.57 / 351.36 |
| 1000 / 350000 | 1944.50 / 1966.03 | 1.22 / 1.34 | 1.92 / 1.92 | 459.58 / 479.61 | 743.42 / 769.91 | 744.41 / 771.33 |
| 5000 / 1750000 | 11002.87 / 11045.80 | 1.25 / 1.30 | 1.77 / 1.93 | 2541.91 / 2557.69 | 3864.53 / 3875.10 | 3865.55 / 3876.45 |

| Stationen | Callback alt | Callback neu (gemischt) | Callbacks gemischt | SELECTs / Kandidatenseiten | Qt-Abstand neu | Abschlusscallback |
|---|---|---|---|---|---|---|
| 10 | 16.59 / 16.61 | 0.10 / 0.12 | 3 | 112 / 35 | 20.66 / 28.72 | 9.76 / 18.28 |
| 100 | 166.20 / 167.29 | 0.10 / 0.11 | 3 | 112 / 35 | 19.38 / 33.36 | 10.80 / 20.62 |
| 500 | 961.48 / 964.10 | 0.22 / 0.24 | 5 | 113 / 35 | 17.27 / 21.67 | 9.57 / 20.14 |
| 1000 | 1919.94 / 1921.41 | 0.25 / 0.26 | 5 | 218 / 70 | 17.05 / 26.12 | 10.02 / 20.54 |
| 5000 | 10682.23 / 11097.80 | 0.22 / 0.23 | 5 | 1058 / 350 | 20.04 / 28.87 | 10.51 / 20.26 |

Callback-Zeit je Wiederholung ist der langsamste Fortschritts-/Diagnostikcallback; gezählt werden auch Diagnoseaufrufe innerhalb eines Fortschrittscallbacks. SELECTs enthalten Revisions-/Metadatenprüfungen. Ursprung: immer genau ein vollständiger Lesezugriff.

| Stationen | Worker nur eigene | Callback nur eigene | Callbacks nur eigene (Median / Max.) | Qt-Abstand nur eigene | RSS alt / neu gemischt (Maximum MiB) |
|---|---|---|---|---|---|
| 10 | 14.28 / 14.96 | 0.21 / 0.22 | 4.00 / 4.00 | 20.49 / 29.54 | 87.5 / 132.5 |
| 100 | 77.44 / 78.53 | 0.24 / 0.45 | 4.00 / 4.00 | 23.79 / 33.36 | 123.7 / 136.3 |
| 500 | 363.65 / 369.05 | 0.72 / 0.82 | 10.00 / 10.00 | 21.90 / 22.12 | 287.3 / 143.1 |
| 1000 | 806.97 / 851.25 | 0.66 / 0.73 | 16.00 / 18.00 | 20.28 / 24.02 | 492.0 / 153.0 |
| 5000 | 4224.36 / 4440.30 | 0.62 / 0.63 | 72.00 / 72.00 | 23.27 / 26.26 | 1961.7 / 174.1 |

RSS sind Prozess-Stichproben aus /proc, keine garantierten Spitzenwerte und keine
isolierten Python-Heapmessungen. Neue Prozesse enthalten zusätzlich das echte Widget
und können Speicherarenen der außerhalb der Messung erstellten A/B-Referenz halten.
Die Messung erlaubt daher keine exakte Zuweisung des gesamten RSS zum Suchlauf.
Bei 5.000 Stationen lag der neue Ausgangs-RSS nach Referenzbereinigung/Widgetaufbau
bei rund 176 MiB, die Stichproben während/nach der Suche bei höchstens 174 MiB
(Allocator-/Freigabeeffekte); alt rund 932 MiB vor und 1.962 MiB nach Cache-Kopien.

Der alte rekonstruierte Gesamtlauf benötigt bei 100 Stationen 7.617 / 7.682 ms,
passend zur bisherigen Größenordnung von 7,9 s. Alte Callback-Strecken: bei 500
Stationen 961 ms statt des früheren Befunds von 1.060 ms; bei 5.000 rund 10.682 ms
statt 12.140 ms. Es sind unterschiedliche Messläufe, keine identischen Bedingungen.

Neue Fortschrittscallbacks bleiben in beiden Modi unter 1 ms (Ziel <5 ms).
Größter gemessener Qt-Timerabstand inklusive Abschluss: 33,37 ms. Keine sekundenlange
GUI-Blockade im synthetischen Lauf; eine allgemeine Garantie für schwächere PCs folgt
daraus nicht. Bei 5.000 Stationen bleibt die Hintergrundsuche mit 3,9–4,4 s sichtbar
lang: 35 relevante Waren gegen bis zu 4.999 Ziele bedeuten etwa 175.000 Kandidaten,
350 begrenzte Seiten und bestehende fachliche Filter/Rangbildung. Es wird weder die
vollständige DB noch deren 1,75 Millionen Warenzeilen in Python projiziert.
