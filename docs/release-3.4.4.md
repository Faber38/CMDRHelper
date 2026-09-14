# CMDRHelper 3.4.4 – Hotfix

Lokale Releasevorbereitung des bereits getesteten Fixstands. Keine neuen
Funktionen; noch kein Commit, Tag, Push oder Veröffentlichung.

## Ausgangsproblem und Lösung

Sehr große MissionIDs konnten bei der Commander-Zustandsreparatur, der initialen
Journalübernahme und späteren Journalaktualisierungen einen `OverflowError`
auslösen. Python hält die Ganzzahl korrekt, SQLite INTEGER unterstützt jedoch
nur den signed-64-bit-Bereich von -2^63 bis 2^63-1.

Normale IDs bleiben INTEGER. Ganzzahl-IDs außerhalb dieses Bereichs werden
verlustfrei als gekennzeichnetes TEXT (`id:<Dezimaldarstellung>`) gespeichert.
Beim Lesen entsteht wieder der ursprüngliche Python-int. Kein Abschneiden,
Float, Modulo oder NULL-Ersatz. **Keine DB-Schemaänderung und keine zusätzliche
Migration.** Missionszuordnung, Commander-Trennung und Transaktionsgarantien
bleiben erhalten. Die Lösung ist plattformunabhängig.

## Weitere Bestandteile desselben Hotfixes

- **Journal-Watcher:** Nach fehlgeschlagener Persistenz erneuter Versuch mit
  Backoff: 2, 4, 8, 16, 32, maximal 60 Sekunden. Auch Dateiwachstum umgeht die
  Pause nicht. Fehler bestätigen weder Journaloffset noch Signatur; vollständiger
  Replay bleibt nach Behebung möglich. Erfolg setzt das Backoff zurück.
- **Score-Analyzer:** Ohne erkannten aktiven Commander zunächst leere Statistik
  statt ValueError; normale Auswertung, sobald ein Commander verfügbar ist.
- **Privacy-Diagnose:** Sichere technische Klassifikation mit Feld, normalisiertem
  Python-Typ und Werteklasse. Keine konkrete MissionID im Diagnose-Log. Die
  bestehende Unterdrückung freier Exceptiontexte bleibt erhalten.

Das Updatefenster und die zwölf READMEs beschreiben ausschließlich diese vier
Hotfix-Inhalte. Die integrierte Hilfe bleibt unverändert und versionsunabhängig.
Der interne Analysebericht bleibt im Repository erhalten und wird nicht in das
Release-Paket übernommen. Diagnosematerial gehört nicht zum Release.

## Kompatibilität und Downgrade

Eine vorhandene 3.4.3-Datenbank kann von 3.4.4 ohne zusätzliche Migration geöffnet
werden. Hat 3.4.4 jedoch bereits eine übergroße MissionID in der neuen TEXT-
Darstellung gespeichert, kann ungepatchtes 3.4.3 diese möglicherweise nicht korrekt
verarbeiten. **Kein Downgrade auf 3.4.3 mit derselben anschließend veränderten
Datenbank empfehlen.** Falls ein Downgrade erforderlich ist, eine vor dem
3.4.4-Betrieb erstellte DB-Sicherung verwenden. Kein automatischer Downgrade-
Mechanismus wurde ergänzt.

## Bereits erfolgte Validierung des Produktivfixes

Die vollständige Suite bestand vor der Releasevorbereitung: **1.381 Tests,
409,609 Sekunden, OK**. Abgedeckt wurden normale und übergroße MissionIDs,
signed-64-bit-Grenzen, Direktpersistenz, repair_commander_state,
apply_commander_journal_delta, bestehende Missionen, Commander-Trennung,
Neustart/Persistenz, Journalrekonstruktion und Replay, Retry/Backoff, Score-Start
sowie Privacy-Logging.

Für diese Releasevorbereitung wurden keine Tests neu erstellt, erweitert oder
geändert und keine vollständige Suite erneut gestartet. Prüfungen beschränken
sich auf die vorhandene statische i18n-Prüfung, Versions-/Dokumentkonsistenz,
Packaging-Struktur, Fixdateivergleich und ZIP-Integrität.

Der frühere Produktivtest lief unter Linux x86_64, Python 3.12.3, SQLite 3.45.1
und PySide6/Qt 6.11.2. Die Bindungsursache wurde auch anhand des CPython-3.11.9-
Quellcodes geprüft. Kein nativer Windows-Test wird behauptet. Windows-Installer,
Startskript und Updater werden auf Vollständigkeit im Paket geprüft.
