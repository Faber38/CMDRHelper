# CMDRHelper v3.9.6.6

- Verbesserte Powerplay-Merit-Zuordnung bei aufeinanderfolgenden Warenverkäufen.

Die PP2-Tageschronik berücksichtigt bei gewöhnlichen Warenverkäufen, ob einem früheren Verkauf bereits vor dem nächsten Verkauf eine Merit-Gutschrift plausibel zugeordnet wurde. Dieser frühere Verkauf blockiert die nachfolgende Zuordnung dann nicht mehr fälschlich.

Plausible zeitliche Zuordnungen bleiben mit ≈ gekennzeichnet; sie sind keine direkte Ursachenangabe des Journals. Mehrdeutige Fälle bleiben ?. Das Zwei-Sekunden-Fenster, Macht-, Stations- und Systemprüfung, Commander- und Sitzungsgrenzen, Rare-Goods-Sonderregeln und PP2-Abgaben bleiben erhalten. Merit-Gesamtstand und Rangberechnung ändern sich nicht.

DB-Schema bleibt 23. Die bestehende Updatefunktion und die Startskripte werden weiterverwendet. Dieses Wartungsrelease enthält keine neue Datenmigration und erzwingt keine vollständige Journal-Neueinlesung. Persönliche Daten und Einstellungen bleiben beim regulären Update erhalten.

Die Prüfungen umfassen isolierte Regressionstests unter Linux und einen ausschließlich lesenden Original-Replay. Eine erfolgreiche Installation auf einem externen Windows-Rechner ist damit nicht nachgewiesen.
