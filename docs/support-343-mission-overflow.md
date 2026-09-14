# Supportanalyse CMDRHelper 3.4.3 – Missionspersistenz

Stand: 14.09.2026. Arbeitsprojekt: `/home/holger/Projekte/CMDRHelper`.
Keine Änderung an Version, README oder Release-Dateien; kein Commit, Push oder Deployment.

## Diagnosematerial und Zeitlinie

Der angegebene Ordner `Downloads/Homm` existiert hier nicht. Untersucht wurde der
vorhandene Ordner `/home/holger/Downloads/homm`, ausschließlich lesend.
Alle sechs Dateien wurden vollständig eingelesen bzw. das Bild betrachtet:

| Datei | Bytes | Befund |
| --- | ---: | --- |
| cmdrhelper.log | 154271 | 514 zeitgestempelte Einträge, einschließlich Ende 10:11:31 |
| cmdrhelper1.log | 154164 | 513 Einträge, Ende Diagnoseexport 10:10:55 |
| cmdrhelper2.log | 151966 | 512 Einträge, Ende Beginn Diagnoseexport 10:10:55 |
| diagnose_summary.txt | 1439 | Exportzusammenfassung; enthält ausdrücklich keine Journale/DB |
| system_info.json | 465 | Windows AMD64, Python 3.11.9, PySide6/Qt 6.11.2, Version 3.4.3 |
| 2026-09-14_10-19.png | 62200 | Vorbereitungsdialog zeigt fehlgeschlagenen Start; keine Rekonstruktion verdeckter Inhalte |

Nach Normalisierung der Zeilenenden sind die beiden kürzeren Logs **exakte Präfixe**
des längsten. Keine zusätzlichen Rotationen, Journale oder Datenbank enthalten.
Die drei Dateien dürfen nicht als drei unabhängige Fehlerreihen addiert werden.
Systeminformationen: Datenbank erreichbar, 2043904 Bytes; Journalordner erreichbar,
3892 Journaldateien laut Diagnose, aber keine davon mitgeliefert. Das Exportdatum
08:10:55 UTC entspricht 10:10:55 lokaler Logzeit.

| Lokale Logzeit | Vorgang |
| --- | --- |
| 09:53:40–41 | Erster Start, Sicherungen vor v3-/v4-Migration, DB geöffnet |
| 09:53:44 | Score-Auswertung ohne aktiven Commander: ValueError |
| 09:56:08–09 | Acht Startup-Repair-Meldungen; Feature/Ergebnis redigiert, Erfolg nicht ableitbar |
| 10:00:06 | repair_commander_state → store_commander_missions: OverflowError, Rollback |
| 10:00:08 | Initialer Journalindex → apply_commander_journal_delta, Zweig Missions: gleicher Overflow |
| ab 10:00:10 | Watcher wiederholt fehlgeschlagene Übernahme zunächst ungefähr sekündlich |
| 10:01:24–28 | Zweiter Start; erneut Score-ValueError 10:01:27 |
| 10:04:31 / 10:04:34 | Wiederholung von Repair-/Initialindex-Overflow |
| 10:05:01 | Derselbe Overflow erreicht unbehandelten Ausnahmehandler |
| 10:05:15 / 10:05:40 | Journalarchivimport gestartet / Importarbeit gemeldet |
| bis 10:07:01 | Missions-Overflow weiterhin protokolliert |
| 10:07:08–10:09:48 | Fünf fehlgeschlagene Watcher-Übernahmen mit SQLITE_BUSY bei upsert_commander; längere Intervalle |
| 10:10:34–38 | Dritter Start; Score-ValueError 10:10:36 |
| 10:10:55 | Diagnoseexport |
| 10:11:31 | Anwendung beendet |

Gezählt im längsten Log: 161 Rollback-Meldungen: 153 bei Overflow, fünf bei
SQLITE_BUSY, drei beim Score-ValueError. 153 Watcher-Warnungen: 148 nach Overflow,
fünf nach SQLITE_BUSY. Die 306 Overflow-Tracebacks spiegeln Mehrfachprotokollierung
in Datenbank und Aufrufer wider, nicht 306 unabhängige Transaktionen.
Der zeitgleich laufende Archivimport ist ein plausibler Kontext für SQLITE_BUSY;
der tatsächliche Sperreninhaber ist aus dem Paket nicht feststellbar. Kein Lock-Fix
auf Verdacht vorgenommen.

## Ursache, Felder und Beleggrenzen

