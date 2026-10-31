# CMDRHelper v3.9.23

- Die Startvorbereitung endet nach den lokalen Erstversuchen, auch bei weiteren Journalaufträgen und langsamen Uploads. Fehler bleiben sichtbar.
- Der Bewertungsleser überspringt ungültige JSON-Strukturen und kann nachfolgende gültige Metadaten lesen.
- Historische Reparaturen melden technische Fehler genauer; unveränderte Fehler werden wiedererkannt und korrigierte Dateien erneut geprüft.
- Beschädigte Journale werden nicht automatisch repariert oder als erfolgreich importiert bestätigt. Bestehende Daten bleiben geschützt.

## Umfang und Datenintegrität

Der Startabschluss berücksichtigt die anfänglichen Quellen und ihre Generationen.
Folgeaufträge und externe Transfers laufen nach dem Abschluss weiter. Fehlgeschlagene
lokale Erstversuche bleiben Fehler; fehlgeschlagene oder unvollständige historische
Reparaturen werden als Teilfehler angezeigt. Ein Catch-up löscht diese Information nicht.

Der Bewertungsleser prüft JSON-Ereignisse vor Feldzugriffen. Fachliche Berechnungen,
Commander-/FID-Trennung und Transaktionsgrenzen bleiben unverändert. Reparaturfehler
enthalten einen technischen Grund, eine Zeilennummer und eine anonymisierte
Quellenreferenz. Es werden keine Journalinhalte ausgegeben.

Bis zu 128 Wiederholungshinweise werden in der bestehenden app_meta-Tabelle gespeichert.
Vor einer unterdrückten Planung werden Inhaltshashes, Dateisignaturen, Identität,
historische Abdeckung, geschützte Präfixe und Reparaturversionen erneut geprüft.
Unsichere Nachweise führen zu einem neuen Versuch. Hinweise sind keine Erfolgsmarker.
Keine Datenbankmigration; keine neuen fachlichen Funktionen.

## Belastungstest und Grenzen

Der isolierte X11-Test verwendete 3.002 synthetische Dateien: 3.000 gültige Journale
mit je sieben Ereignissen auf zwei Quellen und zwei FIDs sowie zwei beschädigte
Dateien einer dritten Quelle. Umfang etwa 3,08 MB, kein Ersatz für reale große
Windows-Journalbestände. Die Warteschlange wurde alle 100 ms nachgefüllt; Transfers
waren bis zum Startabschluss kontrolliert blockiert. Keine echten Uploads.

Der Dialog schloss nach 121,200 Sekunden beim Erststart und 38,937 Sekunden beim
zweiten Start, jeweils mit genau einem Abschlusssignal. Zwischen letztem lokalem
Abschluss und Fensterschluss lagen 57 beziehungsweise 5 ms. Die GUI-Timerlücken
betrugen maximal 81 beziehungsweise 96 ms. Messbeginn war die AppState-Initialisierung,
nicht der Prozessstart. Tests liefen teilweise parallel; keine Windows-Zeitprognose.

Nachträgliche Ereignisse wurden genau einmal verarbeitet. 3.000 Biologieeinträge,
3.002 Systembesuche, keine doppelten Besuchsschlüssel, SQLite-Integrität und
Fremdschlüsselprüfung ohne Befund. Ein korrigiertes bestätigtes Journal löste erneut
alle fünf Reparaturen aus; unveränderte Fehler blieben failed ohne erneute Planung.

Bekannte Einschränkungen:

- Kein nativer Windows-Test beim betroffenen Benutzer.
- Zeitabhängiger Quellenpanel-Test: exakte Benachrichtigungs- und Abfragezahlen sind
  nicht in jedem Gruppenlauf stabil. Ein WAL-Checkpoint invalidiert den Statistikcache
  auch ohne Journaländerung; dies wurde im aktuellen und vorherigen Stand bestätigt.
- Der Archivparser kann beschädigte Journalstrukturen weiterhin kontrolliert ablehnen.
  Diese Veröffentlichung repariert keine beliebig beschädigten Dateien.
- Eine tatsächlich blockierte lokale Erstverarbeitung besitzt keinen allgemeinen Watchdog.
- Inhaltsnachweise benötigen weiterhin Dateizugriffe; der erste Reparaturfehler kann
  durch die zusätzliche Fingerabdruckprüfung mehr Aufwand verursachen.

Die abschließenden Funktionsprüfungen vor der Releasevorbereitung umfassten 151
bestandene Tests für Start, Reparaturen, Bewertung, Import, Catch-up, Quellen,
Transfers, Datenschutz und Fortschrittsanzeige. Fünf isolierte Paneltests bestanden;
von zwei Gruppenläufen bestand einer vollständig, der andere zeigte zusätzliche
Benachrichtigungen. Assertions wurden nicht abgeschwächt oder übersprungen.
Die Paket-Ausschlussregeln aus 3.9.22 bleiben unverändert.

## Release-Abschlussprüfung

Mit Versionsstand 3.9.23 bestanden erneut 151 Funktionsregressionen (106,869 s),
53 Release-, Update-, Paketierungs-, Publisher- und Sprachprüfungen sowie drei
gezielte Quellen-/Commanderwechseltests. Das reale Updatefenster bestand zusätzlich
unter X11 alle zwölf Sprachen in beiden Themes (24 Kombinationen).
Die Sprachprüfung bestätigte 2.346 Schlüssel, passende Platzhalter und keine
Duplikate. Syntaxprüfung für 604 Python-Dateien, Imports der betroffenen Module
und git diff --check bestanden. Alte Übersetzungen und Release-Zusammenfassungen
wurden auf unveränderte Inhalte geprüft.

Der Release-Probebuild bestand die ZIP-Integritätsprüfung. Seine 490 Einträge
enthielten keine Datenbanken, persönlichen Einstellungen, Logs, Testverzeichnisse,
Python-Caches oder Entwicklungsumgebungen. Der Publisher baut nach der regulären
Bestätigung erneut aus dem finalen Commit und prüft das veröffentlichte Asset.
