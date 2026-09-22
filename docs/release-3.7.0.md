# CMDRHelper 3.7.0

## Neu: Handelsassistent

- Eigener Hauptbereich „Handel“ mit „Verkaufen“, „Einkaufen“ und „Empfehlungen“.
- Verkaufen sucht Ankaufsangebote mit ausreichender Nachfrage (Demand); Einkaufen sucht Angebote mit ausreichendem Vorrat (Supply). Umkreis, Datenalter, Landeplatz, Carrier und Anflug lassen sich filtern.
- Beim Öffnen des Elite-Warenmarkts übernimmt der laufende Helper automatisch sicher zugeordnete eigene Stationsmärkte. Diese bleiben commanderbezogen über Helper-Neustarts erhalten und sind strikt weniger als 24 Stunden gültig. Der gewählte Datenalterfilter gilt zusätzlich.
- Verkaufen und Einkaufen kombinieren eigene Marktstände mit Community-Marktdaten über Spansh. Für denselben Markt gewinnt der jüngere gültige Stand; bei gleichem Zeitpunkt die eigene Beobachtung. Gemeinsam nach Preis sortiert werden höchstens 100 Treffer angezeigt. Die vorgelagerten Suchgrenzen des Community-Dienstes bleiben bestehen.
- Bei einem Community-Ausfall bleiben passende eigene Treffer nutzbar. Ein Hinweis kennzeichnet die unvollständige Suche; bessere Community-Angebote können fehlen.
- Empfehlungen beginnen am aktuellen eigenen Einkaufsmarkt und suchen eigene oder Community-Ziele. „Nur eigene Marktdaten“ beschränkt ausschließlich Empfehlungen auf selbst beobachtete Ziele.
- Das aktuelle Schiff und sein sicher bekannter freier Frachtraum, Supply und Demand bestimmen die mögliche Menge. Mindestgewinn, Gewinn pro Tonne und „Möglicher Gewinn“ erleichtern die Auswahl. Marktstände sind Momentaufnahmen; Gewinn und Verfügbarkeit bleiben ungarantiert.
- Fortschrittsanzeige, Abbruch, „Diagnose kopieren“ und der Marktstatus „Eingelesen“ machen den Suchstand nachvollziehbar.
- Ein gemerkter Handelsflug hält eine ausgewählte Empfehlung mit Ware, Ziel und damaligem möglichen Gewinn fest. „System kopieren“ kopiert den Zielsystemnamen. Der Merkzettel ist keine automatische Route und bleibt nicht über einen Helper-Neustart erhalten.

## Systemkarte

- Neue Option „Automatisch an Fenster anpassen“ in der Gesamtansicht: standardmäßig aktiviert und global gespeichert. Sie passt die Ansicht beim Öffnen einmal ein, ebenso beim Einschalten im geöffneten Fenster. Anschließend bleiben manuelles Zoomen, Verschieben, „100 %“ und manuelles Einpassen verfügbar; Fensteränderungen lösen kein ständiges Auto-Fit aus.

## Hilfe und Übersetzungen

- In-App-Hilfe vollständig überarbeitet: alle zwölf Themen gegen die vorhandenen Funktionen geprüft und in zwölf Sprachen synchronisiert.
- Handel, Stationen und Services, Cacheverhalten, Routenfortschritt, Navigation, Missionen und Belohnungen sowie Flottenaktionen genauer dokumentiert.
- Veraltete Bezeichnungen und zahlreiche ältere Übersetzungsfehler korrigiert. Technische Dateinamen bleiben unverändert; lokale Umbruchhilfen verbessern die Darstellung bei großer Schrift.

## Fehlerkorrektur

- Kurze Shutdown-Journale unterbrechen die bestätigte Kontinuität der Mining-Carrierbestände nicht mehr.

## Bestehende Funktionen und Datenquellen

Stationssuche, Typ-/Körperfilter, Details und Services im Explorer sowie die optionale Spansh-Stationsergänzung mit manueller Aktualisierung waren bereits vor 3.7.0 vorhanden. Ihre Hilfe beschreibt nun genauer den separaten persistenten Stationscache. Dieser enthält keine Handelsmarktpreise: Community-Handelsdaten verwenden einen flüchtigen RAM-Suchcache; eigene beobachtete Marktstände werden getrennt und zeitlich begrenzt gespeichert.

Auch Schiffs-Routenfortschritt, automatisches Kopieren des nächsten Systems, Carrier-CSV-Export, Planeten-Navigation, gespeicherte Positionen, Encounter-Aufträge, Kopfgelder, Kampfbelohnungen und persönliche Flottenbilder sind keine neu eingeführten 3.7.0-Funktionen. Ihre vorhandene Bedienung ist jetzt vollständiger erklärt.

## Aktualisierung

Seit v3.6.2 ist keine zusätzliche Datenbank- oder Cachemigration erforderlich. Bestehende Einstellungen und persönliche Daten bleiben erhalten; eine manuelle Datenbanklöschung oder ein Neuimport ist nicht nötig. Die vorhandenen automatischen Reparaturen für ältere Installationen bleiben unverändert. Für die neue Handelsquelle genügt es, den Warenmarkt in Elite bei laufendem Helper zu öffnen.
