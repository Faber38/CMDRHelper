# Materialbestandsrekonstruktion

`cmdrhelper.material_inventory.MaterialInventoryReader` ist eine UI-unabhängige,
rein lesende Auswertung. Der Reader benötigt keine eigene Tabelle, Migration oder Start-Reparatur und
ändert die bestehende Rhino-/Explorer-Datenhaltung nicht. Die vorhandene
[Materialansicht](material-view.md) verwendet ihn über den MaterialController.

## Verwendung

```python
reader = MaterialInventoryReader()  # Instanz für wiederholte Abfragen behalten
inventory = reader.reconstruct(commander_id, fid, journal_sessions)
stock = inventory.material("sulphur")
# stock.category, stock.name, stock.count, stock.known, stock.display_name
```

`journal_sessions` sind vorhandene Indexzeilen als Dictionaries oder
`sqlite3.Row`. Die aufrufende Schicht liefert die zusammengehörige Commander-ID
und FID aus `commanders`. Auch bei einer Liste mit mehreren Commandern werden
nur eindeutig passende Zeilen berücksichtigt. Die Dateiidentität wird zusätzlich
über die enthaltenen Commander-/LoadGame-FIDs überprüft. Widersprüche zwischen
Datei und Index machen das Ergebnis unbekannt. `unknown`/`ambiguous`-Indexzeilen
werden ausgeschlossen; gemischte FIDs innerhalb einer Datei werden abgewiesen.

Bei Journaländerungen kann dieselbe Instanz erneut abgefragt werden. Sie verändert
keinen AppState und benötigt keinen gemeinsamen Live-/Archiv-Verarbeitungsmarker.
Die Abfrage führt Datei-I/O aus. Der MaterialController ruft sie im
Hintergrund außerhalb des UI-Threads auf. Ein Neustart erzeugt denselben Bestand mit einer
neuen Reader-Instanz. Der Cache ist eine Optimierung, keine Wahrheitsquelle.

## Semantik

Alle drei Arrays Raw/Manufactured/Encoded müssen vorhanden und valide sein, damit
ein Materials-Event als vollständiger Snapshot gilt. Ein gültiger Snapshot ersetzt
den Bestand; historisch nachgewiesene Materialidentitäten bleiben mit 0 erhalten,
wenn sie fehlen. Folgeereignisse werden nach Eventzeit verarbeitet, bei Gleichstand
nach Journalpfad und physischem Byteoffset. Frühere Bestandsänderungen sind nach
einem neuen Snapshot vollständig überschrieben. Ohne Snapshot bleiben Mengen
unbekannt, auch wenn bereits einzelne Sammelereignisse vorhanden sind.

Interne Namen werden kleingeschrieben; Frontier-Wrapper `$…_Name;` werden entfernt.
Lokalisierte Namen dienen ausschließlich der Anzeige. Die Phase-1-Zugriffe bleiben auf
beobachtete Identitäten beschränkt; die vollständige Katalogprojektion ist separat.
Ein unbekannter Name liefert `count=None, known=False`. Bekannte Nullbestände liefern
`count=0, known=True`. Datenfehler werden als `issues` zurückgegeben und vom Reducer
protokolliert. Solange sie nicht durch einen späteren gültigen Snapshot behoben
sind, liefern die öffentlichen Bestandszugriffe unbekannte Mengen. Fehlende oder
beschädigte Dateien bleiben eine Unsicherheit für die gesamte Rekonstruktion.

Unterstützt werden Materials, MaterialCollected, MaterialDiscarded, MaterialTrade,
EngineerCraft/Ingredients, Synthesis/Materials, MissionCompleted/MaterialsReward
und EngineerContribution mit Type=Materials. Bei Contributions wird Quantity,
nicht TotalQuantity, abgezogen. Commodity-Contributions verändern nichts.
Transaktionen werden vollständig geprüft, bevor sie angewendet werden. Unterläufe,
negative/nicht ganzzahlige Mengen, Kategorie-Konflikte und nicht zuordenbare Zutaten
werden erkannt; es wird kein negativer Bestand und keine halbe Tauschtransaktion
veröffentlicht. Journalmengen werden nicht multipliziert.

