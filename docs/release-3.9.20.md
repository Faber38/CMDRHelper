# CMDRHelper v3.9.20

- NEU: Gespeicherte Märkte unabhängig vom aktuellen Standort ansehen.
- NEU: Vollständige Warenlisten mit Einkaufs- und Verkaufspreisen sowie Angebot und Nachfrage in Tonnen.
- NEU: Märkte nach Entfernung, Landeplatzgröße und Datenalter filtern.
- VERBESSERT: Märkte und Waren nach Namen, Preisen und Mengen sortieren.
- VERBESSERT: Übersichtlichere Bedienleiste in der PP2-Tageschronik.
- BEHOBEN: Stronghold-Carrier-Märkte werden korrekt erkannt und gespeichert.

Die Marktansicht verwendet ausschließlich gespeicherte Marktstände. Fehlende Koordinaten und Landeplätze bleiben unbekannt; Preise werden nicht ergänzt oder berechnet. Alte Marktstände bleiben ohne Altersfilter sichtbar.

Stronghold-Märkte benötigen ein gültiges Market-Ereignis und passende Market.json-Daten. Vor dem Helper-Start bereits vergangene Market-Ereignisse werden nicht nachträglich importiert; den Warenmarkt bei laufendem Helper erneut öffnen. Identitäts- und Zeitprüfungen bleiben erhalten.

Datenbankschema bleibt 23. Keine neuen Produktfunktionen außerhalb der bereits vorbereiteten Arbeiten. Die Releaseprüfung verlangt vor Commit, Push oder Tag gültige Neuerungen in allen zwölf Sprachen. Automatisierte UI-Prüfungen erfolgen mit Qt offscreen; keine native Windows- oder Live-Spiel-Prüfung.
