# Optionales Performance-Profil

Das Profil ist eine reine Diagnose. Es verändert weder Cachefristen noch
Journalzuordnung, Uploadfreigaben, Worker-Reihenfolge oder GUI-Fachlogik.

## Start und Ende unter Linux

Den bisherigen Helper normal beenden. Elite Dangerous muss nicht neu starten.
Im Projektverzeichnis:

```bash
cd ~/Projekte/CMDRHelper
CMDRHELPER_PROFILE=1 ./start.sh
```

Der geprüfte Startweg ist `start.sh` → `venv/bin/python main.py` →
`cmdrhelper.app.run()`. Das Startscript reicht die Umgebungsvariable weiter.
Die bestehende Instanzsperre bleibt erhalten. Es gibt keine GUI-Aktivierung und
keine nachträgliche Instrumentierung eines bereits laufenden Prozesses.
Nur der exakte Wert `1` aktiviert die Diagnose; ohne Variable oder mit `0`
bleibt sie aus. Der normale Startbefehl lautet weiterhin `./start.sh`.

Beim regulären Beenden wird der Diagnose-Timer gestoppt. Nach Rückkehr der
Ereignisschleife wird der Schreibpuffer geleert und die Zusammenfassung erstellt.
Auch ein Startfehler nach Erlangen der Instanzsperre schließt die Diagnose ab.
Bei einem dauerhaft hängenden Schreibmedium wartet der Prozess höchstens zwei
Sekunden auf den Diagnose-Schreibthread und meldet einen unvollständigen Abschluss.
Bei Absturz/erzwungenem Prozessende kann der letzte Datensatz fehlen.

## Ausgabe und Grenzen

Ausgabe ausschließlich unter `/tmp/cmdrhelper-profile/`:

- `profile-<UTC>-<PID>-<Zufall>.jsonl`: Zeitstempel, monotone Zeit, Messpunkt,
  Dauer, Thread-CPU-Zeit und freigegebener technischer Kontext.
- Gleichnamige `.jsonl.summary.json`: Häufigkeiten und jeweils die 20 längsten
  Vorgänge für Menü, Hauptthread, Journal, Ergebnisübergaben, Spansh sowie
  Hintergrund-/GUI-Arbeit.

Der GUI-Thread schreibt keine Diagnosedateien. Nur im Profilmodus übernimmt ein
Schreibthread Dateiausgabe und Zusammenfassung. Es gibt **keine Dateigrößenlimits**,
kein Gesamtbudget für das Verzeichnis und keine automatische Löschung alter Dateien.
Die Aufzeichnung läuft bis zum regulären Ende der Anwendung.

Schnelle Routinevorgänge werden im Speicher aggregiert. Höchstens 512 Kombinationen
von Messpunkt, Threadklasse, Ansicht, Ergebnis und Journalereignistyp werden geführt.
Jede enthält Anzahl, Minimum, Maximum, Mittelwert sowie summierte Wand-, CPU- und
Eigenzeiten. Ein Histogramm mit 37 festen Klassen liefert p50/p95/p99 als ausdrücklich
ungefähre obere Schranken (logarithmische Zweierabstände, keine exakten Perzentile).
Überlauf neuer Kombinationen zählt `aggregate_overflow`; vorhandene Gruppen laufen weiter.

Nur interessante Detaildatensätze kommen in die nicht wartende Schreibwarteschlange
mit maximal 2.048 Einträgen. Routinefluten können diese Reserve nicht belegen.
Bei einer Überlast ausschließlich durch wichtige Datensätze werden auch solche
verworfen: `important_dropped` zählt verlorene Detailzeilen einschließlich
Span-Kontextzeilen; `dropped` enthält zusätzlich verworfene Übergabemarkierungen.
`queue_peak`, `aggregated_routine` und `unmatched_handoffs` ergänzen die Auswertung.
Es gibt keine Garantie verlustfreier Ausgabe bei beliebig langsamen Schreibmedien.

| Detail ab einschließlich | Messpunkte |
|---|---|
| 20 ms | Datenbank und SQL |
| 100 ms | Menü, GUI, Refresh-Unterabschnitte, Signale/Slots und Handoffs |
| 200 ms | Journal, Worker, Warteschlangen, Source-Timer und sonstige Dauern |
| 200 ms | Qt-Dispatch und Qt-Timerverzögerung (bestehende Instrumentierung) |

Fehler, Spansh-Fehlerpausen/Serverwartezeiten, Spansh-Start/Ergebnis sowie ausgewählte
Journalereignisse und Wiederholungen werden unabhängig von der Dauer detailliert
erhalten. Spansh-Cachetreffer und gewöhnliche Nichtstarts werden aggregiert.
Die Schwellen stammen aus der Sitzung vom 08.11.2026: SQL-execute p95 1,12 ms,
Connect p95 2,27 ms, Transaktionsabschluss p95 6,24 ms. 20 ms hebt auffällige
DB-Vorgänge hervor; GUI-Schwellen liegen unter der kritischen 200-ms-Grenze.

