# Gezielte Inventarinvalidierung – CMDRHelper 3.9.21

Stand: 30.10.2026. Keine Versions-, Schema- oder Frachtberechnungsänderung.

## Ursache und geprüfte Kette

`JournalWatcher.check_now()` meldet geänderte Quellen an `SourceManager.request()`.
Der serialisierte Worker ruft `SourceProcessor.process()` auf. Index/Archivimport
und `journal_catchup.catch_up()` validieren Identität, Präfix und Cursor; nach
committeten Deltas stehen `(journal_file, fid, event)` einschließlich Byteoffset
in `context['applied_events']`. Eine Liste umfasst sämtliche Catch-up-Durchläufe
eines Aufrufs und sämtliche bearbeiteten Dateien dieser Quelle.

Bisher erhöhte `SourceManager._finished()` bei jedem erfolgreichen Durchlauf
alle drei `_inventory_revisions` und sendete `inventoryChanged`, auch ohne Delta.
`refresh_selected()` projiziert anschließend die gewählte Quelle über
`AppState.refresh()`. Dort erhöhte die bereits vorhandene ereignisbezogene
Erkennung die Revisionen bei relevanten Live-Ereignissen nochmals.

Material-, Mining- und Odyssey-Controller prüfen bereits ihre eigene Revision
und Identität, bevor sie Hintergrundarbeit starten. Ihre Leser rekonstruieren
Inventare aus den zugeordneten Journalsitzungen. Die pauschale Erhöhung setzte
diese vorhandene Vermeidung unnötiger Arbeit außer Kraft. Sie konnte auch bei
reinen Positionsänderungen erneutes Parsen und historischen Replay auslösen.

Die separaten Pfade für `cargoSnapshotChanged`, Odyssey-Sidecars,
Commanderidentität, `journalIndexReady`, `databaseImportFinished`, manuelle
Aktualisierung und Cargo-Retry wurden geprüft und bleiben erhalten.

## Geänderte Dateien dieses Auftrags

- `cmdrhelper/inventory_invalidation.py`: gemeinsame Ereigniszuordnung und konservative Batchprüfung.
- `cmdrhelper/source_processing.py`: Ergebnis der Batchprüfung; konservativer Fehler-/Wiederholungszustand.
- `cmdrhelper/source_manager.py`: gezielte Revisionserhöhung und Benachrichtigung nach der Quellenprojektion.
- `cmdrhelper/state.py`: gemeinsame Ereigniszuordnung; keine doppelte Zählung einer Quellenprojektion.
- `tests/test_inventory_invalidation.py`: gezielte Regel-, Worker- und AppState-Integrationstests.
- `tools/benchmark_inventory_invalidation.py`: isolierter Vergleich mit echten X11-Fenstern.
- `docs/inventory-invalidation.md`: dieser Bericht.
- `docs/inventory-invalidation-x11.json`: Rohdaten des Vergleichs.

## Invalidierungsregeln

1. Ein erfolgreich verifizierter Anhang an dieselbe aktuelle, eindeutig
   zugeordnete Sitzung verwendet die bestehenden `EVENTS`-Mengen der drei Leser.
   Jeder betroffene Typ erhält pro Batch genau eine neue Revision.
   `CarrierStats` betrifft zusätzlich Mining und Odyssey, da deren Ergebnis von
   der gespeicherten eigenen Carrieridentität abhängt.
2. Ein reiner FSDJump-/Positionsbatch ohne andere relevante Änderungen erhöht
   keine Revision. Ein unveränderter erfolgreicher Durchlauf sendet auch kein
   `inventoryChanged`. Ein bloßes Touch bei unverändertem bestätigtem Hash einer
   identifizierten Datei benötigt ebenfalls keine Rekonstruktion.
3. Initialisierung und expliziter Archivimport invalidieren alle Typen.
   Neue/entfernte Sitzungen, Änderungen von Commander/FID/Zuordnung/Startzeit,
   historische Ergänzungen, unbekannte Cursoränderungen und Änderungen an
   unveränderten Cursorn zugeordneten Dateiinhalten invalidieren konservativ alle.
