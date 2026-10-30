# Frühe lokale Positionsveröffentlichung – CMDRHelper 3.9.21

Stand: 30.10.2026. Gezielter Eingriff ohne neue Uploadarchitektur, Versionsänderung
oder Datenbankmigration. Alle Messungen verwenden synthetische Daten.

## Ursache und tatsächlich geänderte Dateien

Der Quellenworker in `SourceManager._next()` führte bisher
`SourceProcessor.process()` und danach `source_transfers.transfer()` aus, bevor
`finished` die lokale GUI-Projektion freigab. Dadurch warteten sowohl die lokale
Systemanzeige als auch `journalPositionsReady` und der EDSM-Statusworker auf die
Uploads desselben Batches. Die Netzwerkaufrufe liefen bereits im Hintergrund;
der Engpass war der Zeitpunkt der Veröffentlichung.

In diesem Auftrag geändert bzw. neu angelegt:

- `cmdrhelper/source_manager.py`: frühes `ingested`-Signal, getrennte lokale Veröffentlichung und Transferabschluss; Statusinvalidierung bei Quellenwechsel/-entfernung, Commanderwechsel während Ingestion und beim Stoppen.
- `cmdrhelper/edsm_system_status.py`: veraltete, noch wartende Statusaufträge mit `QThreadPool.tryTake()` entfernen.
- `tests/test_source_publication.py`: Integration der lokalen Veröffentlichung mit blockierten Transfers, Fehlern, Quellen-/Commanderwechseln, Shutdown und realem Inara-Outbox-Pfad.
- `tests/test_edsm_status_queue.py`: tatsächlicher Zwei-Platz-Pool, wartende und laufende Anfragen, A → B → A und Commanderwechsel.
- `tools/benchmark_edsm_publication.py`: reproduzierbarer X11-Vergleich mit kontrollierten Antwortzeiten.
- `docs/edsm-publication.md`: dieser Abschlussbericht.
- `docs/edsm-publication-x11.json`: Messrohdaten.

`source_processing.py`, `state.py`, Uploadimplementierungen, Inventarleser,
Cargo-Snapshots und Datenbankcode wurden in diesem Auftrag nicht geändert.

## Neue Ereignis- und Veröffentlichungsreihenfolge

1. Journal-Polling und bestehende Quellenqueue starten den serialisierten Worker.
2. `SourceProcessor.process()` führt die lokale Journal-/DB-Verarbeitung vollständig aus, einschließlich verifizierter Projektion. Erst nach erfolgreicher Rückkehr wird `ingested` gesendet.
3. Das explizit als QueuedConnection verbundene GUI-Signal prüft Quellengeneration und Abbruchzustand. `_publish_local()` übernimmt den vorhandenen lokalen Veröffentlichungspfad: Sitzungszuordnung, Watcherbestätigung, gezielte Inventarrevisionen und Quellenprojektion.
4. `AppState.refresh()` sendet die bestätigten Positionen über `journalPositionsReady`; `EdsmSystemStatus.observe()` startet den separaten Statusworker. GUI- und HUD-Ausgabe verwenden weiterhin dessen akzeptiertes, generationengeprüftes Ergebnis.
5. Der Quellenworker führt parallel zur GUI-Veröffentlichung seinen bisherigen Transfer aus. Er wartet nicht auf die GUI. Daher kann ein Upload bereits beginnen, bevor die GUI `ingested` verarbeitet; sein **Abschluss** ist jedoch keine Voraussetzung mehr für die lokale Veröffentlichung.
6. Das spätere `finished` verarbeitet Uploadstatus, Importfortschritt und Quellenqueue. Ein bereits lokal veröffentlichter Batch wird dabei nicht nochmals projiziert oder inventarseitig invalidiert. Bei lokalem Fehler bleibt der konservative Fehlerpfad erhalten.

