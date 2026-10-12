# CMDRHelper v3.9.4

- Verbesserter Schiffsroutenplaner mit 7A-SCO-FSD, korrekter Übernahme von Engineering, Guardian-Booster, Fracht und Reservetreibstoff.
- Neuer Schiffsdaten-Assistent zum Erklären, Ergänzen und schiffsbezogenen Speichern fehlender Werte; bestätigte automatische Daten haben Vorrang.
- Präzisere zeitliche Zuordnung von Powerplay-Lieferungen zu Meritmeldungen innerhalb von bis zu drei Sekunden bei eindeutigem Kontext.
- Mining-, Odyssey-, Material- und Flottenansichten vermeiden unnötige Neuaufbauten und verwenden vorhandene Anzeigeelemente weiter.
- Neue Odyssey-Aufräumhilfe mit 81 Standardkandidaten, persönlicher Auswahl aus 223 Gegenständen, farbiger Markierung und gespeicherter Sortierung.
- Verbesserte Eingabeprüfung, Fehlermeldungen und Ladeanzeigen sowie angepasste Texte in allen zwölf Sprachen.

Der Schiffsdaten-Assistent verwendet die vorhandenen QSettings. Manuelle Live-Werte gelten höchstens zwei Minuten; technische Ergänzungen werden passend zu Schiff, FSD und Engineering wiederhergestellt.

Powerplay-Lieferungen werden bei eindeutigem Macht-, Stations-, System- und Sequenzkontext innerhalb von 0 bis einschließlich 3 Sekunden zeitlich zugeordnet (≈). Mehrere Meritmeldungen bleiben einzeln erhalten. Es erfolgt keine automatische Wochenbonus-Klassifizierung. Die Rare-Goods-Zuordnung bleibt bei 0–2 Sekunden; Merit-Gesamtstand und Rangberechnung bleiben unverändert.

Die Odyssey-Aufräumhilfe enthält 50 Daten- und 31 Warentypen. Die persönliche Auswahl lässt sich suchen, filtern, speichern oder auf den Standard zurücksetzen. Markierungen, Legende und Barkeeper-Hinweis unterstützen Dark- und Light-Mode. Aufräumlisten- und alphabetische Sortierung werden gespeichert.

Datenbankschema: **23**, keine neue Migration.