4. Dateiduplikate sind eine Rekonstruktionsgrundlage: Ändert ein Anhang die
   Digest-Deduplizierung, werden alle Typen invalidiert. Die Prüfung bezieht
   auch andere Quellen im gemeinsamen Sitzungsindex ein.
5. Ein fehlgeschlagener Worker kann zuvor einzelne Dateien committet haben.
   Deshalb invalidiert er konservativ; auch der nächste erfolgreiche Versuch
   bleibt konservativ, selbst wenn dessen `applied_events` bereits leer sind.
   Generationen ausgeschiedener Quellen werden weiterhin verworfen.
6. Quellen-/Commanderwechsel verwenden weiterhin die bestehenden Identitäts-
   und Resetpfade. Die Inventarbenachrichtigung erfolgt nach `refresh_selected()`,
   damit die Leser bei ihrem Request die aktuelle Quellenprojektion sehen.
7. `AppState.refresh()` zählt Ereignisse nur im eigenen, nicht vom SourceManager
   projizierten Aktualisierungspfad. Die Projektion selbst zählt den Batch nicht
   nochmals und wendet keine zusätzliche Frachtberechnung an.

`Cargo`, `CargoTransfer`, `MiningRefined`, `CollectCargo`, Materialereignisse
und Odyssey-Ereignisse bleiben über die Leser-Ereignismengen erfasst. Vollständige
Cargo-Snapshots, Ship/SRV-Trennung, Checkpoints und Bestandsstatusberechnung
wurden nicht verändert. Der Carrier-Leser liest bei einem späteren Transfer auch
die seit seinem letzten Cursor aufgelaufenen Positionsereignisse; das Überspringen
einer Rekonstruktion beim FSDJump entfernt diese Ereignisse nicht aus dem Journal.

Die Revisionen bleiben global pro Inventartyp. Eine relevante Änderung einer
anderen Quelle kann daher weiterhin den aktuell angezeigten Leser anstoßen.
Eine feinere Revision pro Commander/Quelle wäre ein eigener Architekturumbau.

## Messverfahren

Echtes X11 (`QApplication.platformName() == 'xcb'`, Display `:0`), tatsächliches
MainWindow mit Explorer- und PP2-Navigationsschaltflächen. Ausschließlich
isolierte temporäre Datenbanken, Einstellungen und synthetische Journale;
keine produktiven Journaldateien wurden verändert. Steam und Heroic werden als
getrennte Quellen angelegt. Der ausgewählte Commander hat sechs historische
Dateien mit jeweils 500 Materialdeltas sowie Material-, Cargo- und
ShipLocker-Snapshots. Alle Läufe erzeugen denselben logischen Datenbestand.

Je Konfiguration acht reine FSDJump-Batches und danach acht gemischte Batches
mit tatsächlichen Material-, Cargo- und Odyssey-Snapshots. Leser sind vorgewärmt.
Bei der Kontrolle ohne aktive Leser werden nach dem Warm-up ihre Jobstarts
unterbunden, während das echte Fenster und seine Signale aktiv bleiben.

Gezählt werden Revisionsdifferenzen und tatsächliche Aufrufe von `reconstruct()`.
CPU-Zeit ist die mit `time.thread_time()` gemessene Summe innerhalb dieser
Rekonstruktionsaufrufe; SQL-Vorbereitung und sonstige UI-Arbeit sind nicht darin
enthalten. Ein 10-ms-QTimer misst die größte positive Überschreitung seines
Intervalls. Die Klickmessung beginnt beim Einreihen eines synthetischen Qt-Klicks
und endet beim ersten Paint-Event der Zielseite. Pro Seite gibt es vier Samples.
Das misst weder die Ausgabe des Compositors noch einen externen X11-Eingabestempel.
Die Klicks werden beim Start der Quellenverarbeitung eingereiht; sie treffen
nicht garantiert den späteren Rekonstruktionszeitraum nach dem 150-ms-Debounce.

