# v3.8: Kaufen und Verkaufen lesen MarketStore

Aktueller Folgestand: [gemeinsame lokale Märkte, Schema 2 und Mining](shared-markets-mining.md).
Die früheren Phasenmessungen und FID-Verträge unten sind historische Dokumentation;
für aktuelle Lese-APIs, Migration und Aufbewahrung gilt der verlinkte Folgestand.

Phasenbericht Kaufen/Verkaufen. Die nachfolgende Umstellung der Empfehlungen und
die Freigabe der vollständigen Übergangsprojektion sind in
[Empfehlungen über MarketStore](recommendations-market-store.md) dokumentiert.

## Datenweg und Fachsemantik

TradeView.start_search kopiert keine Marktlisten mehr und ruft weder cache.all()
noch local_distances() auf. prepare_trade_source übergibt nur Pfade,
FID, Ursprungssystem und gegebenenfalls das Initialisierungs-Future.
Der vorhandene MarketWorker öffnet seine eigene read-only SQLite-Verbindung.
Auch die bestehende Koordinatenauflösung erfolgt mit eigener read-only
Commander-DB-Verbindung im Worker, ohne Schemaänderung oder Online-Abfrage.

TradeMarketSource liest pro Seite höchstens 500 aktuelle Stationsheader plus
genau die gesuchte Commodity. Historie und vollständige Warenlisten bleiben
ungelesen. Der Zeitanker wird nach der Provider-Antwort einmal bestimmt und für
sämtliche Seiten festgehalten. Der Revisionsvertrag verhindert, dass zwischen
Seiten geänderte Marktstände unbemerkt als konsistentes Ergebnis ausgegeben werden.
Bei Revisionswechsel/DB-Fehler liefert der vorhandene Worker den bestehenden
Fehlerstatus; kein teilweise zusammengeführtes Ergebnis wird veröffentlicht.

Candidate-Abfragen verwenden absichtlich **keinen BUY-/SELL-Vorfilter**:
Ein aktueller kompletter Markt ohne die gesuchte Ware oder mit Nullpreis/
ungenügendem Bestand muss ein älteres Spansh-Angebot verdrängen können.
Pro Kandidat entsteht dafür ein schmales Snapshot-Objekt mit null oder einer
Warenzeile. Die vorhandenen local_offer(), merge_destinations(),
matches_location() und die unveränderte Sortierung/Limitierung entscheiden
weiterhin über Quellenwahl und Handelbarkeit.

Erhalten bleiben FID/MarketID, Altersgrenze inklusive exakter Grenze, lokale
Priorität bei gleichem Zeitstempel, Buy/Sell, Supply/Demand, Radius, Stationstyp,
Carrier-Filter sowie unbekannte Landeplatz-/Ankunftsdaten. Diese Metadaten werden
weiterhin nicht aus dem Stationstyp geraten. Lokale Koordinaten werden mit
dem bestehenden Resolver ermittelt; gleiche bekannte SystemAddress bedeutet null
Lichtjahre. Planetare Stations-/Körperinformationen, Merkliste, Clipboard und
Datenalterdarstellung benutzen unverändert die bestehenden MarketOffer-Objekte.

Spansh bleibt unverändert zusätzlicher Provider. Ein Abbruch wird vor Providerstart,
zwischen DB-Seiten, pro Kandidat und über SQLite-progress_handler geprüft.
Das Warten auf eine laufende Migration erfolgt ebenfalls abbrechbar im Worker.

## Verbleibender Übergangscode

Der anschließende [Übergangsabschluss](market-transition.md) entfernt die
vollständige Writer-Projektion und stellt die Statusanzeige auf DB + WAL + SHM um.
Auch Empfehlungen lesen nun direkt MarketStore. Der Listenpfad dient dem
JSON-Lesefallback vor erfolgreicher Aktivierung und den A/B-Tests. Nach Aktivierung
führen DB-Fehler zu Fehlerstatus/Logging, niemals zu alten JSON-Angeboten.
Mining, Version und Commander-Schema bleiben unverändert.

