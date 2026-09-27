# v3.8: Migration und produktiver Schreibpfad

Aktueller Folgestand: [gemeinsame lokale Märkte, Schema 2 und Mining](shared-markets-mining.md).
Die früheren Phasenmessungen und FID-Verträge unten sind historische Dokumentation;
für aktuelle Lese-APIs, Migration und Aufbewahrung gilt der verlinkte Folgestand.

Dieses Dokument hält den Stand der Migration-/Schreibpfad-Phase fest.
Die anschließende Umstellung der Kaufen-/Verkaufen-Leser ist in
[trade-market-store.md](trade-market-store.md) dokumentiert.

## Aktivierung und Originaldatei

AppState aktiviert den neuen Schreibpfad mit
`ObservedMarketObserver(use_market_store=True)`. Beim ersten Cachezugriff startet
ein dedizierter MarketStoreWriter. Der Pfad bleibt
`AppDataLocation/market_cache/markets.db`, separates Schema 1.
Version und `cmdrhelper.db`-Schema 20 werden nicht geändert.

Der Worker führt vor allen eingereihten Beobachtungen diese Schritte aus:

1. Existierende markets.db nur mit korrekter Store-Identität, Schema und
   `migration_complete=1` übernehmen. Eine unmarkierte/fremde Datei niemals
   überschreiben. Eine bereits aktivierte DB wird nicht erneut aus JSON befüllt;
   auch eine später extern geänderte Original-JSON löst keinen erneuten Import aus.
2. Fehlt die DB, JSON vollständig lesen, Größen-/Versions-/Listenlimits prüfen,
   doppelte JSON-Schlüssel, NaN, doppelte FID/MarketID und ungültige Felder ablehnen.
   Der bestehende Validator bestimmt die normalisierte Semantik. Kein Überspringen
   einzelner ungültiger Zeilen, keine Altersfilterung, alle FIDs.
3. Fehlende JSON bedeutet leeren Anfangsbestand. Eine gültige leere Marktliste
   wird ebenfalls übernommen. Eine vorhandene **Datei mit null Bytes ist
   beschädigte JSON** und wird nicht stillschweigend als leer akzeptiert.
4. Alle Stände in eine temporäre DB im selben Verzeichnis schreiben. Danach
   Markt-/Snapshot-/Beobachtungs-/Warenanzahlen, jeden normalisierten Inhalt,
   Foreign Keys und SQLite-integrity_check prüfen. Auch alte letzte Stände bleiben
   erhalten. Vom bisherigen Loader erlaubte zukünftige Zeitstempel werden beim
   Import erhalten; normale Live-Schreibaufträge lehnen Zukunftszeiten weiterhin ab.
5. Den SHA-256 der Quelle erneut prüfen. Quelle geändert: Import abbrechen.
   ANALYZE ausführen und Quellhash, importierte Anzahl und Abschlussmarker in einer
   Transaktion schreiben. WAL vollständig checkpointen, Verbindung schließen und
   die temporäre Hauptdatei synchronisieren.
6. Die fertige Hauptdatei per Hardlink ohne Überschreiben unter markets.db
   veröffentlichen; auf POSIX auch das Elternverzeichnis synchronisieren.
   Gewinnt ein zweiter Migrator das Rennen, dessen fertige DB prüfen/übernehmen.
   Auf Dateisystemen ohne Hardlink-Unterstützung sicher mit Fehler abbrechen,
   keine unsichere Kopier-/Überschreibfallback-Lösung.

Die Original-JSON wird weder verändert, umbenannt noch gelöscht. Temporäre Dateien
werden bei regulären Fehlern und kooperativem Abbruch entfernt. Nach einem harten
Prozessabbruch kann ein unbenutztes Staging-Verzeichnis zurückbleiben; es wird
niemals als aktive Datenbank betrachtet.

Der Abschlussmarker liegt schon in der verifizierten Staging-Datei. Eine aktive
Datei ist daher nie ein halber Import. Fehler vor Veröffentlichung lassen nur die
JSON-Lesesicht zurück. Scheitert die abschließende Verzeichnissynchronisierung,
meldet der aktuelle Versuch einen Fehler; die bereits veröffentlichte,
vollständig markierte Datei kann beim Wiederanlauf sicher übernommen werden.

## Observer, Worker und bisherige Leser

Der Observer validiert weiterhin Journal-/Market.json-Zusammenhang. Er reicht
eigene Kopien erfasster Beobachtungen in die FIFO-Warteschlange ein. Seine
`consume()`-Rückgabe bleibt false, solange Schreibbestätigungen fehlen; der
vorhandene Watcher wiederholt den Aufruf. Neue erfasste Beobachtungen dürfen
während Migration und ausstehender Commits zusätzlich eingereiht werden.

Der Worker öffnet/verwendet/schließt seine SQLite-Verbindung ausschließlich im
eigenen Thread. Alle Schreibtransaktionen inklusive FULL-COMMIT laufen dort.
Future-Erfolg und Callback erfolgen erst nach COMMIT. Gleiche Beobachtungen
lassen sich idempotent wiederholen; ältere Wiederholungen setzen den letzten Stand
nicht zurück. Fehlgeschlagene Observer-Aufträge werden mit ihrem bereits
erfassten Inhalt erneut eingereiht, ohne eine inzwischen andere Sidecar einzulesen.
FIFO gilt für die angenommenen Versuche; ein fehlgeschlagener Versuch kann bei
Wiederholung hinter bereits angenommenen Aufträgen liegen.