Alle 60 Sekunden schreibt der bestehende Writer kumulative Aggregate als
`session.aggregate`, beim Ende nochmals den vollständigen Stand. Diese Stände
**nicht addieren**: jeweils der letzte ist maßgeblich. Der Writer leert seinen
Dateipuffer spätestens bei seiner nächsten Prüfung nach einer Sekunde oder bei
Leerlauf. Nach einem Absturz können seit dem letzten Zwischenstand hinzugekommene
Routinewerte sowie noch gepufferte Details fehlen; ohne `session.end` ist die
Sitzung unvollständig. Es wird kein zusätzliches fsync pro Datensatz erzwungen.

Schreibfehler oder weniger als 8 MiB tatsächlich freier Dateisystemplatz deaktivieren
nur die Diagnose; Prüfung beim Öffnen und anschließend alle fünf Sekunden im
Writer. Das ist kein Sitzungs-/Verzeichnisbudget. Eine feste stderr-Meldung enthält
keine Pfade oder Ausnahmetexte. Bei vollem Medium kann kein Abschluss mehr gespeichert
werden; der letzte vorhandene Zwischenstand bleibt offline auswertbar.
Dateien werden exklusiv mit 0600 erstellt, neue Verzeichnisse mit 0700. Fremde oder
als Symlink angelegte Zielverzeichnisse werden abgelehnt.

Ohne Aktivierung bleiben Messdekoratoren identisch zur Originalfunktion: keine
zusätzlichen Aufrufwrapper, Zeitabfragen, Threads, Timer oder Diagnoseausgaben.
An einzelnen Integrationsstellen verbleibt eine Prüfung des Aktivierungsflags.
Es wird keine absolute Null-Overhead-Garantie behauptet. Im aktiven Modus sind
insbesondere Zeitabfragen pro Qt-Ereignis zusätzliche Arbeit; die Diagnose ist
kein unverfälschter Benchmark des deaktivierten Betriebs.

## Messpunkte

| Messpunkt | Aussage |
|---|---|
| `menu.switch.begin/end` | Synchroner Wechsel einschließlich der im Aufruf ausgeführten Aktualisierungen; feste Ansichtskennung, Wandzeit und CPU-Zeit des aufrufenden Threads. Alle 13 Hauptseiten sind benannt. Mining innerhalb Materialien erscheint als Materialien. |
| `qt.dispatch` | Qt-`notify()`-Aufruf ab 200 ms; numerischer Ereignistyp, Wand-/CPU-Zeit und Anzahl verschachtelter Ereigniszustellungen. |
| `qt.event_delay` | Verspätung eines zusätzlichen präzisen 100-ms-Timers ab 200 ms gegenüber dem erwarteten nächsten Aufruf. |
| `gui.state_refresh`, `gui.refresh_all`, `gui.visible_details` | Ausgewählte synchrone Zustands-/GUI-Aktualisierungen. |
| `journal.read` | Lesen des Rohinhalts in einem Catch-up-Durchlauf. |
| `journal.read_delta` | Lesen **und Dekodieren** eines Journaldeltas. |
| `journal.reconstruct` | Vollständige bestehende Zustandsrekonstruktion; enthält weitere Lese-/Verarbeitungsschritte. |
| `journal.process`, `journal.catchup`, `journal.pass` | Gesamtverarbeitung und enthaltene Catch-up-Abschnitte; verschachtelte Zeiten nicht addieren. |
| `journal.events` | Nur Anzahl ausgewählter Ereignistypen, u. a. FSDJump, Location, CarrierJump, Cargo, Transfers, Kauf/Verkauf. Keine Nutzdaten. |
| `journal.retry`, `journal.retry_wait` | Angeordnete Fehlerpause und tatsächlich verstrichene Zeit bis zum nächsten zugelassenen Watcher-Poll. |
| `source.queue_wait` | Aufnahme einer normalen Quellenanforderung bis zur Entnahme aus der bestehenden Warteschlange; nicht jede interne Start-/Reimport-Anforderung durchläuft diesen Messpunkt. |
| `source.handoff` | Fertigstellung lokaler Verarbeitung/Signalversand bis zum Eintritt in den GUI-Empfänger. |
| `journal.to_gui` | Beginn der Quellenverarbeitung bis zum Ende der synchronen lokalen Veröffentlichung einschließlich direkt angeschlossener GUI-Slots. |
| `source.gui_publish`, `source.project`, `source.finished` | Veröffentlichung, Projektion und Abschlussbehandlung. |
| `worker.thread`, `worker.pool`, `worker.queue_wait`, `worker.handoff` | Bestehende Startup-/Quellen-Threads und über ExitTasks verfolgte Qt-Jobs, Warteschlange und verzögerte Abschlusszustellung. Nicht jeder fremde Thread wird erfasst. |
| `worker.online_transfers`, `worker.edsm`, `worker.inara` | Bestehende Serviceverarbeitung; keine zusätzlichen Netzwerkaufrufe, unveränderte Autorisierung. |
| `spansh.decision`, `spansh.lookup`, `spansh.result` | Automatisch/manuell, Cachetreffer und Alter, Fehlerpause/Serverwartezeit, Start sowie Ergebnis und Stationsanzahl. |
| `spansh.request`, `spansh.fetch`, `spansh.worker`, `spansh.handoff` | Gesamtanfrage, Abruf, Worker und Ergebniszustellung. |
| `spansh.publish`, `spansh.state_update`, `spansh.gui_update`, `spansh.explorer_update` | Veröffentlichung und synchrone Aktualisierung von Stationsmodell und betroffenen Ansichten. Der Tabellenmesspunkt kann auch lokale Aktualisierungen ohne Netzabruf erfassen. |

