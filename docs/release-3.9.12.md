# CMDRHelper v3.9.12

- Explorer-Zusatzfenster: zuverlässige Aktualisierung und Wertsortierung in allen zwölf Sprachen.
- PP2-Ereignischronik ab- und andocken: frei skalierbares Zusatzfenster mit gespeicherter Größe und Position; Filter bleiben erhalten. Einzeilige Meritsumme für die angezeigten Tagesereignisse und den gewählten Uhrzeitfilter, einschließlich unbekannter Gutschriften.
- Live-Commander-Folgen direkt in der Übersicht steuern; mit der CMDR-Ansicht synchronisiert und dauerhaft gespeichert. Bei manueller Commander-Auswahl erklärt ein gelber Hinweis die deaktivierte Automatik; er blinkt zehn Sekunden und bleibt danach sichtbar.
- Favoriten: Systemnamen per Kopiersymbol ohne Auswahl oder Navigation kopieren; grünes Häkchen bestätigt den Kopiervorgang für zwei Sekunden.
- Lange aktive Journale: geprüfte Verarbeitungsergebnisse wiederverwenden, doppelte Zustandsrekonstruktion vermeiden und UI-Pausen reduzieren.
- Start-Fortschrittsfenster wiederhergestellt: gemeinsame Anzeige für aktivierte Journalquellen und korrekte Fehlermeldung bei fehlgeschlagenem Erstimport.

Die Übersicht verwendet dieselbe gespeicherte Folgeeinstellung wie die CMDR-Ansicht. Beim Aktivieren greift die vorhandene automatische Commander-Auswahl; beim Deaktivieren bleibt die aktuelle Auswahl erhalten.

Die abgedockte PP2-Chronik verwendet die bestehende Tabelle und bleibt auch bei verborgenem PP2-Tab aktuell. Größe und Position werden gespeichert; der abgedockte Zustand selbst wird nicht über einen Neustart hinweg gespeichert.

Die Langjournal-Korrektur verwendet das geprüfte Ergebnis der Quellenverarbeitung auch für die aktive UI-Projektion. Eine vollständige Rekonstruktion im Worker bleibt bestehen; eine vollständig inkrementelle Verarbeitung oder ein grundsätzlich pausenfreier Betrieb wird nicht zugesichert.

Das vorhandene Start-Fortschrittsfenster zeigt die Verarbeitung aller aktivierten Quellen gemeinsam im unbestimmten Fortschrittsmodus an. Es gibt keine künstliche Mindestanzeigedauer. Bei einem Erstimportfehler wird der globale Start nicht mehr als erfolgreich gemeldet; das Fenster schließt auch im Fehlerfall. Ohne aktivierte Quelle bleibt der normale Start erhalten.

Das Datenbankschema bleibt bei Version 23; eine neue Schemamigration ist nicht erforderlich.

Die gezielte UI-Prüfung erfolgt mit Qt offscreen. Die native Fensterprüfung unter KDE X11/KWin und Windows steht aus. Synthetische Journaltests ersetzen keine Messung im echten Spielbetrieb.

Die PP2-Meritsumme steht als Einzeiler neben dem Uhrzeitfilter. Sie addiert ausschließlich die numerischen Gutschriften der angezeigten Ereignisgruppen, einschließlich unbekannter Zuordnungen. Tageswahl, lokale Uhrzeitfilterung, neue Ereignisse und Commanderwechsel aktualisieren die Anzeige. Merit-Gesamtstände und Rangberechnung bleiben unverändert; das Summenfeld wandert beim Ab- und Andocken mit.

Das Kopiersymbol in Navigation → Favoriten übernimmt nur den gespeicherten Systemnamen. Es löst weder Auswahl noch Navigation aus und benötigt keine zusätzliche Datenbankabfrage. Nur der angeklickte Eintrag zeigt für zwei Sekunden ein grünes Häkchen; erneutes Klicken startet seine Dauer neu. Ohne gültigen Systemnamen erfolgt keine erfolgreiche Kopierbestätigung.