Kaufen, Verkaufen und Empfehlungen lesen nach Aktivierung direkt MarketStore.
Der Writer veröffentlicht ausschließlich kleine Stationsheader (FID/MarketID,
Zeitpunkt, System-/Stationsidentität) für den Empfehlungsausgangspunkt. Er lädt
keine Warenlisten und keine Historie in eine vollständige Python-Projektion.
Die frühere vollständige Projektion und ihre Writer-Option sind entfernt.

Vor erfolgreicher Aktivierung bleibt JSON als Lesefallback verfügbar. Die
Handelsworker warten auf die Initialisierung; nur bei einem Fehler vor
DB-Veröffentlichung verwenden sie den ursprünglichen JSON-Bestand. Es gibt keinen
JSON-Dual-Write. Neue Beobachtungen werden erst nach SQLite-COMMIT bestätigt.
`cache.put()` ist bei aktiviertem Writer gegen JSON-Schreibzugriffe gesperrt.

Nach Veröffentlichung wird `markets.db.activated` dauerhaft angelegt. Existierende
DB oder Aktivierungsmarker verhindern jeden automatischen JSON-Rückfall, auch nach
Neustart, beschädigter oder fehlender DB. Unmarkierte existierende Datenbanken werden
weiterhin geprüft und nicht ersetzt. DB-/Writer-Fehler sind über Futures, Logging
und Statusanzeige diagnostizierbar. Eine fehlende DB muss wiederhergestellt werden;
die alte JSON wird nicht automatisch als Ersatz importiert.

Die Statusanzeige zählt im Writer eindeutige MarketIDs über alle FIDs, ohne
Altersfilter oder Spansh-Daten. Im GUI werden nur die veröffentlichte Anzahl und
drei Dateigrößen gelesen: `markets.db`, `markets.db-wal`, `markets.db-shm`.
Details und Messwerte: [Abschluss des Übergangs](market-transition.md).

## Fehler und App-Ende

`ready` und Auftrags-Futures liefern konkrete Exceptions; `status` und
`last_error` stellen Initialisierung/Migration/Schreibfehler bereit.
Ein späterer erfolgreicher anderer Auftrag verdeckt einen vorherigen
unbestätigten Schreibfehler nicht. Erfolgreiche Wiederholung desselben Auftrags
bereinigt dessen Fehlerstatus. Fehler werden protokolliert; kein neuer UI-Dialog.

`aboutToQuit` ruft Observer.close() auf: weitere Annahme sperren,
angenommene Aufträge abarbeiten, Verbindung im Worker schließen, Thread joinen.
Der reguläre Shutdown kann deshalb auf langsame Datenträger warten. Er ist kein
Schreiben im GUI-Thread, aber bewusst ein wartender Shutdown. close() meldet false,
wenn unbestätigte Fehler bestehen; diese bleiben protokolliert.

Es gibt keine persistente Outbox. Bei SIGKILL/Stromausfall können noch nicht
committete RAM-Aufträge verloren gehen; sie wurden nicht als gespeichert bestätigt.
SQLite schützt bereits bestätigte Transaktionen und verwirft unvollständige
Transaktionen beim Wiederanlauf. Ein kontrollierter Neustart nach einem
Migrationsfehler darf die unveränderte JSON erneut importieren. Ein erfolgreicher
Import wird anhand der aktiven DB-Marker nicht wiederholt.

## Cleanup und Optimizer

Nach erfolgreicher Initialisierung wird einmal ausdrücklich Cleanup im Worker
ausgeführt. Zusätzlich steht `writer.cleanup(cancel=Event)` als geordneter
Wartungsauftrag bereit. Kein Timer, UI-Schalter oder Cleanup durch Lesen beziehungsweise
Altersfilterwechsel. Jeder letzte Stand je FID/MarketID bleibt dauerhaft; nur
zusätzliche Beobachtungen vor der 30-Tage-Grenze und verwaiste Snapshots werden
transaktional bereinigt.

ANALYZE läuft einmal bei Anlage/Migration vor Aktivierung, auch für einen leeren
Anfangsbestand. Erfolgreiche Neustarts führen kein vollständiges ANALYZE aus.
Nach einem zusätzlich explizit angeforderten Cleanup erfolgt PRAGMA optimize
mit analysis_limit=400. Dadurch bleibt spätere Statistikpflege an Worker-Wartung
gebunden statt an jeden Start oder Marktbesuch.

## Tests

```sh
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests venv/bin/python -m unittest test_market_migration test_market_store test_observed_market_cache test_combined_trade test_trade_recommendations
```

177 Tests bestanden. Neue Tests prüfen leere/fehlende/ungültige JSON, FID-Trennung,
alte und zukünftige Zeitstempel, uint64, exakte Cache-Semantik, Quellenänderung,
Abbruch, Schreib-/Publikationsfehler, konkurrierende Migration, idempotenten
Neustart, Beobachtungen während Migration, FIFO, echte COMMIT-Fehler,
Legacy-Projektion, Observer-Wiederholung, Shutdown und Cleanup.
Alle Daten liegen ausschließlich in temporären Verzeichnissen; keine produktive
Marktdatei, QSettings, Commander-DB oder Netzabfrage wird verwendet.
