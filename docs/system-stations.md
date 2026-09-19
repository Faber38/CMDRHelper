# Bekannte Einrichtungen in der Systemkarte (v3.5)

Referenzsystem der Offline-Tests: **Plio Aihm UC-V d2-159**, SystemAddress **5474145570075**.

## 1–3. Vorhandene Daten und Quellen

Ausgangsschema **19**: Kein Stationsverzeichnis: `commander_locations` speichert nur den letzten System-/Stations-/Körpernamen, SystemAddress, Event und Zeitpunkt; `commander_carriers` speichert numerische CarrierID, Rufzeichen, Name, SystemAddress/-name und Zeitpunkt. Die Körper stehen fachlich getrennt in `bodies`. Im Standortdatensatz fehlen MarketID, StationType, BodyID und Koordinaten. Die über `journal_sessions` referenzierten Journaldateien waren für die lesende Prüfung verfügbar.

| Event | Verwendbare Information / Grenze |
| --- | --- |
| Docked | MarketID, StationName, StationType, SystemAddress, Zeitpunkt; normalerweise kein Parent |
| Location (Docked) | Zusätzlich Body/BodyID/BodyType; **BodyType Station bezeichnet die Station selbst**, keinen Parent |
| ApproachSettlement | Name, MarketID soweit geliefert, SystemAddress, BodyID/BodyName, Latitude/Longitude; sicherer Oberflächenbezug, aber nicht automatisch Odyssey-Siedlung |
| CarrierLocation | Numerische CarrierID, SystemAddress, BodyID und Zeitpunkt; explizite Carrierposition |
| CarrierJump | Tatsächliche Ankunft; MarketID/StationName und BodyID/BodyType soweit vorhanden |
| FSDJump | Systemkontext; keine Station und kein Stationsparent |
| FSSSignalDiscovered | SignalName, SignalType, teilweise IsStation; keine stabile MarketID und kein sicherer Parent: zunächst keine Kartenentität |
| SupercruiseExit | BodyID bei BodyType Station ist die Stations-ID; kein orbitaler Parent |
| CarrierStats | Identität/Eigentum/Name; vorhandenes Eigentumsmodell wird nur gelesen |
| CarrierJumpRequest | Geplantes Ziel, **keine** bestätigte Position; nicht verwendet |
| Market / Shipyard / Outfitting / Docking-Events | Keine zusätzliche eindeutige Parent-Zuordnung; keine Ableitung aus zeitlicher Nähe |