Reproduzierte Ursache: Ein Python-`int` außerhalb `[-2^63, 2^63-1]` wird in
`store_commander_missions()` an `sqlite3.executemany()` gebunden. Die Python-
Ganzzahl selbst läuft nicht über; die Konvertierung auf `sqlite_int64` schlägt
vor dem Schreiben fehl. Der Originaltest liefert:
`OverflowError: Python int too large to convert to SQLite INTEGER`.

Der wiederkehrende Logstack zeigt `database.py:2063`, den Zweig `Missions`:
`Missions.Active[].MissionID → _new_mission().mission_id → int() → SQLite`.
Dort wird Reward nicht aus dem Journal übernommen, sondern mit 0 initialisiert;
is_open ist 1. commander_id stammt aus der bereits zuvor erfolgreich verwendeten
DB-Identität. Für den numerischen Overflow in diesem Zweig bleibt MissionID.
PassengerMissionID, Commodity-ID und Target-ID werden dort nicht gebunden.

Sämtliche 19 Bindefelder wurden verfolgt:

| Bindefelder | Herkunft / Konvertierung |
| --- | --- |
| commander_id | Interne DB-Identität, int; zuvor für Commander-Abfragen gebunden |
| mission_id | MissionID aus Missions.Active, MissionAccepted, MissionRedirected, CargoDepot, MissionCompleted/Failed/Abandoned; vor Fix int direkt gebunden |
| reward | Reward aus Annahme/Abschluss bzw. optional NPC-Angebot; int, MAX beim Upsert. Im betroffenen Missions-Snapshot immer 0 |
| is_open | Programmseitig bool → int, ausschließlich 0/1 |
| name, internal_name | LocalisedName / Name_Localised / Name und Ersatzbezeichnungen → str |
| mission_type | Aus Missionsnamen abgeleitet → str |
| faction | Faction → str |
| status, terminal_state | Programmlogik für Annahme, Umleitung, Fortschritt und Abschluss → str |
| destination_system | DestinationSystem / TargetSystem bzw. NewDestinationSystem → str |
| destination_station | DestinationStation / DestinationSettlement bzw. NewDestinationStation → str |
| destination_body | DestinationBody / BodyName → str |
| expiry | Expiry → str |
| summary, next_step, progress_text | Abgeleitete Texte; Commodity, Target, Count und CargoDepot-Fortschritt fließen gegebenenfalls hier ein, nicht als INTEGER-IDs |
| accepted_at, last_updated | Journal-timestamp → str |

Die Vollrekonstruktion verarbeitet dieselben Missionsereignisse, aktualisiert
bekannte Missionen und liefert aktive sowie terminale Zustände an
`repair_commander_state()`. NPC-ReceiveText kann Namen, Ziele, Belohnung und Texte
ergänzen, erzeugt aber keine eigene MissionID. `normalize_missions()` und die
Commander-/Missionsansichten erhalten die Daten über `commander_missions()`.

**Nicht beweisbar:** Homms konkrete ID, Vorzeichen, ursprünglicher JSON-Werttyp
oder exakte Bitbreite. Die Logs zeigen keinen Bindefeldwert. Der Feldschluss gilt
für den reproduzierten numerischen Überlauf; der redigierte Exceptiontext allein
schließt andere theoretische Bindungs-Overflows (z.B. extrem große TEXT-Payloads)
nicht formal aus. Der Fix korrigiert den konkret reproduzierten Datenmodellfehler,
ohne einen vermeintlichen Homm-Wert zu erfinden.

Frontier dokumentiert `2^64-1` als früheren MissionID-Sentinel in Inventardaten,
der seit Journalmanual v31 für nicht missionsbezogenes Inventar entfallen soll.
Das ist ein Primärbeleg für Journalwerte oberhalb signed 64-bit, **kein Beleg für
eine gültige aktive Mission mit genau dieser ID**. Das Missionskapitel definiert
keine ausdrückliche obere numerische Grenze. Ob Homm eine echte große ID, einen
Sentinel oder abweichende Daten hatte, bleibt offen. Die Persistenz bewahrt deshalb
IDs verlustfrei, statt ihnen aus dem Zahlenwert eine neue fachliche Bedeutung zu
geben. Negative und über 64-bit große Testwerte sind Robustheitsfälle, keine
Behauptung über reguläre Elite-Missionsnummern.

Primärquellen:

