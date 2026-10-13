# CMDRHelper v3.9.5

- Neue Odyssey-Rangbewertung: 192 von 223 Gegenständen sind mit A–D bewertet; 31 bleiben als ungeprüft mit ? gekennzeichnet.
- Farbige Rangspalte mit Tooltips und gespeicherter Sortierung A–D oder D–A; persönliche Aufräummarkierungen bleiben unabhängig.
- Korrigierte Fleet-Carrier-Routen: Die gesamte bestätigte Belegung wird an Spansh übergeben, Tank- und Lagertritium bleiben getrennt.
- CarrierStats übernimmt Kapazitäts- und Tankdaten mit Identitäts-, Sitzungs- und Aktualitätsprüfung; Lagertritium wird weiterhin manuell eingegeben.
- Verständlichere Carrier-Eingabehinweise, markierte ungültige Felder und dreimaliges oranges Blinken bei fehlender Bestätigung, in beiden Themes und zwölf Sprachen.
- Zusätzliche Absicherung gegen veraltete Carrier-Bestätigungen und verspätete Routenergebnisse nach Kontextwechseln; CTSVision-Export bleibt kompatibel.

Bei fehlenden oder ungültigen CarrierStats erscheint der vorhandene Hinweis
in Elite-Gelb auf kontrastreichem Hintergrund. Er blinkt beim ersten Anzeigen
und bei einem erneuten Berechnungsklick dreimal dezent und bleibt danach gelb.
Ein gültiger Snapshot entfernt den Hinweis; Menüwechsel und Schließen stoppen
die Animation. Die orange Bestätigungsanimation bleibt davon unabhängig.

Die eigene Odyssey-Bewertung umfasst A: 16, B: 54, C: 28, D: 94 und ?: 31.
Waren, Material und Daten sowie die sechs vorhandenen Verbrauchsgüter bleiben
im bestehenden Katalog erhalten. Die persönliche Aufräumliste mit 81
Standardkandidaten ist unabhängig von der Rangbewertung.
Details und Quellen: [Odyssey-Ränge](odyssey-ranks.md).

Der gemeldete Carrier-Fall von nyenyon übergibt nun die bestätigte Gesamtbelegung
5334 statt nur 4400 Lagertritium. Spansh erhält mass=25000, capacity=25000,
capacity_used=5334, fuel_loaded=1000, tritium_stored=4400 und
calculate_starting_fuel=0. Es gibt keine eigene Verbrauchsformel und keine
behauptete Spansh-Gesamtmasse von 31334 t.

CarrierStats-Snapshots gelten höchstens 15 Minuten und sind kein Live-Bestand.
Unbekannte Werte werden nicht durch null ersetzt. Transfers und relevante
Änderungen erfordern neue Werte und Bestätigung; nicht lokal protokollierte
Änderungen muss der Benutzer selbst berücksichtigen. Unterstützt wird das
persönliche Carrier-Profil. Details: [Carrier-Eingaben](carrier-route-inputs.md).

Datenbankschema: **23**, keine neue Migration.
