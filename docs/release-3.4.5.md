# CMDRHelper 3.4.5 – Stabilität und Performance

Lokale Releasevorbereitung des bereits getesteten Arbeitsstands. Kein Commit,
Tag, Push oder Veröffentlichung im Rahmen dieser Vorbereitung. Diese Version
enthält die vorhandenen P1-Verbesserungen und die stille Chronik-Kopierfunktion;
die Hotfixes aus 3.4.4 bleiben erhalten und werden nicht als neue Funktionen
ausgewiesen.

## Große Journalarchive: Import und Live-Verarbeitung

Der Archivimport und der Live-Watcher verwenden getrennte SQLite-Verbindungen.
Eine lange Schreibtransaktion des Imports konnte dadurch einen synchronen
Schreibzugriff des GUI-Watchers blockieren. Während SQLite wartete, konnte die
Qt-Eventloop keine Ereignisse verarbeiten.

Die Live-Verarbeitung wird nun während des koordinierten Archivimports und der
anschließenden Nachholung zurückgestellt. Der GUI-Watcher versucht in dieser
Phase keinen konkurrierenden synchronen DB-Schreibzugriff. Die Nachholung läuft
im Worker; der Mainthread übernimmt das Ergebnis. Der bestehende Watcher-Backoff
bleibt als Schutz für Persistenzfehler erhalten. Es gibt keine neue zentrale
DB-Writer-Infrastruktur; der große Import-Schreibblock bleibt eine Transaktion.

`journal_catchup.py` erfasst den Ausgangsstand und verarbeitet gewachsene sowie
neue Journaldateien in chronologischer Dateireihenfolge. Wiederholte Prüfungen
des Verzeichnisses berücksichtigen weitere Änderungen bis zur Übergabe an den
Watcher. Mehrere neue Dateien und Commander-Wechsel während der Pause werden
berücksichtigt. Dateiersetzung, Kürzung oder eine nicht eindeutig verifizierbare
Identität führen zu einem sicheren Abbruch mit weiterhin ausstehender Nachholung.

Cursor, Signatur und Zustandsübernahme werden für die jeweilige Datei atomar
bestätigt. Ein fehlgeschlagener Übernahmeschritt bestätigt keine ungespeicherten
Inhalte; bereits erfolgreich übernommene Dateien müssen bei einem erneuten
Versuch nicht nochmals angewendet werden. Erfolgreich übernommene Inhalte werden
genau einmal verarbeitet. Eine unvollständige letzte Zeile bleibt offen.
Commander-Zuordnung, Missionen, Besuche, Systeme/Körper, BIO/GEO/Codexdaten und
Kartographie-Lerndaten bleiben geschützt.

## Kürzerer Archiv-Schreibblock und korrekte Importmarker

Importierte Körper werden vor dem Schreibblock einmal nach System gruppiert.
Der bisherige vollständige Körperdurchlauf für jedes System entfällt:
O(Systeme × Körper) wird für diese Zuordnung durch eine einmalige Gruppierung
und direkte Zugriffe ersetzt. Reine Python-Vorbereitung liegt damit außerhalb
der Writer-Sperre; fachliche Reihenfolge und resultierende DB-Inhalte bleiben
erhalten.

Der Importmarker bestätigt ausschließlich den tatsächlich erfolgreich gelesenen
Dateistand. Wachstum nach dem gelesenen EOF wird nicht durch eine später erneut
ermittelte Dateigröße fälschlich bestätigt. Neue Inhalte und unvollständige letzte
Zeilen bleiben für die weitere Verarbeitung offen.

## Mining-Aktualisierung

Der Live-Pfad wird vor der Ereignisschleife einmal mit `Path.resolve()` aufgelöst.
Die Pfadnormalisierung bleibt erhalten. Innerhalb eines Refresh-Auftrags werden
die gelesenen und geparsten Live-Ereignisse für Mining und Carrier gemeinsam
verwendet; beide erhalten denselben geprüften Dateistand. Die schwere Dateiarbeit
bleibt im QThreadPool-Worker.

