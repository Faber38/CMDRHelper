# CMDRHelper v3.9.32

- Grüne Fußspuren kennzeichnen Erstbetretungen auf der Explorer-Systemkarte und in BIO / GEO / ABBAU, mit Legende und übersetzten Tooltips. Wertliste und BIO / GEO / ABBAU zeigen einheitliche Kurznamen; vollständige Körpernamen bleiben im Tooltip verfügbar.

- Die Chronik bietet drei kombinierbare Filter für Erstbetretungen, Erstentdeckungen und Erstkartierungen. Ergebnisse der ausgewählten Commander lassen sich gemeinsam durchsuchen, als Liste kopieren und als UTF-8-CSV mit Semikolon exportieren.

- Der obere Chronikbereich zeigt Suche und Zeitraum neben den Filtern und wechselt bei Platzmangel untereinander. Commander-Auswahl und Aktionen können umbrechen; Export-Schaltflächen bleiben direkt über der Ergebnisliste erreichbar.

- Vorhandene Journal- und Datenbankinformationen werden wiederverwendet, ohne neue Erstbetretungsheuristik oder Datenbankstruktur. Erstbetretungen sind abgeleitet, Erstentdeckungen eigene Scan-Kandidaten und Erstkartierungen eigene Kartierungen solcher Kandidaten. Offizielle Erstansprüche bleiben unbestätigt.

- Zeiträume filtern vorhandene Ereigniszeitpunkte in UTC; unbekannte Zeitpunkte werden dabei ausgeschlossen und sonst ohne erfundenes Datum angezeigt. Erstentdeckungen haben keinen verlässlichen Ereigniszeitpunkt, Erstkartierungen verwenden den Zeitpunkt der eigenen Kartierung. Neue Texte sind in zwölf Sprachen verfügbar.

Die Entdeckungsliste verwendet ausschließlich gespeicherte Körperbeobachtungen. Ein Körper kann mehrere getrennte Ereignistypen haben; die Zuordnung zu Commander, System und BodyID bleibt erhalten. Kopieren und CSV-Export verwenden denselben angezeigten Ergebnisstand. Fehlende Zeitpunkte bleiben im Export leer. Ein Zeitraumfilter schließt daher Erstentdeckungskandidaten aus.

Geöffnete Entdeckungslisten werden nach abgeschlossenem Archivimport oder Journal-Catch-up über die bestehenden Signale aktualisiert. Mining-Filter behalten beim Wechsel in die Entdeckungssuche ihre Einstellungen. Es gibt keine zusätzliche Journalverarbeitung und keine neue Datenbankstruktur.

Unter Linux bestanden 102 gezielte Regressionstests, einschließlich Explorer-Kennzeichnung, Körpernamen, Erstbetretungspersistenz, Archivimport, Entdeckungssuche, Commander-Zuordnung, UTC-Zeiträumen, Export, Chronik-Layout und Mining-Filtern. Unbehandelte Qt-Callback-Ausnahmen wurden als Fehler gewertet. Die Funktionen wurden zusätzlich vom Benutzer im Live-Betrieb bestätigt.