Interessante Dauermesspunkte tragen `.begin` und `.end`; `span` und `parent_span` verbinden
verschachtelte Messungen. Ereignismeldungen im selben Thread übernehmen die
aktive Span-Kennung. Übergaben zwischen Threads werden über nur im Speicher
gehaltene Schlüssel und die technische `origin_span` verbunden; Quellen-/System-/Commander-Identitäten werden
nicht geschrieben. `outcome=success` eines allgemeinen Funktions-Endes bedeutet
normale Rückkehr, nicht zwingend fachlichen Erfolg. Für Spansh ist dafür die
separate Meldung `spansh.result` maßgeblich.

## Interpretation

`duration_ms` verwendet `perf_counter_ns()`, `cpu_ms` die CPU-Zeit des ausführenden
Threads. Große Wandzeit bei kleiner CPU-Zeit ist ein Hinweis auf Warten, jedoch
kein Beweis für einen bestimmten Lock oder den GIL. UTC-Zeitstempel werden aus
einem Startanker und monotoner Zeit abgeleitet; nachträgliche Wanduhrkorrekturen
verändern die gemessenen Dauern nicht.

Eine lange `qt.dispatch`-Dauer kann eine verschachtelte Ereignisschleife, etwa
in einem modalen Dialog, enthalten. `nested_dispatches` hilft bei der Einordnung.
Sie darf nicht pauschal als durchgehend eingefrorene GUI bezeichnet werden.
`qt.event_delay` ergänzt diese Sicht; dessen zusätzliche Verspätung ist nicht
identisch mit der Gesamtdauer einer einzelnen Funktion. Alle Werte dienen der
Ursacheneingrenzung, nicht als automatische Reparaturentscheidung.

Menü- und Journal-GUI-Messungen enden bei synchroner Veröffentlichung, **nicht**
bei nachgewiesener Bildschirmausgabe. Späteres Rendering, getrennt gepostete
Slots, Zeit vom Spielereignis bis zum Schreiben ins Journal und vollständige
Ende-zu-Ende-Latenz werden nicht behauptet. Es gibt keine allgemeine Python-
Funktionsverfolgung. SQL-Zeiten werden nur in den unten beschriebenen Datenbankabschnitten erfasst.

## Kurzauswertung

Die Zusammenfassung wird automatisch beim Beenden erstellt. Eine JSONL-Datei
kann unabhängig vom Helper auch nach einem abgebrochenen Lauf ausgewertet werden:

```bash
venv/bin/python -B -m cmdrhelper.performance_profile \
  /tmp/cmdrhelper-profile/profile-<konkrete-Sitzung>.jsonl
```

Dabei werden weder QApplication noch Anwendungszustand gestartet. Unvollständige
letzte JSON-Zeilen werden übersprungen. Zuerst die längsten Menüwechsel und
Qt-Verzögerungen betrachten, dann zugehörige Journal-/Worker-/Spansh-Zeitfenster.
`thread=main/worker` und CPU-Zeit beachten; überlappende Abschnitte nicht addieren.
API-Schlüssel, Journalinhalte, Dateipfade, Commander- und Systemnamen sowie
Ausnahmetexte gehören ausdrücklich nicht zur Ausgabe.


## Phase 2: Restzeit in AppState.refresh

Phase 2 führte `format_version=2` ein. Neue Sitzungen verwenden in Phase 3
`format_version=3`; der Offline-Leser unterstützt weiterhin Format 1 und 2.

Die sieben zusätzlichen `state.*`-Abschnitte messen
`_apply_commander_identity`, `_own_explorer_bodies`, `_visible_commander_missions`,
`_refresh_explorer_values`, `_load_edsm_cache_for_current_system`,
`_apply_live_cargo_snapshot` und `_poll_ship_cargo`.
`source.tick` und `journal.poll` ordnen die vorhandenen Timer-Callbacks zu.
Lange `qt.dispatch`-Datensätze enthalten zusätzlich eine feste technische
Empfängerklasse (`receiver`); unbekannte Klassen erscheinen als `other`.
Objektnamen, Fenstertexte oder dynamische Callbacknamen werden nicht übernommen.

`signal.changed`, `signal.cargoSnapshotChanged`, `signal.shipRouteInputsChanged`,
`signal.inventoryChanged` und `signal.miningSalesChanged` umfassen die
instrumentierten Emissionen in AppState/SourceManager. Die erfassten synchronen
Slots sind über `slot.*` zugeordnet: Handel, Powerplay, Commanderansicht,
Mining-Anzeige, Mining-Inventar/-Markt, Materialien, Odyssey, Missionsankunft
und Routenplaner. Weitere Emissionen aus anderen Modulen und nicht instrumentierte
Empfänger können vorhanden sein. QueuedConnection-Slots sind nicht Teil der
synchronen Emit-Dauer; für sie gelten die bestehenden Handoff-Messpunkte.

### Datenbankzeiten richtig lesen

