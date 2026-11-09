# CMDRHelper v3.9.30

- Linux-Prozessprüfungen laufen gebündelt im Hintergrund und blockieren die Oberfläche nicht mehr synchron. Commander-Zuordnung, Ankunftsanzeige und Screenshots verwenden nur aktuelle, geprüfte Prozessinformationen.
- Der Mining-Controller verwirft verzögerte Startaufrufe nach seiner Zerstörung und trennt seine Signalverbindungen sicher. Geschlossene Controller starten keine manuelle Aktualisierung mehr.
- Das Zurücksetzen von Kopfgeldprämien und Kampfbelohnungen verwendet die bestätigte Journalquelle des ausgewählten Commanders.
- Spansh-Stationsdaten bleiben 90 Tage frisch. Manuelle Aktualisierungen sind erneut möglich; Fehlerpausen und vom Server angeordnete Wartezeiten werden berücksichtigt. Vorhandene Daten bleiben bei Fehlern erhalten.
- Optionale Performance-Diagnose erfasst GUI-, Worker- und Prozesszeiten. Erwartete Dateideskriptorfehler werden aggregiert statt einzeln protokolliert; ohne Aktivierung bleibt die Diagnose aus.

Die Linux-Prozessermittlung läuft in maximal einem Worker. Quellenzuordnung,
Commander-Auswahl, UI und QSettings bleiben im Qt-Hauptthread. Generation,
PID/Start-Ticks und Aktualitätsprüfung schützen vor veralteten Ergebnissen.
Bei fehlender gültiger Evidenz werden Entscheidungen zurückgestellt.
Es gibt keine zusätzlichen periodischen Prozessscans. Unter dauerhaft langsamen
Scans können bestätigte Anzeigen deshalb weiterhin ausstehen.

Der Benutzer bestätigt eine flüssigere Bedienung im Linux-Live-Betrieb.
Daraus wird kein allgemeiner Geschwindigkeitsfaktor abgeleitet.
Die Diagnose ist optional und kann selbst zusätzliche Last erzeugen.

Der Spansh-Cache betrifft Stationsinformationen, keine Marktpreise oder
Warenbestände. Automatische Fehlerpausen betragen fünf Minuten;
explizite Serverwartezeiten gelten auch für manuelle Aktualisierungen.

Die gemeinsame Testvorbereitung wurde von Testfällen getrennt; historische
Releaseprüfungen verwenden ihre jeweilige historische Version.
Datenbankschema und Veröffentlichungsablauf bleiben unverändert.