`running` bleibt bis zum Transferabschluss gesetzt. Die neue Phasenmarkierung
`_ingesting` sperrt ausschließlich während der lokalen Verarbeitung die
Quellenprojektion. Ein Quellen-/Commanderwechsel kann während eines laufenden
Transfers somit die bereits verifizierte Projektion verwenden. Dateisignaturen,
FID-Zuordnung und der bestehende Projektionsschutz bleiben erhalten.

Bei einem Quellenwechsel wird der alte Status auch bei gleicher FID und gleichem
System verworfen. Ein Commanderwechsel während laufender Ingestion verwirft die
alte Statusantwort sofort, obwohl die neue Projektion noch nicht verfügbar ist.
Entfernte Quellengenerationen und Meldungen nach Shutdown werden nicht übernommen.

## Auswirkungen auf Uploads und Fehlerbehandlung

- EDSM-/Inara-Transfers bleiben im bestehenden Worker und in derselben Quellenqueue serialisiert. Es gibt keine neuen Uploadjobs, keine zusätzliche Uploadqueue und keine parallelen Transfers desselben Batches.
- `source_transfers.transfer()`, Uploader, Outbox, Checkpoints, Zugangsdatenprüfung, Quellensnapshot und `is_current` sind unverändert.
- EDSM-Fortschrittsmeldungen verwenden weiterhin `edsmUploadChanged`; Inara-Ergebnisse werden beim Transferabschluss der ursprünglichen FID zugeordnet.
- Ein fehlgeschlagener Upload nimmt eine bereits bestätigte lokale Position nicht zurück. Bestehende persistente Retry-/Backoffregeln bleiben zuständig.
- Ein lokaler Verarbeitungsfehler erzeugt kein frühes Signal und startet keinen Transfer.
- Beim Shutdown bleibt die bestehende kooperative Abbruch-/Joinlogik aktiv. Bereits laufende Netzoperationen werden nicht hart abgebrochen; spätere GUI-Ergebnisse werden verworfen. Bereits eingegangene Inara-Bestätigungen bleiben an ihre ursprünglichen Outboxzeilen gebunden.

Die Integration prüft den echten Inara-Transfer-/Outboxpfad mit einem lokal
blockierten `upload_batch`: Die Position erscheint vorher, ein Commanderwechsel
verändert den Empfänger der Bestätigung nicht, und ein weiterer unveränderter
Durchlauf versendet die bestätigten Zeilen nicht nochmals. Bestehende EDSM-Tests
prüfen Fehler, partielle Bestätigungen, Retry und Präfix-/Cursorschutz.

## Statuspool und schnelle Wechsel

Der Pool bleibt bei **zwei Workerplätzen**. Schon vorher prüfte jeder Statusworker
unmittelbar vor dem Netzaufruf, ob seine Generation noch aktuell ist. Zusätzlich
entfernt `_invalidate()` nun obsolete wartende Aufträge mittels `tryTake()`.
Die betroffenen QRunnables verwenden bereits `setAutoDelete(False)`, sodass die
Entnahme keinen Auto-Delete-Lebensdauerfehler erzeugt. Laufende Aufträge bleiben
referenziert und beenden sich normal; ihre Ergebnisse werden generationengeprüft.

Der reale Pooltest blockiert A und B, reiht C, D und E ein und weist nach:
Nur A, B und E erreichen den kontrollierten Transport; C und D werden aus der
Warteschlange entfernt. Solange A und B beide laufen, kann E trotzdem noch nicht
starten. Nach Freigabe eines Platzes startet E; die spätere alte B-Antwort wird
verworfen. A → B → A verwendet eine neue Generation und akzeptiert keine alte
A-Antwort für den zweiten Aufenthalt.

Eine Poolvergrößerung oder harte Netzwerkabbrüche wurden nicht implementiert.

## X11-Messverfahren

Echtes X11 (`xcb`, Display `:0`), tatsächliches MainWindow mit sichtbarem Explorer
und dessen Statuslabel. Private temporäre Journale, Datenbank und Einstellungen;
keine produktiven Daten und keine echten EDSM-/Inara-Anfragen.