- `db.connect` umfasst die bestehende Verbindungserstellung samt PRAGMAs;
  `db.open` misst den nativen `sqlite3.connect()`-Aufruf separat.
- Fachabschnitte: `db.upsert_commander`, `db.commander_summary`,
  `db.chronicle_system_details`, `db.system_stations`, `db.powerplay_merits`,
  `db.learned_bio_values`.
- Innerhalb dieser Abschnitte: `sql.execute`, `sql.executemany`,
  `sql.executescript`, `sql.fetchone`, `sql.fetchmany`, `sql.fetchall`.
  Keine SQL-Texte, Parameter, Dateipfade oder Zeileninhalte gelangen in die Ausgabe.
- Cursoriteration verursacht **keine Protokollzeile pro Ergebniszeile**:
  `sql_iteration_ms`, `sql_iteration_cpu_ms`, `sql_iteration_steps` sammeln die
  nativen `next()`-Aufrufe einschließlich Endeprüfung im umgebenden Span;
  bereits gesondert gemessene verschachtelte Aufrufe werden dabei abgezogen.
  Auch ein vorzeitig abgebrochener Durchlauf behält seine bis dahin gemessenen
  Schritte. Explizit angeforderte fremde Cursorfabriken bleiben unverändert.
- `db.transaction_exit` misst den vorhandenen Kontextabschluss (Commit oder
  Rollback). Explizite Aufrufe tragen `db.commit`, `db.rollback` bzw. `db.close`.
  Ein SQLite-`with` schließt die Verbindung nicht: Es wird **kein zusätzlicher
  close-Aufruf eingeführt**. Implizite Freigabe durch Garbage Collection wird
  nicht zuverlässig gemessen und erhält deshalb keinen erfundenen Abschlusswert.
- Verbindungen außerhalb `CMDRDatabase._connect()` werden nicht ersetzt.

SQLite kann bereits während `execute()` erste Ergebnisse berechnen; Fetch und
Iteration können die Abfrage weiter ausführen und Zeilen konvertieren. Die
Abschnitte sind daher API-Zeiten, keine perfekte Trennung von Datenbank-CPU,
Datenträgerarbeit, Sperrwartezeit und Python-Konvertierung. Insbesondere ist
`db.open` keine reine Verbindungswartezeit. Eine lange SQL-/Commit-Dauer kann
Warten enthalten, weist aber keine bestimmte Sperre nach. Isolation, Timeout,
Transaktionsgrenzen und Rückgabewerte bleiben unverändert.

### Verschachtelung ohne doppelte Zählung

Jeder abgeschlossene Span enthält zusätzlich `self_ms` und `self_cpu_ms`:
Gesamtzeit minus die Zeiten direkt enthaltener Messspannen desselben Threads.
Die Unteraufrufe enthalten ihrerseits bereits ihre Kinder; diese werden beim
Elternaufruf nicht nochmals abgezogen. Gemessene Cursoriterationsschritte werden
ebenfalls berücksichtigt. Die Restzeit ist **nicht ausschließlich Eigenarbeit**:
Sie enthält weiterhin nicht instrumentierte Unterfunktionen, Wartezeit und
Messaufwand. Gesamtzeiten von Eltern und Kindern niemals addieren.

Die Zusammenfassung gruppiert Datenbank, Signale/Slots und Refresh-Abschnitte
separat und enthält auch die Restzeiten. Bei Pufferüberlauf oder Schreibfehlern sind
Detailspannen möglicherweise unvollständig; die Restzeitberechnung selbst
verwendet den Laufzeit-Stack unabhängig von der Dateiausgabe.

## Phase 3: zeitliche Zuordnung und nächste Sitzung

Ein langsamer Kindaufruf erhält seine gesamte aktive Elternkette: ursprüngliche
Beginnzeit, Span-ID, Parent-ID und später die vollständigen Endwerte. Beginnzeilen
können daher nachträglich in der Datei erscheinen; für die Chronologie sind
`monotonic_ns`/`start_ns` maßgeblich, nicht die Zeilenreihenfolge.
Auch ein wichtiger Einzelstatus innerhalb eines Spans erhält diesen Kontext.
Fast abgeschlossene Kinder werden nicht rückwirkend einzeln gespeichert; ihre Zeiten
bleiben in den Aggregaten und in der Subtraktion für die Eigenzeit des Elternspans.
Uninstrumentierte Arbeit lässt sich dadurch weiterhin nicht genauer zuordnen.
Bei Übergabemarkierungen wird die Herkunftskette erhalten, ohne Schlüsselwerte zu loggen.

`counts` zählt ausgegebene Details; `aggregates[*].count` zählt beobachtete Vorgänge
(einschließlich Details). `aggregated_routine` zählt nur nicht einzeln ausgegebene
Routinevorgänge. Aggregate enthalten keine zusätzlichen künstlichen Begin-Ereignisse.
Die automatisch geschriebene Zusammenfassung und der Offline-Leser liefern diese
Kennzahlen; alte `capped`-Sitzungen bleiben lesbar, neue Sitzungen besitzen kein Limit.

Den bisherigen Helper für den nächsten Live-Test regulär beenden und einmal mit
`CMDRHELPER_PROFILE=1 ./start.sh` starten. Danach mindestens 60 Minuten typische
Menüwechsel, Systemwechsel und Frachtaktionen erfassen und regulär beenden.
Vor der Auswertung Vollständigkeit, `important_dropped` und `aggregate_overflow`
prüfen. Der Live-Test wird nicht automatisch gestartet.