Die bestehende EDSM-Integration in `online_services.py` nutzt `/api-v1/system` und `/api-system-v1/bodies` sowie deren Cache. Sie liefert im verwendeten Pfad keine Stationsliste. Der Bodies-Adapter verarbeitet Himmelskörper (`bodyId`, Name, Typ, Elternpfad und Körperattribute), keine MarketID/Stationsentitäten. EDSM beschreibt Stationsinformationen an einem **separaten**, bislang ungenutzten Endpunkt: [EDSM API System V1](https://www.edsm.net/en/api-system-v1). Dieser wurde nicht hinzugefügt und nicht abgefragt. Es gibt daher keinen neuen EDSM-/Journal-Merge; die Stationsquelle bleibt ausdrücklich `Journal`.

## 4. Anonymisierte Referenzfixture

`tests/fixtures/system_stations_plio.json` enthält sieben Einrichtungen mit
MarketID, davon zwei mit sicherem Parent und fünf ohne Parent. Der Carrier hat
eine fiktive Kennung und ID; die Zeiten wurden einheitlich verschoben.
SystemAddress, Stations- und BodyIDs bleiben für die Zuordnungsregression erhalten.

Eine Orbitalstation mit `BodyType=Station` und eigener BodyID erhält dadurch
keinen Planetenparent. `ApproachSettlement` kann dagegen Parent und Koordinaten
belegen; `CarrierLocation` ordnet den Test-Carrier ausdrücklich einem Körper zu.

Ein alter `SurfaceStation`-Beleg und ein späteres gleichnamiges FSS-Coriolis-Signal
werden ohne gemeinsame stabile Identität nicht zusammengeführt. Signalnamen allein
beweisen weder aktuelle Anwesenheit noch eindeutige Entitätsanzahlen. Das gilt auch
für umbenannte Carrier. Unbelegte Siedlungs-/Megashiptypen werden nicht geraten.

## 5–6. Zuordnung, Identität und Persistenz

`station_observations` ist eine eigene additive Tabelle, keine Erweiterung der Körper um Stationen. Felder: identity, event_type, system_address, station_name, station_type, market_id, body_id, body_name, parent_body_id, is_planetary, latitude, longitude, last_seen, source. Unbekannte Werte bleiben NULL bzw. fehlen im projizierten Modell.

Je Identität und Eventtyp bleibt der neueste explizite Beleg erhalten. Unterschiedliche Eventtypen bewahren z.B. ApproachSettlement-Koordinaten neben einem späteren Docked. Die Projektion verarbeitet diese Belege chronologisch. Numerische MarketID/CarrierID hat Vorrang. Ohne MarketID wird nur eine ausdrücklich beobachtete Oberfläche mit SystemAddress, BodyID, exakten Koordinaten und Name identifiziert; sonst wird auf eine Entität verzichtet. Keine unscharfe oder reine Namenszusammenführung. Koordinatenidentitäten werden nicht spekulativ mit späteren MarketIDs verschmolzen.

Ein Parent wird ausschließlich aus ApproachSettlement, CarrierLocation oder einem Stationsereignis mit BodyType Planet/Star übernommen. Er muss im geladenen Systemmodell existieren; widersprüchlicher vollständiger BodyName oder Gürtel verhindern die Zuordnung. BodyType Station, FSS-Namen, vorheriger Aufenthaltskörper und Anflugnähe begründen **keinen** Parent.

Neue Belege werden im vorhandenen Live-Delta und im gesammelten Archiv-Schreibblock persistiert. Bestehende Journale werden einmalig über die versionierte Hintergrund-Nachlese (`stations`, Revision 1) aufgearbeitet: validierte Commander-Zuordnung und bereits konsumierte Dateipräfixe, Backup vor Änderungen, atomarer Abschlussmarker. Bei fehlenden/defekten Journalen keine falsche Erfolgsmeldung. Erfolgreiche Folgestarts scannen die Journale dafür nicht erneut.

## 7–11. Darstellung, Gruppen, Carrier, Details und Performance

- Beide Karten (Explorer/Chronik und zoombare Gesamtansicht) verwenden dieselben kompakten Einrichtungen.
- Bestehende Körperlayoutlogik reserviert zusätzliche Höhe direkt unter dem Parent. Einrichtungen sind keine BodyNodes und erscheinen nicht in der Planeten-Hauptreihe.
- 252 × 64 Pixel große Qt-Painter-Karten mit vorhandenem Theme-Auswahlrahmen, Symbol, Namen in 10 pt fett und Typzeile in 9 pt; keine neuen Bilder. Typklassen Orbitalstation, Außenposten, Oberfläche, Siedlung, Fleet Carrier, Megaship, unbekannte Station.
- Bis **3 Einrichtungen je Körper/Bereich** direkt; ab **4** eine Zeile „Einrichtungen (N)“. 76 Pixel Zeilenabstand und 16 Pixel Abstand zum Parent; maximal 244 zusätzliche Pixel pro Parent bei drei Einrichtungen. Die vorhandene Layoutengine reserviert außerdem 252 Pixel Breite. Ohne Einrichtungen bleiben die Maße unverändert. Klick auf eine Gruppe öffnet eine auswählbare Liste; ein Eintrag öffnet dieselbe große Detailansicht wie eine einzelne Karte.
- Unbekannte Parents erscheinen unter „Weitere Einrichtungen“, ebenfalls gruppiert; bei fünf Einträgen stehen Titel und Anzahl direkt in einer gemeinsamen umrahmten Karte. In der Referenzfixture: Metalworks unter 9 g, eigener Carrier unter 7 d, fünf weitere Einrichtungen in einer Gruppe.
- Namen werden elidiert, vollständiger Name im Tooltip (bei Gruppen Vorschau plus Anzahl; vollständige Liste per Klick).
- Details: nichtmodales Fenster (720 × 630 Pixel), Bildfeld (640 × 300 Pixel), hervorgehobener Name, Typ inklusive technischer Journaltyp soweit bekannt, System, bestätigter Parent, MarketID, letzter Belegzeitpunkt und Quelle. Unbekannte Angaben werden ausgeblendet. Kein Ausbau um Services/Wirtschaft/Fraktion.
- Fremde Carrier werden zunächst vollständig aus der Karte herausgefiltert. Eigener Carrier nur bei passender numerischer Eigentums-ID und belegtem System; vorhandenes Carrier-/Odyssey-/Mining-Tracking unverändert.
- Neuere Carrierbelege in einem anderen System verdrängen den alten Standort. Neuere CarrierLocation/CarrierJump-Belege ersetzen den Parent; auch der vorhandene aktuellere Eigentümer-Standort kann alte Kartenbelege unterdrücken. Keine aus einem JumpRequest abgeleitete Ankunft. Der angezeigte Zeitpunkt ist ein Belegzeitpunkt, keine Echtzeitgarantie.
- Stationsdaten werden mit dem Systemmodell geladen: eine Sammelabfrage für Belege plus eine Abfrage für den eigenen Carrier. Kein SQL und keine API in Paint oder einzelnen Stationselementen. Fremde Carrier erzeugen keine Grafikobjekte. Keine schweren Widgets pro Einrichtung; die Detail-Liste entsteht erst beim Klick.
- Zoom und 100%-Reset bleiben die bestehenden QGraphicsView-Transformationen. Alle Einrichtungen skalieren mit. Ohne Einrichtungen bleiben Layoutpositionen unverändert.

## 12–13. Schema und Übersetzungen

Additive Schemamigration **19 → 20**, atomar und wiederholbar; **Programmversion bleibt 3.5**. Migration und Nachlese wurden nur auf temporären Datenbanken/Kopien getestet. Eingabedatenbanken bleiben bei Kopiertests unverändert.

**14 neue i18n-Schlüssel**, jeweils DE EN EL ES FI FR IT NL NO PL SV TR, insgesamt **1506 Referenzschlüssel**. Präfix `facilities.`: station, group, orbital, outpost, surface, settlement, carrier, megaship, other, parent, updated, source, type, system. `common.unknown` wird wiederverwendet. Der vorhandene i18n-Prüfer bestätigt Schlüssel, Platzhalter und fehlende Duplikate.

## 14. Dateien dieses Auftrags

- `cmdrhelper/stations.py` (neu)
- `cmdrhelper/database.py`, `cmdrhelper/startup_repairs.py`, `cmdrhelper/state.py`
- `cmdrhelper/ui/station_items.py` (neu)
- `cmdrhelper/ui/system_layout.py`, `cmdrhelper/ui/system_view.py`, `cmdrhelper/ui/system_overview.py`, `cmdrhelper/ui/main_window.py`
- `cmdrhelper/i18n/{de,en,el,es,fi,fr,it,nl,no,pl,sv,tr}.py`
- `tests/test_system_stations.py` (neu), `tests/test_startup_repairs.py`, `tests/test_system_overview.py`
- `tests/fixtures/system_stations_plio.json` (14 anonymisierte, auf relevante Felder gekürzte Referenzereignisse)
- `docs/system-stations.md` (dieser Bericht)

Bereits vorhandene Änderungen, insbesondere Flotte, persönliche Bilder, Frachtraum-HUD und zugehörige Tests, wurden erhalten. Die vollständige Git-Differenz enthält deshalb mehr Änderungen als dieser Auftrag.

## 15–17. Abschlussprüfungen

Gezielter Prüflauf (keine vollständige Suite):

```bash
PYTHONPATH=.:tests QT_QPA_PLATFORM=offscreen venv/bin/python -m unittest \
  tests.test_system_stations tests.test_system_overview tests.test_system_layout \
  tests.test_system_map_belts tests.test_system_map_name_layout \
  tests.test_startup_repairs tests.test_commander_journal_delta \
  tests.test_import_catchup tests.test_p1_performance -q
```

**129 Tests bestanden**, darunter **22 neue Stationsprüfungen**, in 40,035 Sekunden. Abgedeckt: unverändertes leeres Stationslayout, Orbital-/Oberflächenstation, sichere und widersprüchliche Parents, MarketID-Identität, fehlende Identität, Carrierwechsel/Filter, Gruppen bis 200 Einrichtungen, lange Namen, Details, Körperklick, Zoom/Reset, Dark/Light, Paint ohne SQL/API, Migration/Rollback, Live-/Archivpersistenz und einmalige Nachlese. Die anonymisierte Journalfixture bestätigt sieben Einrichtungen, davon zwei sicher zugeordnet und fünf ohne Parent.

## UI-Erweiterung: lesbare Karten und große Detailansicht

Reine UI-/Layoutänderung; Datenmodell, Schema 20, Gruppierungsgrenze und Carrierregeln unverändert.

Die bestehende Kartenpalette wurde unverändert nach `ui/system_theme.py` ausgelagert:
Dark-Rahmen `selected` = `#ffb34f`, Light-Rahmen `selected` = `#965900`.
Die Karten nutzen die passenden Hintergrund-/Textfarben derselben Palette. Der
Rahmen ist 1,3 Pixel, bei Hover in der Gesamtansicht 2 Pixel breit. Die vorhandene
Scene-Transformation skaliert Karten und Text; keine separate Zoomlogik.

`ui/station_assets.py` ordnet Journaltypen zentral den Bildklassen dodec, coriolis,
orbis, ocellus, outpost, surface_station, settlement, megaship und fleet_carrier zu.
Unbekannte Typen verwenden standard. Priorität: lesbares lokales Typbild →
`standard.png` → bestehender technischer Platzhalter. Das Verzeichnis
`cmdrhelper/assets/stations/` enthält nur eine README, keine neuen Bilder.

`ui/station_details.py` verwendet unverändert `ShipImage` und dessen
`ShipImageViewer`. Doppelklick öffnet ein tatsächlich vorhandenes Bild in voller
Auflösung mit Einrichtungsname als Fenstertitel. Für den Platzhalter gibt es keine
Bildquelle und daher keinen Bildviewer. Keine persönliche Bildauswahl und keine
Änderung an persönlichen Schiffs-/Carrierbildern.

Gezielte UI-Prüfung: **72 Tests erfolgreich** (10 neue Darstellungs-/Resolvertests,
6 vorhandene Stations-UI-Tests sowie 56 bestehende Karten-/Layouttests).
Realtest: Plio Aihm UC-V d2-159 ausschließlich aus SQLite `mode=ro` geladen;
Carrier unter 7 d, Metalworks unter 9 g und fünf weitere Einrichtungen als Gruppe.
Dark/Light, 100 % und Fensteranpassung anhand tatsächlicher Qt-Renderings geprüft.
Keine vollständige Testsuite, keine Migration, kein Commit/Push/Release.
