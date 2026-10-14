# CMDRHelper v3.9.9

- Planeten-Navigation in ein separates Fenster auslagern und mit unverändertem Ziel und Live-Daten wieder einbetten.
- Favoritenbilder in Originalauflösung öffnen, per Mausrad zoomen und mit der Maus verschieben.
- Favoritentitel erscheinen in Elite-Gelb (#FFCC33); Auswahlmarkierung und weitere Textzeilen bleiben erhalten.
- Alle oder ausgewählte Favoriten mit Bildern und Koordinaten im bestehenden kompatiblen ZIP-/JSON-Format exportieren.
- Klarere Menüführung mit Kompass-Symbol und „Zur Planeten-Navigation“.

„Separates Fenster“ verschiebt dieselbe Navigationsansicht aus dem Hauptfenster.
„Zurück ins Hauptfenster“ und das Schließen des separaten Fensters betten sie
wieder ein. Ziel und Live-Daten bleiben erhalten, Position und Größe werden
gespeichert. Es wird keine zweite Navigationsinstanz erzeugt.

Ein Doppelklick auf die Bildvorschau in den Favoritendetails öffnet die vergrößerte
Ansicht. Das Mausrad zoomt, Ziehen mit gedrückter linker Maustaste verschiebt das
vergrößerte Bild. Doppelklick setzt die Ansicht zurück; Escape schließt sie.
Originalbilder bleiben unverändert.

Der Exportdialog bietet standardmäßig alle Favoriten oder eine unabhängige,
scrollbare Checkboxauswahl mit Name, System und gegebenenfalls Planet/Mond.
„Alle auswählen“, „Keine auswählen“ und ein Auswahlzähler unterstützen die
Mehrfachauswahl. Ohne Markierung ist der selektive Export gesperrt. Such-,
Entfernungs-, Kategorie- und Typfilter schränken die Exportauswahl nicht ein.
Abbrechen verändert keine Daten. Der bestehende Dateidialog, das ZIP-/JSON-Format,
die Bildbehandlung und das Importverhalten bleiben erhalten.

Die integrierte Hilfe und die Release-Kurztexte berücksichtigen alle zwölf
Sprachen. Dark- und Light-Mode werden unterstützt.

DB-Schema bleibt **23**, ohne neue Datenmigration. Persönliche Datenbanken und
Einstellungen bleiben beim regulären Update erhalten. Das Release erzwingt
keine vollständige Neuindizierung. Updatefunktion und Startskripte bleiben
unverändert.
