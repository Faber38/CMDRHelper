# SQLite-MarketStore – isolierter Prototyp für v3.8, Phase 2

Aktueller Folgestand: [gemeinsame lokale Märkte, Schema 2 und Mining](shared-markets-mining.md).
Die früheren Phasenmessungen und FID-Verträge unten sind historische Dokumentation;
für aktuelle Lese-APIs, Migration und Aufbewahrung gilt der verlinkte Folgestand.

Dieser Bericht dokumentiert den abgenommenen Phase-2-Stand samt damaligen
Messungen. Die anschließende Aktivierung, Migration und Schreibworker-Anbindung
sind in [market-migration.md](market-migration.md) beschrieben.

## Geltungsbereich

`cmdrhelper.market_store` wird noch von keinem produktiven Aufrufer verwendet.
Der Konstruktor verlangt einen expliziten Pfad. `market_store_path()` liefert erst
bei ausdrücklichem Aufruf
`QStandardPaths.AppDataLocation/market_cache/markets.db`; es erzeugt keine Datei.
Tests und Benchmark verwenden ausschließlich `TemporaryDirectory`.

Keine Migration, Observer-/Handels-/Mining-/UI-Anbindung, keine Versionsänderung.
Die bestehende `cmdrhelper.db` mit Schema 20 bleibt getrennt und unverändert.
Der Store importiert reine Normalisierungs-/Identitätshilfen aus
`observed_market_cache`, instanziiert aber keinen JSON-Cache und öffnet keine
produktive Marktdatei. Community-Daten werden als Eingabe zurückgewiesen.

## Schema 1

`PRAGMA user_version=1`, eigene `application_id=0x434D484D`.
Fremde, beschädigte oder unbekannt versionierte Datenbanken werden nicht ersetzt.

| Tabelle | Primärschlüssel | Beziehungen und Zweck |
|---|---|---|
| stations | market_id | Globale Marktidentität; keine Verdopplung je Besuch/FID |
| commodity_keys | commodity_key | Technische Identität aus Frontier-ID und kanonischem Symbol; unbekannte Symbole auch ohne ID |
| market_snapshots | snapshot_id | FK market_id → stations; FID/MarketID/Payload-Hash eindeutig |
| commodity_observations | snapshot_id, commodity_key | FK zu Snapshot (ON DELETE CASCADE) und Commodity; vollständige Warenwerte |
| market_observations | observation_id | Zusammengesetzter FK zu Snapshot/FID/MarketID; FID/MarketID/observed_at eindeutig |
| current_markets | fid, market_id | Zusammengesetzter FK zu Observation/FID/MarketID/observed_at; ein letzter Stand |
| store_meta | key | Revision und history_retention_days=30 |

Stationsname, System, SystemAddress und Stationstyp stehen an der Beobachtung:
Ein bewegter Carrier behält seine MarketID, seine historischen Standorte bleiben
korrekt. Die Stations-Tabelle enthält deshalb nur die stabile Identität.
`current_markets` hält Systemfilterfelder zusätzlich für gezielte Indexabfragen.
Der aktuelle Snapshot ist eindeutig über die referenzierte Beobachtung erreichbar.

Externe IDs, Preise und Mengen sind **acht Byte große Big-Endian-BLOBs** mit
Längen-/Typprüfungen. Damit bleiben alle bisher erlaubten unsigned-64-Bit-Werte
verlustfrei, einschließlich Werte über 2^63−1. Gleichheit, Bereich und Sortierung
verwenden dieselbe Kodierung; die Python-API liefert Integer. Keine REAL-Werte,
keine Fließkomma-Konvertierung. Zeiten sind UTC-Mikrosekunden als INTEGER,
ohne Umweg über einen float-Zeitstempel.

Indizes:

- Eindeutige Commodity-Identitäten, getrennt für bekannte IDs und reine Symbole.
- Snapshot-Deduplizierung nach FID/MarketID/Hash.
- Warenwerte nach Snapshot/Commodity sowie Snapshot/Ordinal.
- Commodity/Verkaufspreis/Snapshot und Commodity/Einkaufspreis/Snapshot.
- Beobachtungen nach FID/MarketID/Zeit, FID/Zeit, Snapshot/Zeit und Zeit/ID.
- Aktuelle Stände nach FID/MarketID, FID/Zeit/MarketID,
  FID/SystemAddress/MarketID, FID/Systemname/MarketID und MarketID/FID.