- [Frontier Journalmanual v31, Änderungsliste S. 2 und Missions-Snapshot S. 8](https://hosting.zaonce.net/community/journal/v31/Journal_Manual_v31.pdf)
- [CPython 3.11.9, bind_param: _pysqlite_long_as_int64 / sqlite3_bind_int64](https://github.com/python/cpython/blob/v3.11.9/Modules/_sqlite/cursor.c#L530)
- [SQLite-Datentypen und INTEGER-Affinität](https://www.sqlite.org/datatype3.html)

## Reproduktion vor Fix und Datenmodellentscheidung

`tests/test_mission_id_persistence.py` wurde vor der Produktivcodeänderung erstellt
und ausgeführt. Drei Tests scheiterten mit OverflowError: Direktpersistenz,
Journalrekonstruktion/Repair und Journaldelta mit Missions.Active. Beim Deltatest
entsprachen die Originalzeilen 2063 und 2773 exakt Homms Stack; bei Repair 2664 und
2773. Der SQLite-Kontrolltest bestand bereits vor dem Fix.
Das damalige lokale Testergebnis liegt in `/tmp/cmdrhelper-mission-before.txt`.
Die unveränderte Ausgangsdatei database.py aus Git HEAD wurde byteweise mit
release/CMDRHelper_v3.4.3/cmdrhelper/database.py verglichen: identisch.

Gewählt: Legacy-IDs im signed-Bereich bleiben INTEGER. Andere Ganzzahl-IDs werden
als `id:<kanonische Dezimaldarstellung>` in derselben Spalte gespeichert. Beim Lesen
wird immer der unveränderte Python-int wiederhergestellt. Autoritative Updates
vergleichen und binden die gespeicherten Schlüssel; die öffentliche Sortierung
behält ihre numerische ID-Reihenfolge als letzten Sortierschlüssel.

Warum nicht bloß `str(id)`? INTEGER-Affinität wandelt eine zu große reine
Dezimalzeichenfolge in REAL um. Der Kontrolltest belegt den Verlust für `2^63+1`.
Warum keine signed/unsigned-Abbildung? Diese würde zusätzliche Annahmen über die
Bedeutung negativer IDs verlangen und könnte unterschiedliche Eingaben gleichsetzen.
Warum keine Schemaänderung? Die bestehende Tabelle ist nicht STRICT und hat einen
zusammengesetzten Primärschlüssel. Gekennzeichnetes TEXT ist dort zulässig, exakt
und eindeutig. Keine Migration, kein neuer user_version-Wert, keine Umschreibung
bestehender Missionen, keine Änderung an Commander-Fremdschlüsseln.

Kompatibilität: Der neue Code liest bestehende DBs und ihre INTEGER-Schlüssel.
Ungepatchter 3.4.3-Code versteht neue `id:`-Schlüssel nicht; ein Downgrade nach dem
Speichern großer IDs ist daher nicht rückwärts lesekompatibel. Auch rohe SQL-
Numerik auf mission_id muss die Kodierung beachten. Die Programmansichten nutzen
die dekodierende DB-Methode. Unabhängige Datenmodellfelder wie Reward werden nicht
auf Verdacht verändert. Ein künstlich übergroßes Reward kann weiterhin die signed-
Bindung verletzen; das ist nicht der in Homms Missions-Snapshot nachgewiesene Pfad.

## Watcher, Score und Privacy

Der Watcher setzte bisher nach fehlgeschlagener Bestätigung lediglich den laufenden
Versuch zurück. Da die bestätigte Signatur unverändert blieb, löste der 1-s-Timer
sofort wieder denselben State-Refresh samt Rollback aus.

Jetzt exponentielles Backoff nach Fehlerabschluss: 2, 4, 8, 16, 32, maximal 60 s,
gemessen mit monotonic(). Keine Umgehung durch weiteres Dateiwachstum. Erfolgreiche
Bestätigung und Ordnerwechsel setzen das Backoff zurück. Normale erfolgreiche
Überwachung bleibt beim 1-s-Timer. Ereignisse, Byteoffsets und bestätigte Signaturen
werden bei Fehlern ausdrücklich nicht als verarbeitet markiert. Der Integrationstest
belegt Rollback von Ort/Mission/Offset und vollständigen Replay nach Fehlerbehebung.

Score: `_require_commander_id()` wirft bei `active_commander_id is None`.
Die drei frühen Start-Stacks treten vor der Missionsreparatur auf. Es handelt sich
um eine fehlende Behandlung des noch nicht initialisierten Commander-Kontexts,
nicht um einen nachgewiesenen Benutzerfehler oder die Folge des Overflows.
`_target_system_rows()` liefert jetzt vor einer DB-Abfrage [] zurück. Die vorhandene
Auswertungslogik behandelt das als fehlende Statistik; nach Commander-Auswahl werden
wie bisher nur dessen Daten ausgewertet. Keine Änderung am globalen DB-Guard. Die bestehende UI in
`MainWindow._refresh_score_page()` fängt diesen Fehler bereits ab und zeigt eine
fehlgeschlagene Auswertung. Er ist daher für sich kein belegter Startabbruch;
der Rollback-Logger protokollierte schon den erfolglosen Lese-Kontext.

Privacy: Bestehende Exceptiontext-Unterdrückung bleibt erhalten. Pro Speicherbatch
und vorkommender großer ID-Klasse gibt es eine technische Meldung mit:
`field=mission_id`, `python_type=int` (Typ nach Normalisierung vor der Bindung),
`value_class=unsigned_64|above_unsigned_64|below_signed_64`,
`outside_sqlite_int64=True`. Keine konkrete ID, Mission, Commander-Zuordnung, Pfade
oder Journalinhalte. Klassen werden über geschlossene Enum-Listen validiert; das
Bereichsflag akzeptiert ausschließlich bool. retry_seconds ist auf 0–60 begrenzt.
Die Meldung beschreibt den erforderlichen Speichertyp, nicht einen bereits
bestätigten Commit. Rohes LogRecord und PrivacyFormatter-Ausgabe werden getestet.

## Validierung und Projektzustand

Neue Regressionen:

- Normalwert, 0, `2^63-1`, `2^63`, direkt benachbarte große ID, `2^64-1`, `2^80`,
  negative Grenzen; exakte Persistenz und numerische Reihenfolge.
- Reales synthetisches Journal → Index → Delta/Repair → SQLite; Location und
  bestätigte Offsets, idempotenter Replay, erneutes Öffnen der DB.
- Vorhandene INTEGER-Mission, int/string-ID-Upsert, aktive/abgeschlossene/
  fehlgeschlagene/abgebrochene Missionen, autoritativ inaktiv setzen ohne Löschen,
  Commander-Isolation, Umleitung nach Neustart, Normalisierung für Missionsansicht.
- Backoff, Deckelung, Dateiwachstum, Reset bei Erfolg/Ordnerwechsel und Replay einer
  tatsächlich zurückgerollten Transaktion.
- Score-Start ohne Commander und anschließende Auswertung nach Auswahl.
- Technische Klassifikation ohne IDs und Ablehnung unerlaubter Diagnosefelder.

Testumgebung: Linux x86_64, Python 3.12.3, SQLite 3.45.1, PySide6 6.11.2;
Qt offscreen. Windows/Python 3.11.9 ist hier nicht als ausführbare Testumgebung
verfügbar. Die plattformunabhängige Bindungsursache wurde unter Linux reproduziert
und gegen CPython-3.11.9-Quellcode geprüft. Keine Windows-Sonderlösung eingebaut.

Gezielte Läufe: sechs neue Missionstests, drei Watcher-Tests, sechs Score-Tests
bestanden. Vollständige Python-Testsuite:

```text
QT_QPA_PLATFORM=offscreen venv/bin/python -m unittest discover -s tests -v
Ran 1381 tests in 409.609s
OK
```

Exitcode 0, keine Fehler oder übersprungenen Tests. Enthalten sind die bestehenden
Missions-, Journaldelta-, Index-, Rekonstruktions-, Commander-, Startup-, Score-
und Privacy-Tests. Gesamtes lokales Testprotokoll: `/tmp/cmdrhelper-full-suite.txt`.
Windows-native PowerShell/Pester-Tests wurden mangels Windows/PowerShell nicht
ausgeführt; die plattformbezogenen Python-Tests sind Teil des obigen Laufs.

`git diff --check`: sauber. `git status --short`: vier geänderte Produktivdateien,
eine geänderte Testdatei, zwei neue Testdateien und dieser neue Bericht (siehe
Liste unten). Keine anderen Änderungen, nichts gestagt. Version unverändert 3.4.3.

Geänderte/neu angelegte Projektdateien:

- cmdrhelper/database.py
- cmdrhelper/journal_watcher.py
- cmdrhelper/logging_config.py
- cmdrhelper/score_analyzer.py
- tests/test_mission_id_persistence.py (neu)
- tests/test_journal_watcher_retry.py (neu)
- tests/test_score_analyzer.py
- docs/support-343-mission-overflow.md (dieser Bericht, neu)

Verbleibende Grenzen: Homms tatsächliche Daten sind nicht enthalten; keine
Reparatur oder erfolgreiche Wiederinbetriebnahme seines Rechners behauptet.
SQLITE_BUSY-Ursache/Sperreninhaber nicht eindeutig bestimmt. Keine Aussage, dass
beliebig fehlerhafte Journalfelder nun akzeptiert würden. Die ursprünglichen
Transaktionsgarantien bleiben bestehen; bestätigter Datenverlust wird nicht
zur Fehlerbehandlung eingesetzt.

Abschließender SHA-256-Abgleich aller sechs Diagnosebestandteile gegen den
Beginn: unverändert; Dateiliste ebenfalls unverändert.