Vorher- und Nachherlauf verwenden denselben synthetischen Quellenbestand und
je drei Samples pro Szenario. Der Vorherlauf lädt nur die vor diesem Auftrag
gesicherten Module `source_manager.py` und `edsm_system_status.py`; alle früheren
unveröffentlichten Optimierungen sind in beiden Varianten aktiv.

Zeitnull ist das Schreiben des synthetischen FSDJump ins Journal; direkt danach
folgt `watcher.check_now()`. Die normale variable Pollingwartezeit ist also nicht
enthalten. Uploadzeiten sind kontrollierte Wartezeiten von 0/500/1.500 ms.
Der Fehlerfall wartet 500 ms und wirft einen Timeout. Die Statusantwort wartet
jeweils lokal 40 ms und liefert abwechselnd `known`, `unknown`, `no_response`.

„Position“ ist die erste beobachtete `state.changed`-Meldung mit dem neuen System.
„Statusstart“ ist der Eintritt in den kontrollierten Statustransport. Dieser kann
vor der gemessenen `state.changed`-Meldung liegen, weil `AppState.refresh()` die
bestätigten Positionsereignisse früher innerhalb derselben GUI-Projektion sendet.
„Antwort → GUI“ misst bis zur akzeptierten Notice nach Aktualisierung des
Statuslabels, „Antwort → Paint“ bis zum ersten Paint-Event des Labels. Ein
Compositor-Ausgabestempel wird nicht gemessen. Alle Zahlen sind lokale Messwerte,
keine echten Serverlaufzeiten oder allgemeinen Latenzgarantien.

Aufruf:

```bash
QT_QPA_PLATFORM=xcb venv/bin/python tools/benchmark_edsm_publication.py --baseline-dir /tmp/cmdr-edsm-before
QT_QPA_PLATFORM=xcb venv/bin/python tools/benchmark_edsm_publication.py
```

## Vorher-/Nachher-Ergebnisse

Median aus je drei Samples, alle Angaben in ms. Rohdaten einschließlich aller Einzelwerte in `edsm-publication-x11.json`.

| Uploadwartezeit | Ergebnis | Stand | Sprung → Position | Sprung → Statusstart | Antwort → GUI | Antwort → Paint |
|---:|---|---|---:|---:|---:|---:|
| 0 | Erfolg | vorher | 53.96 | 37.40 | 34.61 | 37.71 |
| 0 | Erfolg | nachher | 52.06 | 36.24 | 45.12 | 48.11 |
| 500 | Erfolg | vorher | 549.44 | 532.47 | 36.66 | 39.10 |
| 500 | Erfolg | nachher | 52.38 | 35.01 | 13.17 | 15.56 |
| 1500 | Erfolg | vorher | 1549.67 | 1532.02 | 37.18 | 39.60 |
| 1500 | Erfolg | nachher | 50.06 | 33.58 | 13.01 | 15.43 |
| 500 | Timeout | vorher | 549.72 | 532.35 | 36.41 | 38.82 |
| 500 | Timeout | nachher | 48.37 | 32.24 | 12.10 | 14.54 |

Die künstliche Transferwartezeit verschiebt nachher weder die lokale
Positionsveröffentlichung noch den Start der Statusprüfung entsprechend mit.
Insbesondere wartet die Anzeige nicht auf den simulierten Timeout. Dass kurze
lokale Antwort-/Paintzeiten schwanken, bleibt erwartbar; die entscheidende
Messung ist das Entfernen der 500-/1.500-ms-Abhängigkeit.

## Tests und Bestandsschutz

**240 Tests in 105,574 s: alle bestanden, keine übersprungen.**

