# CMDRHelper 3.4.6 – Stabilität, Performance und Windows-Darstellung

Lokale Releasevorbereitung des bereits implementierten und getesteten Stands.
Keine neuen Funktionen oder weiteren technischen Optimierungen im Rahmen dieser
Vorbereitung. Kein Commit, Push, Tag oder Veröffentlichung.

## Journalarchive und P1-Stabilität

Archivimport und Live-Watcher sind koordiniert: Während Import und anschließender
Nachholung versucht der GUI-Watcher keinen konkurrierenden synchronen
DB-Schreibzugriff. Die Nachholung neuer und gewachsener Journale läuft im Worker;
der Mainthread übernimmt das Ergebnis. Dateiersetzung, Kürzung oder nicht sicher
verifizierbare Identitäten führen zum sicheren Abbruch mit ausstehender Nachholung.
Cursor, Signatur und Zustandsübernahme werden für die jeweilige Datei atomar
bestätigt; eine unvollständige letzte Zeile bleibt offen.

Der Importmarker bestätigt nur den tatsächlich erfolgreich gelesenen Dateistand.
Späteres Wachstum wird nicht vorzeitig als verarbeitet markiert. Körper werden
vor dem Schreibblock einmal nach System gruppiert; wiederholte vollständige
Körperdurchläufe pro System entfallen. Die fachliche Verarbeitung bleibt erhalten.

## Mining und Chronik

Der Live-Pfad wird einmal vor der Ereignisschleife aufgelöst. Innerhalb eines
Refreshs werden gelesene und geparste Live-Ereignisse gemeinsam für Mining und
Carrier verwendet. Die schwere Dateiarbeit bleibt im QThreadPool-Worker;
Bestandssemantik und vollständiges historisches Replay bleiben erhalten.

Ein Klick auf den Systemnamen in der geöffneten Chronik-Systemansicht kopiert
exakt den Namen über die Qt-Zwischenablage. Ein Hand-Cursor zeigt die Klickbarkeit;
zusätzliche Schaltflächen, Dialoge oder Erfolgsmeldungen gibt es nicht.

## Windows-Tab-Darstellung

Ursache waren nicht vollständig gestylte Tabs: Die native Qt-Windows-Darstellung
konnte helle Flächen des Basisstils mit heller Theme-Schrift kombinieren.
`cmdrhelper/ui/styles.py` definiert explizite Light-/Dark-Styles für `QTabWidget`,
`QTabWidget::pane`, `QTabBar` und `QTabBar::tab` einschließlich `:selected`,
`:!selected`, `:hover` und `:selected:hover`. Materialien- und Routenplaner-Tabs
haben damit lesbare aktive, inaktive und Hover-Zustände sowie passende Rahmen.
Keine Eingabefeld-, ComboBox- oder SpinBox-Änderung war nötig.

Die bereits bestandenen **522 Offscreen-Tabprüfungen** mit Qt „Windows“ und
„Fusion“ decken beide Views, Light/Dark, Themewechsel und die Tab-Zustände ab.
Der Mindestkontrast der Theme-Textfarben beträgt **11,81:1**. Pane-Rahmen und
Seitenhintergründe wurden ebenfalls geprüft. **24 Regressionstests bestanden**;
für vergleichbare Bildaufnahmen lag die Maus außerhalb der Tabs.
**Kein nativer Windows-Test wurde durchgeführt.**

## Kompatibilität, Testbasis und Packaging

**Keine DB-Schemaänderung und keine Migration.** Die integrierte Hilfe bleibt
unverändert. Updatefenster und alle zwölf READMEs erhalten neue Hinweise für
3.4.6; sämtliche historischen Releaseeinträge bleiben erhalten.

Vorhandene Testbasis: **1.397 bestandene Tests**, ergänzt durch die oben genannten
**522 Offscreen-Tabprüfungen und 24 Regressionstests**. Diese Ergebnisse stammen
aus der vorherigen Validierung. Für 3.4.6 werden keine neuen Tests erstellt und
keine vollständige Testsuite erneut gestartet. Die Releaseprüfungen beschränken
sich auf Version, i18n-Konsistenz, Releasezuordnung, Historienerhalt und ZIP-Inhalt
sowie Integrität.

Der normale Releaseweg ist `bash create_release.sh`; das Ziel lautet
`release/CMDRHelper_v3.4.6.zip`. Packaging-Prüfungen umfassen aktuelle
Produktivdateien, Tab-Styles, `journal_catchup.py`, Chronik-Zwischenablagecode,
Installer, Startskripte, Updater und vorhandene Windows-/UNC-Pfadbehandlung.
Die Paketvollständigkeit und Übereinstimmung mit dem Arbeitsstand sind keine
native Windows-Laufzeitprüfung. Die vorhandene `pathlib.Path`-Verwendung bleibt
unverändert. Einschränkung: `start.bat` verwendet `cd /d`; ein direkter Start
aus einem UNC-Installationspfad ist damit nicht abgesichert. Diese Vorbereitung
ändert die Start- oder Pfadlogik nicht. Datenbanken, Backups, Journale, Logs,
Diagnosepakete, Homm-/Supportdaten, temporäre Analysen, Testartefakte und
Python-Caches gehören nicht ins ZIP.