## Missionsankunft: interne Abschnitte

`slot.mission_arrival.update` enthält jetzt folgende Abschnitte. Sie verwenden
wie bisher Wandzeit, Thread-CPU, Eigenzeiten und Span-/Parent-IDs; schnelle Aufrufe
werden aggregiert, `arrival.*`-Aufrufe ab 100 ms detailliert erhalten.

| Messpunkt | Gemessene Arbeit |
|---|---|
| `arrival.snapshot` | Gesamte Ermittlung und Validierung des Arrival-Snapshots |
| `arrival.process_check` | Vorhandener Prozessbeobachtungs-Cache einschließlich nötiger Abfrage |
| `arrival.inspect_instances` | Nur tatsächlich ausgeführte Prozessabfragen innerhalb der Arrival-Prüfung |
| `arrival.source_binding` | Bestätigte Quelle, Commander-Prüfung und Auswahl der Index-Sitzungen |
| `arrival.projection` | `SourceProcessor.projection_for()`, einschließlich dessen Dateisignaturen und vollständiger Projektionskopie |
| `arrival.journal_checks` | Projektionszuordnung, Pfadauflösung, Journalauflistung/-sortierung, Dateisignatur und Prozessidentität |
| `arrival.cache_check` | Vergleich der gespeicherten Identität und Dateisignatur |
| `arrival.cache_rebuild` | Bei Cachemiss: vorhandenes Journal lesen/dekodieren, prüfen und Arrival-Zustand rekonstruieren |
| `arrival.status_read` | `Status.json` lesen, dekodieren und auf konsistente Datei prüfen |
| `arrival.status_validation` | Zeit-, Flag-, Orts- und Ankunftsnachweise auswerten |
| `arrival.journal_recheck` | Erneute Journal-Dateiprüfung nach Statuszugriff |
| `arrival.mission_match` | Missionsabgleich und bestehende Identitäts-/Blinkzustandsberechnung |
| `arrival.table_update` | Zellentexte, Tooltips, vorhandener Blinktimer und Anforderung der Viewport-Aktualisierung |
| `signal.arrivalChanged` | Synchrone Signalzustellung an die bestehenden Empfänger |
| `slot.missions.selection_changed` | Tatsächlicher Missionsdetail-Empfänger in MainWindow, auch bei anderen Aufrufanlässen |

`arrival.cache` zählt `cache_hit` und `cache_miss` ohne Journalpfade oder Identitäten.
Prozesscachetreffer erkennt man am `process_check` ohne enthaltenen `inspect_instances`;
die Prüfungen werden dadurch weder häufiger noch seltener ausgeführt.
`table_update` ist keine Messung abgeschlossener Bildschirmausgabe. Die Projektion
umfasst weiterhin sowohl interne Dateiprüfung als auch `deepcopy`; ihre Zeit ist
nicht automatisch reine Kopierzeit. Nicht gemessene Unterarbeit und Objektfreigaben
können weiterhin in der Eigenzeit des übergeordneten Abschnitts liegen.

Ohne Aktivierung führen die Blockmarkierungen keine Zeitabfragen, Dateizugriffe,
Thread- oder Timerstarts aus. Ein gemeinsam genutzter inaktiver Kontext vermeidet
zusätzliche Kontextobjekte; die kleinen Python-Aufrufe der Blockmarkierungen bleiben.
Die Geschäftsanweisungen einschließlich früher Rückgaben und Fehlerbehandlung
bleiben an ihrer bisherigen Stelle. Die neuen lokalen Tests und Messszenarien
verwenden ausschließlich synthetische Journale, Prozessverzeichnisse und Qt-Ansichten.

## Phase 4: Source-Timer und Linux-Prozessprüfung

`source.tick` bleibt der äußere Abschnitt von `SourceManager._tick()`.
Folgende Messpunkte ergänzen seine bestehenden Unterspannen:

| Messpunkt | Tatsächlich gemessene Operation |
|---|---|
| `process.inspect_instances` | Linux-Prozessprüfung insgesamt, auch bei Aufrufen aus Arrival |
| `process.enumerate` | Uptime, Tickfrequenz und Auflistung des Prozessverzeichnisses |
| `process.cmdline` | Lesen und Aufteilen einer Prozess-Kommandozeile |
| `process.identity` | Lesen von `stat`, Start-Ticks und bestehende Startzeitberechnung |
| `process.environ` | Lesen und Auswerten der Umgebung einschließlich vorhandener Prefix-Auflösung |
| `process.fd_scan` | Auflistung und Prüfung der Dateideskriptoren eines Elite-Kandidaten |
| `process.fd_resolve` | Einzelne vorhandene Symlink-/Pfadauflösung |
| `process.identity_recheck` | Bestehende erneute Start-Tick-Prüfung gegen PID-Wiederverwendung |
| `process.source_binding` | `confirmed_selection()`: Prozess-, Quellen- und Commander-Zuordnung |
| `source.choose`, `source.select` | Auswahl und Anwendung der Commander-Auswahl |
| `source.select_commander` | Commander-Datenbankabfrage und Auswahl des passenden Eintrags |
| `source.settings_compare` | Vorhandenen Einstellungswert lesen und vergleichen |
| `source.settings_write` | Ausschließlich tatsächlich ausgeführte `setValue()`-Aufrufe in Auswahl/Projektion |
| `source.settings_sync` | Ausschließlich tatsächlich ausgeführtes `QSettings.sync()` in `_select()` |
| `source.transfer_check` | Initialisierungs-/Transferbedarf prüfen, einschließlich etwaiger `request()`-Aufrufe |
| `source.project` | Bereits vorhandene Messung von `refresh_selected()`, einschließlich früher Rückgaben |

