# CMDRHelper v3.9.6.7

- Verbesserte Powerplay-Merit-Zuordnung bei Schiffsscans und Warenverkäufen.
- Schiffsscans berücksichtigen +5 und +10 Merits; gewöhnliche Warenverkäufe können mehrere Gutschriften innerhalb von vier Sekunden erhalten (≈). Konkurrierende oder mehrdeutige Ereignisse bleiben ungeklärt (?).
- Frachtraumanzeigen bleiben bei aktiviertem Anzeige-Haken ohne Inaktivitäts-Ausblendung sichtbar; Fracht- und Drohnenwerte werden ohne erneute Anzeigezyklen aktualisiert.
- Neues aufklappbares Hauptmenü Navigation mit Favoriten und Planeten-Navigation; die bisherigen Explorer-Buttons entfallen.
- Die integrierte Hilfe beschreibt die neuen Menüpfade in allen zwölf unterstützten Sprachen.

Abgeschlossene Schiffsscans werden anhand von ShipTargeted mit TargetLocked=true
und ScanStage=3 erkannt. Das Scanfenster bleibt bei drei Sekunden. Erneutes
Anvisieren und konkurrierende Scanabschlüsse werden konservativ behandelt;
auch nicht zugeordnete Scans bleiben mögliche konkurrierende Ursachen.

Das Vier-Sekunden-Fenster gilt ausschließlich für gewöhnliche Warenverkäufe
und beginnt beim ursprünglichen Verkauf. Weitere Gutschriften verlängern es
nicht. Gültige PowerplayRank-Meldungen derselben Macht und Cargo unterbrechen
eine ansonsten gültige Verkaufsverbindung nicht und beseitigen keine Mehrdeutigkeit.

Mehrere plausible Gutschriften erscheinen als Summe in einer Verkaufszeile.
Die einzelnen Journalereignisse und ihre absoluten TotalMerits bleiben erhalten
und im Tooltip nachvollziehbar. ≈ bezeichnet eine zeitlich plausible Verbindung,
keine vom Journal ausdrücklich bestätigte Ursache. Auch bereits gutgeschriebene
Verkäufe bleiben innerhalb ihres Fensters mögliche Konkurrenten: Eng aufeinanderfolgende
Verkäufe können deshalb weiterhin oder nun wieder als unbekannt (?) erscheinen.

Rare-Goods-Sonderregeln, PP2-Abgaben, Kopfgelder und Kampfbelohnungen behalten
ihre bisherigen Zuordnungsregeln und Zeitfenster. Merit-Gesamtstand,
Rangberechnung, Quellenidentität, Deduplizierung sowie Commander- und
Sitzungsgrenzen bleiben erhalten.

Frachtraumfenster und Frachtraum-HUD verwenden keine Inaktivitäts-Ausblendung
mehr. Die Anzeige-Haken bleiben unabhängig; ausgeschaltete Anzeigen werden
durch spätere Frachtänderungen nicht erneut geöffnet. Fensterpositionen und
Größen bleiben erhalten. Die bisherigen Sichtbarkeitsbedingungen des HUDs
(unter anderem ein sichtbares Elite-Fenster im Vordergrund) gelten weiterhin;
fehlende gültige Frachtdaten werden als unbekannt dargestellt.

Das linke Hauptmenü Navigation lässt sich aufklappen und öffnet Favoriten sowie
Planeten-Navigation über die bisherigen Aufrufmethoden. Die beiden bisherigen
Explorer-Buttons entfallen. Funktionen, Favoritendaten und Fensterverhalten
bleiben unverändert. Die integrierten Hilfetexte enthalten die neuen Menüpfade
in allen zwölf Sprachen; bestehende Hilfekontexte bleiben erhalten.

DB-Schema bleibt **23**, ohne neue Datenmigration. Die bestehende Updatefunktion
und die Startskripte werden weiterverwendet. Das Release erzwingt keine vollständige
Neuindizierung. Persönliche Daten und Einstellungen bleiben beim regulären Update erhalten.

Die Validierung umfasst gezielte Regressionstests unter Linux und ausschließlich
lesende Original-Replays. Eine erfolgreiche Installation auf fremden Rechnern
ist damit nicht nachgewiesen.
