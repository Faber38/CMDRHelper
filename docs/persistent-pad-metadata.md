# Persistente lokale Padbelege (Schema 22)

Die Hauptdatenbank hält lokale konkrete LandingPads aus `Docked` und
`DockingRequested`. `markets.db`, Preise, Spansh-Frische und Stationsdarstellung
bleiben unverändert. Keine neuen Netzabfragen; keine Services-Persistierung.

## Schema und Migration

`CMDRDatabase._maybe_migrate_v22()` ergänzt in einer Transaktion:

- `station_pad_journals`: eindeutiger kanonischer Journalpfad, Ordner,
  Dateisignatur (Device, Inode, Größe, mtime, ctime), bestätigter vollständiger
  Zeilenoffset, Parser-Version, Fortsetzungskontext, Anfangs-/Offset-Prüfsummen.
- `station_pad_evidence`: neuester konkreter Beleg je Journal und MarketID,
  optionale SystemAddress/StationType, System-/Stationsname, drei Padanzahlen,
  Quelle, Ereignistyp, UTC-Beobachtungszeit und ursprünglicher Ereignisoffset.

MarketID und SystemAddress verwenden verlustfreie unsigned-64-Bit-BLOBs.
Die Stationsauflösung wählt den neuesten Beleg über die Dateien hinweg.
Gleiche Zeitpunkte behalten die bisherige Reihenfolge: spätere Zeile innerhalb
derselben Datei, bei verschiedenen Dateien der erste sortierte Dateipfad.

Reguläres Schema 20 und das historische Codex-Schema 21 gehen direkt nach 22.
Version 21 wird nicht neu vergeben. Vor Migration bestehender Versionen 17–21
wird die vorhandene SQLite-Backupfunktion mit Integritätsprüfung verwendet.
Historische Codex-Tabellen und -Daten werden weder gelesen noch geändert durch
die Migration; bei Schema 20 werden sie nicht angelegt. Eine fehlgeschlagene
Migration rollt Tabellen und Versionsänderung gemeinsam zurück. Schema 22 wird
beim erneuten Öffnen nicht nochmals migriert; zukünftige unbekannte Versionen
werden abgewiesen. Anwendungsversion bleibt unverändert.

## Import und Fehlerverhalten

Der bestehende Startworker ruft den Padabgleich nach dem Journalindex auf.
Jede Handels-/Empfehlungsabfrage gleicht vor ihrem lokalen Padlesen ebenfalls
inkrementell ab. Das ist ein bedarfsabhängiger Import, kein neuer Poller.
Zwischen zwei Abfragen hinzugekommene Ereignisse werden spätestens beim nächsten
Start oder Padabruf persistiert. Persönliche Commander-/Archiv-/Reparaturmarker
werden weder verändert noch als Padfortschritt interpretiert.

Unveränderte Dateien benötigen ausschließlich Dateimetadaten, keine Inhalte.
Neue Dateien werden einmal gelesen. Normales Wachstum nutzt eigenen Offset und
Kontext; zur Prüfung werden höchstens zwei 4-KiB-Bereiche des alten Präfixes und
zur Bestätigung zwei Bereiche am neuen Offset gelesen. Nur vollständige Zeilen
werden bestätigt. Sitzungsgrenzen setzen Kontext zurück; ungültiges JSON
verwirft unsicheren Kontext. Fehlende MarketID oder unvollständige/ungültige
Padanzahlen erzeugen keinen Beleg. StationType wird nicht zur Padableitung benutzt.

Parsing findet außerhalb der Schreibtransaktion statt. Vor dem atomaren Commit
werden Dateisignatur und DB-Fortschritt erneut geprüft. Belege und Fortschritt
werden zusammen geschrieben. Abbruch rollt die aktuelle Datei zurück, vorherige
Dateien bleiben bestätigt. Wiederholung ist idempotent. Pro Datenbank serialisiert
eine abbrechbar wartende Sperre die Aufträge im Prozess; eine weitere
Fortschrittsprüfung schützt vor konkurrierenden Schreibern anderer Prozesse.