`process.inspect_instances.end` erhält ausschließlich numerische Zähler:
`process_count` zählt untersuchte numerische Prozesseinträge, `fd_count` die
geprüften Deskriptoren einschließlich fehlgeschlagener Auflösungsversuche,
`elite_count` die nach erneuter Identitätsprüfung übernommenen Instanzen.
Die Zähler sind auch in Routineaggregaten als Anzahl, Minimum, Maximum, Summe
und Mittelwert verfügbar. Prozessargumente, Umgebungswerte, PID und Dateipfade
werden nicht ausgegeben. Native Windows-Prozessabfragen wurden nicht erweitert.

Die tatsächlichen Emissionen von `viewedCommanderChanged`, `observedMarketsChanged`,
`journalPositionsReady`, `commanderIdentityChanged` und `changed` in Auswahl/Projektion
erhalten Signalspannen. Zusätzlich zu den bestehenden Slotmessungen werden die
Empfänger `slot.overview.follow_live`, `slot.chronicle.commander_changed`,
`slot.screenshots.commander_changed` und `slot.edsm_status.observe` gemessen.
Direkte synchrone Aufrufe bilden Kindspannen; später eingereihte Qt-Zustellungen
werden dadurch nicht zu synchronen Aufrufen und sind nicht Teil der Emit-Dauer.

Für `process.*` und `source.settings_*` gilt die Detailschwelle 100 ms;
Signale/Slots behalten 100 ms, übrige neue `source.*`-Abschnitte 200 ms.
Schnelle Vorgänge bleiben aggregiert, langsame Kinder erhalten die bestehende
Elternkette. Wandzeit, Thread-CPU und beide Eigenzeiten verwenden unverändert
den bestehenden Span-Stack. Eigenzeiten enthalten auch Instrumentierungsaufwand.

Ein unveränderter Commander kann weiterhin durch `choose()`/`_select()` laufen.
Die Messung unterscheidet dies von tatsächlichen Schreib- und Sync-Aufrufen;
auch der vorhandene Sync-Wiederholungsfall bei QSettings-Fehlerstatus bleibt bestehen.
Das ist keine neue Auswahl-, Cache- oder Speicherlogik. Ohne Aktivierung entstehen
keine Zähler, Recorder, Zeitabfragen, Threads oder Timer; die inaktiven Blockmarkierungen
verursachen lediglich kleine Python-Aufrufe.

`tests/test_source_tick_profile.py` verwendet synthetische Prozessverzeichnisse,
temporäre QSettings und QObject-Signale. Es prüft große Kandidaten-/FD-Mengen,
Identitätsstabilität, Commander-/Quellenwechsel, Datenschutz sowie gezielt verzögerte
Prozesszugriffe, Syncs und synchrone Empfänger. Künstliche Wartezeiten belegen die
korrekte Zuordnung, nicht die Ursache früherer Live-Verzögerungen. Eine große
Wandzeit bei kleiner Thread-CPU trennt allein I/O-, GIL- und Scheduling-Wartezeiten
nicht voneinander; dafür bleibt eine weitere Live-Messung erforderlich.

## Phase 5: erwartete FD-Auflösungsfehler

Die Prozessprüfung selbst bleibt unverändert. Der Recorder erkennt ausschließlich
im bestehenden `process.fd_scan` unter `process.inspect_instances` folgende
`OSError`-Kategorien aus `process.fd_resolve`: `ENOENT` → `missing`, `ESRCH` →
`process_gone`, `EBADF` → `closed`, `EACCES`/`EPERM` → `permission`.
Verschwundene Deskriptoren und nicht als Dateien auflösbare Socket-/Pipe-Ziele
können solche Fehler im normalen Ablauf erzeugen. Die Kategorie beschreibt den
Fehlercode, nicht eine nachgewiesene Ursache oder einen konkreten Deskriptor.

Diese bereits vom Aufrufer behandelten Fehler erhalten `outcome=expected_error`.
Ihre einzelnen Begin-/End-Details entfallen auch bei langsamen Fehlversuchen;
Anzahl, Wand-/Thread-CPU-Zeiten, Eigenzeiten und Histogramme bleiben in den
`process.fd_resolve.end`-Aggregaten, getrennt nach `error_category`, erhalten.
Am Ende jeder betroffenen Prozessprüfung wird je Kategorie genau eine
`process.fd_errors`-Detailmeldung geschrieben. Ihre `span` bezeichnet die
zugehörige Prozessprüfung; deren Begin-/End-Datensätze und Elternkette werden
mitgespeichert. `fd_error_count`, `fd_error_ms` und `fd_error_cpu_ms` enthalten
Anzahl und summierte Fehlerzeiten dieses Abschnitts. In Sitzungsaggregaten
zählt `count` die Zusammenfassungen; die Fehleranzahl ist dagegen
`metrics.fd_error_count.sum`.

