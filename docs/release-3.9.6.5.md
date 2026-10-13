# CMDRHelper v3.9.6.5

- Robusterer Windows-Start: Nichtkritische Hintergrundfehler werden als Teilfehler angezeigt; das Hauptfenster bleibt nutzbar.
- Begrenzte Wiederholungen bei Landeplatzdaten und Journal-Catch-up, verbesserte Kartografiereparatur sowie abgesicherte Journalindex- und Shutdown-Abläufe.
- Aussagekräftigere technische Fehlerkategorien in der Diagnose bei weiterhin anonymisierten persönlichen Daten.
- Ruhigere Frachtraumanzeigen beim Mining durch wiederverwendete Fenster und Tabellenzeilen; automatisches Ausblenden erst 15 Sekunden nach der letzten Bestandsänderung.
- Einheitliche lokalisierte Rohstoffnamen ohne Änderung der Bestandsberechnung oder der separaten Drohnenanzeige.
- PP2-Tageschronik: Auch normale Warenverkäufe können konservativ Merit-Gutschriften zugeordnet werden (≈); mehrdeutige Fälle bleiben ?, Gesamtstand und Rangberechnung unverändert.

DB-Schema bleibt 23. Die bestehende Updatefunktion und die Startskripte werden weiterverwendet. Dieses Wartungsrelease enthält keine neue Datenmigration und erzwingt keine vollständige Journal-Neueinlesung.

Die PP2-Zuordnung ist eine zeitliche Plausibilitätszuordnung, keine explizite Ursachenangabe des Journals. Rare-Goods-Regeln bleiben erhalten.

Die Regressionstests verwenden isolierte synthetische Daten unter Linux, einschließlich simulierter Windows-Fehlerpfade. Eine erfolgreiche Installation auf einem externen Windows-Rechner ist damit nicht nachgewiesen.
