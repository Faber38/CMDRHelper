# Engineering-Materialkatalog

Prüfdatum: **2026-09-08**. Der Katalog ist statisch, global, UI-unabhängig und
offline verwendbar. Keine Laufzeit-Webabfrage, DB-Tabelle oder Migration.
`cmdrhelper/_material_catalog_data.py` enthält die expliziten Datensätze;
`cmdrhelper/material_catalog.py` validiert Struktur, Identitäten und Verteilungen
beim Laden und stellt unveränderliche Definitionen bereit.

## Quellen und Revisionsstand

- [EDCD/FDevIDs material.csv](https://github.com/EDCD/FDevIDs/blob/d7f0dbe56656d7411d47041562a98594d27bfab9/material.csv),
  Revision `d7f0dbe56656d7411d47041562a98594d27bfab9`: alte Basis mit 137 Einträgen
  (28/64/45), Frontier-Symbole und Untergruppen. Keine unveränderte Übernahme der
  dort teilweise veralteten Guardian-Grade.
- [ED Odyssey Materials Helper, Enums](https://github.com/jixxed/ed-odyssey-materials-helper/tree/2e6d4c3e767d2b714ffddc5c9386831d66812916/application/src/main/java/nl/jixxed/eliteodysseymaterials/enums),
  Revision `2e6d4c3e767d2b714ffddc5c9386831d66812916`: `Raw.java`,
  `Manufactured.java`, `Encoded.java` für den regulären Umfang, Grade und Gruppen;
  `Rarity.java` sowie `getMaxAmount()` für Kapazitäten. UNKNOWN-Einträge sind
  keine Materialien. Die Quellwerte wurden nur beim Erstellen ausgewertet;
  jeder endgültige Datensatz enthält seinen eigenen Maximalwert.
- [EDCD/EDDI, Materialnamen](https://github.com/EDCD/EDDI/tree/aacbf3b921eff696e3e590fc13c09a3dad49bd2c/DataDefinitions/Properties),
  Revision `aacbf3b921eff696e3e590fc13c09a3dad49bd2c`: `Materials.resx`,
  `Materials.de.resx`, `Materials.it.resx`, `Materials.fr.resx`, `Materials.es.resx`.
  Ausschließlich nicht leere Namen nach kanonischem Symbol übernommen. Die
  bestehenden 24 Namen pro CMDRHelper-Sprache haben Vorrang und bleiben unverändert.
  EDDI wird hier nicht als Grade-/Kategoriequelle verwendet: Dort vorhandene
  veraltete Guardian-Grade bzw. die Einordnung von tg_shutdowndata werden nicht übernommen.
- [INARA, Kapazitätskorrektur Tactical Core Chip](https://inara.cz/kingdom-come-2/board-thread/1/8952/?page=958):
  Rückmeldung und Bestätigung durch den Betreiber vom 19.02.2024 für 100 statt 250.
- [INARA, Guardian-Inventarbericht](https://inara.cz/elite/cmdr-logbook-entry/7656/31376/):
  zusätzlicher Abgleich der Blueprint-Grenzen 150 für Module/Waffen, 100 für Schiffe.

Das sind überprüfte Community-Datenquellen; es wird kein offizieller vollständiger
Frontier-Katalog behauptet. Widersprüchliche oder unbestätigte Angaben bleiben offen.

## Umfang, Grade und Gruppen

| Kategorie | G1 | G2 | G3 | G4 | G5 | unbekannt | Gesamt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Raw | 7 | 7 | 7 | 7 | 0 | 0 | 28 |
| Manufactured | 13 | 14 | 17 | 13 | 14 | 0 | 71 |
| Encoded | 7 | 8 | 12 | 10 | 9 | 1 | 47 |
| Gesamt | 27 | 29 | 36 | 30 | 23 | 1 | 146 |

Gruppen: **108 standard, 13 guardian, 25 thargoid**.
Untergruppen übernehmen die stabilen `HorizonsMaterialType`-Bezeichner der
EDOMH-Quelle kleingeschrieben, z. B. `raw_1`, `capacitors` und `wake_scans`.
Guardian/Thargoid erhalten keine zusätzlich erfundene Untergruppe (`None`).
Symbole sind kleingeschriebene Frontier-Namen, niemals lokalisierte Identitäten.

### Neun Ergänzungen gegenüber FDevIDs

| Symbol | Kategorie | Grad | Maximum |
| --- | --- | ---: | ---: |
| tg_abrasion03 | Manufactured | 1 | 300 |
| tg_causticshard | Manufactured | 2 | 250 |
| unknowncorechip | Manufactured | 2 | 100 |
| tg_causticgeneratorparts | Manufactured | 3 | 200 |
| tg_abrasion02 | Manufactured | 3 | 200 |
| tg_causticcrystal | Manufactured | 4 | 150 |
| tg_abrasion01 | Manufactured | 5 | 100 |
| tg_shutdowndata | Encoded | 3 | 200 |
| tg_interdictiondata | Encoded | 3 | 200 |

Alle neun gehören zur Gruppe thargoid. Fünf Guardian-Grade wurden gegenüber
FDevIDs korrigiert: `ancienthistoricaldata` 4→1, `ancientculturaldata` 4→2,
`ancientbiologicaldata` 4→3, `guardian_moduleblueprint` 4→5 und
`guardian_weaponblueprint` 4→5.

## Explizite Kapazitäten und offene Fälle

Die bestätigte Standardregel für Raw/Manufactured/Encoded lautet
G1=300, G2=250, G3=200, G4=150, G5=100 (`Rarity.java`). Sie dient nur zur
Erstellung/Validierung; die fachliche Abfrage liest ausschließlich `maximum`
des jeweiligen Eintrags. Keine Laufzeit-Ableitung des Maximums aus dem Grad.

`Encoded.getMaxAmount()` bestätigt für Guardian:

| Symbol | Grad | Maximum |
| --- | ---: | ---: |
| ancienthistoricaldata | 1 | 150 |
| ancientculturaldata | 2 | 150 |
| ancientbiologicaldata | 3 | 150 |
| ancientlanguagedata | 4 | 150 |
| ancienttechnologicaldata | 4 | 150 |
| guardian_moduleblueprint | 5 | 150 |
| guardian_weaponblueprint | 5 | 150 |
| guardian_vesselblueprint | 5 | 100 |

Die beiden G4-Obeliskdaten und das Schiffsblueprint stimmen mit der Standardregel
überein, sind zur vollständigen Prüfung der Sondergruppe dennoch aufgeführt.
Alle fünf Guardian-Manufactured-Materialien folgen der Standardregel.
`Manufactured.getMaxAmount()` setzt `unknowncorechip` trotz G2 ausdrücklich auf
**100**. Die übrigen bestätigten Thargoid-Kapazitäten folgen der Standardregel.

`tg_shipsystemsdata` bleibt regulärer Eintrag mit **grade=None, maximum=None**:
INARA führt Grad 3, während FDevIDs/EDDI/EDOMH Grad 4 führen. Dieser Konflikt ist
nicht aufgelöst; es wird weder ein Grad noch ein daraus abgeleitetes Maximum geraten.
`tg_structuraldata02` ist ausgeschlossen: Eine Definition in EDDI allein bestätigt
keine aktuelle reguläre Verfügbarkeit. Keine 147. Zeile, keine anderen Alt-/Debugsymbole.

## Übersetzungen

Alle Namen verwenden `body_detail.material.<symbol>`; keine parallelen Keys.
Die bestehenden 24 BodyDetail-Keys bleiben in allen zwölf Sprachen unverändert.

| Sprache | Vorhandene Materialnamen | Englischer Fallback |
| --- | ---: | ---: |
| en | 146 | 0 |
| de | 146 | 0 |
| it | 146 | 0 |
| fr | 135 | 11 |
| es | 135 | 11 |
| no | 24 | 122 |
| sv | 24 | 122 |
| fi | 24 | 122 |
| pl | 24 | 122 |
| nl | 24 | 122 |
| tr | 24 | 122 |
| el | 24 | 122 |

In fr/es fehlen jeweils: tg_abrasion01, tg_abrasion02, tg_abrasion03,
tg_biomechanicalconduits, tg_causticcrystal, tg_causticgeneratorparts,
tg_causticshard, unknowncorechip, tg_interdictiondata, tg_shipflightdata,
tg_shipsystemsdata. In den übrigen sieben Sprachen fehlen alle neuen 122 Keys.
Es werden keine englischen Kopien als angebliche Übersetzungen gespeichert.
`tr_for_language()` übersetzt ohne Änderung der aktiven UI-Sprache; sowohl diese
Funktion als auch der bestehende `tr()` nutzen Englisch als Fallback.
`tools/check_i18n.py` erlaubt fehlende Übersetzungen ausschließlich für die neuen
validierten 122 Katalogkeys mit vorhandenem englischem Text. Die alten 24 und
alle übrigen UI-Keys bleiben verpflichtend.

## Fachliche API und Phase-1-Verbindung

```python
from cmdrhelper.material_catalog import (
    all_materials, get_material, materials_by_category, localized_name, merge_inventory,
)

definition = get_material("vanadium")
raw = materials_by_category("Raw")
name = localized_name("vanadium", "de")
rows = merge_inventory(inventory)  # 146 unveränderliche CatalogStock-Zeilen
# row.material: symbol, english_name, category, grade, maximum, group, subgroup, i18n_key
# row: commander_id, fid, snapshot_timestamp, count, known, percent, fill_state
```

Ein zuverlässiger vollständiger Phase-1-Snapshot macht im Katalog fehlende
Materialien zu bekannten Nullbeständen. Ohne Snapshot oder bei ungeklärten
Bestandsfehlern bleibt `count=None, known=False`. Kategorie-Widersprüche werden
in der Projektion nicht umgedeutet, sondern als unbekannt behandelt.
Die Projektion verändert weder Phase-1-Bestände noch deren historisch beobachtete
Identitätsmenge. Nicht katalogisierte Journalsymbole bleiben in Phase 1 erhalten.
Katalogdefinitionen werden geteilt, Commanderwerte bei jeder Projektion neu erzeugt.

Data-Missionsbelohnungen können nun durch eine eindeutige Encoded-Katalogidentität
zugelassen werden, auch wenn der Commander sie nie besaß. Odyssey-Data wird nicht
pauschal aufgenommen. Der bestehende Nachweis über zuvor eindeutig als Encoded
beobachtete, noch nicht katalogisierte Identitäten bleibt erhalten.

`percent = count * 100 / maximum`, sofern Bestand und Maximum bekannt sind.
Keine Rundung oder Begrenzung des fachlichen Wertes. `fill_state` ist `empty` bei 0,
`low` bei >0 bis einschließlich 20%, `near_full` bei mindestens 80% und unter 100%,
`full` bei genau 100%. Dazwischen, oberhalb des Maximums oder bei unbekanntem
Bestand/Maximum lautet der Wert `None`. Insbesondere unbekanntes Maximum + 0
wird nicht als `empty` eingestuft. Die Materialansicht behandelt „Alle“ unabhängig davon.

Nach Journaländerungen rekonstruiert der Controller im Hintergrund und projiziert
den Bestand in die vorhandene [Materialansicht](material-view.md).
`inventory.last_change` liefert die Live-Hervorhebung; alte Replay-Änderungen
werden anhand ihrer Quellenidentität erkannt.

## Regression und UI-Anbindung

Alle 119 historisch bekannten FABER38-Symbole (28/56/35) lösen sich eindeutig auf.
Die Projektion liefert 146 Zeilen: 118 positive, 28 Nullbestände, darunter
27 zuvor nie beobachtete Katalogsymbole und `dataminedwake=0`.
Bestätigt: sulphur=300, vanadium=244/250=97,6%, tin=53, molybdenum=63,
niobium=53, yttrium=35. Portable Originalevent-Fixture und optionaler Test über
die vorhandenen Originaljournale prüfen dies; der lokale Test misst zusätzlich
kalte/warme Rekonstruktion und Katalogprojektion.

Die Materialansicht baut auf diesem Modell auf. Offen bleiben der ausdrücklich
unbekannte Grad/das Maximum von tg_shipsystemsdata und die dokumentierten fehlenden
Namensübersetzungen mit funktionierendem englischen Fallback. Die UI zeigt
unbekannte Kapazität ohne Prozent/Balken; Reader-Aufrufe und Hervorhebungen
sind an den Live-Pfad angebunden. Kein Eingriff in Rhino, Explorer,
Body-Zusammensetzung, Frachtraum, EDSM, BIO/GEO oder Start-Reparaturen.