Diese Summen sind bereits in FD-/Prozesszeiten enthalten und dürfen nicht
hinzuaddiert oder erneut von Eigenzeiten abgezogen werden. Bei einem Absturz
vor Ende einer Prozessprüfung kann deren Abschnittszusammenfassung fehlen;
bereits gespeicherte kumulative Aggregate enthalten die bis dahin erfassten
Einzelmessungen. Es gibt weiterhin keine Garantie gegen Queue-/Schreibverluste.

Andere Fehler bleiben `outcome=error` und detailliert sichtbar, mit fester
Kategorie `other_os_error` oder `other_exception`; außerhalb dieses geprüften
Aufrufkontexts werden auch bekannte Fehlercodes nicht unterdrückt. Weder
Ausnahmetexte noch Pfade, Prozessargumente oder Umgebungswerte werden gespeichert.
Die Messschwellen für Prozessprüfung, `/proc`-Auflistung, FD-Scan, Arrival,
Source-Tick und Qt bleiben unverändert. Ohne Startoption entstehen keine
Recorder-, Fehlerklassifizierungs- oder Aggregationsaktivitäten.

`tools/profile_fd_stress.py` erzeugt standardmäßig 2,5 Millionen synthetische
`ENOENT`-Fehler in 5.000 Prozessprüfungen, über mehr als 60 virtuelle Minuten.
Es greift nicht auf `/proc`, Spielprozesse oder Anwendungsdaten zu. Beispiel:

```bash
venv/bin/python -B tools/profile_fd_stress.py --output /tmp/cmdrhelper-fd-after
venv/bin/python -B tools/profile_fd_stress.py --output /tmp/cmdrhelper-fd-before \
  --recorder-source /tmp/performance_profile_before.py
venv/bin/python -B tools/profile_fd_stress.py --output /tmp/cmdrhelper-fd-inactive --inactive
```

Für den Vorher-Lauf muss die vorherige Recorder-Datei vor der Änderung gesichert
werden. Die drei Läufe nacheinander ausführen. Der Test wartet nach jeder Gruppe
auf die Queue; dies dient ausschließlich einem verlustfreien Datenmengenvergleich
und ändert nicht das nicht wartende Verhalten produktiver Diagnoseproduzenten.
`stress-result.json` dokumentiert Prozess-/Produzenten-CPU, reale Laufzeit,
Dateigrößen, Detailanzahl, Prüfsumme des Recorders und erhaltene langsame Vorgänge.
Die Dauerwerte innerhalb der Spans sind synthetisch; die gemessenen CPU-Kosten
des Testprozesses sind real, einschließlich Testschleife und Diagnose-Writer.
Der Vergleich ist kein Nachweis einer entsprechenden Verbesserung im Live-Spiel.

Kontrolllauf vom 09.11.2026, je 2.500.000 Fehler und 5.000 Prüfungen:

| Kennzahl | Vorher | Nachher |
|---|---:|---:|
| JSONL-Bytes | 1.282.164.710 | 6.953.532 |
| JSONL-Zeilen einschließlich Checkpoints | 5.030.240 | 25.340 |
| FD-Fehler-Enddetails (jeweils zusätzlich Beginn) | 2.500.000 | 0 |
| Fehlerzusammenfassungen je Prüfungsabschnitt | 0 | 5.000 |
| Reale Prozess-CPU einschließlich Writer/Testschleife | 60,471 s | 29,119 s |
| Davon aufrufender Thread | 30,802 s | 28,693 s |
| Reale Laufzeit bis Writer-Abschluss | 60,582 s | 29,335 s |

Die gleiche Testschleife ohne Diagnose benötigte 0,874 s Prozess-CPU. Beide
aktiven Läufe erfassten alle 2,5 Millionen Fehler sowie je 50 langsame
Prozessprüfungen, FD-Scans, `/proc`-Auflistungen, Source-Ticks und Qt-Verzögerungen.
88 kumulative Checkpoints deckten jeweils 5.275 virtuelle Sekunden ab;
Verwerfungen, Aggregatüberlauf und offene Detailspannen waren jeweils null.
Die Reduktion betrifft vor allem den Writer; der Produzentenaufwand bleibt
erheblich. Einzelmessungen auf diesem Rechner sind kein allgemeiner Benchmark.
Die Rohdaten und maschinenlesbaren Ergebnisse dieses Laufs liegen unter
`/tmp/cmdrhelper-phase5/stress-{before,after,inactive}/`.

## Phase 6: Linux-Prozessprüfung im Worker

Der Linux-`SourceManager` besitzt einen gemeinsamen `ProcessScan`-Koordinator.
Der vorhandene Source-Timer, Arrival und Screenshot-Zuordnung fordern darüber
Prozessevidenz an. Ein ausstehender Scan nimmt gleichzeitige Anforderungen auf;
es gibt keinen weiteren Timer und keinen zweiten gleichzeitig laufenden Scan.
Ein bereits angeforderter Scan für eine inzwischen geänderte Quellengeneration
kann einmal nachfolgen. Veraltete Ergebnisse allein lösen keine Wiederholung aus.

