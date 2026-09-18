# CMDRHelper 3.6 — finaler Releasecheck

Feature Freeze. Kein Commit, Push, Tag, GitHub-Release oder github.sh.

## Vollständiger Git-Arbeitsstand

A = Produktcode/Assets; B = Tests/Dokumentation/Prüfwerkzeuge; C = Benutzerdaten; D = temporäre Artefakte; E = ungeklärt.

| Git | Datei | Klasse | Entscheidung |
|---|---|---|---|
| ` M` | `.gitignore` | A | Releasehygiene und Laufzeitdaten-Ausschluss. |
| ` M` | `README.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `README_DE.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `README_EL.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `README_ES.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `README_FI.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `README_FR.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `README_IT.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `README_NL.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `README_NO.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `README_PL.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `README_SV.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `README_TR.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `cmdrhelper/database.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/favorites.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/i18n/de.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/i18n/el.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/i18n/en.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/i18n/es.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/i18n/fi.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/i18n/fr.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/i18n/it.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/i18n/nl.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/i18n/no.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/i18n/pl.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/i18n/sv.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/i18n/tr.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/journal_catchup.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/journal_reader.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/mining_carrier.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/online_services.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/planet_navigation.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/release_summaries.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/startup_repairs.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/state.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/ui/belt_cluster_widget.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/ui/body_detail_window.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/ui/cargo_hud.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/ui/commander_view.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/ui/favorites_view.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/ui/main_window.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/ui/navigation_hud.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/ui/planet_3d_widget.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/ui/planet_navigation_window.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/ui/screenshot_view.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/ui/system_layout.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/ui/system_overview.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/ui/system_view.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `cmdrhelper/version.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| ` M` | `create_release.sh` | A | Releasehygiene und Laufzeitdaten-Ausschluss. |
| ` M` | `docs/update-summary.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_cargo_hud.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_commander_fleet.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_commander_unsold_data.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_edsm_system_status.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_explorer_value_sort.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_favorites.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_material_row_style.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_material_tabs.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_navigation_hud.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_navigation_hud_windows.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_parent_migration.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_performance_round2.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_quick_favorite.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_screenshot_multi_commander.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_startup_repairs.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_surface_mining_history.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tests/test_system_overview.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` D` | `tools/fleet-carrier-Pro Aec ZW-I b37-7-Plio Aihm JZ-R c4-12-707546D4-A444-11F1-ADA1-B4060BC487B5.csv` | C | Persönlicher Routenexport: geprüft, lokal im ignorierten Backup erhalten, Repository-Entfernung vorgesehen. |
| ` M` | `tools/hud_x11_probe.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tools/test_cargo_hud_x11.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tools/test_edsm_status_x11.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| ` M` | `tools/test_quick_favorite_x11.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `RELEASE_CHECK_3.6.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `cmdrhelper/assets/ships/README.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `cmdrhelper/assets/ships/standart.png` | A | Mitgeliefertes Programmasset; kein persönliches Bild. |
| `??` | `cmdrhelper/assets/stations/README.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `cmdrhelper/assets/stations/coriolis.png` | A | Mitgeliefertes Programmasset; kein persönliches Bild. |
| `??` | `cmdrhelper/assets/stations/dodec.png` | A | Mitgeliefertes Programmasset; kein persönliches Bild. |
| `??` | `cmdrhelper/assets/stations/fleet_carrier.png` | A | Mitgeliefertes Programmasset; kein persönliches Bild. |
| `??` | `cmdrhelper/assets/stations/megaship.png` | A | Mitgeliefertes Programmasset; kein persönliches Bild. |
| `??` | `cmdrhelper/assets/stations/ocellus.png` | A | Mitgeliefertes Programmasset; kein persönliches Bild. |
| `??` | `cmdrhelper/assets/stations/orbis.png` | A | Mitgeliefertes Programmasset; kein persönliches Bild. |
| `??` | `cmdrhelper/assets/stations/outpost.png` | A | Mitgeliefertes Programmasset; kein persönliches Bild. |
| `??` | `cmdrhelper/assets/stations/settlement.png` | A | Mitgeliefertes Programmasset; kein persönliches Bild. |
| `??` | `cmdrhelper/assets/stations/standard.png` | A | Mitgeliefertes Programmasset; kein persönliches Bild. |
| `??` | `cmdrhelper/assets/stations/surface_station.png` | A | Mitgeliefertes Programmasset; kein persönliches Bild. |
| `??` | `cmdrhelper/fleet_reconstruction.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/ship_ownership.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/spansh_cache.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/spansh_stations.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/stations.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/ui/explorer_status.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/ui/fleet_actions.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/ui/personal_ship_images.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/ui/ship_assets.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/ui/ship_widgets.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/ui/station_assets.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/ui/station_details.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/ui/station_items.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/ui/stations_view.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/ui/system_theme.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `cmdrhelper/ui/visible_animation.py` | A | 3.6-Produktcode oder Sprachkatalog. |
| `??` | `docs/fleet-manual-deletion.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `docs/release-3.6.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `docs/spansh-stations.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `docs/system-stations.md` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `tests/fixtures/system_stations_plio.json` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `tests/test_explorer_mapping_status.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `tests/test_hud_navigation_performance.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `tests/test_mining_safe_preamble.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `tests/test_release_36.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `tests/test_spansh_stations.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `tests/test_station_presentation.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `tests/test_stations_view.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `tests/test_system_stations.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |
| `??` | `tests/test_visibility_performance.py` | B | 3.6-Test, Dokumentation oder benötigte Prüfhilfe. |

