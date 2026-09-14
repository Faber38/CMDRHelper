# Kurzbeschreibung im Update-Dialog

`MainWindow._update_check_finished()` öffnet `UpdateConfirmationBox`, eine
QMessageBox mit unveränderten Ja/Nein-Aktionen. Version und Release Notes kommen
weiterhin aus `check_latest_release()`; die installierte Version aus `version.py`.

`cmdrhelper/release_summaries.py` ordnet Versionen Übersetzungsschlüssel zu.
Für 3.4.1 sind fünf Punkte in allen zwölf Sprachen hinterlegt: Korrektur alter
Systemhierarchien, verbesserte Systemkarte, sichere Datenbankmigration mit
Backup/Rollback, ausschließlich gelesene Journale und Stabilitätsverbesserungen.
Für 3.4 sind sechs aktuelle Punkte in allen zwölf Sprachen hinterlegt: Mining,
Schiff/SRV und manuell bestätigte Carrierbestände mit Transferverfolgung,
kombinierbare Filter, ABBAU-Navigation, Kartographiewerte bei Sitzungswechseln
und Hilfe/Bedienung. Die integrierte Hilfe bleibt versionsunabhängig.
Für 3.2 sind sechs Hauptpunkte in allen zwölf `cmdrhelper/i18n/*.py` hinterlegt.
Für 3.3 sind fünf Hauptpunkte in allen zwölf Sprachen hinterlegt: Systemanalyse,
Spielmodus, Kopieren letzter Systeme, verständlichere Erfahrungsdaten und der
Archivimport-Fix. `tools/publish_release.py` verwendet dieselben Schlüssel für
die GitHub-Release-Beschreibung und deren mehrsprachige Update-Metadaten.
Für 3.3.1 sind sechs Bugfix-Punkte in allen zwölf Sprachen hinterlegt: zuverlässige
DSS-Erkennung einschließlich später eintreffender Scans, korrigierte Live-Bewertung
ohne Verkaufskorrekturfaktoren, Speicherung eigener Kartierungen, Werterhalt beim
Archivimport, Wiederherstellung betroffener Anzeigewerte und Regressionstests.
Legacy-Daten erhalten keinen Live-Bonus; die Creditwerte werden erst am Ende
abgeschnitten. Fehlende Kartographieschätzungen werden auch bei positiven alten
Cachewerten ergänzt.
Weitere lokal bekannte Versionen können als weiterer Dictionary-Eintrag ergänzt
werden, mit den zugehörigen Übersetzungen.

Für zukünftige, der installierten Anwendung noch unbekannte Versionen kann die
bestehende GitHub-Release-Beschreibung eine explizite Kurzbeschreibung enthalten:

```html
<!-- cmdrhelper-update-summary
{"de": ["Erste Verbesserung", "Zweite Verbesserung"],
 "en": ["First improvement", "Second improvement"]}
-->
```

Alle unterstützten Sprachcodes: de, en, fr, it, no, sv, fi, pl, nl, es, tr, el.
Die Liste der aktiven Sprache hat Vorrang vor lokal hinterlegten Punkten.
Höchstens sechs Punkte werden als Text angezeigt, kein vollständiger Changelog.
Fehlende oder ungültige Metadaten verwenden die lokale Versionsliste; fehlt auch
diese, erscheint die bisherige Updatefrage ohne Änderungsblock.

Der Änderungsbereich ist maximal 200 Pixel hoch und scrollbar. Farben werden aus
dem bestehenden Theme übernommen, die Buttons liegen außerhalb des Bereichs.
Die Erweiterung wird erst von Installationen angezeigt, die diesen Dialogcode
bereits enthalten; ein unveränderter älterer Client erhält keine neue UI allein
durch die Release Notes.

## 3.4.3

Sechs neue Punkte in allen zwölf Sprachen (`release.3_4_3.0` bis `.5`):
Favoriten mit Entfernungsfilter und portablem ZIP-Transfer inklusive Bildern,
Explorer-Sortierung und gespeicherte Spaltenbreiten, getrennte Mining-Bestände,
Diagnosepaket und datensparsame Logs, direkte Datenbank-Upgrades mit sicherer
Backup-Aufbewahrung sowie Bedienungs-, Hilfe- und Chronikverbesserungen.
Die Zuordnung steht zusätzlich zu den unveränderten historischen Einträgen in
`RELEASE_SUMMARIES`. Es sind keine zukünftigen Funktionen enthalten.

## 3.4.4 – Hotfix

Vier Punkte in allen zwölf Sprachen (`release.3_4_4.0` bis `.3`): zuverlässige
Speicherung sehr großer Missions-IDs, erneute Journalübernahme mit zunehmenden
Pausen nach Speicherfehlern, verbesserter Start ohne bereits erkannten aktiven
Commander und aussagekräftigere technische Diagnose ohne konkrete Missions-IDs.

Die neue Zuordnung in `RELEASE_SUMMARIES` ergänzt die unveränderten historischen
Einträge. Das Updatefenster zeigt nur diese benutzerorientierten Hotfix-Hinweise;
keine internen SQLite-Erklärungen, Supportfallnamen oder zukünftigen Funktionen.
Die integrierte Hilfe bleibt unverändert und versionsunabhängig.
