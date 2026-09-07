# Planetarer Lat/Lon-Kompass

**Explorer → Planeten-Navigation → Manuelle Eingabe …** öffnet die Zieleingabe jederzeit.
Der aktuelle Body wird aus Status bzw. Journal übernommen. Alternativ lässt sich
sein Name auswählen oder eingeben. Latitude und Longitude akzeptieren sechs
Nachkommastellen, Null und negative Werte. Der Zielname ist optional.
BodyID und SystemAddress werden, soweit eindeutig bekannt, intern ergänzt.
Sie sind weder Eingabefelder noch Voraussetzungen für die Navigation.

Ein Ziel bleibt bis „Navigation beenden“ im Arbeitsspeicher. Es kann jederzeit
ersetzt werden. Favoriten stehen unter **Explorer → ★ Favoriten** zur Verfügung.
Oberflächenfavoriten übergeben über **▶ Zum Ziel** den gespeicherten Body und
Latitude/Longitude an den bestehenden Planeten-Navigator. Sie besitzen keine
eigene Navigationslogik. Eine Routen- oder Systemwechselverwaltung gibt es nicht.
Nach einem Helper-Neustart werden Journal und Status neu eingelesen; ein neues
Ziel funktioniert ohne vorherigen Navigationszustand oder ApproachBody.

Jeder Poll liest Status.json vollständig neu. BodyName muss zum Ziel passen,
HasLatLong muss gesetzt sein und Latitude, Longitude, Heading sowie PlanetRadius
müssen gültig sein. Ein aktuell gesetztes Hypersprungflag macht den Snapshot
ungültig. Bei fehlenden, unvollständigen, ungültigen oder unpassenden Daten erscheint
„Warte auf planetare Koordinaten …“. Die Liveberechnung wird geleert.
Sobald der aktuelle Snapshot wieder passt, startet der Kompass unmittelbar.

Journaldaten dienen nur als optionale Body-Metadaten. Journalereignisse, FID,
technische IDs, historische Zeitstempel und frühere Flugphasen geben die Berechnung
weder frei noch sperren sie diese. Es gibt keinen Ereignis-Latch, keine Generation,
keinen Bewegungsnachweis und keine künstliche Altersgrenze. Auch ein unverändert
von Frontier bereitgestellter vollständiger Snapshot wird ausgewertet; es werden
niemals einzelne Felder aus älteren Snapshots ergänzt. Der Zeitpunkt des letzten
vollständigen Status bleibt separat sichtbar.

Über 380 km Zielentfernung erscheint die große Kugel; bis einschließlich 380 km
erscheint das gekippte Perspektivraster mit 50-km-Entfernungslinien. Es gibt nur
diese eine Darstellungsgrenze und keine Hysterese. Die Zeichenfläche bleibt gleich groß. Der eigene
weiße Kreis steht bei der Kugel in der Mitte und beim Raster unten; der kleinere
Zielpunkt ist orange auf der sichtbaren
und rot auf der verdeckten Halbkugel. Heading dreht die schematische Oberfläche.
Zielentfernung über die Oberfläche, aktuelle und Zielkoordinaten, Peilung,
Heading, relative Richtung links/rechts und Zielkurs stehen zusätzlich als Zahlen
bereit. An Polen, Gegenpunkten und identischen Positionen werden nicht eindeutige
Richtungen ausdrücklich gekennzeichnet. Ein Anflugprofil gibt es nicht. Das Fenster öffnet und aktualisiert sich ohne aktive Fokusanforderung.

Tests prüfen Snapshot-Wechsel, Neustart, wiederholte Zieleingabe, fehlende IDs,
unabhängige Journalmetadaten, Geometrie, Markerfarben, Kugelgröße und Fensterfokus.