117 Einträge: A: 65, B: 51, C: 1, D: 0, E: 0. Nichts gestagt.

## Version und Umfang

Zentrale Version 3.6. Fenstertitel, Seitenleiste, Einstellungsanzeige, Diagnose und Updater verwenden diese Quelle. Spansh-, EDSM- und Inara-Versionen in HTTP-/API-Metadaten ebenfalls auf die zentrale Quelle umgestellt. Versionslose Route-Planner-User-Agents bleiben versionslos. Historische 3.5-Dokumentation bleibt erhalten; zwölf READMEs haben einen neuen 3.6-Abschnitt vor der Historie.

Kein Feature nach Freeze begonnen. Releasekorrekturen: geprüftes Vorab-Backup für Schema 17–19 → 20, Ausschluss persönlicher Bild-/Cacheordner beim Paketbau, Versionskonsistenz. Testpflege: Schema-20-Erwartungen, Consumer-Methoden der nativen HUD-Testadapter, expliziter Maus-/Hoverzustand und vollständiges Qt-HoverLeave für reproduzierbare Pixelvergleiche; logischer SQLite-Inhaltsvergleich statt WAL-abhängiger physischer Dateibytes im Carrierbild-Test. Alle ursprünglichen fachlichen Assertions bleiben erhalten.

## Datenbank

Veröffentlichte v3.5: Schema 17; 3.6: Schema 20. Additive Migrationen: 18 commander_deleted_ships, 19 commander_ship_sales, 20 station_observations plus Systemindex. Keine Spansh-Daten in SQLite.

Eine Kopie eines vorhandenen Schema-17-Snapshots wurde isoliert migriert. Automatisches geprüftes Backup vor dem ersten Schemaeingriff; Backup entspricht inhaltlich dem Ausgangszustand. Schema 20, foreign_keys=1, foreign_key_check leer, integrity_check=ok. Alle bisherigen Tabellen haben identische Datensatz-Digests. Erhalten: 1 Commander, 2.360 Systeme, 17.885 Bodies, 65.500 Materialzeilen, 128 Missionen, 22 Schiffe und alle weiteren vorhandenen Tabellen. Erneutes Öffnen erzeugt kein weiteres Backup. Backupfehler verhindert Schemaänderungen. Originalsnapshot unverändert; produktive DB nicht migriert.

## Stationen, Spansh, Flotte

Zehn PNGs (coriolis, dodec, fleet_carrier, megaship, ocellus, orbis, outpost, settlement, standard, surface_station) vorhanden, von Qt dekodierbar und über Resolver erreichbar. Paketdateien stimmen bytegenau mit den Originalassets überein. Keine Bilder verändert.

Regressionsmodule test_system_stations, test_station_presentation, test_stations_view und test_spansh_stations prüfen Parents, weitere Einrichtungen, Gruppierung, Details, Services/Pads, Quellen/Zeitstempel, Bildviewer, Suche/Filter/Sortierung, Aufklappen, Themes sowie Servicehinweis und Livewechsel.

Spansh standardmäßig AUS. Keine historischen Netzwerkimporte. JSON-Cache getrennt von SQLite, automatische sieben Tage und persistenter Tagesversuch unverändert. Manueller heutiger Erfolg sperrt ohne Worker/HTTP/Schreibzugriff/Merge; Fehler erlaubt sofortigen Retry, Tageswechsel verwendet lokale Zeitzone. Parallelität, Offlinefallback, Cacheerhalt, Carrierfilter und Journalpriorität geprüft. Kein echter Spansh-Request während des Checks.