SRV-, Schiffs- und Carrierbestände, Transfers und Cargo-Checkpoints behalten ihre
Semantik. Das historische Replay bleibt vollständig: Aus den vorhandenen
Checkpoints wurde keine allgemein sichere verkürzte Replay-Grenze abgeleitet.
Es gibt weder eine neue Mining-Projektion noch eine neue persistente Cache-Struktur.

## Chronik

Ein einfacher Linksklick auf den Systemnamen in der geöffneten Chronik-Systemansicht
kopiert exakt den Namen über die Qt-Zwischenablage. Ein Hand-Cursor zeigt die
Klickbarkeit. Darstellung und Chronikdaten bleiben erhalten; es gibt keine
zusätzliche Schaltfläche, keinen Dialog und keine Erfolgsmeldung.

## Synthetische Messungen

Die folgenden Werte stammen aus der bereits durchgeführten synthetischen
Skalierungs- und Lock-Reproduktion. Sie sind Labormessungen, keine Zusicherung
für einzelne Rechner oder reale Archive. Insbesondere sind die Mining-Reader-
Zeiten keine Messung der gesamten manuellen Aktualisierung. Die Gruppierungswerte
messen ausschließlich die Körperzuordnung, nicht den vollständigen DB-Import.

| Journaldateien | Reader kalt vorher | Reader kalt nachher | Reader warm vorher | Reader warm nachher |
| ---: | ---: | ---: | ---: | ---: |
| 973 | 3,45 s | 1,99 s | 1,72 s | 0,25 s |
| 1.946 | 6,90 s | 4,05 s | 3,52 s | 0,58 s |
| 3.892 | 13,95 s | 8,17 s | 7,08 s | 1,26 s |

| Systeme × Körper je System | Gruppierung vorher | Gruppierung nachher |
| ---: | ---: | ---: |
| 1.000 × 10 | 202 ms | 1,06 ms |
| 2.000 × 10 | 788 ms | 2,64 ms |
| 4.000 × 10 | 3.207 ms | 6,09 ms |

In der Qt-/Lock-Reproduktion wurde vor der Koordination eine Heartbeat-
Unterbrechung von etwa 5 Sekunden beobachtet. Danach betrug die größte gemessene
Lücke etwa 23 ms bei einer 6,2 Sekunden gehaltenen Writer-Sperre; die Nachholung
war anschließend erfolgreich. Das belegt den koordinierten Importpfad, nicht
die Abwesenheit aller möglichen GUI-Verzögerungen oder externer DB-Sperren.

## Kompatibilität und Validierung

**Keine DB-Schemaänderung, keine neue Tabelle oder Spalte und keine Migration
notwendig.** Die integrierte Hilfe bleibt unverändert und versionsunabhängig.
Updatefenster und alle zwölf READMEs enthalten die neuen Release-Hinweise;
historische Einträge bleiben erhalten.

Vor der Releasevorbereitung bestand die vollständige Suite unter Linux:
**1.397 Tests, keine Fehler, keine übersprungenen Tests.** Für die Vorbereitung
werden keine Tests ergänzt oder geändert und keine vollständige Regression
wiederholt. Die zusätzlichen Prüfungen betreffen Version, Übersetzungen,
Release-Zuordnung, Dokumentkonsistenz und Paketinhalt/-integrität.

Ein nativer Windows-Test wurde nicht durchgeführt. Windows-Installer,
Startskript, Updater, Qt-Zwischenablagecode, pathlib-Pfadlogik und Catch-up-Modul
werden auf Vorhandensein und Übereinstimmung mit dem Arbeitsstand im ZIP geprüft.
Private Supportdaten, interne Supportberichte, temporäre Analyseprogramme und
Testartefakte gehören nicht ins Release-Paket.

Spätere Arbeiten können feinere Importtransaktionen, weitere Startup-Entlastung
und eine fachlich abgesicherte Begrenzung des Mining-Replays untersuchen. Diese
Version führt keine dieser zusätzlichen Architekturänderungen ein.