Der Vorherlauf lädt ausschließlich die vor Arbeitsbeginn gesicherten drei
Produktionsmodule `source_manager.py`, `source_processing.py` und `state.py`.
Alle vorhandenen unveröffentlichten UI-Optimierungen bleiben in beiden Varianten
aktiv. Beispiel:

```bash
QT_QPA_PLATFORM=xcb venv/bin/python tools/benchmark_inventory_invalidation.py --baseline-dir /tmp/cmdr-inventory-before
QT_QPA_PLATFORM=xcb venv/bin/python tools/benchmark_inventory_invalidation.py
# Für beide Varianten zusätzlich: --without-readers
```

## Messergebnisse

Die zugehörigen Rohdaten stehen in `inventory-invalidation-x11.json`.
Alle Zeitwerte in Millisekunden. Tripel sind Material / Mining / Odyssey;
Revisionen, Rekonstruktionen und CPU sind Summen über acht Batches. Klickwerte
und Eventloop-Verzögerung sind Maxima. Die vier finalen Läufe erfolgten
nacheinander ohne parallel laufende Regressionstests.

| Leser | Batch | Stand | Revisionen M/Mi/O | Rekonstruktionen M/Mi/O | CPU M/Mi/O | Explorer | PP2 | Eventloop |
|---|---|---|---|---|---|---:|---:|---:|
| aktiv | FSDJump | vorher | 8 / 8 / 8 | 8 / 8 / 8 | 94.09 / 14.74 / 4.6 | 101.22 | 107.84 | 105.83 |
| aktiv | FSDJump | nachher | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 103.62 | 120.97 | 118.08 |
| aktiv | Inventar | vorher | 16 / 16 / 16 | 8 / 8 / 8 | 88.31 / 19.14 / 5.64 | 105.17 | 98.82 | 100.19 |
| aktiv | Inventar | nachher | 8 / 8 / 8 | 8 / 8 / 8 | 85.07 / 21.81 / 6.02 | 105.33 | 111.86 | 105.39 |
| inaktiv | FSDJump | vorher | 8 / 8 / 8 | 0 / 0 / 0 | 0 / 0 / 0 | 106.95 | 117.32 | 115.99 |
| inaktiv | FSDJump | nachher | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 106.83 | 117.25 | 114.33 |
| inaktiv | Inventar | vorher | 16 / 16 / 16 | 0 / 0 / 0 | 0 / 0 / 0 | 113.10 | 102.84 | 109.53 |
| inaktiv | Inventar | nachher | 8 / 8 / 8 | 0 / 0 / 0 | 0 / 0 / 0 | 101.48 | 108.17 | 105.83 |

Bei acht reinen FSDJump-Batches entfallen nachher alle **24 unnötigen
Rekonstruktionen**. Bei den gemischten Inventarbatches bleiben **24 erforderliche
Rekonstruktionen** erhalten; die Revisionen sinken von jeweils 16 auf jeweils 8.
Die Klick- und Eventloop-Werte zeigen keine belastbare Beschleunigung und werden
nicht als solche interpretiert.

## Regressionen

Abschließender Lauf: **337 Tests in 101,447 s; 336 bestanden, einer übersprungen**.
`git diff --check` und die Python-Kompilierungsprüfung waren ebenfalls erfolgreich.

Die gezielte Serie umfasst Quelle/Worker/Catch-up, Material, Mining, Carrier,
Cargo-Live, Cargo-Historie, Ship-Cargo, Odyssey, bestehende Performance-Tests und
alle drei unveröffentlichten UI-Caches. Ein optionaler Test mit einer externen
Referenzdatenbank ist ohne `CMDRHELPER_TEST_DATABASE` bewusst übersprungen.

Die neuen Tests prüfen:

- Alle vorhandenen Leser-Ereignismengen und `CarrierStats`.
- FSDJump: keine Revisionserhöhung und kein Start eines der drei Leser.
- Materialänderung: genau ein Material-Replay und aktualisierter tatsächlicher Bestand.
- Mining-, Odyssey- und gemischte Batches: unabhängige Revisionen, jeweils genau einmal.
- Unveränderte Verarbeitung, historische Ergänzung/Import, neue Sitzung, Korrektur und erneute Zuordnung eines Indexeintrags.
- Fehler nach Commit und anschließender Retry ohne erneut gelieferte Ereignisse.
- Digest-Deduplizierung einschließlich Kopien in einer anderen Quelle.
- Commanderwechsel und Steam–Heroic–Steam bei gleicher FID.
- Schiff-/SRV-Trennung: Transfer nach übersprungener FSDJump-Rekonstruktion, unveränderter erneuter Durchlauf und Quellenrückwechsel ohne doppelte Anwendung.

Die bestehenden Cargo-/Carrier-Tests decken vollständige und Count-only-Snapshots,
Checkpoints, fehlende Snapshots, Wiederanlauf, fremde Carrier, SRV-Transfers,
Cursor-/Duplikatschutz und unbekannte/inkonsistente Bestände ab. Ihre Berechnungen
und Erwartungen wurden nicht geändert.

## Grenzen und verbleibende Risiken

Die ursprünglichen Ausreißer von 726 ms im Explorer bzw. 1.371 ms in PP2 und die
1.339 ms vor Beginn der Klickverarbeitung konnten mit diesem synthetischen
Bestand nicht reproduziert werden. Aus diesen Messungen folgt keine garantierte
Klickbeschleunigung. Nachgewiesen wird die vermiedene Inventararbeit beim
unveränderten aktuellen Bestand; verbleibende UI-/Ingestion-Arbeit bleibt erhalten.

Neue Sitzungen, Importe, Fehler und unsichere Zuordnungen kosten weiterhin
Rekonstruktionen. Ein FSDJump kann außerdem mit einem tatsächlich geänderten
Sidecar oder einer Identitätsinitialisierung zusammentreffen; die dann nötigen
unabhängigen Aktualisierungen sind ausdrücklich nicht abgeschaltet.

Die Tests verwenden synthetische Daten, keinen laufenden Elite-Client und keine
produktive Journalhistorie. Keine Windows-Liveprüfung und keine komplette
projektweite Testsuite. Keine Änderung an EDSM-/Inara-Uploads.

## Git-Status und Bestandsschutz

Vorher:

```text
 M cmdrhelper/ui/favorites_view.py
 M cmdrhelper/ui/journal_sources.py
 M cmdrhelper/ui/system_overview.py
 M tests/test_journal_sources_ui.py
 M tests/test_source_manager.py
?? cmdrhelper/ui/favorite_preview_cache.py
?? tests/test_favorite_preview_cache.py
?? tests/test_system_overview_cache.py
```

Die fünf vorhandenen getrackten Diffs wurden vor Beginn gesichert; ein
byteweiser Vergleich mit dem abschließenden Diff dieser fünf Dateien bestätigt
ihren unveränderten Erhalt. Die drei bereits ungetrackten Cache-Dateien wurden
nicht bearbeitet. Journalquellen-, Favoriten-Bild- und Planetengrafik-Cache bleiben
erhalten. `github.sh` wurde nicht ausgeführt. Kein Commit, Tag, Push oder Release.

Nachher:

```text
 M cmdrhelper/source_manager.py
 M cmdrhelper/source_processing.py
 M cmdrhelper/state.py
 M cmdrhelper/ui/favorites_view.py
 M cmdrhelper/ui/journal_sources.py
 M cmdrhelper/ui/system_overview.py
 M tests/test_journal_sources_ui.py
 M tests/test_source_manager.py
?? cmdrhelper/inventory_invalidation.py
?? cmdrhelper/ui/favorite_preview_cache.py
?? docs/inventory-invalidation-x11.json
?? docs/inventory-invalidation.md
?? tests/test_favorite_preview_cache.py
?? tests/test_inventory_invalidation.py
?? tests/test_system_overview_cache.py
?? tools/benchmark_inventory_invalidation.py
```

Die Implementierung bleibt uncommittet. Weitere Arbeiten warten auf Freigabe.