Ersetzung, Verkürzung, Änderungen gleicher Länge, geänderte Parser-Version oder
fehlgeschlagene Append-Prüfungen führen zur Neuerfassung nur dieser Datei.
Ihre bisherigen Belege werden im erfolgreichen Commit vollständig ersetzt.
Andere Dateibelege bleiben verfügbar. Entfernte Dateien werden nach erfolgreicher
Verzeichnisinventur aus dem aktiven Bestand entfernt; ein nicht lesbarer Ordner
gilt nicht als leer.

Bei Dateirennen, I/O- oder DB-Fehlern liefert der gesamte Abruf einen Fehler statt
einer potenziell veralteten Teilprojektion. Alte gespeicherte Beiträge einer noch
nicht erfolgreich neu erfassten Datei werden dadurch nicht ausgeliefert.
Startfehler werden gemeldet; Suchworker verwenden ihre vorhandenen Fehlerpfade.
Es gibt keinen Rückfall auf den früheren flüchtigen Journalvollscan.

Begrenzte Append-Prüfungen erkennen nicht jede denkbare Änderung mitten in einem
gleichzeitig verlängerten Präfix. Vollständige Manipulationserkennung würde dessen
erneutes Lesen verlangen. Dieses Verfahren folgt der vorhandenen begrenzten
Präfix-/Offset-Prüfung des Live-Journallesers. Unveränderte Signaturen werden nicht
vorsorglich durch vollständiges Hashen verifiziert.

## Resolver

`PadMetadata` liest lokale Belege über den Importdienst und ergänzt den bisherigen
Spansh-Dateicache. Lokale konkrete Belege haben Vorrang unabhängig vom Alter einer
Spansh-Angabe. Drei Nullen bleiben ein lokaler Beleg mit unbekannter positiver
Padklasse und werden nicht durch Spansh ersetzt. `PadSize`, `matching_pad()` und
Preis-/Filtersemantik bleiben erhalten. Die DB wird explizit über
`TradeMarketSource` übergeben; fehlende Konfiguration ist ein sichtbarer Fehler.

## Reale Messung vom 03.10.2026

525 Journale, 312.172.137 Bytes. Migration der tatsächlichen Schema-21-DB nach
verifizierter Sicherung: 14,5 ms. Alle 39 vorherigen Tabellen und ihre Inhalte
sowie sämtliche vorherigen Schemadefinitionen vor/nach Migration und Erstimport
verglichen: unverändert; darunter 638 Codex-Ereignisse und 460 Codex-Importmarker.

- Einmaliger Import einschließlich Commits: 4,158 s; 525 Dateien, 705 Belege,
  252 eindeutige lokale MarketIDs, keine ungültigen JSON-Zeilen.
- Gelesen beim Erstimport: 316.108.143 Bytes einschließlich begrenzter Prüfbereiche.
- Vorheriger Resolver erneut gemessen: 2,111 s.
- Vollständiger erster Resolverabruf in drei jeweils frischen Prozessen:
  42,68 / 41,57 / 39,44 ms, jeweils **0 Journaldateien geöffnet und 0 Journalbytes**.
  Ein instrumentierter Dateiöffner ließ historische Journalöffnungen fehlschlagen.
- Lokaler Abgleich einschließlich Inventur und DB-Projektion: 11,90–12,64 ms.
- DB-Abfrage plus Python-Projektion: 2,55–2,70 ms.
- Separater Spansh-Aufbau einschließlich Merge: 13,24–14,10 ms.
- Gesamtergebnis des alten und neuen Resolvers für alle 1.188 MarketIDs exakt gleich.
- `tracemalloc` nach vorab geladenen Modulen: ca. 0,96 MiB verbleibend,
  1,59 MiB Spitze für Resolver und Ergebnis; kein Gesamtprozess-RSS.
- Kleine Delta-Messung an einer temporären Kopie des neuesten realen Journals
  (1.140.297 Bytes), ergänzt um je ein synthetisches Padereignis: 285 neue Bytes,
  insgesamt 16.669 gelesene Bytes einschließlich Prüfbereichen, 6,81–8,47 ms
  einschließlich Commit. Produktive Journale wurden nicht verändert.

Die Prozesse waren frisch, der Betriebssystem-Dateicache warm. Die Messung ist
keine Aussage über einen kalten Datenträger oder die gesamte Startzeit.
Die getrennten historischen Leser für Spielmodus und Catch-up sind unverändert.