Raw/Elements, Manufactured und Encoded werden auch in Frontier-Kategorietokens
normalisiert. Bei Missionsbelohnungen darf Data nur dann Encoded bedeuten, wenn
der interne Name im validierten Katalog als Encoded geführt wird oder (bei einem
noch nicht katalogisierten Symbol) bereits durch einen Engineering-Snapshot oder
ein eindeutiges Engineering-Ereignis als Encoded nachgewiesen wurde. Nicht belegte
Data-Belohnungen werden nicht aufgenommen. Component/Item/Consumable-Belohnungen
gehören nicht in diesen Bestand.

`last_change` enthält Eventtyp, Zeit, physische Quelle und Änderungen. Die Materialansicht verwendet es für die Live-Hervorhebung und erkennt alte
Replay-Änderungen anhand der Quelle, statt sie bei jeder Abfrage erneut hervorzuheben.

## Dateigrenzen und Doppelverarbeitung

Die Ereignisidentität besteht aus aufgelöstem Journalpfad und Byteoffset des
Zeilenanfangs. Identische Daten in zwei unterschiedlichen echten Zeilen zählen
zweimal. Wiederholte Indexzeilen und erneutes Einlesen zählen nicht doppelt.
Importer-Batchschlüssel werden überhaupt nicht verwendet. Kopierte Journale unter
unterschiedlichen echten Pfaden werden nicht durch Payload-Heuristiken dedupliziert;
der bestehende Index muss die originalen Journaldateien liefern.

Gelesen werden ausschließlich vollständige, newline-terminierte Zeilen. Allgemeine
`last_read_offset`-Werte sind keine Material-Checkpoints und beschränken daher nicht
die lesende Rekonstruktion. So sind auch noch nicht vom übrigen Live-Pfad verarbeitete
Folgeereignisse sichtbar. Geänderte Dateigröße, mtime/ctime oder Dateiidentität
invalidieren den Cache. Änderungen während des Lesens erfordern eine erneute Abfrage.

## Regression und offene Aufgaben

Die portable Regression in `tests/fixtures/materials_faber38.json` enthält einen
früheren echten vollständigen Snapshot (einschließlich dataminedwake), den letzten
vollständigen Snapshot und alle 43 folgenden MaterialCollected-Ereignisse. Andere
Spielaktivitäten wurden nicht übernommen.

Der zusätzliche lokale Integrationstest verwendet die Originaljournale von FABER38/FTEST0001
bis einschließlich Journal.2026-09-08T123632.01.log. Ohne diese privaten lokalen
Daten wird nur dieser Integrationstest übersprungen; die synthetischen Tests sind
portabel. Belegter Endbestand: sulphur 300, vanadium 244, tin 53, molybdenum 63,
niobium 53, yttrium 35. Historisch bekannte Kategorien: 28/56/35, davon positiv
28/56/34; dataminedwake ist bekannt mit 0.

Phase 2 ergänzt den statischen Katalog und `merge_inventory(inventory)` für alle
146 Katalogzeilen; siehe [Materialkatalog](material-catalog.md). Phase-1-Zugriffe
`material()`/`by_category()` und ihre historischen Identitätsmengen bleiben erhalten.

Separater offener Bug, hier unverändert: Die Rhino-Fundhistorie kann dieselben
Ereignisse unter `delta:…` und `line:…` mehrfach zählen. Am 08.09.2026 stehen für
Body 24/System 7879797001587 in der DB Vanadium 17, Molybdän 8 und Zinn 8 gegenüber
Journalmengen 15/7/7. Diese neue Bestandsauswertung liest keine der betroffenen
surface_mining-Tabellen oder deren Verarbeitungsmarker.
