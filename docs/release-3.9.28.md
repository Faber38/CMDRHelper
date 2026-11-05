# CMDRHelper v3.9.28

- Offene Warenmissionen berücksichtigen gültige Schiffsfracht in Details, Tabellenstatus und nächstem Schritt. Lieferfortschritt bleibt getrennt; mehrere Missionen teilen denselben Bestand ohne Reservierung.
- Passende Bestände des eigenen Carriers erscheinen separat mit manueller Bestätigung, Transfer-Fortschreibung und Aktualitätskennzeichnung. Veraltete oder falsch zugeordnete Ergebnisse werden abgesichert; keine gemeinsame bestätigte Schiff-/Carrier-Summe.
- Abbaurohstoffe zeigen die rosa Missionskugel und dieselbe blaue/rosa Symbollegende wie die Handelsansichten. Bestandsfarben, Mengen und Filter bleiben erhalten.
- Markt ansehen erklärt bei fehlender Auswahl, dass zuerst ein gespeicherter Markt gewählt werden muss und der Frachtraumfilter keine eigenständige Inventarliste ist.

## Vollständiger Änderungsumfang seit v3.9.27

Ausgangspunkt: main, Commit 288bbd4640610e61a4d068fa79f9022f0e5ea1c6,
identisch mit Tag v3.9.27. Vor der Releasepflege: 19 geänderte Produktdateien
und drei neue Testdateien; keine zusätzlichen Commits. Alle Änderungen bleiben erhalten.

- Gemeinsamer Missions-/Frachtabgleich für Handelsansichten, Mining und Missionen.
  Gültiger Nullbestand wird von unbekanntem Bestand unterschieden. Explizite
  MissionID-Bindungen bleiben berücksichtigt; fremd gebundene Ware ist nicht frei.
  Ohne auswertbare offene Warenmission entfällt die zusätzliche Frachtprüfung.
- Missionsdetails zeigen passende Schiffsfracht getrennt von Bedarf, bestätigter
  Lieferung und Restbedarf. Aktualisierung über bestehende Missions-, Fracht-,
  Commander- und Schiffssignale sowie bei initial vorhandenen Daten.
- Missionsliste zeigt „Fracht vorhanden (x/y t)“ und den passenden nächsten Schritt.
  Bei bekanntem Lieferstand gilt der Restbedarf, sonst die Gesamtanforderung.
  Unbekannter Lieferstand erhält bei Nachbeschaffung einen Prüfhinweis.
  Gemeinsamer Bestand bleibt ausdrücklich unreserviert. Bestätigte vollständige
  Lieferung hat Vorrang. Rosa Statusschrift erhält die goldene Zielmarkierung;
  Sortierung und Auswahl bleiben bei Aktualisierungen erhalten.
- Carrier-Bestände werden nur aus dem veröffentlichten Mining-Ergebnis separat
  angezeigt: manuell bestätigt, transferbasiert fortgeschrieben, zuletzt bekannt,
  unbekannt oder widersprüchlich. Quellen-, Commander-, CarrierID- und
  Revisionszuordnung werden geprüft. Ein flüchtiger Veröffentlichungskontext
  und ein Anzeige-Signal kennzeichnen ausstehende Aktualisierungen. Keine neuen
  Abfragen, Worker, Timer, Bestandsverwaltung oder bestätigte Gesamtsumme.
- Mining ergänzt die rosa Kennzeichnung am Rohstoffnamen sowie die wiederverwendete
  blaue/rosa Handelslegende. Bestandslegende, Mengen, Farben und Filter bleiben erhalten.
- Markt ansehen erklärt fehlende Marktauswahl und die Bedeutung des Frachtraumfilters;
  bei Marktauswahl verschwindet die Erklärung. Keine automatische Marktauswahl.
- Alle neuen Texte sind in zwölf Sprachen vorhanden; Dark-/Light-Mode berücksichtigt.
- Drei neue Regressionstestdateien: test_mission_cargo_usability.py,
  test_mining_mission_legend.py und test_mission_cargo_status_carrier.py.
