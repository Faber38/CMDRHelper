# Flottenanalyse und manuelle Löschung (Entwicklungsstand 3.5)

## Neutrale Journalbeispiele

Zwei Schiffe desselben Test-Commanders haben unterschiedliche ShipIDs (23 und 4),
aber dieselbe frei benannte Kennung `TST-01`. Die Identität ist
`(commander_id, ship_id)`, nicht der frei wählbare Schiffsname oder die Kennung.

Ein `ShipyardSwap` mit `StoreShipID: 23` belegt zunächst nur die Einlagerung.
Erst ein späteres `ShipyardSell` mit `SellShipID: 23` belegt den Verkauf.
Ein anschließendes `StoredShips` mit ShipID 4 bestätigt weiterhin deren Besitz.
Eine ältere Standortangabe eines eingelagerten Schiffs ist kein Verkaufsbeleg.

Die Kennung kann bereits vor einem Verkauf mehrfach vorkommen. Auch eine
mögliche Wiederverwendung einer ShipID darf nicht ohne Beleg ausgeschlossen werden.

## Bisherige Persistenz

Flottendaten einschließlich Modul-JSON liegen in `commander_ships`; keine
separate schiffsbezogene Modultabelle muss mitgelöscht werden. Journalindex,
Besuche, Materialien, Missionen und übrige Fachtabellen sind unabhängig.

LoadGame, Loadout, ShipyardSwap/Buy und Modulereignisse schreiben die Flotte.
ShipyardSell/SellShip/SellStoredShip und SellShipID beim Kauf werden bisher
nicht als Flottenentfernung verarbeitet. Historische Schiffe bleiben dadurch
liegen; eine ausdrücklich modellierte Verkaufs-/Historienentscheidung gab es
nicht. Das Beispielschiff bleibt also wegen fehlender Verkaufsbehandlung erhalten.
Die ursprüngliche manuelle Löschfunktion führte keine automatische
Verkaufsbereinigung ein. Die unten beschriebene Ergänzung verarbeitet jetzt
nachgewiesene Journalverkäufe.

Der normale Start nutzt persistente Daten und Journalcursor, nicht pauschal eine
vollständige Flottenrekonstruktion. Ohne Löschmarkierung könnten erneute
historische Verarbeitung oder spätere Schiffereignisse einen entfernten Eintrag
aber wieder anlegen.

## Neue Löschstrategie

Schema 18 ergänzt additiv `commander_deleted_ships` mit Commander-Fremdschlüssel,
ShipID und UTC-Löschzeitpunkt. Commander ist über die bestehende eindeutige FID
identifiziert. Tabelle und Flottenzeile werden in derselben SQLite-Transaktion
geändert. Alle regulären Schreibwege prüfen den zusammengesetzten Schlüssel.
Helper-/Elite-Neustart, historische Verarbeitung, Catch-up und UI-Refresh heben
Löschmarkierungen nicht allein durch Wiedergabe alter Ereignisse auf.

Das gespeicherte aktuelle bzw. eindeutig letzte Schiff sowie die explizite
Live-ShipID sind gegen Löschung geschützt; nach dem Dialog erfolgt die Prüfung
nochmals in der Transaktion. Der Dialog wählt standardmäßig Abbrechen.

Persönliches Bild und QSettings-Zuordnung werden nur für die genaue FID/ShipID
entfernt. Bei Datei-, Einstellungs- oder DB-Fehlern wird zurückgerollt; die
Bildkopie wird für eine mögliche Kompensation vorübergehend im Speicher gehalten.
Programmassets und andere Bilder bleiben unberührt. Dateisystem, QSettings und
SQLite sind keine gemeinsame crash-atomare Ressource: die Kompensation behandelt
abgefangene Fehler, nicht einen Prozessabbruch/Stromausfall mitten im Vorgang.

**Explizite Live-Rückkehr:** Nur der letzte eindeutige aktive Schiffsbeleg
(LoadGame, Loadout, ShipyardSwap/Buy) in einem als aktuell markierten Delta des
neuesten Journals darf eine Markierung aufheben. Sein UTC-Zeitpunkt muss nach der
manuellen Löschung liegen und darf nicht in der Zukunft liegen. Historische
Speicher-/Rekonstruktionsaufrufe erhalten diese Berechtigung nicht. So bleiben
neue tatsächliche Aktivmeldungen funktionsfähig, unabhängig von einer unbelegten
Annahme zur Wiederverwendung von ShipIDs. Persönliche Bilder kommen nicht zurück.

## Alle Schiffe neu einlesen