## A/B-Prüfungen

Identische synthetische Bestände werden durch den bisherigen Cache-/Listenpfad
und den MarketStore-Pfad gesucht. Verglichen wird das vollständige Suchergebnis
einschließlich aller Offer-Felder, Reihenfolge, Quellenentscheidung, Status und
Truncated-Flag. Abgedeckt: beide Richtungen, FIDs, Grenzzeiten, alte Stände,
fehlende Waren, Nullpreise, Mengen, neuere/ältere/gleich alte Spansh-Angebote,
Providerfehler, Planetary/Carrier/Outpost, Landeplatz, Ankunft, Entfernung,
mehrere Seiten und Ergebnislimits.

Zusätzliche Tests verbieten cache.all() und vollständige Store-Payloads im neuen
Pfad, prüfen tatsächliche Worker-Threadöffnung, Abbruch bei laufender Migration
und verwerfen zwischenzeitlich veränderte Revisionen.
Bestehende UI-Tests für Kaufen/Verkaufen, Merkliste, Clipboard, Stationskörper
und Altersdarstellung werden weiterverwendet.

## Reproduzierbare Performance-Messung

```sh
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 venv/bin/python tools/benchmark_trade_store.py > /tmp/trade-store.json
```

Temporäre synthetische Märkte: 100/500/1.000/5.000 Stationen mit jeweils 350 Waren,
ein aktueller vollständiger Stand je Station, lokal gespeicherte Koordinaten.
Spansh liefert ausschließlich eine gemockte leere Antwort. Jeder alte/neue Pfad
läuft in einem eigenen Prozess, beide Richtungen je fünfmal. Resultate werden
auch im Benchmark auf dieselben 100 Angebote in derselben Reihenfolge geprüft.

Gemessen werden die bisherigen GUI-Vorbereitungsoperationen (Cache-Kopie und
Entfernungen) gegen die neue reine Pfad-/Parameterübergabe, die Laufzeit des
tatsächlichen Qt-Suchworkers und die Gesamtdauer bis zur Rückgabe an den GUI-Thread.
Widget-Erstellung und Ergebnis-Tabellenrendering liegen außerhalb dieser Messung.
Ein GUI-Timer mit 10-ms-Intervall protokolliert zusätzlich den größten Abstand
zwischen Ausführungen. Das ist keine Simulation eines langsamen PCs.

Beim alten Pfad wird der bestehende Cache-Speicherbestand vor der Messung aus
synthetischen Ständen aufgebaut. 5.000 Stationen überschreiten die ursprünglichen
JSON-Limits: Dieser Vergleich misst den bisherigen Kopier-/Suchalgorithmus
beziehungsweise die heutige Kompatibilitätsprojektion, keinen zulässigen
5.000-Stationen-Import durch den alten begrenzten JSON-Loader.

Die neue Messung lädt keine Empfehlungsprojektion; cache.all() und
MarketStore._payload() sind dort mit fehlschlagenden Guards versehen.
RSS-Werte sind /proc-Stichproben im jeweiligen Prozess inklusive Qt/Python/
SQLite und können Allocator-Reste enthalten. Sie sind weder eine isolierte
Python-Heap-Messung noch der gesamte App-RAM mit noch aktiven Empfehlungen.

## Ergebnisse vom 26.09.2026

Python 3.12.3 / SQLite 3.45.1, Linux, Qt offscreen. Fünf Wiederholungen
je Richtung/Pfad. Zeiten **Median / Maximum in ms**.