- Releasepflege: zentrale Version, lokalisierte Kurztexte, Versionshistorie in
  zwölf READMEs und dieser neue Bericht. Alte Releaseberichte bleiben unverändert.

Keine Datenbankmigration; Schema-Version 23 bleibt erhalten. Missionsstatus,
Lieferfortschritt, Cargo-Snapshots, Carrier-Bestandsführung und Handelsberechnungen
werden durch die Anzeige nicht verändert.

## Entwicklungsprüfungen und bekannte Grenzen

Die vorhandenen Protokolle dokumentieren 66 bestandene gezielte Regressionstests
und anschließend neun bestandene erweiterte Tests unter Linux/offscreen. Die
betreffenden Produktdateien wurden danach bis zur Releasepflege nicht verändert.
Die Protokolle enthalten keinen kryptografischen Quellstandsnachweis; eine volle
Regression wird für diese Releasevorbereitung nicht nochmals durchgeführt.

Rosa Fracht ist keine Bestätigung der Warenannahme durch Elite. Gemeinsame
Warenbestände sind nicht je Mission reserviert. Carrier-Werte sind manuell
verankerte und gegebenenfalls durch Transfers fortgeschriebene Angaben, kein
vollständiger Elite-Inventarsnapshot. Unbeobachtete Handelsvorgänge können fehlen;
Carrier-MissionID-Bindungen sind nicht aufgeschlüsselt. Unbekannt bleibt unbekannt.
Linux/offscreen ersetzt keinen nativen Windows-Praxistest.

Der Publisher baut erst nach ausdrücklicher Bestätigung über github.sh aus dem
finalen Commit. Seine normalisierte finale ZIP-Prüfsumme ist vom Probebuild zu
unterscheiden und wird bei Veröffentlichung mit dem GitHub-Asset verglichen.

## Abgeschlossene schlanke Releaseprüfung

- Syntaxprüfung von 644 Python-Dateien, Imports von 21 betroffenen Produktmodulen
  und Release-Sprachmetadaten bestanden. Alte Releaseberichte sind byteidentisch.
- Sprachprüfung: 2.446 Referenzschlüssel in zwölf Sprachen, passende Platzhalter,
  keine doppelten Schlüssel; bestehende deklarierte Material-Fallbacks erhalten.
- Vollständiger Probebuild mit unverändertem create_release.sh in einer eigenen
  temporären Sandbox: ZIP-Integrität, bytegenauer Paketvergleich, alle Produktmodule
  und Ausschlüsse bestanden. 485 Dateien; keine Tests, Journale, Datenbanken oder
  temporären Prüfdateien im Paket. data enthält ausschließlich .gitkeep.
- Paketierter MainWindow-Start mit echtem AppState unter Linux/offscreen bestanden:
  Initialisierung erfolgreich, Fenster sichtbar, reguläres Beenden erfolgreich.
  Einstellungen, Datenbank und XDG-Verzeichnisse vollständig unter /tmp isoliert.
  Journalerkennung, Prozessabfrage, Stationsabruf und Updateabfrage waren ersetzt.
- Isolierter Update-Smoke mit dem echten Updater aus v3.9.27 auf v3.9.28 bestanden:
  Entpacken, Backup, Kopieren und Versionsprüfung; alle ausgelieferten Produktdateien
  bytegenau geprüft. Synthetische Datenbank und Einstellungen blieben unverändert;
  integrity_check und Fremdschlüsselprüfung bestanden. Interpreterbindung,
  Prozesswarten, Abhängigkeitsinstallation und Neustart waren kontrolliert ersetzt.
  Quell-ZIPs blieben unverändert; das produktive release-Verzeichnis wurde nicht
  als Testinstallation verwendet.
- Keine vollständige Regression erneut ausgeführt; git diff --check bestanden.