Nach Bestätigung liest ein Hintergrundauftrag die verfügbaren Journale aus dem
konfigurierten Ordner und den noch vorhandenen commanderbezogenen Indexpfaden.
FID-Zuordnung wird aus jedem Journal erneut eindeutig ermittelt; fremde,
mehrdeutige und unbekannte Identitäten werden nicht übernommen. Es werden nur
Schiffs-, Ausrüstungs- und notwendige Ortsereignisse ausgewertet. Keine globalen
Import-/Repair-Funktionen und keine Journalcursor werden verändert.

Erst nach erfolgreichem Lesen werden ausschließlich die Löschmarkierungen dieses
Commanders zusammen mit der rekonstruierten Flotte transaktional veröffentlicht.
Leere, defekte oder während des Lesens geänderte Eingaben entfernen keine
Markierungen. Noch nicht vollständig geschriebene letzte Zeilen werden ignoriert.
Vorhandene Flottenzeilen, für die das verfügbare Archiv keinen Beleg mehr enthält,
bleiben aus Sicherheitsgründen erhalten; neuere Live-Beobachtungen werden nicht
mit älteren Daten überschrieben. Das zuletzt bekannte Schiff bleibt geschützt.

Manuell gelöschte Schiffe können wieder erscheinen, soweit die nachfolgende
Ereigniskette keinen späteren Verkauf belegt. Das verkaufte Beispielschiff erscheint
mit der Verkaufs-Ergänzung nicht wieder.
Bilder werden nicht aus Journalen erzeugt. Wiederhergestellte Schiffe verwenden
Typbild bzw. standart.png, solange kein neues persönliches Bild gewählt wurde.


## Ergänzung: belegte Journalverkäufe

Quelle: [Frontier Journal Manual v37](https://hosting.zaonce.net/community/journal/v37/Journal_Manual_v37.pdf),
Abschnitte 8.44, 8.47–8.53. Unterstützt werden ausschließlich dokumentierte
Verkaufsereignisse mit expliziter numerischer Identität und gültigem UTC-Zeitpunkt:

- `ShipyardSell` mit `SellShipID`.
- `SellShipOnRebuy` mit `SellShipId` (abweichende Feldschreibweise).
- `ShipyardBuy` und `ShipyardSwap`, jeweils nur mit optionalem `SellShipID`.

`StoreShipID`, ShipyardTransfer, Died, SelfDestruct und Resurrect sind für sich
keine eindeutigen Verkaufsbelege mit betroffener Schiffidentität. Die erfundenen
Ereignisnamen SellShip/SellStoredShip werden nicht unterstützt. Fehlende Einträge
in StoredShips werden ebenfalls nicht als Verkauf interpretiert.

Schema 19 ergänzt `commander_ship_sales` mit Commander-ID, ShipID, jüngstem
Verkaufszeitpunkt und Ereignistyp. Das sind Journalfakten, keine manuellen
Löschmarkierungen. Verkauf, Flottenentfernung und Importcursor werden gemeinsam
transaktional gespeichert. Die Markierungen in commander_deleted_ships bleiben
bei automatischen Verkäufen unverändert.

Schiffsmeldungen mit einem Zeitpunkt kleiner oder gleich dem gespeicherten
Verkaufszeitpunkt werden nicht erneut übernommen. Eine spätere ausdrückliche
Besitzmeldung (LoadGame, Loadout, ShipyardSwap/New oder positiver StoredShips-
Eintrag) darf das Schiff wieder anlegen, sofern keine manuelle Sperre greift.
Ein alter verspätet importierter Verkauf entfernt keine neuere Besitzbeobachtung.
Module-/Ortsereignisse allein erzeugen ein verkauftes Schiff nicht erneut.
ShipyardNew verwendet das dokumentierte Feld NewShipID.

Die vollständige Flottenrekonstruktion sortiert die relevanten Ereignisse nach
UTC-Zeit, verarbeitet Verkäufe und übergibt auch ihre Belege an die Persistenz.
Dadurch werden bereits gespeicherte Altlasten wie ShipID 23 beim bewussten
Neueinlesen entfernt. Auch eine ausschließlich Verkäufe enthaltende Rekonstruktion
ist ein gültiges Ergebnis. Die Verkaufsbelege bleiben bei diesem Vorgang erhalten;
es werden nur die manuell gesetzten Löschmarkierungen aufgehoben.

Persönliche Bilder werden durch automatische Journalverkäufe bewusst **nicht**
gelöscht: Hintergrundimporte verändern weder QSettings noch Benutzerdateien.
Die vorhandene manuelle Löschaktion entfernt weiterhin das zugehörige Bild.
Typbilder und standart.png bleiben unverändert. Es entstehen keine neuen UI-Texte.

Die Regression prüft, dass ein ausdrücklich verkauftes Beispielschiff fehlt,
während das andere weiterhin vorhanden ist. Bereits quittierte alte Journale
werden beim normalen Start nicht pauschal erneut eingelesen; für solche Altbestände
ist „Alle Schiffe neu einlesen…“ der gezielte Aktualisierungsweg.
