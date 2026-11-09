# CMDRHelper v3.9.31

- Gemeinsames Frachtfenster mit Schiff links und SRV rechts: getrennte Bestände, Kapazitäten, Fortschrittsbalken und Frachttabellen. Automatische Aktualisierung sowie gespeicherte Fensterposition und Größe bleiben erhalten.
- Die Schiffsfracht verwendet dieselbe veröffentlichte Bestandsprojektion wie die Mining-Tabelle. Vorhandene Mengen bleiben unabhängig von ihrer Farbkennzeichnung und bei fehlendem oder unvollständigem Loadout sichtbar. Unbekannte Werte, bestätigte Nullbestände und ein inaktives SRV werden unterschieden.
- Die Sprachaktualisierung der Frachtanzeige berücksichtigt jetzt auch unveränderte Bestände. Texte sind in allen zwölf Sprachen verfügbar.

Die Schiffsmengen stammen aus derselben veröffentlichten Datenprojektion wie
MiningView. Die Frachtanzeige führt keine zusätzliche Bestandsberechnung aus
Journaldateien und keine zusätzlichen Identitätsfilter ein. Ein fehlendes oder
unvollständiges Loadout unterdrückt vorhandene Mengen nicht; unbekannte Kapazität
und unbekannter Bestand werden mit „–“ statt als bestätigte Null angezeigt.
Ohne aktives SRV erscheint ein entsprechender Hinweis.

Die bestehende automatische Aktualisierung sowie das Speichern von Fensterposition
und Größe bleiben erhalten. Die vom Benutzer im laufenden Spiel bestätigte
Oberfläche bleibt bestehen. Bei unveränderten Beständen berücksichtigt die
Darstellung nun auch einen Wechsel der Sprache; vorhandene Journal-Lokalisierungen
behalten nach den bisherigen Übersetzungsregeln Vorrang.

Die Regressionstests wurden auf die getrennten Frachtbereiche und die veröffentlichte
Mining-Projektion abgestimmt. 132 gezielte Tests bestanden unter Linux, einschließlich
aller 14 Dual-Fracht-Tests und aller 18 Präsentationstests. Keine Tests wurden
übersprungen; unbehandelte Qt-Callback-Ausnahmen wurden als Fehler gewertet und
traten nicht auf. Syntaxprüfung und git diff --check waren erfolgreich.