- Zusätzliche UNIQUE-Indizes sichern die zusammengesetzten Fremdschlüssel.

## Beobachtungen und Historie

Jede Beobachtung ist ein vollständiger Snapshot; fehlende Waren werden niemals
aus älteren Snapshots ergänzt. Nullpreise, Nullangebot und Nullnachfrage bleiben
gespeichert. Qualifizierte Kaufen-/Verkaufen-Abfragen schließen nicht handelbare
Zeilen ausdrücklich aus.

Der kanonisch sortierte Payload wird gehasht; identischer Inhalt derselben
FID/MarketID verwendet den vorhandenen Snapshot erneut. Vor Wiederverwendung
wird dessen Inhalt zusätzlich verglichen. Jede neue Beobachtungszeit erhält einen
eigenen Eintrag, auch bei unverändertem Payload. A → B → A verweist beim letzten
Besuch erneut auf Snapshot A. Ältere nachgelieferte Beobachtungen setzen den
aktuellen Stand nicht zurück. Gleiche Zeit und gleicher Inhalt/Kontext ist
idempotent; widersprüchlicher Inhalt oder Kontext löst `ObservationConflict` aus.

Verbindliche Aufbewahrung:

- Der letzte bekannte Stand **je FID/MarketID bleibt dauerhaft** erhalten,
  einschließlich seiner Beobachtung und seines vollständigen Snapshots.
- Zusätzliche Beobachtungen mit `observed_at < jetzt − 30 Tage` sind bereinigbar.
  Der exakte Grenzzeitpunkt bleibt erhalten.
- `cleanup(cancel=Event)` löscht diese Beobachtungen, danach ausschließlich
  unreferenzierte Snapshots samt Warenzeilen und verwaiste Commodity-Schlüssel.
- Eine Transaktion umfasst alle Löschungen und die neue Revision. Fehler,
  SQLite-Abbruch und kooperative Stornierung führen zum vollständigen Rollback.
- Kein Lesen, Schreiben oder Altersfilterwechsel startet Cleanup. Kein Timer.
- Bei vorhandener Qt-Anwendung wird Cleanup im Anwendungs-/GUI-Thread abgewiesen.
  Der spätere Aufrufer muss es in einen Worker legen und dort die Verbindung öffnen.
- SQLite darf freigegebene Seiten wiederverwenden. Cleanup verkleinert die Datei
  nicht zwingend; automatisches VACUUM ist ausdrücklich nicht enthalten.

Die 30 Tage begrenzen das historische Zeitfenster, nicht eine absolute Bytezahl
oder Besuchszahl innerhalb dieses Fensters. Bis zum expliziten Cleanup können
physisch ältere historische Zeilen vorhanden sein. Eine spätere regelmäßige
Worker-Ausführung ist für die tatsächliche Aufbewahrung nötig.

## API und Leseverträge

- `get_current(fid, market_id, max_age)`: Ein kompletter letzter Stand in einer
  konsistenten Lesetransaktion. `max_age=None` erhält auch sehr alte letzte Stände.
- `get_current_headers(fid, market_ids, max_age)`: Bis 500 gezielte Header ohne
  Laden der Warenlisten.
- `query_current_candidates(fid, commodity=None, ...)`: Höchstens 500 Ergebnisse
  je Seite, MarketID-Keyset-Cursor, optional FID/Alter/System/Kauf-/Verkaufsrichtung
  und Mindestmenge. `commodity=None` liefert reine Header für Altersabfragen.
  Ohne Richtung bleibt ein fehlender Warenwert als `commodity=None` sichtbar:
  Das ist bei späterer Zusammenführung mit älteren Community-Angeboten wichtig.
  Eine reine BUY-/SELL-Treffermenge alleine genügt nicht zur Unterdrückung
  überholter Community-Waren.
