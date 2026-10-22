# CMDRHelper v3.9.17

- Externe Explorer-Systemsuche oberhalb von „AKTUELLES SYSTEM“: Enter oder Schaltfläche starten die asynchrone Spansh-Namensauflösung. Die bestehende Systemkarte zeigt Sterne, Planeten, Monde und Einrichtungen in einem separaten, größenveränderbaren Fenster ohne erzwungenes Always-on-Top; Körperdetails öffnen sich per Klick.
- Spansh-Körperdaten, eindeutig identifizierte lokale EDSM-Caches und Chronikdaten aller Commander werden mit Quellen und Konflikten zusammengeführt. Eigene Scan- und Kartierungsnachweise bleiben dem jeweiligen Commander zugeordnet; externe Daten gelten nicht als eigene Entdeckungen. Die Chronik wird nur gelesen.
- Landbare Planeten sind deutlich markiert. Körperdetails zeigen Planetentyp, Schwerkraft, Atmosphäre und bekannte Materialien; unbestätigte Spansh-Materialanteile werden nicht als Prozentwerte ausgegeben. Spansh/EDSM garantieren keine konkreten Rhino-Abbaugebiete oder deren Rohstoffe.
- Abgeschlossene Explorer-Suchworker und ihre Signalobjekte werden freigegeben; überholte Suchergebnisse werden verworfen. Wiederholte Suchen sammeln keine QRunnable-Objekte an.
- Die PP2-Tageschronik verwendet unveränderte Tagesdaten und Tabellen weiter. Neue Merits und nachträgliche Korrekturen aktualisieren die Anzeige; Tages- und Zeitfilter, Commanderwechsel und abgedockte Chronik bleiben unterstützt.
- Externe Fenster zeigen Snapshots. EDSM-Caches ohne eindeutige Systemidentität werden nicht zusammengeführt. Datenbankschema weiterhin 23; Hinweise in zwölf Sprachen. Die native Windows-Prüfung steht aus.

Die externe Suche verwendet die vorhandene Spansh-Namensauflösung und Systemkarte. Sie folgt weder dem aktuellen Spielsystem noch einem späteren Commanderwechsel. Ein erneuter Suchlauf lädt einen neuen Snapshot. Fehlende Daten bleiben unbekannt; fehlgeschlagene externe Abrufe können einen ausdrücklich unvollständigen lokalen Bestand anzeigen.

Die Quellenpriorität ist lokal, Spansh, EDSM. Abweichende Werte bleiben als Konflikte mit Quellenangabe sichtbar. EDSM wird ausschließlich aus eindeutig identifizierten lokalen Caches ergänzt, nicht separat live abgerufen. Legacy-Caches ohne eindeutige Systemidentität werden ausgelassen. Persönliche Nachweise erscheinen mit Commander-Zuordnung. Die Suche schreibt weder Chronikdaten noch externe Caches; Datenbankschema Version 23 bleibt unverändert.

Rhino-Planung: Landbarkeit, Planetentyp, Schwerkraft, Atmosphäre und bekannte Oberflächenmaterialien helfen bei der Vorauswahl. Sie belegen keine Rohstoffe eines konkreten Abbaugebiets. Es werden keine Rhino-Abbaugebiete erfunden; unbekannte Materialeinheiten werden nicht als bestätigte Prozentangaben dargestellt.

Die Suchworker werden vom Qt-Threadpool nach Abschluss freigegeben. Der PP2-Cache prüft SQLite-Datenänderungen und vergleicht die geordneten Tagesdaten vor einer Neuberechnung. Neue und korrigierte Merit-Ereignisse werden dabei berücksichtigt; persönliche Merit- und Rangwerte werden weiterhin unabhängig aktualisiert.

Validierungsumfang: gezielte automatisierte Tests mit synthetischen Suchantworten, temporären Datenbanken und Qt offscreen, einschließlich 100 wiederholter Suchläufe, Dark-/Light-Mode und zwölf Sprachen. Keine vollständige Regression und keine native Windows-Prüfung; die native visuelle Prüfung unter Windows steht aus.