Der kurzlebige Python-Daemonthread führt ausschließlich die unveränderte
`inspect_instances()`-Funktion aus. Er liefert Verfügbarkeit, unveränderliche
Prozessdatensätze und Generation/Zeitpunkte über eine queued Qt-Verbindung.
Quellenkontext, QSettings, Commander-Auswahl, Projektion und GUI verbleiben im
Hauptthread. Die bestehenden Windows-Abfragen und gesonderten Sicherheitsprüfungen
für Migration/Update verwenden weiterhin ihre bisherigen Verfahren.
Die Ergebnisübernahme projiziert nur eine tatsächlich geänderte Quellen-/Commander-
Auswahl neu; gewöhnliche Aktualisierungen bleiben beim bisherigen Timer und der
Journal-Veröffentlichung. Arrival und Screenshots erhalten ein Ergebnissignal.

Der Quellenkontext umfasst Runtime-Generation, Quelle/Pfad, Aktivierung/Status
und die neueste Journal-/Commander-/FID-/Sitzungsidentität. Routine-Byteoffsets
sind keine Identitätsänderung. Manuelle Commander-/Follow-Wechsel und Reconcile
invalidieren zusätzlich die Generation. Die Ergebnisse werden gegen diesen
aktuellen Kontext geprüft, ohne Kontextwerte zu protokollieren.

Die konservative Frist von `ProcessObservation.MAX_AGE` (100 ms) gilt vom
**Scanbeginn** bis zur Nutzung, einschließlich Scan und Qt-Zustellung. Sie ist
nicht gleitend. Ein mehrsekündiger Scan blockiert die GUI nicht und autorisiert
auch nach Abschluss keine Entscheidung. Erst eine spätere bereits vorhandene
Anforderung kann neue Evidenz liefern. Unter anhaltender Last können deshalb
Live-Zuordnung/Arrival länger unbestätigt bleiben. Die Frist wird nicht pauschal
erhöht, um solche Wartezeiten zu verdecken.

Linux-Ergebnisse ohne ganzzahlige stabile Start-Ticks werden abgelehnt; die
bestehende erneute Start-Tick-Prüfung innerhalb des Scans bleibt unverändert.
Commander-Auswahl prüft die Evidenz nochmals unmittelbar vor der Übernahme.
Arrival/Screenshots behalten ihre Journal-/Projektions-/Statusprüfungen und
kontrollieren danach erneut die Aktualität. Historische Commander-/Journaldaten
werden bei fehlender Prozessevidenz nicht entfernt. Screenshot-Anforderungen
warten auf die Ergebniszustellung; stabile Dateibeobachtungen bleiben während
dieser Pause erhalten. Abgelaufene Evidenz darf keine Konvertierung autorisieren.

Beim Exit-Drain werden neue Anforderungen abgewiesen. `SourceManager.stop()`
sperrt den Koordinator endgültig, invalidiert Evidenz und unterdrückt verspätete
Ergebnisse. Es gibt kein `join()` im Hauptthread. Ein schon laufender, rein lesender
`/proc`-Zugriff darf im Daemonthread auslaufen; er wird nicht gewaltsam abgebrochen
und ist kein Schreibauftrag, auf den der Exit-Dialog warten müsste.

| Messpunkt | Bedeutung |
|---|---|
| `process.scan_worker` | Worker inklusive unverändertem `process.inspect_instances` und dessen Kindspannen |
| `process.scan_wait` | Erste Anforderung bis GUI-Ergebniseintritt; `scan_requests` und `scan_coalesced` zählen Anforderungen pro Durchlauf |
| `process.scan_apply` | GUI-Ergebnisbehandlung einschließlich synchroner Empfänger |
| `process.scan_discard` | Verworfene Ergebnisse, summiert über `metrics.scan_discarded.sum` |
| `process.scan_failure` | Unerwarteter Worker-/Threadstartfehler ohne Ausnahmetext |

Diese Werte werden nach den bestehenden Regeln aggregiert; keine Meldung je
zusammengeführter Einzelanforderung. Scan-Wandzeit und Ergebniswartezeit überlappen
und werden nicht addiert. Phase-5-FD-Aggregation, Eigenzeiten und Parent-Spans
bleiben erhalten. `arrival.process_check` misst nun die nicht wartende Anfrage;
`arrival.inspect_instances` entfällt auf dem asynchronen Linux-Pfad. Die eigentliche
Prozessprüfung erscheint stattdessen im Worker. Ohne Profilstartoption entstehen
keine zusätzlichen Diagnosedaten; die Uhr für die Aktualitätsprüfung bleibt nötig.

Gezielte Tests: `test_process_scan`, `test_source_manager`,
`test_process_selection_regression`, `test_process_observation`,
`test_mission_arrival`, `test_screenshot_sources`, `test_source_startup`,
`test_source_publication` sowie die bestehenden Profiltests. Tests benötigen
`PYTHONPATH=tests:.` und für Qt ohne Bildschirm `QT_QPA_PLATFORM=offscreen`.
Alle Prozessdaten dieser Regressionstests sind synthetisch; kein Live-Teststart.
