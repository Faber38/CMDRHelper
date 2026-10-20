# CMDRHelper v3.9.14

- PP2-Konfliktansicht für nicht besetzte Systeme überarbeitet: größere vorhandene Machtporträts, Machtname und Kontrollpunkte in einem responsiven Layout; Fortschrittssortierung und vorhandene Machtfarben bleiben erhalten.
- Konflikt-Kontrollpunkte als empirisch gestützte Näherung: CP ≈ ConflictProgress × 120000. Die Balkenfüllung verwendet eine angenommene Skala von 0 bis 180000 CP, begrenzt auf 100 %; fehlende Werte bleiben unbekannt.
- Gestrichelte Konfliktmarkierungen bei 36000 CP (20 %) und 120000 CP (66,67 %), mit Symbolen und übersetzten Tooltips. Grenzen und Balkenskala sind keine bestätigten offiziellen Spielkonstanten; ein Überschreiten ändert keinen Systemstatus.
- Die eigene Macht erscheint bei fehlender Präsenz separat mit „Keine Präsenz“, ohne doppelte Teilnehmeranzeige. Namensvarianten derselben Macht werden zusammengeführt.
- Odyssey-Missionen: generierte Detailtexte folgen späteren Zieländerungen. Explizite ursprüngliche Ziele bei MissionRedirected werden getrennt und commanderbezogen gespeichert; das neue Ziel bleibt Navigationsziel. Fehlende Orte oder Planeten werden nicht geschätzt.
- Das Hauptfenster speichert Größe, Position und Maximierungszustand und stellt sie beim Neustart wieder her. Ungültige gespeicherte Geometrie erhält einen Standardwert; nicht mehr sichtbare Positionen werden korrigiert.

Die Konfliktansicht verwendet weiterhin die zwölf vorhandenen Machtporträts und das Ersatzbild. Für Aisling Duval und Nakato Kaine bleiben die vorhandenen Machtfarben erhalten; andere Mächte behalten die neutrale Darstellung. Die bereits vorhandene Fortschrittssortierung wird beibehalten. Die eigene Macht wird nur dann separat angezeigt, wenn sie nicht bereits unter den Teilnehmern vertreten ist. Namensvarianten werden als dieselbe Macht behandelt.

Die CP-Umrechnung ist eine empirisch gestützte Näherung. Die Skala bis 180000 CP ist eine Darstellungsannahme, keine exakte Frontier-Balkenformel. Die auch in Community-Quellen dokumentierten Grenzwerte 36000 CP und 120000 CP bleiben im Programm als Näherungen gekennzeichnet; sie sind keine unabhängig bestätigten offiziellen Frontier-Spielkonstanten. Die Marker werden durch Division durch 180000 positioniert und bleiben unabhängig von der Füllung sichtbar. Ein Überschreiten löst weder eine Erfolgsmeldung noch einen Systemstatuswechsel aus. Persönliche Merits und Rangberechnung bleiben unverändert; kontrollierte Systeme behalten ihre bisherige Darstellung.

Missionskorrekturen betreffen generierte Zieltexte und ausdrücklich gemeldete ursprüngliche Ziele. Das erste explizite ursprüngliche Ziel bleibt bei weiteren Umleitungen erhalten. Aktuelle Ziele bleiben für die Navigation maßgeblich; fehlende Zielorte oder Planeten werden nicht ergänzt. Ursprungsdaten werden pro Commander und MissionID im vorhandenen Metadatenspeicher abgelegt. Die vorhandene Missionssortierung bleibt erhalten.

Das Datenbankschema bleibt bei Version 23; eine neue Schemamigration ist nicht erforderlich. Zusatzfenster behalten ihre vorhandene Geometrieverwaltung.

Neue Release- und Updatehinweise sind in allen zwölf Sprachen verfügbar. Die gezielte UI-Prüfung erfolgt mit Qt offscreen in Dark- und Light-Mode und verschiedenen Fensterbreiten. Eine native Fensterprüfung unter KDE X11/KWin und Windows steht aus; eine vollständige Regression ist nicht Bestandteil dieser Release-Vorbereitung.