- `get_history(fid, market_id, since=None, cursor=None)`: Header der letzten
  höchstens 30 Tage, absteigende Zeit-/ID-Paginierung. `since` schränkt weiter ein.
- `get_observation(fid, observation_id)`: Ergänzende gezielte Detailabfrage für
  genau eine gespeicherte Beobachtung; FID wird auch hier geprüft.
- `best_sell_prices(fid, commodities, scope=..., max_age=..., since=...)`:
  Bis 128 Commodity-Identitäten, jeweils höchster qualifizierter eigener Preis,
  einschließlich tatsächlicher Beobachtungszeit, Station, System und Nachfrage.
- `record_observation(snapshot)`: Vollständige Validierung, Identitäten, Payload,
  Besuch, gegebenenfalls aktueller Zeiger und Revision in einer Schreibtransaktion.
  Rückgabe erst nach erfolgreichem COMMIT.
- `cleanup(cancel=None)`: Explizite atomische Bereinigung mit Löschzählern.
- `get_stats()`: SQL-Zähler sowie Dateimetadaten für DB/WAL/SHM. Keine Warenlisten
  in Python; Zähler können bei großen Beständen dennoch teuer sein.

Es gibt kein `all()`. Seiten tragen die Store-Revision. Mit `expected_revision`
werden zwischenzeitliche Commits durch `StaleReadError` erkannt; der Aufrufer
startet dann die Suche neu. Jede Seite hat ihre eigene kurze Lesetransaktion.
Die Uhrzeit wird pro Abfrage bestimmt; ein langer mehrseitiger Abruf kann daher
an der Altersgrenze weiterlaufende Zeit sehen. Ein fester Zeitanker für einen
späteren gesamten Suchauftrag bleibt Aufgabe der Integrationsphase.

Mining-Preisarten werden ausdrücklich getrennt:

| Preisart | API |
|---|---|
| Letzter eigener Preis, unabhängig vom Alter | scope='last_known' |
| Eigener aktueller Preis innerhalb des Suchalters | scope='current', max_age=Suchalter |
| Historischer Bestpreis der letzten 30 Tage | scope='history', max_age=None |
| Fester Mining-Referenzpreis | Bestehende externe Referenzlogik, nicht dieser Store |

Bei `history` begrenzt ein ausdrücklich kleineres `max_age` das Fenster weiter.
Der allgemeine API-Standardwert ist wie bisher 24 Stunden. Die Rückgabe markiert
ihren Scope; kein historischer Preis wird als aktueller Preis ausgegeben.

## Verbindungen, Haltbarkeit und Fehler

Eine Verbindung gehört ihrem Erzeugerthread. Worker erzeugen und schließen ihre
eigenen Store-Instanzen. SQLite-Threadprüfung und zusätzliche Besitzerprüfung
verhindern Weitergabe zwischen Threads. Leser erhalten eigene Werte, keine
lebenden SQLite-Cursor. `read_only=True` verwendet URI mode=ro und query_only.

Foreign Keys sind aktiv, der Writer prüft WAL, synchronous=FULL gilt für jede
Verbindung. Schreiben verwendet BEGIN IMMEDIATE; Lesen BEGIN. Standard-Busy-Timeout:
250 ms, konfigurierbar. Es gibt keinen stillen Retry und keinen stillen Ersatz
fehlerhafter Datenbanken. Die bisherigen Grenzen von 2.048 Märkten/64 MiB des
JSON-Caches werden nicht auf SQLite übertragen; der Validator begrenzt weiterhin
einen einzelnen vollständigen Markt auf 2.048 Waren.

Alle Store-Aufrufe sind synchron. Lang laufende Suchen, FULL-Commits, Öffnen,
Statistik und Cleanup müssen später in Worker; der Prototyp verschiebt sie nicht
automatisch. Kein heutiger GUI-Pfad benutzt den neuen Store. Noch keine
Aussage über gemessene UI-Blockade oder schwache CPUs.

## Tests und Messverfahren