Flottentests prüfen persistente Löschmarkierungen, erneutes Einlesen, Verkaufswatermarks, Buy/Swap und das tatsächliche Journalereignis SellShipOnRebuy (nicht ShipyardSellOnRebuy), fehlende Deduplizierung über Kennung, persönliche/Typ-/Standardbilder, eigenen Carrier, Bildviewer und sichere Plattformpfade. Keine realen Flottendaten geändert.

## Mining-Carrier

Kopie der vorhandenen QSettings gelesen. Historische bestätigte Ausgangsbestände wurden über die reguläre confirm-API auf tatsächliche Journalzeitpunkte zurückgeführt und anschließend mit echten Journalen fortgeschrieben. Eine fehlende Zwischenkette erzeugte reguläre resume_count-Werte; nach Bereitstellung der geprüften Fileheader/Friends/Friends-Datei ergab advance erneut Grandidierit 101, Palladium 11, Silber 22, Tritium 18.653. Keine künstliche Beförderung von last_confirmed zum aktuellen Bestand. Die inzwischen aktuelle Speicherung enthält 19.134 Tritium; sie wurde nicht zurückgesetzt. Produktions-QSettings hashgleich. Negative Fälle sind durch test_mining_safe_preamble abgedeckt.

## HUD, Navigation und Performance

Tests decken Schiff/SRV, Status-Fallback, 0/Capacity, EDSM-HUD, Vordergrundregel, fail closed, Fenster-/Randlosgeometrie, Plattformadapter und Verbrauchermodell ab. Ohne Verbraucher keine Navigationspolls; Favoriten nutzen das gemeinsame Sample.

Native Linux-X11-Prüfungen: Cargo, Schnellfavoriten und EDSM erfolgreich; leere Eingaberegion, unveränderter Fokus im erfolgreichen Lauf, Timerablauf, Geometrie, Verstecken/Wiederherstellen und unabhängige Meldungskanäle. Beim ersten, unmittelbar auf den Cargo-Prozess folgenden EDSM-Lauf änderte sich der gemessene Vordergrund während der Wartezeit; die Ursache dieses Fokuswechsels wurde nicht eindeutig zugeordnet. Der anschließende isolierte EDSM-Lauf bestand vollständig. Testfenster statt Eingriff in Elite.

Windows wurde nicht nativ ausgeführt. Vorhandene Windows-Adapter-/Bootstrap-/Update- und plattformneutrale Pfadtests laufen unter Linux mit ihren vorgesehenen Testadaptern. navigation_hud_windows.py unverändert gegenüber v3.5.

Visibility-Timer betreffen dekorative Animationen. Screenshot-Automatik läuft unabhängig von Galerie-Sichtbarkeit. Journalwatcher, Sidecar-/Inventar- und Carriererfassung sowie notwendige Persistierung werden nicht durch UI-Sichtbarkeit gestoppt. Tests zu Runde 1/2, Dirty-Tabs und versteckter Verarbeitung enthalten.

## Explorer

Exakt acht Spalten: Körper, Typ, Entfernung, Scanwert, Wert nach Scanstand, Kartographie-Schätzung, Kartierung, Status. self_mapped=True hat Vorrang: SELBST KARTIERT blau; BEREITS KARTIERT grün; NICHT KARTIERT gelb; ? grau. Dunkle/helle Paletten und alle neun Tri-State-Kombinationen geprüft. Ausführliche Körperdetails erhalten.

## i18n

1.562 englische Referenzschlüssel, zwölf Sprachen. Keine unerwartet fehlenden/zusätzlichen Schlüssel, Duplikate, Platzhalter- oder Formatstringfehler. Alle neuen 3.6-Texte übersetzt. Die vorhandene dokumentierte Materialnamen-Fallbackregel bleibt bestehen: 122 englische Materialnamen in EL/FI/NL/NO/PL/SV/TR, 11 in ES/FR; DE/EN/IT vollständig direkt hinterlegt.

Zusätzliche Verwendungsprüfung: sieben neue scheinbar verwaiste Kartierungs-Schlüssel werden dynamisch über explorer.mapping_status_ verwendet. 49 weitere Kandidaten waren bereits in v3.5 vorhanden; keine neue verwaiste 3.6-Schlüsselgruppe. Historische/ungenutzte Schlüssel im Freeze nicht entfernt. Statische Analyse dynamischer tr()-Aufrufe ist grundsätzlich begrenzt.

## Hygiene und Paket

Keine neu hinzugefügten Debugprints, TODO/FIXME, persönlichen absoluten Pfade oder /tmp-Testpfade im Produktcode. Persönlichen Pfad in neuer Spansh-Dokumentation durch generischen Benutzerpfad ersetzt. Bestehender historischer Supportbericht mit lokalen Pfaden wird vom offiziellen Builder ausgeschlossen.