| Stationen | Richtung | GUI alt | GUI neu | Worker alt | Worker neu | Übergabe gesamt alt | Übergabe gesamt neu |
|---:|---|---:|---:|---:|---:|---:|---:|
| 100 | Kaufen | 82.39 / 100.26 | 0.03 / 0.03 | 3.78 / 4.36 | 3.21 / 22.03 | 86.63 / 104.09 | 3.40 / 22.27 |
| 100 | Verkaufen | 82.21 / 83.68 | 0.03 / 0.04 | 3.82 / 3.92 | 2.91 / 3.68 | 86.26 / 87.38 | 3.05 / 3.82 |
| 500 | Kaufen | 435.74 / 448.96 | 0.03 / 0.04 | 17.02 / 18.90 | 13.69 / 33.54 | 452.68 / 467.49 | 13.85 / 33.76 |
| 500 | Verkaufen | 434.25 / 442.66 | 0.03 / 0.04 | 18.37 / 19.10 | 13.24 / 14.08 | 451.70 / 461.59 | 13.42 / 14.29 |
| 1000 | Kaufen | 923.33 / 945.50 | 0.03 / 0.04 | 34.71 / 37.37 | 27.19 / 45.77 | 956.25 / 983.21 | 27.39 / 46.04 |
| 1000 | Verkaufen | 906.20 / 926.70 | 0.03 / 0.03 | 34.72 / 35.15 | 26.04 / 27.69 | 940.32 / 961.63 | 26.19 / 27.88 |
| 5000 | Kaufen | 5131.82 / 5196.07 | 0.03 / 0.04 | 249.69 / 262.30 | 139.66 / 157.26 | 5380.66 / 5393.32 | 139.89 / 157.49 |
| 5000 | Verkaufen | 5152.70 / 5178.94 | 0.03 / 0.04 | 241.52 / 248.27 | 138.70 / 140.97 | 5393.20 / 5422.82 | 138.92 / 141.20 |

Bei 5.000 Stationen und 1,75 Millionen Warenzeilen:

- GUI-Timer: maximal 5.196 ms Abstand im alten Pfad, 15,14 ms im neuen Pfad.
- Alter Prozess: vor Suche 983,3 MiB RSS, nach Suche bis 1.552,4 MiB;
  zusätzlich rund 569 MiB für Kopier-/Sucharbeit und Allocator-Reste.
- Neuer Prozess ohne Empfehlungsprojektion: vor Suche 99,9 MiB, nach Suche
  113,9 MiB; Zuwachs rund 14 MiB inklusive DB-Seiten und Ergebnisobjekten.
- Alle A/B-Ergebnislisten waren identisch. Im neuen Prozess waren
  vollständige Payload-Ladevorgänge und cache.all() ausdrücklich gesperrt.

Die ersten neuen Workersuchen enthalten zusätzlich einmalige Import-/Cachekosten;
deshalb liegen einige Maxima über den Medianen. Gesamtsuche bei 5.000 Stationen
rund 139 ms: weiterhin Worker-Arbeit, keine Freigabe für GUI-Ausführung.
Die frühere Vollkopie verursachte hier bereits bei 500 Stationen etwa 435 ms
GUI-Arbeit und bei 1.000 rund 0,9 Sekunden. Keine Aussage über langsamere CPUs
oder gesamte Empfehlungs-/Startup-Performance wird daraus abgeleitet.

## Verifikation

210 gezielte Tests bestanden, verteilt auf den erweiterten Handels-/Store-Lauf,
die bestehenden 38 Verkaufen-UI-Tests und den ergänzenden Aktivierungsvertrag.
Dazu gehören Tests der unveränderten Empfehlungs-Alterskopplung, Merkliste,
Clipboard und planetaren Stationskörper. Die bisherigen UI-Fixtures für lokale
Handelssuchen migrieren ihren temporären JSON-Bestand nun ausdrücklich in eine
temporäre DB.

Eine zusätzliche read-side-Eigenschaft am Writer meldet, ob der Store tatsächlich
aktiviert wurde. Ein fertig fehlgeschlagenes Startup-Future darf nicht einfach
ignoriert werden: Solange keine Aktivierung erfolgte, propagiert die Suche diesen
Fehler, statt einen eventuell vorhandenen unmarkierten Store zu lesen.
Nach erfolgreicher Wiederholung ist eine neue Suche möglich.

Keine produktiven Daten, keine Live-Netzabfragen; Spansh bleibt in den Tests
gemockt. git diff --check und Whitespace-Prüfung der neuen Dateien ohne Befund.
