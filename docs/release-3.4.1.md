# CMDRHelper 3.4.1

Dieses Wartungsrelease korrigiert ältere gespeicherte Systemhierarchien und
verbessert die hierarchische Systemkarte. Mining aus 3.4 und die A-6-a-Korrektur
bleiben erhalten. Es enthält keine neuen Handels-, CAPI- oder Rare-Goods-Funktionen.

## Benutzergeführte Datenbank-Aktualisierung

Bei einer bestehenden Datenbank mit Körperdaten erscheint die Aktualisierung
vor der normalen Datenbankinitialisierung und vor Journal-Watchern. Abbrechen
beendet diesen Start ohne Datenbankänderung oder neue Sicherung. Nach einer
bestätigten erfolgreichen Aktualisierung erscheint der Dialog für diese
Datenbank nicht erneut.

Der Dialog nennt den gefundenen Journalordner, die Anzahl sowie die älteste und
neueste Datei. Er behauptet nicht, dass die historische Sammlung vollständig
sei. Elite Dangerous muss beendet sein; archivierte Journale sollten möglichst
wieder im verwendeten Journalordner liegen. Journaldateien werden ausschließlich
gelesen, niemals verändert, verschoben oder gelöscht.

Die vorhandene Zwei-Schiff-Animation läuft während der Hintergrundarbeit. Fünf
Schritte zeigen Journalprüfung, Sicherung, Hierarchieprüfung, Aktualisierung und
Integritätsprüfung. Bestätigte Schritte erhalten ein Häkchen. Die Erfolgszahlen
stammen ausschließlich aus der jeweiligen Datenbank und den vorgefundenen
Journalen.

## Sicherung und Transaktion

Vor Reparaturschreibzugriffen wird ein vorhandenes SQLite-WAL kontrolliert in die
Hauptdatei übernommen. Eine Schreibsperre schützt anschließend Sicherung und
Reparatur. Die vollständige Kopie heißt
`cmdrhelper_pre_parent_repair_3.4.1_<UTC-Zeitstempel>.db`.
Größe, SHA-256 und ein blockweiser Bytevergleich müssen übereinstimmen.

Die Sicherung wird weder bei Erfolg noch bei Fehlern automatisch gelöscht.
Eine benachbarte `.db.json` enthält Zweck, Release, UTC-Zeitpunkt, Pfad, Größe,
Prüfsumme und Aufbewahrungskennung. Nach Erfolg liegen dieselben Angaben unter
`parent_hierarchy_backup.3.4.1` in `app_meta`. Ein späteres Release kann diese
Informationen für eine kontrollierte Bereinigung verwenden; 3.4.1 tut dies nicht.

Nur belegte, widerspruchsfreie Scan-Parents mit eindeutiger Kombination aus
SystemAddress und BodyID werden übernommen. Es gibt keine Namensheuristik,
keine pauschale Ersetzung von 0 und keine neu erfundenen Körper. Journal-Parents
haben Vorrang; die korrigierte EDSM-Normalisierung bleibt erhalten.

Geändert werden nur `bodies.parent_id`, `bodies.parent_star_id`, die vorgesehenen
`body_parents.v1:`-Einträge sowie Migrations- und Sicherungsmetadaten. Alle übrigen
Tabelleninhalte und Körperfelder werden zusätzlich durch einen vollständigen
Vorher-/Nachher-Vergleich geschützt. Vor dem Commit müssen `integrity_check`,
`foreign_key_check` und ein zweiter Reparaturlauf ohne weitere Feld- oder
Metadatenänderungen bestehen. Der Journalbestand wird nochmals verglichen,
einschließlich seiner Dateiprüfsummen.

`parent_hierarchy_migration = 3.4.1-complete` wird gemeinsam mit den geprüften
Änderungen atomar committed. Bei Fehlern erfolgt ein Rollback mit Integritäts-
und Inhaltsvergleich. Kann der ursprüngliche Zustand nicht bestätigt werden,
wird die verifizierte Sicherung wiederhergestellt und erneut geprüft. Die
Meldung über eine erfolgreiche Wiederherstellung erscheint nur bei bestätigtem
Originalzustand. Fehlende verwertbare Daten, Fehler und Abbruch hinterlassen
keine Erfolgskennung. Nach einem fehlgeschlagenen Versuch wird der Dialog beim
nächsten Programmstart mit frischem Journalstatus angeboten.

## Systemkarte und Dokumentation

Beide Karten verwenden den vorhandenen gemeinsamen hierarchischen Layoutstand:
horizontale Hauptkörper, rekursive Monde und Untermonde, kompakte Mondgruppen,
Baryzentren, Mehrfachsterne und erhaltene Belt-Gruppierung. Körperbilder,
Körperidentitäten und Klickaktionen bleiben erhalten.

Alle zwölf Sprachkataloge enthalten die neuen Dialog- und Update-Texte. Die
versionsunabhängige Übersichtshilfe erklärt die Aktualisierung kurz. Alle zwölf
READMEs enthalten einen neuen 3.4.1-Abschnitt; die historischen 3.4-Abschnitte
bleiben unverändert.

## Reproduzierbare lokale Regression

```bash
QT_QPA_PLATFORM=offscreen venv/bin/python -m unittest discover -s tests -q
venv/bin/python tools/check_i18n.py
QT_QPA_PLATFORM=offscreen venv/bin/python tools/check_parent_migration.py \
  data/cmdrhelper_pre_parent_repair_3.4.1_20260912.db --reference-341
bash create_release.sh
```

Das Regressionswerkzeug erstellt immer eine neue Arbeitskopie in einem temporären
Ordner. Es prüft den echten Dialog inklusive Abbrechen und erfolgreichem
Workerlauf, die unveränderte Quelldatenbank, alle Journalprüfsummen,
Idempotenz sowie beide Layouts aller gespeicherten Systeme. Die Referenzprüfung
ist optional und ausschließlich für das bekannte ursprüngliche 3.4-Backup:
1.262 korrigierte Systeme, 10.985 Körper, 10.980 `parent_id`, 5.961
`parent_star_id`, 16.941 Feldwerte und anschließend 0 weitere Änderungen.
Diese Zahlen sind keine Erwartungen im Produktdialog.

Die tatsächliche Vollständigkeit historischer Journale kann nicht automatisch
festgestellt werden. Native Windows-Bedienung muss auf Windows geprüft werden;
Linux- und Qt-Tests ersetzen diesen Plattformtest nicht. Dieses Release wird
lokal geprüft und gebaut, ohne Commit, Push oder Veröffentlichung.