Reale DB/Backups unter data, Logs, externe Spansh-Caches/Attempts, persönliche ship_images/carrier_images, QSettings und Screenshots sind ausgeschlossen. Die zuvor versionierte persönliche Routen-CSV ist lokal im ignorierten backup/release-3.6-excluded erhalten und zur Entfernung vorgemerkt (nicht gestagt). Solange kein späterer Commit erfolgt, existiert ihr bisheriger Index-/Historieneintrag weiter. Die reduzierte Stationsfixture ohne Commanderkennung ist ein gewollter Regressionstest, kein vollständiges Journal; nicht im Paket.

Offizieller lokaler Build via bash create_release.sh. ZIP-Integritätsprüfung und eigener Inhaltsabgleich bestanden. 354 Dateien; ZIP-Größe 183.660.861 Bytes (175,15 MiB), SHA-256 `5979719e5a8b09b441fee5d8f7c55bc932d3b5873af22855419f11709f1d8a04`. Alle neuen Module, zwölf Sprachkataloge und zehn Stationsbilder enthalten. Keine Tests, Cache-/Attempt-Dateien, persönliche Bilder, reale Datenbank, Backups, Journale, QSettings, lokale Analyseartefakte oder persönlichen absoluten Pfade. data enthält ausschließlich leere .gitkeep. Mitgelieferte Dokumentationsbilder sind bewusst enthalten.

Entpackter Start einschließlich unverändertem main.py-Einstieg mit isolierten Qt-Einstellungen, leerer Testdatenbank, ausgeschalteten Online-Diensten und unterdrücktem Updatecheck erfolgreich. Fenstertitel/Einstellungen/Diagnose melden 3.6; Oberfläche in beiden Themes gerendert. Kein nativer Windows-GUI-Test.

README in zwölf Sprachen aktualisiert. docs/release-3.6.md enthält den unveröffentlichten Entwurf mit Neu / Verbessert / Behoben. Lokalisierte Updatehinweise für 3.6 ergänzt; historische Zuordnungen beibehalten.

## Abschließender Teststand

Vorläufe deckten veraltete Schema-19-Testannahmen, während der Versionsumstellung bereits geladene 3.5-Werte, eine zunächst nicht AST-literal lesbare neue Release-Zuordnung sowie drei instabile GUI-/Dateivergleiche auf. Die Release-Zuordnung ist wieder ein rein literales Dictionary. Die Schemaerwartungen entsprechen der beabsichtigten Stationsmigration. Die ursprünglichen Farb-/Pixel-/Dateninhaltsanforderungen wurden nicht gelockert: Cursorposition wird explizit vorgegeben, Qt-HoverLeave setzt den privaten Tab-Hoverzustand zurück, und der Carrierbild-Test vergleicht vollständige logische SQLite-Daten statt checkpointabhängiger Dateibytes. Der Hoverfehler wurde mit absichtlich eingespeistem HoverMove separat reproduziert und danach erfolgreich gegengeprüft; zwölf Carrierbild-Wiederholungen bestanden.

Finaler vollständiger Lauf: `QT_QPA_PLATFORM=offscreen venv/bin/python -m unittest discover -s tests -v`.

**1.707 Tests bestanden, 0 Fehler, 0 Fehlschläge, 0 übersprungene Tests; 522,130 Sekunden.** Keine regulären Tests ausgeschlossen. Ergänzend: echter Schema-17-Kopietest, historischer Mining-Replay, zehn Asset-Decoderprüfungen, vier negative Paketierungsproben für persönliche Bilder/Spansh-Daten, Versionsheader-Prüfung ohne Netzwerk, native X11-Proben und entpackter main.py-Smokestart erfolgreich. Alle 165 Produkt-Pythondateien syntaktisch gültig; bash -n für Release-/Start-/Installationsskripte erfolgreich.

`git diff --check`: ohne Befund. Unversionierte neue Python-/Markdown-Dateien zusätzlich mit --no-index --check geprüft: ohne Befund. Vollständiger Arbeitsstand oben klassifiziert; keine gestagten Änderungen. Produktstand im ZIP bytegenau mit dem geprüften Quellstand abgeglichen.

Keine verbleibenden nachgewiesenen Releaseblocker. Bekannte Prüflimits: kein echter Windows-GUI-Lauf; deklarierte bestehende englische Materialnamen-Fallbacks; historische ungenutzte i18n-Kandidaten unverändert. Diese Grenzen wurden nicht als erfolgreich durchgeführte Tests ausgegeben.

Version 3.6, Schema 20. Kein Commit, Push, Tag, GitHub-Release oder github.sh. Feature Freeze bleibt bestehen.

CMDRHelper 3.6 ist releasebereit.
