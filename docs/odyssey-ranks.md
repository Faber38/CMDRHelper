# Odyssey-Rangbewertung

Prüfstand: 2026-10-13. Eigene CMDRHelper-Prioritäten für Anzug-/Waffen-Upgrades,
Modifikationen und Ingenieur-Freischaltungen; keine offiziellen Elite-Materialgrade.
Keine Aussage über Verkaufspreis, allgemeine Nützlichkeit, Missionsbedarf oder
Powerplay-Wert. Persönliche Aufräumcheckboxen und Standardauswahl bleiben unabhängig.

## Quellen und Prüfung

- Vorhandener [Identitätskatalog](odyssey-catalog.md): 223 eindeutige Elite-Kennungen,
  englische Namen, vorhandene lokalisierte Namen und Kategorien.
- [Odyssey Materials Helper: OdysseyBlueprintConstants.java](https://github.com/jixxed/ed-odyssey-materials-helper/blob/2e6d4c3e767d2b714ffddc5c9386831d66812916/application/src/main/java/nl/jixxed/eliteodysseymaterials/constants/OdysseyBlueprintConstants.java),
  exakt dieselbe Datenrevision wie die bestehenden Engineering-Merkmale. Alle fünf
  Rezeptmaps erneut geprüft; die Vereinigungsmenge stimmt mit allen 98 bisherigen
  Engineering-Gegenständen überein. Rezeptkennungen pro Gegenstand sind lokal in
  `_odyssey_rank_data.py` hinterlegt. Lizenz: [MIT-Attribution](odyssey-catalog-licenses.md).
- [INARA-Gegenstandsliste](https://inara.cz/elite/components/), abgerufen am Prüfdatum:
  180 exakte englische Namenszuordnungen. Alle 81 bisherigen Standardkandidaten
  (50 Daten, 31 Waren) haben dort Used=0 und in den fünf Rezeptmaps keine Verwendung.
  Kein Standardkandidat musste höher eingestuft werden.
- [INARA: Power Regulator](https://inara.cz/elite/componentitem/10271/): im Detail
  jeweils 0 Modifikationen, Upgrades und Ingenieure. Die allgemeine Liste nennt
  dennoch Used=1. Deshalb wird deren Used-Zahl nicht als Engineering-Zahl interpretiert.
  Der Reaktor-Einsatz ist keine Engineering-Verwendung; nach der vorgegebenen
  Definition erhält dieser Gegenstand D.

## Bewertungsregeln

Die lokale Tabelle enthält explizite Bewertungen für alle 223 Kennungen. Sie wird
beim Öffnen der Ansicht weder aus dem Netz geladen noch dynamisch neu bewertet.

1. **A**: direkte Anzug-/Waffen-Upgrade-Zutat (wiederkehrender Ausbau bis G5), oder
   mindestens fünf unterschiedliche Modifikationsfamilien über Anzüge UND Waffen.
2. **B**: bekannte Ingenieur-Freischaltung/Weiterempfehlung, unabhängig von der
   Rezeptanzahl; außerdem mehrere unterschiedliche Modifikationsfamilien.
3. **C**: genau eine bekannte Modifikationsfamilie, keine Upgrade-/Freischaltfunktion.
4. **D**: keine Referenz in den fünf Rezeptmaps UND bestätigtes Used=0 bei INARA;
   zusätzlich der einzeln geprüfte Power Regulator.
5. **?**: keine ausreichend geprüfte Engineering-Bewertung. Insbesondere werden
   Powerplay-Used-Zahlen nicht in Engineering-Verwendungen umgedeutet.

Kinetische, Laser- und Plasma-Varianten desselben Modifikationsnamens zählen als
**eine** Familie. Upgrade-Stufen zählen nicht als eigenständige Wichtigkeitsgründe.
So werden weder bloße Rezeptzahlen noch lokalisierte Namen zur Rangidentität.
Freischaltungen berücksichtigen auch die Weiterempfehlung zu weiteren Ingenieuren.
Die Bewertung setzt keinen persönlichen Freischaltfortschritt voraus.
Eine vergleichbare, belastbare Beschaffungsschwierigkeit für jeden Gegenstand
liegt nicht vor; es werden keine Seltenheitswerte erfunden oder als Rangbonus benutzt.

Die Tooltips enthalten Rangdefinition, eigene Bewertung, Empfehlung und die Zahl
belegter Rezeptreferenzen je Verwendungsart. Diese Zahlen enthalten Quellvarianten
und Upgrade-Stufen; sie sind keine Beschaffungs- oder Seltenheitswerte.

## Abdeckung

Es gibt drei Hauptkategorien: Waren (Items), Material (Components), Daten (Data).
Die bereits separat katalogisierten sechs Verbrauchsgüter bleiben unverändert
Consumables; sie werden nicht in eine der drei Hauptkategorien umklassifiziert.
Die Material-Untergruppen Chemicals/Circuits/Tech bleiben Untergruppen.

| Katalogbereich | Gesamt | A | B | C | D | ? |
|---|---:|---:|---:|---:|---:|---:|
| Waren | 61 | 5 | 5 | 1 | 34 | 16 |
| Material | 33 | 10 | 20 | 3 | 0 | 0 |
| Daten | 123 | 1 | 29 | 24 | 60 | 9 |
| Verbrauchsgüter (bestehender Zusatzbereich) | 6 | 0 | 0 | 0 | 0 | 6 |

Gesamt: **223 erfasst**, davon **192 mit A–D bewertet**, **31 offen**.
A=16, B=54, C=28, D=94, ?=31.

## Offene Bewertungen

- `amm_grenade_emp` — Shield Disruptor (Consumables)
- `amm_grenade_frag` — Frag Grenade (Consumables)
- `amm_grenade_shield` — Shield Projector (Consumables)
- `bypass` — E-Breach (Consumables)
- `energycell` — Energy Cell (Consumables)
- `healthpack` — Medkit (Consumables)
- `nm_seed` — Unica Seed (Items)
- `operationscounterattackdata` — Facilities Intelligence Report (Data)
- `operationsstrikedata` — Researcher Location Data (Data)
- `poweragriculture` — Agricultural Sample (Items)
- `powerclassifieddata` — Power Classified Data (Data)
- `powercomputer` — Computer Parts (Items)
- `powerelectronics` — Electronics Package (Items)
- `poweremployeedata` — Power Association Data (Data)
- `powerequipment` — Personal protective Equipment (Items)
- `powerexperiment` — Experiment Prototype (Items)
- `powerextraction` — Extraction Sample (Items)
- `powerfinancialrecords` — Power Industrial Data (Data)
- `powerindustrial` — Industrial Component (Items)
- `powerinventory` — Inventory Record (Items)
- `powermedical` — Medical Sample (Items)
- `powermisccomputer` — Data Storage Device (Items)
- `powermiscindust` — Industrial Machinery (Items)
- `powerplaymilitary` — Military Schematic (Items)
- `powerpower` — Energy Regulator (Items)
- `powerpreparationspyware` — Power Injection Malware (Data)
- `powerpropagandadata` — Power Political Data (Data)
- `powerresearch` — Research Notes (Items)
- `powerresearchdata` — Power Research Data (Data)
- `powersecurity` — Security Logs (Items)
- `powerspyware` — Power Tracker Malware (Data)

Diese 31 Einträge umfassen sechs Verbrauchsgüter, 22 Powerplay-Gegenstände,
zwei Operations-Daten und Unica Seed. Fehlende Daten sind kein Nachweis für Rang D.
Unbekannte künftige Kennungen und Kategorie-Konflikte erhalten ebenfalls „?“.

## Oberfläche und Persistenz

Die kompakte Rangspalte steht visuell unmittelbar vor dem Namen. Die bestehenden
logischen Mengen-/Carrier-Spalten bleiben stabil; alte gültige Spaltenlayouts werden
um die Rangspalte ergänzt. Beide Themes färben nur den Rangtext. Die unabhängige
Aufräum-Markierung bleibt auf der ganzen Zeile sichtbar. Auswahlkontrast hat Vorrang.

`materials/odyssey/sort` behält `cleanup` und `alphabetical`; neu sind `rank_asc` und
`rank_desc`. „?“ kommt immer zuletzt, danach sortiert QCollator in aktueller Sprache,
bei gleichen Namen die Elite-Kennung und anschließend die vorhandene Stack-Identität.
Filter, Commanderwechsel, Navigation und Neustart behalten den Sortiermodus.
Vorhandene Tabellen- und Summenzeilen werden weiterverwendet. Kein zusätzlicher
Controller-Aufruf, keine Journalverarbeitung, Inventarrekonstruktion oder Netzabfrage.
Alle neuen Oberflächentexte sind in den zwölf UI-Sprachen vorhanden. Die schon
bestehenden Lücken bei lokalisierten **Gegenstandsnamen** werden nicht verändert.
DB-Schema, Version, Inventar, Kapazitäten, Journal und Cache bleiben unverändert.

## Prüfung je Kennung

Englische und deutsche Namen stammen aus dem vorhandenen Katalog; weitere
Lokalisierungen bleiben über `localized_name` zugänglich. Die Verwendungsspalte
enthält die exakten Quell-Rezeptkennungen (keine neuen UI-Texte). „—“ bedeutet keine
Referenz in den geprüften Rezeptmaps, nicht automatisch allgemeine Nutzlosigkeit.
INARA-Used ist ausdrücklich keine Engineering-Rezeptzahl.

| Elite-Kennung | Englisch | Deutsch | Katalogkategorie | Rang | Quell-Rezepte | INARA-Used |
|---|---|---|---|---|---|---|
| `accidentlogs` | Accident Logs | Unfall-Logs | Data | D | — | [0](https://inara.cz/elite/componentitem/10297/) |
| `aerogel` | Aerogel | Aerogel | Components | A | ARTEMIS_SUIT_GRADE_1_2, ARTEMIS_SUIT_GRADE_2_3, ARTEMIS_SUIT_GRADE_3_4, ARTEMIS_SUIT_GRADE_4_5 | nicht zugeordnet |
| `agriculturalprocesssample` | Agricultural Process Sample | Agrikulturverfahren-Probe | Items | D | — | [0](https://inara.cz/elite/componentitem/10385/) |
| `airqualityreports` | Air Quality Reports | Berichte zur Luftqualität | Data | C | INCREASED_AIR_RESERVES | [3](https://inara.cz/elite/componentitem/10298/) |
| `amm_grenade_emp` | Shield Disruptor | Schildunterbrecher | Consumables | ? | — | nicht zugeordnet |
| `amm_grenade_frag` | Frag Grenade | Splittergranate | Consumables | ? | — | nicht zugeordnet |
| `amm_grenade_shield` | Shield Projector | Schildgenerator | Consumables | ? | — | nicht zugeordnet |
| `atmosphericdata` | Atmospheric Data | Atmosphärische Daten | Data | C | NOISE_SUPPRESSOR | [11](https://inara.cz/elite/componentitem/10372/) |
| `audiologs` | Audio Logs | Audio-Logs | Data | C | AUDIO_MASKING | [11](https://inara.cz/elite/componentitem/10304/) |
| `axcombatlogs` | AX Combat Logs | AX-Kampf-Logs | Data | D | — | [0](https://inara.cz/elite/componentitem/10398/) |
| `ballisticsdata` | Ballistics Data | Ballistische Daten | Data | B | DAMAGE_RESISTANCE, GREATER_RANGE_KINETIC | [7](https://inara.cz/elite/componentitem/10327/) |
| `biochemicalagent` | Biochemical Agent | Biochemischer Wirkstoff | Items | D | — | [0](https://inara.cz/elite/componentitem/10362/) |
| `biologicalweapondata` | Biological Weapon Data | Biowaffen-Daten | Data | D | — | [0](https://inara.cz/elite/componentitem/10399/) |
| `biomechanicalcomponent` | Spire Refinery Compound | Raffinerierter Spitzen-Verbund | Items | D | — | [0](https://inara.cz/elite/componentitem/10454/) |
| `biometricdata` | Biometric Data | Biometrische Daten | Data | B | HEADSHOT_DAMAGE_LASER, HIGHER_ACCURACY_KINETIC, SCOPE | [18](https://inara.cz/elite/componentitem/10400/) |
| `blacklistdata` | Blacklist Data | Daten der Schwarzen Liste | Data | D | — | [0](https://inara.cz/elite/componentitem/10366/) |
| `bloodtestresults` | Blood Test Results | Bluttest-Ergebnisse | Data | C | HEADSHOT_DAMAGE_PLASMA | [4](https://inara.cz/elite/componentitem/10299/) |
| `buildingschematic` | Building Schematic | Gebäudeplan | Items | D | — | [0](https://inara.cz/elite/componentitem/10334/) |
| `bypass` | E-Breach | E-Breach | Consumables | ? | — | nicht zugeordnet |
| `californium` | Californium | Kalifornium | Items | D | — | [0](https://inara.cz/elite/componentitem/10386/) |
| `campaignplans` | Campaign Plans | Kampagnenpläne | Data | D | — | [0](https://inara.cz/elite/componentitem/10317/) |
| `carbonfibreplating` | Carbon Fibre Plating | Carbonfaserplatten | Components | A | MAVERICK_SUIT_GRADE_1_2, MAVERICK_SUIT_GRADE_2_3, MAVERICK_SUIT_GRADE_3_4, MAVERICK_SUIT_GRADE_4_5, DAMAGE_RESISTANCE | nicht zugeordnet |
| `castfossil` | Cast Fossil | Fossilfund | Items | D | — | [0](https://inara.cz/elite/componentitem/10387/) |
| `catmedia` | Cat Media | Katzen-Medien | Data | B | ENGINEER_B3 | [1](https://inara.cz/elite/componentitem/10300/) |
| `censusdata` | Census Data | Zensusdaten | Data | D | — | [0](https://inara.cz/elite/componentitem/10357/) |
| `chemicalcatalyst` | Chemical Catalyst | Chemischer Katalysator | Components | B | INCREASED_SPRINT_DURATION, HEADSHOT_DAMAGE_KINETIC, HIGHER_ACCURACY_PLASMA | nicht zugeordnet |
| `chemicalexperimentdata` | Chemical Experiment Data | Chemieexperiment-Daten | Data | C | HEADSHOT_DAMAGE_PLASMA | [4](https://inara.cz/elite/componentitem/10340/) |
| `chemicalformulae` | Chemical Formulae | Chemische Formeln | Data | C | GREATER_RANGE_PLASMA | [4](https://inara.cz/elite/componentitem/10285/) |
| `chemicalinventory` | Chemical Inventory | Chemische Bestandsliste | Data | C | EXTRA_BACKPACK_CAPACITY | [3](https://inara.cz/elite/componentitem/10322/) |
| `chemicalpatents` | Chemical Patents | Chemische Patente | Data | C | HIGHER_ACCURACY_PLASMA | [4](https://inara.cz/elite/componentitem/10320/) |
| `chemicalprocesssample` | Chemical Process Sample | Chemieverfahren-Probe | Items | D | — | [0](https://inara.cz/elite/componentitem/10388/) |
| `chemicalsample` | Chemical Sample | Chemieprobe | Items | D | — | [0](https://inara.cz/elite/componentitem/10348/) |
| `chemicalsuperbase` | Chemical Superbase | Chemische Superbase | Components | A | MANTICORE_1_2, MANTICORE_2_3, MANTICORE_3_4, MANTICORE_4_5 | nicht zugeordnet |
| `chemicalweapondata` | Chemical Weapon Data | Chemiewaffen-Daten | Data | D | — | [0](https://inara.cz/elite/componentitem/10401/) |
| `circuitboard` | Circuit Board | Schaltplatte | Components | B | ENHANCED_TRACKING, AUDIO_MASKING, GREATER_RANGE_LASER, STOWED_RELOADING | nicht zugeordnet |
| `circuitswitch` | Circuit Switch | Elektroschalter | Components | C | NIGHT_VISION | nicht zugeordnet |
| `classicentertainment` | Classic Entertainment | Klassische Unterhaltung | Data | B | ENGINEER_B3 | [1](https://inara.cz/elite/componentitem/10290/) |
| `cocktailrecipes` | Cocktail Recipes | Cocktail-Rezepte | Data | B | ENGINEER_D1_2 | [1](https://inara.cz/elite/componentitem/10402/) |
| `combatantperformance` | Combatant Performance | Kampfleistung | Data | B | ADDED_MELEE_DAMAGE, FASTER_HANDLING, HIGHER_ACCURACY_KINETIC, HIGHER_ACCURACY_LASER, HIGHER_ACCURACY_PLASMA | [25](https://inara.cz/elite/componentitem/10380/) |
| `combattrainingmaterial` | Combat Training Material | Kampftraining-Materialien | Data | B | ADDED_MELEE_DAMAGE, FASTER_HANDLING, RELOAD_SPEED | [25](https://inara.cz/elite/componentitem/10274/) |
| `compactlibrary` | Compact Library | Kompakt-Bibliothek | Items | D | — | [0](https://inara.cz/elite/componentitem/10293/) |
| `compressionliquefiedgas` | Compression-Liquefied Gas | Komprimiertes Flüssiggas | Items | A | KARMA_1_2, KARMA_2_3, KARMA_3_4, KARMA_4_5 | [16](https://inara.cz/elite/componentitem/10308/) |
| `conflicthistory` | Conflict History | Konflikthistorie | Data | D | — | [0](https://inara.cz/elite/componentitem/10403/) |
| `criminalrecords` | Criminal Records | Strafakten | Data | D | — | [0](https://inara.cz/elite/componentitem/10404/) |
| `cropyieldanalysis` | Crop Yield Analysis | Ernteertrag-Analyse | Data | D | — | [0](https://inara.cz/elite/componentitem/10405/) |
| `culinaryrecipes` | Culinary Recipes | Kulinarische Rezepte | Data | B | ENGINEER_D1_2 | [1](https://inara.cz/elite/componentitem/10406/) |
| `deepmantlesample` | Deep Mantle Sample | Innerer-Mantel-Probe | Items | D | — | [0](https://inara.cz/elite/componentitem/10339/) |
| `degradedpowerregulator` | Degraded Power Regulator | Ausrangierter Energieregulator | Items | D | — | [0](https://inara.cz/elite/componentitem/10361/) |
| `digitaldesigns` | Digital Designs | Digitale Konzepte | Data | B | ENGINEER_D2, ENGINEER_D3, EXTRA_BACKPACK_CAPACITY, STOWED_RELOADING | [15](https://inara.cz/elite/componentitem/10407/) |
| `dutyrota` | Duty Rota | Dienstpläne | Data | D | — | [0](https://inara.cz/elite/componentitem/10328/) |
| `electricalfuse` | Electrical Fuse | Elektrosicherung | Components | B | REDUCED_TOOL_BATTERY_CONSUMPTION, GREATER_RANGE_PLASMA | nicht zugeordnet |
| `electricalwiring` | Electrical Wiring | Elektroverkabelung | Components | B | FASTER_SHIELD_REGEN, IMPROVED_BATTERY_CAPACITY, REDUCED_TOOL_BATTERY_CONSUMPTION, HIGHER_ACCURACY_LASER | nicht zugeordnet |
| `electromagnet` | Electromagnet | Elektromagnet | Components | B | GREATER_RANGE_PLASMA, HEADSHOT_DAMAGE_PLASMA, HIGHER_ACCURACY_PLASMA, RELOAD_SPEED | nicht zugeordnet |
| `employeedirectory` | Employee Directory | Mitarbeiterverzeichnis | Data | D | — | [0](https://inara.cz/elite/componentitem/10333/) |
| `employeeexpenses` | Employee Expenses | Aufwendungen für Mitarbeiter | Data | D | — | [0](https://inara.cz/elite/componentitem/10408/) |
| `employeegeneticdata` | Employee Genetic Data | Gen-Daten von Mitarbeitern | Data | B | ENGINEER_C5 | [1](https://inara.cz/elite/componentitem/10381/) |
| `employmenthistory` | Employment History | Beschäftigungshistorie | Data | D | — | [0](https://inara.cz/elite/componentitem/10384/) |
| `encryptedmemorychip` | Encrypted Memory Chip | Verschlüsselter Speicherchip | Components | C | STOWED_RELOADING | nicht zugeordnet |
| `energycell` | Energy Cell | Energiezelle | Consumables | ? | — | nicht zugeordnet |
| `enhancedinterrogationrecordings` | Enhanced Interrogation Recordings | Optimierte Vernehmungsaufzeichnungen | Data | D | — | [0](https://inara.cz/elite/componentitem/10409/) |
| `epinephrine` | Epinephrine | Epinephrin | Components | B | ADDED_MELEE_DAMAGE, COMBAT_MOVEMENT_SPEED | nicht zugeordnet |
| `epoxyadhesive` | Epoxy Adhesive | Epoxy-Klebstoff | Components | B | DAMAGE_RESISTANCE, EXTRA_BACKPACK_CAPACITY | nicht zugeordnet |
| `espionagematerial` | Espionage Material | Spionagematerial | Data | D | — | [0](https://inara.cz/elite/componentitem/10410/) |
| `evacuationprotocols` | Evacuation Protocols | Evakuierungsprotokolle | Data | C | COMBAT_MOVEMENT_SPEED | [3](https://inara.cz/elite/componentitem/10279/) |
| `explorationjournals` | Exploration Journals | Erkundungstagebücher | Data | D | — | [0](https://inara.cz/elite/componentitem/10318/) |
| `extractionyielddata` | Extraction Yield Data | Daten zur Förderungsausbeute | Data | C | HIGHER_ACCURACY_KINETIC | [4](https://inara.cz/elite/componentitem/10411/) |
| `factionassociates` | Faction Associates | Fraktionspartner | Data | B | ENGINEER_D2, ENGINEER_D3 | [1](https://inara.cz/elite/componentitem/10277/) |
| `factiondonatorlist` | Faction Donator List | Spenderliste einer Fraktion | Data | D | — | [0](https://inara.cz/elite/componentitem/10296/) |
| `factionnews` | Faction News | Fraktionsnachrichten | Data | D | — | [0](https://inara.cz/elite/componentitem/10289/) |
| `financialprojections` | Financial Projections | Finanzprognosen | Data | B | ENGINEER_C4 | [1](https://inara.cz/elite/componentitem/10329/) |
| `fleetregistry` | Fleet Registry | Flottenliste | Data | D | — | [0](https://inara.cz/elite/componentitem/10330/) |
| `genesequencingdata` | Gene Sequencing Data | Gen-Sequenzierungsdaten | Data | C | INCREASED_SPRINT_DURATION | [3](https://inara.cz/elite/componentitem/10356/) |
| `geneticrepairmeds` | Genetic Repair Meds | Gen-Reparatursets | Items | B | ENGINEER_C2 | [1](https://inara.cz/elite/componentitem/10349/) |
| `geneticresearch` | Genetic Research | Genforschung | Data | B | ENGINEER_C5, COMBAT_MOVEMENT_SPEED | [4](https://inara.cz/elite/componentitem/10286/) |
| `geneticsample` | Biological Sample | Biologische Probe | Items | B | ENGINEER_C5 | [1](https://inara.cz/elite/componentitem/10345/) |
| `geologicaldata` | Geological Data | Geologische Daten | Data | D | — | [0](https://inara.cz/elite/componentitem/10412/) |
| `gmeds` | G-Meds | G-Medizin | Items | C | IMPROVED_JUMP_ASSIST | [3](https://inara.cz/elite/componentitem/10280/) |
| `graphene` | Graphene | Graphen | Components | A | MAVERICK_SUIT_GRADE_1_2, MAVERICK_SUIT_GRADE_2_3, MAVERICK_SUIT_GRADE_3_4, MAVERICK_SUIT_GRADE_4_5, DOMINATOR_SUIT_GRADE_1_2, DOMINATOR_SUIT_GRADE_2_3, DOMINATOR_SUIT_GRADE_3_4, DOMINATOR_SUIT_GRADE_4_5, ARTEMIS_SUIT_GRADE_1_2, ARTEMIS_SUIT_GRADE_2_3, ARTEMIS_SUIT_GRADE_3_4, ARTEMIS_SUIT_GRADE_4_5 | nicht zugeordnet |
| `healthmonitor` | Health Monitor | Gesundheitsmonitor | Items | A | MAVERICK_SUIT_GRADE_1_2, MAVERICK_SUIT_GRADE_2_3, MAVERICK_SUIT_GRADE_3_4, MAVERICK_SUIT_GRADE_4_5, DOMINATOR_SUIT_GRADE_1_2, DOMINATOR_SUIT_GRADE_2_3, DOMINATOR_SUIT_GRADE_3_4, DOMINATOR_SUIT_GRADE_4_5, ARTEMIS_SUIT_GRADE_1_2, ARTEMIS_SUIT_GRADE_2_3, ARTEMIS_SUIT_GRADE_3_4, ARTEMIS_SUIT_GRADE_4_5 | [12](https://inara.cz/elite/componentitem/10292/) |
| `healthpack` | Medkit | Medikit | Consumables | ? | — | nicht zugeordnet |
| `hush` | Hush | Schnurr | Items | D | — | [0](https://inara.cz/elite/componentitem/10389/) |
| `hydroponicdata` | Hydroponic Data | Hydrokultur-Daten | Data | D | — | [0](https://inara.cz/elite/componentitem/10332/) |
| `incidentlogs` | Incident Logs | Zwischenfall-Logs | Data | D | — | [0](https://inara.cz/elite/componentitem/10413/) |
| `inertiacanister` | Inertia Canister | Trägheits-Container | Items | D | — | [0](https://inara.cz/elite/componentitem/10310/) |
| `infinity` | Infinity | Unendlichkeit | Items | D | — | [0](https://inara.cz/elite/componentitem/10390/) |
| `influenceprojections` | Influence Projections | Einfluss-Projektionen | Data | D | — | [0](https://inara.cz/elite/componentitem/10414/) |
| `inorganiccontaminant` | Inorganic Contaminant | Anorganischer Schadstoff | Items | D | — | [0](https://inara.cz/elite/componentitem/10391/) |
| `insight` | Insight | Insight | Items | D | — | [0](https://inara.cz/elite/componentitem/10392/) |
| `insightdatabank` | Insight Data Bank | Insight-Datenbank | Items | D | — | [0](https://inara.cz/elite/componentitem/10282/) |
| `insightentertainmentsuite` | Insight Entertainment Suite | Insight-Entertainment-Bibliothek | Items | B | ENGINEER_B4 | [1](https://inara.cz/elite/componentitem/10294/) |
| `internalcorrespondence` | Internal Correspondence | Interne Korrespondenz | Data | D | — | [0](https://inara.cz/elite/componentitem/10369/) |
| `interrogationrecordings` | Interrogation Recordings | Vernehmungsaufzeichnungen | Data | D | — | [0](https://inara.cz/elite/componentitem/10344/) |
| `interviewrecordings` | Interview Recordings | Aufzeichnungen von Vorstellungsgesprächen | Data | D | — | [0](https://inara.cz/elite/componentitem/10323/) |
| `ionbattery` | Ion Battery | Ionen-Batterie | Components | B | FASTER_SHIELD_REGEN, IMPROVED_BATTERY_CAPACITY, HEADSHOT_DAMAGE_LASER, HEADSHOT_DAMAGE_PLASMA | nicht zugeordnet |
| `ionisedgas` | Ionised Gas | Ionisiertes Gas | Items | A | TK_1_2, TK_2_3, TK_3_4, TK_4_5, MANTICORE_1_2, MANTICORE_2_3, MANTICORE_3_4, MANTICORE_4_5 | [28](https://inara.cz/elite/componentitem/10291/) |
| `jobapplications` | Job Applications | Bewerbungen | Data | D | — | [0](https://inara.cz/elite/componentitem/10415/) |
| `kompromat` | Kompromat | Kompromittierendes Material | Data | D | — | [0](https://inara.cz/elite/componentitem/10416/) |
| `largecapacitypowerregulator` | Power Regulator | Energieregulator | Items | D | — | [1](https://inara.cz/elite/componentitem/10271/) |
| `lazarus` | Lazarus | Lazarus | Items | D | — | [0](https://inara.cz/elite/componentitem/10393/) |
| `literaryfiction` | Literary Fiction | Belletristik | Data | D | — | [0](https://inara.cz/elite/componentitem/10374/) |
| `maintenancelogs` | Maintenance Logs | Wartungs-Logs | Data | C | IMPROVED_BATTERY_CAPACITY | [3](https://inara.cz/elite/componentitem/10314/) |
| `manufacturinginstructions` | Manufacturing Instructions | Herstellungsanweisungen | Data | A | ENGINEER_D2, ENGINEER_D3, MAVERICK_SUIT_GRADE_1_2, MAVERICK_SUIT_GRADE_2_3, MAVERICK_SUIT_GRADE_3_4, MAVERICK_SUIT_GRADE_4_5, DOMINATOR_SUIT_GRADE_1_2, DOMINATOR_SUIT_GRADE_2_3, DOMINATOR_SUIT_GRADE_3_4, DOMINATOR_SUIT_GRADE_4_5, ARTEMIS_SUIT_GRADE_1_2, ARTEMIS_SUIT_GRADE_2_3, ARTEMIS_SUIT_GRADE_3_4, ARTEMIS_SUIT_GRADE_4_5, KARMA_1_2, KARMA_2_3, KARMA_3_4, KARMA_4_5, TK_1_2, TK_2_3, TK_3_4, TK_4_5, MANTICORE_1_2, MANTICORE_2_3, MANTICORE_3_4, MANTICORE_4_5 | [57](https://inara.cz/elite/componentitem/10337/) |
| `medicalrecords` | Medical Records | Medizinische Daten | Data | C | HEADSHOT_DAMAGE_KINETIC | [4](https://inara.cz/elite/componentitem/10351/) |
| `medicaltrialrecords` | Clinical Trial Records | Klinische Prüfberichte | Data | C | INCREASED_SPRINT_DURATION | [3](https://inara.cz/elite/componentitem/10417/) |
| `meetingminutes` | Meeting Minutes | Besprechungsprotokolle | Data | D | — | [0](https://inara.cz/elite/componentitem/10325/) |
| `memorychip` | Memory Chip | Speicherchip | Components | C | EXTRA_BACKPACK_CAPACITY | nicht zugeordnet |
| `metalcoil` | Metal Coil | Metallspule | Components | B | GREATER_RANGE_KINETIC, HIGHER_ACCURACY_LASER, HIGHER_ACCURACY_PLASMA, MAGAZINE_SIZE | nicht zugeordnet |
| `microbialinhibitor` | Microbial Inhibitor | Mikrobieller Hemmstoff | Items | D | — | [0](https://inara.cz/elite/componentitem/10307/) |
| `microelectrode` | Microelectrode | Mikroelektrode | Components | A | TK_1_2, TK_2_3, TK_3_4, TK_4_5, MANTICORE_1_2, MANTICORE_2_3, MANTICORE_3_4, MANTICORE_4_5 | nicht zugeordnet |
| `microhydraulics` | Micro Hydraulics | Mikrohydraulikgeräte | Components | B | QUIETER_FOOTSTEPS, RELOAD_SPEED, STABILITY | nicht zugeordnet |
| `microsupercapacitor` | Micro Supercapacitor | Mikro-Superkondensatoren | Components | B | IMPROVED_BATTERY_CAPACITY, HEADSHOT_DAMAGE_PLASMA | nicht zugeordnet |
| `microthrusters` | Micro Thrusters | Mikro-Schubdüsen | Components | B | ADDED_MELEE_DAMAGE, IMPROVED_JUMP_ASSIST | nicht zugeordnet |
| `microtransformer` | Micro Transformer | Mikro-Transformator | Components | B | FASTER_SHIELD_REGEN, REDUCED_TOOL_BATTERY_CONSUMPTION, GREATER_RANGE_LASER | nicht zugeordnet |
| `mineralsurvey` | Mineral Survey | Mineralienübersicht | Data | C | GREATER_RANGE_PLASMA | [4](https://inara.cz/elite/componentitem/10379/) |
| `mininganalytics` | Mining Analytics | Abbau-Analytik | Data | B | NOISE_SUPPRESSOR, STABILITY | [22](https://inara.cz/elite/componentitem/10418/) |
| `motor` | Motor | Motor | Components | B | IMPROVED_JUMP_ASSIST, GREATER_RANGE_PLASMA | nicht zugeordnet |
| `multimediaentertainment` | Multimedia Entertainment | Multimedia-Unterhaltung | Data | B | ENGINEER_B3 | [1](https://inara.cz/elite/componentitem/10368/) |
| `mutageniccatalyst` | Mutagenic Catalyst | Mutagen-Katalysator | Items | D | — | [0](https://inara.cz/elite/componentitem/10394/) |
| `networkaccesshistory` | Network Access History | Netzwerkzugriffshistorie | Data | D | — | [0](https://inara.cz/elite/componentitem/10354/) |
| `networksecurityprotocols` | Network Security Protocols | Netzwerksicherheitsprotokolle | Data | D | — | [0](https://inara.cz/elite/componentitem/10419/) |
| `nextofkinrecords` | Next of Kin Records | Angehörigen-Aufzeichnungen | Data | D | — | [0](https://inara.cz/elite/componentitem/10287/) |
| `nm_seed` | Unica Seed | Unica-Samen | Items | ? | — | nicht zugeordnet |
| `nocdata` | NOC Data | Geheimoperation-Daten | Data | C | NIGHT_VISION | [3](https://inara.cz/elite/componentitem/10382/) |
| `nutritionalconcentrate` | Nutritional Concentrate | Nahrungskonzentrat | Items | D | — | [0](https://inara.cz/elite/componentitem/10347/) |
| `operationalmanual` | Operational Manual | Bedienungsanleitung | Data | B | FASTER_HANDLING, RELOAD_SPEED, STOWED_RELOADING | [33](https://inara.cz/elite/componentitem/10288/) |
| `operationscounterattackdata` | Facilities Intelligence Report | Facilities Intelligence Report | Data | ? | — | nicht zugeordnet |
| `operationsstrikedata` | Researcher Location Data | Researcher Location Data | Data | ? | — | nicht zugeordnet |
| `opinionpolls` | Opinion Polls | Umfrageergebnisse | Data | B | ENGINEER_A3 | [1](https://inara.cz/elite/componentitem/10420/) |
| `opticalfibre` | Optical Fibre | Glasfaser | Components | A | TK_1_2, TK_2_3, TK_3_4, TK_4_5, SCOPE | nicht zugeordnet |
| `opticallens` | Optical Lens | Optische Linse | Components | B | GREATER_RANGE_LASER, HEADSHOT_DAMAGE_LASER, HIGHER_ACCURACY_LASER, SCOPE | nicht zugeordnet |
| `oxygenicbacteria` | Oxygenic Bacteria | Sauerstoffbakterien | Components | B | INCREASED_AIR_RESERVES, INCREASED_SPRINT_DURATION | nicht zugeordnet |
| `patienthistory` | Patient History | Patientenhistorie | Data | D | — | [0](https://inara.cz/elite/componentitem/10421/) |
| `patrolroutes` | Patrol Routes | Patrouillenrouten | Data | B | QUIETER_FOOTSTEPS, AUDIO_MASKING | [14](https://inara.cz/elite/componentitem/10364/) |
| `payrollinformation` | Payroll Information | Gehaltsinformationen | Data | D | — | [0](https://inara.cz/elite/componentitem/10371/) |
| `personalcomputer` | Personal Computer | Personal Computer | Items | D | — | [0](https://inara.cz/elite/componentitem/10284/) |
| `personaldocuments` | Personal Documents | Persönliche Dokumente | Items | D | — | [0](https://inara.cz/elite/componentitem/10283/) |
| `personallogs` | Personal Logs | Persönliche Logs | Data | D | — | [0](https://inara.cz/elite/componentitem/10370/) |
| `petrifiedfossil` | Petrified Fossil | Versteinertes Fossil | Items | D | — | [0](https://inara.cz/elite/componentitem/10395/) |
| `pharmaceuticalpatents` | Pharmaceutical Patents | Pharmazeutische Patente | Data | C | INCREASED_AIR_RESERVES | [3](https://inara.cz/elite/componentitem/10376/) |
| `phneutraliser` | pH Neutraliser | pH-Neutralisator | Components | B | COMBAT_MOVEMENT_SPEED, INCREASED_AIR_RESERVES | nicht zugeordnet |
| `photoalbums` | Photo Albums | Fotoalben | Data | D | — | [0](https://inara.cz/elite/componentitem/10422/) |
| `plantgrowthcharts` | Plant Growth Charts | Diagramme zum Pflanzenwachstum | Data | D | — | [0](https://inara.cz/elite/componentitem/10423/) |
| `politicalaffiliations` | Political Affiliations | Politische Beziehungen | Data | D | — | [0](https://inara.cz/elite/componentitem/10424/) |
| `poweragriculture` | Agricultural Sample | Agrikulturverfahren-Probe | Items | ? | — | [1](https://inara.cz/elite/componentitem/10467/) |
| `powerclassifieddata` | Power Classified Data | Klassen-Daten der Macht | Data | ? | — | [1](https://inara.cz/elite/componentitem/10476/) |
| `powercomputer` | Computer Parts | Computerbauteile | Items | ? | — | [1](https://inara.cz/elite/componentitem/10465/) |
| `powerelectronics` | Electronics Package | Elektronikpaket | Items | ? | — | [1](https://inara.cz/elite/componentitem/10471/) |
| `poweremployeedata` | Power Association Data | Zugehörigkeitsdaten der Macht | Data | ? | — | [1](https://inara.cz/elite/componentitem/10477/) |
| `powerequipment` | Personal protective Equipment | Persönliche Schutzausrüstung | Items | ? | — | nicht zugeordnet |
| `powerexperiment` | Experiment Prototype | Experimenteller Prototyp | Items | ? | — | [1](https://inara.cz/elite/componentitem/10462/) |
| `powerextraction` | Extraction Sample | Abbauprobe | Items | ? | — | [1](https://inara.cz/elite/componentitem/10469/) |
| `powerfinancialrecords` | Power Industrial Data | Industriedaten der Macht | Data | ? | — | [1](https://inara.cz/elite/componentitem/10480/) |
| `powerindustrial` | Industrial Component | Industrielle Komponente | Items | ? | — | [1](https://inara.cz/elite/componentitem/10468/) |
| `powerinventory` | Inventory Record | Inventaraufzeichnung | Items | ? | — | [1](https://inara.cz/elite/componentitem/10463/) |
| `powermedical` | Medical Sample | Medizinische Probe | Items | ? | — | [1](https://inara.cz/elite/componentitem/10466/) |
| `powermisccomputer` | Data Storage Device | Datenspeichergerät | Items | ? | — | [1](https://inara.cz/elite/componentitem/10472/) |
| `powermiscindust` | Industrial Machinery | Industrielle Maschinen | Items | ? | — | [1](https://inara.cz/elite/componentitem/10464/) |
| `powerplaymilitary` | Military Schematic | Militärbauplan | Items | ? | — | [1](https://inara.cz/elite/componentitem/10461/) |
| `powerpower` | Energy Regulator | Energieregulator | Items | ? | — | [1](https://inara.cz/elite/componentitem/10473/) |
| `powerpreparationspyware` | Power Injection Malware | Macht-Einspeisungs-Malware | Data | ? | — | [1](https://inara.cz/elite/componentitem/10482/) |
| `powerpropagandadata` | Power Political Data | Politische Daten der Macht | Data | ? | — | [1](https://inara.cz/elite/componentitem/10478/) |
| `powerresearch` | Research Notes | Forschungsnotizen | Items | ? | — | [1](https://inara.cz/elite/componentitem/10474/) |
| `powerresearchdata` | Power Research Data | Forschungsdaten der Macht | Data | ? | — | [1](https://inara.cz/elite/componentitem/10479/) |
| `powersecurity` | Security Logs | Sicherheitsprotokolle | Items | ? | — | [1](https://inara.cz/elite/componentitem/10475/) |
| `powerspyware` | Power Tracker Malware | Macht-Tracker-Malware | Data | ? | — | [1](https://inara.cz/elite/componentitem/10481/) |
| `prisonerlogs` | Prisoner Logs | Gefangenen-Logs | Data | D | — | [0](https://inara.cz/elite/componentitem/10425/) |
| `productionreports` | Production Reports | Produktionsberichte | Data | B | EXTRA_AMMO_CAPACITY, RELOAD_SPEED | [14](https://inara.cz/elite/componentitem/10312/) |
| `productionschedule` | Production Schedule | Produktionszeitplan | Data | C | STOWED_RELOADING | [11](https://inara.cz/elite/componentitem/10316/) |
| `propaganda` | Propaganda | Propaganda | Data | D | — | [0](https://inara.cz/elite/componentitem/10426/) |
| `purchaserecords` | Purchase Records | Kaufaufzeichnungen | Data | D | — | [0](https://inara.cz/elite/componentitem/10324/) |
| `purchaserequests` | Purchase Requests | Kaufanfragen | Data | D | — | [0](https://inara.cz/elite/componentitem/10342/) |
| `push` | Push | Schub | Items | B | ENGINEER_A2 | [1](https://inara.cz/elite/componentitem/10396/) |
| `pyrolyticcatalyst` | Pyrolytic Catalyst | Pyrolytischer Katalysator | Items | D | — | [0](https://inara.cz/elite/componentitem/10295/) |
| `radioactivitydata` | Radioactivity Data | Daten zur Radioaktivität | Data | B | NIGHT_VISION, HIGHER_ACCURACY_LASER | [6](https://inara.cz/elite/componentitem/10341/) |
| `rdx` | RDX | Hexogen | Components | B | GREATER_RANGE_KINETIC, HEADSHOT_DAMAGE_KINETIC, HIGHER_ACCURACY_KINETIC | nicht zugeordnet |
| `reactoroutputreview` | Reactor Output Review | Evaluierung der Reaktorleistung | Data | B | FASTER_SHIELD_REGEN, IMPROVED_BATTERY_CAPACITY, REDUCED_TOOL_BATTERY_CONSUMPTION | [9](https://inara.cz/elite/componentitem/10313/) |
| `recyclinglogs` | Recycling Logs | Recycling-Logs | Data | C | EXTRA_AMMO_CAPACITY | [3](https://inara.cz/elite/componentitem/10301/) |
| `refinementprocesssample` | Refinement Process Sample | Raffinerieverfahren-Probe | Items | D | — | [0](https://inara.cz/elite/componentitem/10397/) |
| `residentialdirectory` | Residential Directory | Einwohnerverzeichnis | Data | D | — | [0](https://inara.cz/elite/componentitem/10311/) |
| `riskassessments` | Risk Assessments | Gefährdungsbeurteilungen | Data | B | GREATER_RANGE_LASER, STABILITY | [14](https://inara.cz/elite/componentitem/10427/) |
| `sabotagedcomponent` | Contaminated Spire Refinery Compound | Kontaminierte Verbindung eines Tharg Spire-Standorts | Items | D | — | [0](https://inara.cz/elite/componentitem/10455/) |
| `salesrecords` | Sales Records | Verkaufszahlen | Data | D | — | [0](https://inara.cz/elite/componentitem/10326/) |
| `scrambler` | Scrambler | Störsender | Components | B | AUDIO_MASKING, HEADSHOT_DAMAGE_LASER | nicht zugeordnet |
| `securityexpenses` | Security Expenses | Aufwendungen für Sicherheit | Data | C | MAGAZINE_SIZE | [11](https://inara.cz/elite/componentitem/10305/) |
| `seedgeneaology` | Seed Geneaology | Saatgut-Geneaologie | Data | D | — | [0](https://inara.cz/elite/componentitem/10355/) |
| `settlementassaultplans` | Settlement Assault Plans | Siedlungsangriffspläne | Data | C | QUIETER_FOOTSTEPS | [3](https://inara.cz/elite/componentitem/10428/) |
| `settlementdefenceplans` | Settlement Defence Plans | Siedlungsverteidigungspläne | Data | B | ENGINEER_B2 | [1](https://inara.cz/elite/componentitem/10365/) |
| `shareholderinformation` | Shareholder Information | Aktionärsinformationen | Data | D | — | [0](https://inara.cz/elite/componentitem/10367/) |
| `shipschematic` | Ship Schematic | Schiffsplan | Items | D | — | [0](https://inara.cz/elite/componentitem/10336/) |
| `slushfundlogs` | Slush Fund Logs | Schmiergeld-Logs | Data | D | — | [0](https://inara.cz/elite/componentitem/10429/) |
| `smearcampaignplans` | Smear Campaign Plans | Pläne für Verleumdungskampagne | Data | B | ENGINEER_A5 | [1](https://inara.cz/elite/componentitem/10430/) |
| `spectralanalysisdata` | Spectral Analysis Data | Spektralanalyse-Daten | Data | B | ENHANCED_TRACKING, HEADSHOT_DAMAGE_LASER, SCOPE | [17](https://inara.cz/elite/componentitem/10431/) |
| `spyware` | Spyware | Spyware | Data | D | — | [0](https://inara.cz/elite/componentitem/10432/) |
| `stellaractivitylogs` | Stellar Activity Logs | Sternenaktivitäts-Logs | Data | B | ENHANCED_TRACKING, GREATER_RANGE_LASER | [6](https://inara.cz/elite/componentitem/10358/) |
| `suitschematic` | Suit Schematic | Anzugplan | Items | A | MAVERICK_SUIT_GRADE_1_2, MAVERICK_SUIT_GRADE_2_3, MAVERICK_SUIT_GRADE_3_4, MAVERICK_SUIT_GRADE_4_5, DOMINATOR_SUIT_GRADE_1_2, DOMINATOR_SUIT_GRADE_2_3, DOMINATOR_SUIT_GRADE_3_4, DOMINATOR_SUIT_GRADE_4_5, ARTEMIS_SUIT_GRADE_1_2, ARTEMIS_SUIT_GRADE_2_3, ARTEMIS_SUIT_GRADE_3_4, ARTEMIS_SUIT_GRADE_4_5 | [12](https://inara.cz/elite/componentitem/10306/) |
| `surveillanceequipment` | Surveillance Equipment | Überwachungsausrüstung | Items | B | ENGINEER_A4, NIGHT_VISION | [4](https://inara.cz/elite/componentitem/10335/) |
| `surveilleancelogs` | Surveillance Logs | Überwachungs-Logs | Data | C | NIGHT_VISION | [3](https://inara.cz/elite/componentitem/10321/) |
| `syntheticgenome` | Synthetic Genome | Synthetisches Genom | Items | D | — | [0](https://inara.cz/elite/componentitem/10346/) |
| `syntheticpathogen` | Synthetic Pathogen | Synthetischer Erreger | Items | D | — | [0](https://inara.cz/elite/componentitem/10363/) |
| `tacticalplans` | Tactical Plans | Taktikpläne | Data | C | QUIETER_FOOTSTEPS | [3](https://inara.cz/elite/componentitem/10350/) |
| `taxrecords` | Tax Records | Steuerunterlagen | Data | D | — | [0](https://inara.cz/elite/componentitem/10315/) |
| `titaniumplating` | Titanium Plating | Titanplatten | Components | A | DOMINATOR_SUIT_GRADE_1_2, DOMINATOR_SUIT_GRADE_2_3, DOMINATOR_SUIT_GRADE_3_4, DOMINATOR_SUIT_GRADE_4_5, DAMAGE_RESISTANCE | nicht zugeordnet |
| `topographicalsurveys` | Topographical Surveys | Topographische Erhebung | Data | B | ENHANCED_TRACKING, IMPROVED_JUMP_ASSIST, GREATER_RANGE_KINETIC | [10](https://inara.cz/elite/componentitem/10373/) |
| `transmitter` | Transmitter | Sender | Components | B | ENHANCED_TRACKING, AUDIO_MASKING | nicht zugeordnet |
| `travelpermits` | Travel Permits | Reiseerlaubnisse | Data | D | — | [0](https://inara.cz/elite/componentitem/10319/) |
| `troopdeploymentrecords` | Troop Deployment Records | Truppeneinsatzprotokolle | Data | C | INCREASED_SPRINT_DURATION | [3](https://inara.cz/elite/componentitem/10343/) |
| `trueformfossil` | True Form Fossil | Makelloses Fossil | Items | D | — | [0](https://inara.cz/elite/componentitem/10383/) |
| `tungstencarbide` | Tungsten Carbide | Wolframcarbid | Components | A | KARMA_1_2, KARMA_2_3, KARMA_3_4, KARMA_4_5, MAGAZINE_SIZE | nicht zugeordnet |
| `unionmembership` | Union Membership | Gewerkschaftsmitgliedschaft | Data | D | — | [0](https://inara.cz/elite/componentitem/10352/) |
| `universaltranslator` | Universal Translator | Universal-Übersetzer | Items | D | — | [0](https://inara.cz/elite/componentitem/10302/) |
| `vaccinationrecords` | Vaccination Records | Aufzeichnungen zu Impfungen | Data | D | — | [0](https://inara.cz/elite/componentitem/10377/) |
| `vaccineresearch` | Vaccine Research | Impfstoffforschung | Data | D | — | [0](https://inara.cz/elite/componentitem/10281/) |
| `vehicleschematic` | Vehicle Schematic | Fahrzeugplan | Items | D | — | [0](https://inara.cz/elite/componentitem/10360/) |
| `vipsecuritydetail` | VIP Security Detail | VIP-Sicherheitsdienst | Data | D | — | [0](https://inara.cz/elite/componentitem/10433/) |
| `virologydata` | Virology Data | Virologische Daten | Data | D | — | [0](https://inara.cz/elite/componentitem/10331/) |
| `virus` | Virus | Virus | Data | D | — | [0](https://inara.cz/elite/componentitem/10434/) |
| `viscoelasticpolymer` | Viscoelastic Polymer | Viskoelastisches Polymer | Components | A | QUIETER_FOOTSTEPS, FASTER_HANDLING, HIGHER_ACCURACY_KINETIC, NOISE_SUPPRESSOR, STABILITY | nicht zugeordnet |
| `visitorregister` | Visitor Register | Besucherliste | Data | D | — | [0](https://inara.cz/elite/componentitem/10375/) |
| `weaponcomponent` | Weapon Component | Waffenkomponente | Components | A | EXTRA_AMMO_CAPACITY, KARMA_1_2, KARMA_2_3, KARMA_3_4, KARMA_4_5, GREATER_RANGE_KINETIC, HEADSHOT_DAMAGE_KINETIC, MAGAZINE_SIZE, NOISE_SUPPRESSOR | nicht zugeordnet |
| `weaponinventory` | Weapon Inventory | Waffeninventarliste | Data | B | DAMAGE_RESISTANCE, EXTRA_BACKPACK_CAPACITY | [6](https://inara.cz/elite/componentitem/10338/) |
| `weaponschematic` | Weapon Schematic | Waffenplan | Items | A | KARMA_1_2, KARMA_2_3, KARMA_3_4, KARMA_4_5, TK_1_2, TK_2_3, TK_3_4, TK_4_5, MANTICORE_1_2, MANTICORE_2_3, MANTICORE_3_4, MANTICORE_4_5 | [44](https://inara.cz/elite/componentitem/10309/) |
| `weapontestdata` | Weapon Test Data | Waffentestdaten | Data | B | EXTRA_AMMO_CAPACITY, HEADSHOT_DAMAGE_KINETIC, MAGAZINE_SIZE | [18](https://inara.cz/elite/componentitem/10353/) |
| `xenodefenceprotocols` | Xeno-Defence Protocols | Xeno-Abwehr-Protokolle | Data | D | — | [0](https://inara.cz/elite/componentitem/10303/) |

## Validierung der Umsetzung

Gezielte Prüfung (Qt offscreen):

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=tests:. venv/bin/python -m unittest test_odyssey_ranks test_odyssey_view test_odyssey_cleanup test_odyssey_carrier test_odyssey_catalog test_odyssey_sort
venv/bin/python tools/check_i18n.py
git diff --check
```

102 Tests erfolgreich. Abgedeckt sind Katalog/Quellreferenzen, alle Rangwerte,
alle Katalogbereiche, beide Themes und Tooltips, beide Rangsortierungen sowie
bestehende Sortierungen, Namensgleichheit, QSettings/Prozessneustart,
Commander-/Menüwechsel, persönliche Auswahl und Standardwiederherstellung,
Zeilen-/Summenzeilenwiederverwendung, Mengen, Filter und LoadingScanner.
Der i18n-Check prüfte 2058 Referenzschlüssel in zwölf Sprachen erfolgreich;
keine doppelten Schlüssel oder abweichenden Platzhalter. Dark-/Light-Darstellung
zusätzlich anhand gerenderter Testansichten visuell geprüft. `git diff --check`
ohne Beanstandung. Keine vollständige Testsuite und kein produktiver Datenbestand
verwendet; keine Aussage über einen interaktiven Test mit einem laufenden Spiel.