Der vorhandene native X11-HUD-Test `tools/test_edsm_status_x11.py` bestand
zusätzlich: drei Statusmeldungen, 2.500-ms-Ausblendung, unveränderter Fokus,
leere Eingaberegion sowie erhaltene Cargo- und unabhängige Favoritenanzeige.
Sein Ergebnis steht ebenfalls in der Messrohdaten-Datei.

Die elf neuen Tests umfassen acht Veröffentlichungs-/Integrationstests und drei
Tests mit tatsächlichem Status-Threadpool.

Die Regression umfasst die neuen Veröffentlichungs-/Pooltests, SourceManager,
SourceProcessor, Quellenstartup, EDSM-/Inara-Transfer und Sicherheit,
Statusdarstellung, gezielte Inventarinvalidierung und die drei vorhandenen
UI-Caches. Kontrollierte Fehlerausgaben einzelner Tests sind beabsichtigt.
Zusätzlich wurden `compileall` für die geänderten Pythondateien und
`git diff --check` ausgeführt.

Vor Beginn wurden alle 16 damals geänderten bzw. ungetrackten Dateien per SHA-256
festgehalten. **15 davon sind bytegleich erhalten.** Nur `source_manager.py`
wurde für diesen Auftrag weiterbearbeitet. Seine bisherige gezielte
Inventarinvalidierung wurde in `_publish_local()` übernommen und durch die
vorhandenen sowie neuen Tests bestätigt. Journalquellen-, Favoriten-Bild- und
Planetengrafik-Cache sind unverändert. Keine Versionsänderung, keine Migration,
keine Änderung gespeicherter produktiver Benutzerdaten. Kein Commit, Tag, Push,
Release; `github.sh` wurde nicht ausgeführt.

## Verbleibende Grenzen und Risiken

- Ein weiterer Sprung, der erst während eines vorherigen Transfers eintrifft, wartet weiterhin in der serialisierten Quellenqueue. Im Integrationstest wird A früh angezeigt, während die später eintreffenden B/C bis zur Freigabe des A-Transfers warten; anschließend werden die Positionen in Reihenfolge A/B/C veröffentlicht. Diese Optimierung entfernt die Wartezeit des **eigenen** Transfers nach erfolgreicher lokaler Verarbeitung. Eine umfassende Trennung von Ingestion- und Uploadqueues wäre eine größere Architekturänderung und wurde nicht vorgenommen.
- Zwei bereits laufende langsame Statusanfragen können beide Poolplätze blockieren. Die neueste Anfrage wartet dann bis zum Abschluss bzw. bestehenden Timeout eines laufenden Auftrags.
- Eine frühere Statusprüfung kann EDSM erreichen, bevor der eigene Upload das neue System dort bekannt gemacht hat. `unknown` ist dann ein zeitpunktbezogenes Serverergebnis; es wird kein bekanntes System aus dem eigenen Upload abgeleitet und kein zusätzlicher automatischer Statusabruf eingeführt.
- Pollingwartezeit, bestehende lokale Verarbeitung, GUI-Last und reale Netzwerk-/Serverlaufzeiten bleiben bestehen.
- Kein Live-Elite-Ende-zu-Ende-Test, keine Windows-Livemessung, keine komplette projektweite Testsuite. Shutdown bleibt kooperativ mit dem bestehenden Zeitlimit; fremde blockierte Netzoperationen werden nicht zwangsweise beendet.

## Git-Status

Vorher:

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

Nachher:

```text
 M cmdrhelper/edsm_system_status.py
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
?? docs/edsm-publication-x11.json
?? docs/edsm-publication.md
?? docs/inventory-invalidation-x11.json
?? docs/inventory-invalidation.md
?? tests/test_edsm_status_queue.py
?? tests/test_favorite_preview_cache.py
?? tests/test_inventory_invalidation.py
?? tests/test_source_publication.py
?? tests/test_system_overview_cache.py
?? tools/benchmark_edsm_publication.py
?? tools/benchmark_inventory_invalidation.py
```

Die Änderungen bleiben uncommittet. Weitere Arbeiten warten auf Freigabe.
