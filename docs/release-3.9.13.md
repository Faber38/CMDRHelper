# CMDRHelper v3.9.13

- PP2-Systemkontrolle: vier farbige Bereiche für Nicht besetzt, Erschlossen, Verstärkt und Hochburg; weißes Dreieck für den Systemstatus, gelbes Dreieck für den aktuellen Zyklusfortschritt.
- Die Markerpositionen sind ausdrücklich Näherungen, keine bestätigte Frontier-Berechnung. Der Bereich zwischen den Markern wird rot eingefärbt, wenn Weiß rechts von Gelb steht, und blau, wenn Weiß links steht. Stärkung und Schwächung werden unverändert aus dem Journal in CP angezeigt.
- Eigene PP2-Konfliktansicht für nicht besetzte Systeme: Mächte nach Konfliktfortschritt sortiert, mit relativen Balken und vorhandenen Porträts. Bestätigte Farben für Aisling Duval und Nakato Kaine, sonst neutrale Darstellung; fehlende Werte bleiben unbekannt, absolute Konflikt-CP sind nicht verfügbar.
- Alle zwölf vorhandenen Machtporträts werden verwendet; A. Lavigny-Duval verweist auf Arissa Lavigny-Duval. Bestehende Ersatzanzeigen bleiben erhalten.
- Missionen: alle sieben Spalten auf- und absteigend sortieren, Belohnungen numerisch und Fristen chronologisch; die Sortierung wird über QSettings gespeichert.
- Missionsdetails bleiben nach Sortierung und Aktualisierung der richtigen Mission zugeordnet; beim Commanderwechsel wird die bisherige Auswahl zurückgesetzt. Neue PP2-Texte sind in allen zwölf Sprachen verfügbar.

Die Kontrollgrafik zeigt vier farbige Statusbereiche. Ihre Markerpositionen sind eine ausdrücklich gekennzeichnete visuelle Näherung, keine exakte oder bestätigte Frontier-Berechnung. Ohne ausreichende Journalwerte wird kein Zyklusmarker ergänzt; ein bekannter Status kann durch die Mitte seines Bereichs dargestellt werden. Die angezeigten Stärkungs- und Schwächungswerte bleiben die tatsächlichen Journalwerte in CP.

Nicht besetzte Systeme verwenden eine eigene Konfliktansicht. Die Balken vergleichen vorhandene Konfliktrohwerte relativ zum höchsten angezeigten Wert; sie zeigen weder eine bestätigte Kontrollschwelle noch absolute Konflikt-CP. Eine Konflikt-CP-Umrechnung ist nicht implementiert. Fehlende oder widersprüchliche Konfliktwerte bleiben unbekannt. Nur Aisling Duval und Nakato Kaine verwenden bestätigte Machtfarben, die übrigen Mächte eine neutrale Theme-Farbe. Beim System- oder Commanderwechsel werden veraltete Anzeigen entfernt.

Die zwölf Machtporträts und das vorhandene Ersatzbild werden weiterverwendet. Der zusätzliche Alias A. Lavigny-Duval verwendet das Porträt von Arissa Lavigny-Duval; unbekannte oder fehlende Porträts behalten die bestehende Ersatzanzeige.

Die Missionssortierung verwendet die zugrunde liegenden Belohnungen und Zeitpunkte, nicht die formatierten Anzeigetexte. Fehlende Werte stehen aufsteigend zuerst und absteigend zuletzt. Sortierspalte und Richtung bleiben über QSettings erhalten. Auswahl und Detailanzeige folgen der jeweiligen Mission; beim Commanderwechsel bleibt keine Auswahl des vorherigen Commanders bestehen.

Das Datenbankschema bleibt bei Version 23; eine neue Schemamigration ist nicht erforderlich.

Die gezielte UI-Prüfung erfolgt mit Qt offscreen, in Dark- und Light-Mode und allen zwölf Sprachen. Eine native Fensterprüfung unter KDE X11/KWin und Windows steht aus.
