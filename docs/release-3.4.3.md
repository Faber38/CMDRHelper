# CMDRHelper 3.4.3 – lokale Releasevorbereitung

Dieser Stand bündelt die tatsächlich seit 3.4.1 implementierten Änderungen.
Er ist für den lokalen Probe-Build vorgesehen; keine Veröffentlichung erfolgt
im Rahmen dieser Vorbereitung.

## Änderungen

- **Explorer:** Wertliste und BIO/GEO/ABBAU lassen sich über Spaltenköpfe
  sortieren. Körpernamen werden natürlich, Entfernungen/Credits/Anzahlen
  numerisch und Status/Analyse/Besucht semantisch sortiert. Sortierung und
  Spaltenbreiten bleiben gespeichert, mit getrennten Einstellungen je Tabelle.
- **Chronik:** Anklickbare Systempunkte zeigen einen Hand-Cursor. Klick,
  Verschieben, Zoom und Drehung behalten ihr bisheriges Verhalten.
- **Favoritenfilter:** Der optionale Entfernungsfilter ist zunächst aus;
  Vorgabe 500 Lj, Bereich 1 bis 100.000 Lj. Er verwendet lokale XYZ-Koordinaten
  und filtert nach einem Systemwechsel automatisch neu. Unbekannte Entfernungen
  bleiben sichtbar; es gibt keine zusätzliche Liveabfrage für den Filter.
- **Favoritentransfer:** Ein portables ZIP enthält `favorites.json` und
  vorhandene Bilder unter `images/`. Der Export umfasst alle Favoriten des
  aktiven Commanders, unabhängig von sichtbaren Filtern. Identische Bildinhalte
  werden nur einmal gespeichert. Originalbilder bleiben unverändert.
  Strukturierte Favoritendaten enthalten keine Commander-/FID-/Journal-Daten.
  Importpakete werden vor Änderungen geprüft. Duplikate können gemeinsam
  übersprungen (Standard), ersetzt oder als neue Einträge übernommen werden.
  DB-Änderungen sind atomar; Fehler führen zum Rollback. Fehlende/defekte Bilder
  blockieren gültige Favoritendaten nicht. Importierte Bilder werden lokal
  verwaltet; alte Bilder bleiben beim Ersetzen vorsorglich erhalten.
  Grenzen: 32 MiB je Datei, 256 MiB je Paket. Linux-/Windows-Pfade im Paket
  sind plattformneutral; Pfad-Traversierung wird abgewiesen. Kein Netzwerkzugriff.
- **Mining:** Separate Spalten **SRV | Schiff | Carrier | Gesamt** und getrennte
  Aktualisierung von SRV und Schiff. Bestätigte Carrierbestände bleiben
  unabhängig erhalten. „Nur Bestand“ berücksichtigt positive bekannte Bestände
  an jedem der drei Lagerorte. Gesamtwerte erscheinen nur, wenn alle drei
  Teilbestände bekannt sind. Tabellenpersistenz wurde entsprechend angepasst.
- **Hilfe/README:** Hilfe in allen zwölf Sprachen aktualisiert, einschließlich
  korrigierter Explorer-Begriffe. Die Hilfe bleibt versionsunabhängig.
  Quick Start in allen zwölf READMEs beschreibt die vorhandenen Windows- und
  Linux-Skripte; der normale Benutzerweg beginnt mit dem Release-ZIP.
- **Diagnose:** Einstellungen bieten „Logdatei öffnen“ und „Diagnosepaket
  erstellen“. Das ZIP enthält ausschließlich bereinigte Hauptlogs samt
  Rotationen, `system_info.json` und `diagnose_summary.txt`. Keine Datenbank,
  Elite-Journale, FID-/Commander-Daten, Zugangsdaten, Favoritenpakete oder Bilder;
  keine automatische Übertragung. Dynamische Logargumente und Exception-
  Freitexte werden verborgen, technische Felder gezielt zugelassen. Tracebacks
  behalten Aufrufketten, Fehlertypen und sichere Fehlercodes. Alte Log-Inhalte
  ohne Datenschutzfilter werden nicht exportiert. Hauptlogs: fünf Dateien à
  2 MiB; bestehendes Updater-Statuslog: zwei Dateien à 2 MiB.

## Direkte Upgrades und Migrationsbackups

Eine Zwischeninstallation von 3.4.1 ist nicht nötig. Entscheidend ist der
DB-Marker `parent_hierarchy_migration = 3.4.1-complete`, nicht die laufende
Programmversion. Der Marker und die historischen Backup-Kennungen bleiben
unverändert. Ohne erfolgreichen Marker wird vor normaler DB-Initialisierung
weiterhin die Datenbankaktualisierung angeboten. Elite Dangerous muss beendet
sein; möglichst alle historischen Journale sollten verfügbar sein. Journale
werden ausschließlich gelesen. Abbruch bietet die Migration später erneut an;
Fehler führen zum Rollback ohne Erfolgsmarker und behalten das Backup.

