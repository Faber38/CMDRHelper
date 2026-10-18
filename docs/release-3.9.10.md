# CMDRHelper v3.9.10

- Journalverzeichnisse: mehrere Quellen mit Steam-/Heroic-Erkennung, Bearbeitung, Überwachungs-Checkboxen und getrennten Statistiken verwalten.
- Commander: FID-geprüfte Zuordnung, gespeicherte Auswahl und optionales automatisches Folgen einer eindeutig erkannten Spielinstanz unter Linux.
- Powerplay 2.0: optionaler Uhrzeitfilter, kompakte Transportzeilen und verbesserte Schiffsscan-Zuordnung für +1 bis +100 Merits und erneute vollständige Scans.
- Zusatzfenster bleiben beim Minimieren des Hauptfensters unabhängig geöffnet und werden beim Beenden des Helpers geschlossen.
- EDSM und Inara: getrennte EDSM-Sende-/Empfangsschalter, quellenbezogene Uploadpositionen, sichere Bestätigungen und verbesserte Wiederholungsbehandlung.
- Zuverlässigere Journalverarbeitung mit transaktionalen Lesepositionen und Identitätsprüfungen; datensparsame Odyssey-Darstellungsdiagnose im Diagnosepaket.

Mehrere Journalverzeichnisse lassen sich gemeinsam verwalten. Vorhandene
Einzelordner-Einstellungen werden übernommen. Die Suche erkennt vorhandene
Steam- und Heroic-/Epic-Journale in den unterstützten Verzeichnissen; Symlink-Aliase
werden nicht doppelt überwacht. Quellen können hinzugefügt, benannt, bearbeitet,
aktiviert, deaktiviert und entfernt werden. Pfadprüfung und Dublettenschutz helfen
bei Änderungen. Entfernen löscht weder Journale noch historische Daten.
Die Dateistatistik und „Jetzt einlesen“ beziehen sich auf die ausgewählte Quelle.

Die Commander-Zuordnung beruht auf bestätigten FIDs. Ein Journalverzeichnis darf
Sitzungen mehrerer Commander enthalten. Journalverarbeitung und angezeigter
Commander sind getrennt. Unter Linux kann der optionale Folgemodus eine eindeutig
zugeordnete laufende Elite-Instanz anhand von Prozess-, Präfix- und Journaldaten
erkennen. Bei mehreren Instanzen oder unklarer Zuordnung erfolgt keine erzwungene
Umschaltung. Manuelle Auswahl und die zuletzt gespeicherte Auswahl bleiben erhalten.
Unter Windows steht die quellenbezogene Prozesszuordnung nicht zur Verfügung;
dort wird die gespeicherte beziehungsweise manuelle Auswahl verwendet.

Die PP2-Chronik ergänzt den Tagesfilter um eine optionale lokale Uhrzeit.
Ohne aktivierten Uhrzeitfilter bleibt die Tagesansicht unverändert. Transportzeilen
stellen Menge, Ware und Ort kompakter dar; vollständige Angaben bleiben im Tooltip
zugänglich. Vollständige Schiffsscans können mit ganzzahligen Gutschriften von
+1 bis +100 Merits innerhalb des unveränderten Drei-Sekunden-Fensters verknüpft
werden. Erneute vollständige Scans scheitern nicht allein an gleichem Pilotnamen
oder Schiffstyp. Zielangaben bleiben optional. Konkurrierende Ursachen verhindern
weiterhin die Zuordnung; zeitliche Zuordnungen bleiben als solche gekennzeichnet.
Merit-Gesamtstände, Rangberechnung und Chroniksortierung werden nicht verändert.

Eigenständige Zusatzfenster erhalten eine unabhängige Fensterzuordnung. Dazu zählen
Fracht und Explorer-Liveansichten, Chronik- und Systemansichten, modelose Hilfen,
Stationsansichten, Bildbetrachter und die ausgelöste Navigation. Ihre Datenanbindung
bleibt erhalten. Einzelne Fenster lassen sich unabhängig minimieren und schließen;
beim Beenden des Helpers werden die zugehörigen Fenster geschlossen. Modale
Eingabe- und Bestätigungsdialoge behalten ihr bisheriges Verhalten.

EDSM-Senden und -Empfangen sind getrennt schaltbar. Erreichbarkeit und Uploadstatus
werden getrennt angezeigt; ein Verbindungstest ist keine Uploadbestätigung.
Uploadpositionen unterscheiden FID, Quelle und Journalpfad. Eindeutig zuordenbare
vorhandene Positionen werden übernommen, ohne ungefragt historische Daten erneut
hochzuladen. Teilbestätigungen, Wiederholungswartezeiten und technische
Uploaddiagnosen werden genauer behandelt. Alte Zugangsdaten werden nur bei
bestätigter Identität übernommen.

Inara-Antworten werden über eventCustomID dem ursprünglichen Commander und Auftrag
zugeordnet. Unklare Antworten bestätigen keine Einträge. Sicher zuordenbare
Bestätigungen bleiben auch nach einem Commanderwechsel gültig. Retry-After wird
berücksichtigt; gespeicherte Wartezeiten bleiben nach einem Neustart erhalten.

Journalfakten und Lesepositionen werden weiterhin gemeinsam transaktional
fortgeschrieben. Die Metadatenbehandlung berücksichtigt Catch-up, unvollständige
Schlusszeilen und die Prüfung bereits verarbeiteter Dateibereiche. Widersprüchliche
Identitäten werden abgewiesen; verspätete Ergebnisse dürfen keine fremde
Commander-Ansicht überschreiben.

Das vorhandene Diagnosepaket kann zusätzlich technische Informationen zur
Odyssey-Darstellung enthalten, etwa Skalierung, Geometrie und aggregierte
Darstellungsmerkmale. Persönliche Materialmengen werden dabei nicht erfasst.
Es werden keine automatischen Screenshots oder Diagnoseübertragungen erzeugt.

Die Oberfläche und Update-Zusammenfassungen berücksichtigen alle zwölf
unterstützten Sprachen. Das Datenbankschema bleibt bei Version 23.