Funktionstests einschließlich Rollback, SQLITE_FULL, Commit-Fehler, Threadbindung,
WAL-Lesen, FID/MarketID, uint64, Historie und Cleanup:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests venv/bin/python -m unittest test_market_store test_combined_trade test_trade_recommendations
```

Reproduzierbarer Offline-Benchmark:

```sh
PYTHONDONTWRITEBYTECODE=1 venv/bin/python tools/benchmark_market_store.py > /tmp/market-store-results.json
```

Je Größe ein eigener Prozess, temporäre Datenbank, 350 bekannte Waren pro Station.
Bei 10 % der Stationen drei zusätzliche unterschiedliche Snapshots (21/14/7 Tage)
und eine unveränderte Bestätigung (6 Tage). Aktueller Besuch bei der Hälfte
eine Stunde, bei der anderen Hälfte 48 Stunden alt.
Damit 1,3 Snapshots und 1,4 Beobachtungen pro Station; keine synthetische
Vollkopie aller Märkte in Python. Anlage durch die normale Schreib-API mit FULL.

Sieben Wiederholungen, Median und Maximum. Leseabfragen nach explizitem Warmup,
kein behaupteter Kaltstart-/Langsame-CPU-Test. Altersfilter (24 Stunden) liest alle
passenden Header, Commodity/Kaufen/Verkaufen lesen alle Treffer in 500er-Seiten.
Schreibzeit enthält Validieren, Hashen, SQL und FULL-COMMIT; Fixture-Erzeugung
liegt außerhalb. Neue Stationen wachsen für die Messung um sieben, danach sieben
geänderte und sieben unveränderte Beobachtungen derselben Station.
DB-Größen vor diesen Zusatzmessungen stammen nach Verbindungsschluss/Checkpoint
aus Dateimetadaten; WAL/SHM werden zusätzlich separat ausgegeben.
Linux-RSS umfasst Python, SQLite und native Bibliotheken; es ist keine präzise
isolierte Python-Objektmessung. Abfragepläne stammen aus den tatsächlich
ausgeführten SELECTs, ohne erzwungene Indexwahl oder Benchmark-Sonderindizes.

## Messergebnisse vom 26.09.2026

Linux x86_64, Python 3.12.3, SQLite 3.45.1. Lokale temporäre Dateien;
keine Messung einer künstlich verlangsamten CPU oder tatsächlicher UI-Blockaden.

| Stationen | Aktuelle Warenzeilen | Warenzeilen inkl. Historie | DB nach Checkpoint | WAL vor Checkpoint | RSS nach Anlage / nach Messungen |
|---:|---:|---:|---:|---:|---:|
| 100 | 35000 | 45500 | 6.8 MiB | 5.9 MiB | 26.1 / 26.2 MiB |
| 500 | 175000 | 227500 | 35.6 MiB | 6.9 MiB | 26.0 / 26.7 MiB |
| 1000 | 350000 | 455000 | 71.0 MiB | 7.4 MiB | 26.2 / 27.5 MiB |
| 5000 | 1750000 | 2275000 | 353.3 MiB | 7.5 MiB | 26.0 / 27.4 MiB |

Prozess-RSS vor Anlage: etwa 23,6 MiB. Angegeben sind /proc-Stichproben;
ru_maxrss meldete hier teils kleinere Werte als /proc und wird deshalb nicht als
verlässliche Spitzenmessung interpretiert. Der OS-Dateicache ist nicht im RSS
enthalten. SHM jeweils 32 KiB. Bei 5.000 Stationen: 7.000 Beobachtungen,
6.500 Snapshots; DB nach zusätzlichen Messschreibvorgängen 354,1 MiB.

Alle Zeiten **Median / Maximum in ms**, sieben Wiederholungen
(Cleanup ohne abgelaufene Einträge: drei).

| Operation | 100 | 500 | 1.000 | 5.000 |
|---|---:|---:|---:|---:|
| Öffnen (warm, read-only) | 0.24 / 0.40 | 0.24 / 0.37 | 0.24 / 0.39 | 0.28 / 0.41 |
| Eine Station + 350 Waren | 1.36 / 1.57 | 1.16 / 1.46 | 1.25 / 1.60 | 1.23 / 1.51 |
| Neue Station inklusive COMMIT | 21.06 / 23.79 | 19.45 / 29.15 | 19.57 / 26.37 | 23.56 / 29.52 |
| Geänderter Snapshot inklusive COMMIT | 17.34 / 21.86 | 19.12 / 22.17 | 18.18 / 20.83 | 20.54 / 24.20 |
| Unveränderte Bestätigung inklusive COMMIT | 5.20 / 7.45 | 4.40 / 5.39 | 4.10 / 5.14 | 3.52 / 5.37 |
| Altersfilter 24 h, alle passenden Header | 0.20 / 0.25 | 1.00 / 1.72 | 2.13 / 5.43 | 11.73 / 15.23 |
| Eine Ware, alle Stationen | 0.84 / 1.12 | 5.36 / 7.32 | 12.38 / 12.58 | 63.63 / 66.45 |
| Kaufen-Kandidaten, alle Treffer | 0.82 / 0.84 | 5.26 / 5.48 | 12.89 / 13.91 | 67.10 / 69.00 |
| Verkaufen-Kandidaten, alle Treffer | 0.81 / 0.87 | 5.27 / 7.30 | 13.77 / 15.14 | 66.07 / 79.31 |
| Eigener aktueller Bestverkaufspreis | 0.03 / 0.06 | 0.03 / 0.06 | 0.05 / 0.07 | 0.11 / 0.15 |
| Historischer Bestpreis (30 Tage) | 0.02 / 0.03 | 0.03 / 0.03 | 0.04 / 0.04 | 0.07 / 0.08 |
| Statistik | 0.03 / 0.32 | 0.67 / 1.13 | 1.56 / 2.02 | 9.13 / 10.67 |
| Cleanup ohne abgelaufene Historie | 0.15 / 0.50 | 0.25 / 0.73 | 0.54 / 1.04 | 2.31 / 2.38 |

Stationslesen <10 ms und einzelne Beobachtung <50 ms wurden in diesen Messungen
erreicht, einschließlich Maximum. Der Altersfilter bleibt ebenfalls <50 ms.
Vollständige Commodity-/Kandidatenabfragen mit 5.000 Treffern liegen bei
64–67 ms Median und verfehlen das angestrebte <50-ms-Ziel. Sie gehören in einen
Worker; eine einzelne begrenzte Seite ist nicht mit dem gesamten Suchauftrag
gleichzusetzen. Die aktuelle Bestpreis-Verteilung erlaubt frühe Treffer;
viele unbrauchbare oder fremde/alte hochpreisige Snapshots können mehr Arbeit
verursachen. Das ist kein Worst-Case-Nachweis.

Die Datenanlage dauerte rund 1,4 / 9,4 / 22,2 / 117,3 Sekunden und entspricht
vielen einzelnen FULL-Transaktionen, keiner Start-/Ladezeit und keiner geplanten
JSON-Migrationsmessung. Die warme Öffnungszeit lädt keine komplette Datenbank.
Dateisystem-/Hardware-Schwankungen und Kaltzugriffe sind nicht abgedeckt.

## EXPLAIN QUERY PLAN und Engpässe

Bei 5.000 Stationen:

- Einzelstation: eindeutiger (FID,MarketID)-Index → Observation-PK → Snapshot-PK;
  Waren über (Snapshot,Ordinal), Commodity-Schlüssel per PK.
- Altersfilter: current_age; Sortierung nach MarketID über temporären B-Baum.
- Commodity/BUY/SELL: current_age und gezielter (Snapshot,Commodity)-Index,
  keine Vollsuche über 2,275 Millionen Warenzeilen. Die MarketID-Sortierung
  benötigt dennoch einen temporären B-Baum. Ohne ANALYZE bevorzugt der Plan
  auch bei breitem/unbegrenztem Suchalter den Altersindex. Über mehrere Seiten
  kann dadurch wiederholt mehr als nur eine Seite verarbeitet werden.
- Bestpreise: commodity_sell → Snapshot-PK → observation_snapshot →
  aktueller Observation-Index (bei current). Temporäre Sortierung nur für den
  rechten Teil der Preis-/Zeit-/MarketID-Ordnung.
- Stationshistorie: eindeutiger (FID,MarketID,observed_at)-Index, kein Vollscan.
- Cleanup: observation_retention und eindeutiger Current-Observation-Index.
  Verwaiste Snapshots werden über observation_snapshot auf Referenzen geprüft;
  Commodity-Schlüssel über einen Commodity-geführten Index.

Nicht gewählte vorgesehene Indizes sind erklärbar:

- commodity_buy wird in der Kaufen-Kandidatenabfrage nicht gewählt: Die API
  paginiert nach Station statt nach Einkaufspreis. Der Snapshot/Commodity-Punktzugriff
  ist dafür passender. Ob dieser zusätzliche Preisindex überhaupt bleiben soll,
  ist vor Phase 3 zu entscheiden; er kostet bereits jetzt Speicher/Schreibarbeit.
- current_system wird ohne Optimizer-Statistik zugunsten current_age übergangen.
  Separater diagnostischer Versuch mit 100 temporären Märkten bestätigt:
  Nach ANALYZE verwendet dieselbe Systemabfrage current_system und braucht keine
  zusätzliche Sortierung. Die obigen Messungen wurden **ohne ANALYZE** ermittelt;
  der Prototyp führt noch keine automatische Statistikpflege aus.
- current_station ist für MarketID-übergreifende FID-Abfragen vorgesehen; die
  gegenwärtige API verlangt stets eine FID und benutzt dafür den zusammengesetzten
  FID/MarketID-Index. observation_age wird bei gezielter Stationshistorie durch
  deren spezifischeren Index ersetzt.

Kleinste sinnvolle nächste Schritte: reguläre Optimizer-Statistikpflege als
Worker-Wartung bewerten; Alter-/MarketID-Paginierung anhand realer Selektivität
prüfen; tatsächlich unnötige Indizes entfernen. Nicht vorschnell INDEXED BY
erzwingen. get_stats zählt per SQL und ist keine konstante GUI-Operation.
Komplette Snapshots benötigen bei 5.000 Stationen inklusive dieser begrenzten
Historie rund 353 MiB. Die dauerhaften letzten Stände wachsen mit der Zahl jemals
besuchter Märkte; die 30-Tage-Regel begrenzt nur zusätzliche Historie.

## Ergänzungen gegenüber dem Entwurf und offene Phase 3

Konkretisiert wurden das uint64-BLOB-Format, UTC-Mikrosekunden,
threadgebundene Verbindungen, explizite Konfliktfehler, Keyset-Cursor mit Revision
sowie die zusätzliche Einzelbeobachtungs-Detailabfrage. Die verbindliche
30-Tage-Aufbewahrung ersetzt jede frühere Idee eines zusätzlichen Snapshot-Limits.
Stationskontext wird historisch an Besuchen gehalten, nicht als überschreibbare
globale Stationsmetadaten. Der Snapshot-Bezug von current_markets ist indirekt
über den per Fremdschlüssel geschützten aktuellen Besuch.

Vor produktiver Aktivierung fehlen weiterhin:

1. Idempotente, geprüfte JSON-Migration mit unverändertem Original und Rückfall;
   Aktivierung erst nach erfolgreicher vollständiger Validierung.
2. Worker-Lebenszyklus, Schreibwarteschlange, Busy-/Fehlerdarstellung und
   koordinierte regelmäßige Cleanup-Ausführung außerhalb der GUI.
3. Observer-Anbindung und gezielte Store-Adapter für Handel/Empfehlungen,
   einschließlich fehlender Waren als neuerer Negativnachweis beim Community-Merge.
4. Mining-Integration mit sichtbarer Unterscheidung der vier Preisarten.
5. Fester Zeitanker/Revision für längere Suchaufträge, Optimizer-Wartung,
   Indexauswahl und Messungen auf Zielhardware/Kaltstarts.
6. Weitere Historienlasten, längere Laufzeiten und operative Wartung freier
   DB-Seiten; keine zusätzliche harte Stations-/Bytegrenze ohne fachliche
   Entscheidung. Aktuelle letzte Stände dürfen dadurch nicht verlorengehen.

Kein automatischer produktiver Cleanup, keine produktive Migration oder
Datenbankanlage wurde in Phase 2 aktiviert.