Backup-Metadaten in `app_meta` speichern die tatsächliche Erzeugerversion und
belegen den erfolgreichen Abschluss. Ein Backup wird nie im Erzeugerrelease
gelöscht. Bereinigung ist nur nach erfolgreichem Start einer streng späteren,
veröffentlichten Version möglich, mit passendem Veröffentlichungsnachweis aus
der bestehenden Updateprüfung und geprüften Metadaten, Pfaden und Prüfsummen.
Offline, bei unbekannten Metadaten oder ohne passenden Nachweis bleibt es
konservativ erhalten. Der lokale Probe-Start ist kein Veröffentlichungsnachweis.

## Prüfweg

- Vollständige Testsuite und vollständige i18n-Prüfung.
- Reale ursprüngliche 3.4-Sicherung nur auf einer Arbeitskopie migrieren:
  1.262 Systeme, 10.985 Körper, 10.980 `parent_id`, 5.961 `parent_star_id`,
  16.941 Feldwerte; zweiter Lauf null Änderungen. Originalbackup und alle
  Journale müssen unverändert bleiben.
- Relevante Explorer-, Favoriten-, Mining-, Chronik-, Systemkarten-,
  Barycentre-/Belt-, A-6-a-, Updater-, Windows- und Linux-Startregressionen.
- `bash create_release.sh` erzeugt lokal `release/CMDRHelper_v3.4.3.zip`.
  ZIP-Integrität und Bytegleichheit der ausgelieferten Quellen kontrollieren;
  keine DB, Backups, Logs, Diagnosepakete oder Testartefakte im Paket.
- Isolierter Linux-/Offscreen-Probe-Start aus dem entpackten ZIP mit temporären
  Einstellungen und einer DB-Arbeitskopie. Keine externen Dienste kontaktieren.
  Native Windows-Ausführung muss separat erfolgen; hier werden Windows-Skripte
  und Pfad-/Updater-Verhalten statisch und regressiv geprüft.

## Lokales Prüfergebnis am 14. September 2026

- **1.371 Tests bestanden**, vollständige Suite in vier isolierten Testprozessen.
  Die aktuelle README-Positionsprüfung verwendet die zentrale Version;
  historische Releaseprüfungen bleiben erhalten.
- i18n: 1.421 Referenzschlüssel, keine Duplikate oder Platzhalterfehler.
  Eigene Katalogeinträge: DE/EN/IT je 1.421, ES/FR je 1.410,
  EL/FI/NL/NO/PL/SV/TR je 1.299. Vorhandene Material-Fallbacks unverändert.
- Reale 3.4-Backup-Arbeitskopie: alle oben genannten Referenzzahlen exakt,
  zweiter Lauf null Änderungen; alle 473 Journale und das Originalbackup
  unverändert. Zusätzlich Migration einer mit dem originalen 3.3-Datenbankcode
  erzeugten Testdatenbank unter 3.4.3 erfolgreich; Backup im selben Release
  weiterhin vorhanden.
- Probe-Start aus dem entpackten ZIP unter Linux/offscreen mit bestehender
  Python-Umgebung: **Dark und Light erfolgreich**. Titel 3.4.3, Explorer-Tabellen,
  Favoriten-Entfernungsfilter, echte Export-/Import-Dateidialoge mit Bild und
  Duplikatbehandlung, Mining, Diagnosepaket, Hilfe und Update-Kurzfassung geprüft.
- Eine zusätzliche alte DB-Arbeitskopie durchlief im verpackten Programm den
  Migrationsdialog mit vollständiger Migration und anschließend denselben
  Hauptfenster-Probelauf. Keine Netzwerkversuche; Originaldatenbanken unverändert.
- Die historischen README-Releaseabschnitte wurden gegen `HEAD` verglichen und
  sind in allen zwölf Sprachen unverändert. Der Quick Start bleibt davor.
- Native Windows-Ausführung und eine frische Installation mit neu heruntergeladenen
  Abhängigkeiten wurden hier nicht durchgeführt. Windows-/Linux-Start-, Update-,
  Pfad- und Packaging-Regressionsprüfungen sind Bestandteil der bestandenen Suite.

Der Probe-Start verwendet ausschließlich temporäre DB-Kopien, eigene
Testjournale/-bilder und isolierte Einstellungen. Keine dieser Laufzeitdateien
gehört in das Release-ZIP. Es wurde weder gestagt noch committet, gepusht oder
veröffentlicht.
