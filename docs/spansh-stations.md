# Stand für 3.6

Manuelle Abrufe prüfen den gültigen Cache vor dem Workerstart: Liegt `fetched_at` am heutigen lokalen Kalendertag, wird ohne HTTP, Schreibzugriff oder Modellaktualisierung „Spansh-Daten wurden heute bereits aktualisiert.“ gemeldet. Jeder Erfolg zählt. Nach Fehlern ohne heutigen Erfolg darf sofort erneut versucht werden. Automatische 7-Tage- und Tageslogik bleiben unverändert. Im STATIONEN-Reiter weist bei deaktiviertem Service ein kompakter Hinweis auf das begrenzte Journalwissen hin.

Die folgenden Abschnitte dokumentieren den früheren Entwicklungs- und Prüfstand.

# Optionaler Spansh-Systemcache (CMDRHelper 3.5)

## Aktivierung und Livebetrieb

In den bestehenden Einstellungen unter Online Services kann „Spansh-Stationsinformationen ergänzen“ eingeschaltet werden. Standard ist entsprechend der vorhandenen optionalen Online-Ergänzungen **aus** (`spansh_stations/enabled`). Einschalten lädt vorhandenes Cachewissen, löst aber selbst keine Netzwerkabfrage aus.

Endpoint: `GET https://spansh.co.uk/api/dump/<SystemAddress>`.
Nur bestätigte neue Watcher-Ereignisse FSDJump, CarrierJump oder Location mit geändertem System, passender Commander-Sitzung und Zeitstempel ab Prozessstart dürfen einen Besuch auslösen. Startzustand, Commanderwechsel, historische Importe und Catchup setzen lediglich den Ausgangszustand. Insbesondere gibt es keine Iteration über historische Systeme oder alte Journale für Netzwerkabfragen. Während Catchup verarbeitete Ereignisse lösen bewusst keine Nachladeabfragen aus.

Ein QThreadPool-Worker lädt das einzelne System. Die lokale Karte erscheint sofort; anschließend aktualisiert ein eigenes Signal nur die betroffene Stationsansicht. Kein globales `state.refresh()`, keine Netzwerkabfragen beim Zeichnen. Mehrfachanforderungen während laufender Arbeit werden zusammengefasst; überholte wartende Aufträge werden verworfen.

## Speicherung

Plattformneutral über `QStandardPaths.AppDataLocation`, darunter `external/spansh/<id64>.json`:

- Linux: `~/.local/share/CMDRHelper/CMDRHelper/external/spansh/` (allgemein unter `$XDG_DATA_HOME`, sonst `~/.local/share`).
- Windows: `%APPDATA%\CMDRHelper\CMDRHelper\external\spansh\`.

Keine Administratorrechte, keine Spansh-Daten in SQLite. JSON-Schema 1 enthält `source`, `system_address`, `system_name`, `fetched_at`, optional `source_updated_at` und `stations`. Stationsfelder umfassen ausschließlich gelieferte Identität, Typ, expliziten Parent, Position, Zugehörigkeit, Regierung, Fraktion, Wirtschaft, Pads, ausgewählte Services und Stationszeitstempel. Keine Waren-, Modul- oder Schiffsangebote. Wirtschaftsgewichte werden nicht als Prozentwerte ausgegeben.

Cachezeit: 7 Tage ab Abruf. Automatisch kann nur ein erneuter Livebesuch einen alten Cache aktualisieren; der manuelle Button ist eine ausdrückliche Ausnahme. Offline bleibt vorhandenes Wissen nutzbar. Fehler werden protokolliert, ohne Dialogschleife; defekte Dateien werden ignoriert. Validiert werden Schema, Quelle, Systemidentität, Datentypen und Stationsstruktur. Schreiben erfolgt über temporäre Datei, Flush/fsync und atomaren Replace. Antwort- und Cachegrößen sind begrenzt.

Der Benutzerpfad liegt außerhalb des Releasepakets. Das bestehende `.gitignore` schließt auch den alternativen Projektpfad `data/external/spansh/*.json` aus; der Releaseprozess übernimmt keine Laufzeitdaten. Beides wurde geprüft, kein Release erstellt.

## Zusammenführung und Anzeige

Identität ist die numerische MarketID, niemals nur der Name. Journalstationen bleiben Primärwissen. Nur ein expliziter Spansh-Parent mit passendem vorhandenen Himmelskörper darf einen unbekannten Parent ergänzen. Entfernung und Namensähnlichkeit begründen keine Zuordnung. Widersprüche bleiben intern unter `spansh_conflicts` kenntlich, Journalwerte werden nicht überschrieben. Externe Informationen und Zeitstempel bleiben im separaten `spansh`-Teil des Anzeigemodells.

Spansh-Carrier werden ausgeschlossen. Der eigene Carrier bleibt vollständig aus dem vorhandenen Journal-/Carrierwissen. Die bestehende Gruppierung ab mehr als drei Einrichtungen bleibt erhalten. Unbekannte Parents erscheinen in „Weitere Einrichtungen“.

Die vorhandene große Detailansicht zeigt bekannte Zusatzinformationen, kompakte L/M/S-Angaben und Service-Chips. Quellen und Abruf-, Systemdaten- und Stationsdatenzeitpunkt sind getrennt. Das bestehende Bild und der Bildviewer bleiben erhalten. Lange Inhalte können gescrollt werden; Dark/Light und Zoom bleiben erhalten.

Die Anfrage übermittelt nur die öffentliche id64 sowie feste HTTP-Header. Keine FID, Commandernamen, Inventare oder sonstige Commanderinformationen.

## Einmaliger Realtest am 16.09.2026

Plio Aihm UC-V d2-159, id64 **5474145570075**, wurde einmal gezielt abgefragt. Empfang: **2026-09-16 12:08:38 UTC**; Spansh-Systemdatenstand: **2026-09-13 23:11:44 UTC**. Einzelne Stationen haben ältere eigene Zeitstempel.

70 gelieferte Einträge, davon sechs Carrier ausgeschlossen: **64 externe Einrichtungen** im lokalen Cache (37.845 Bytes). Zusammen mit Journalwissen: **65 eindeutige MarketIDs**, davon **32 mit sicherem Parent**, **33 ohne Parent**. Der eigene Carrier ist genau einmal enthalten.

| Einrichtung | MarketID | Parent im Anzeigemodell | Pads L/M/S |
| --- | --- | --- | --- |
| Ridorana Metalworks | 4359793667 | 9 g / 49 | 4/4/4 |
| Ridorana Forge | 4362443267 | unbekannt | 7/14/8 |
| Ridorana City | 4360397059 | unbekannt | 6/10/6 |
| Sori Relay | 4361726723 | unbekannt | 0/1/3 |
| Bulgarin Vision | 4361762051 | unbekannt | 0/1/3 |
| Ridorana Labs | 4366241539 | unbekannt | 5/12/8 |
| Eigener Carrier B5Y-8XN | 3705965312 | 7 d / 37 | nicht ergänzt |

Die fünf bisher unbekannten Parents werden auch durch diese Spansh-Antwort nicht aufgelöst. Metalworks wird explizit unter Körper 49 geliefert. Bei Labs widerspricht Spansh mit `Coriolis Starport` dem historischen Journaltyp `SurfaceStation`; Journaltyp bleibt erhalten, Abweichung wird intern markiert.

Beispiel Forge: Federation, Democracy, Explorers of Nabudis, Refinery, Entfernung 3074,868464 ls; Services Markt, Ausstattung, Werft, Universal Cartographics, Vista Genomics, Reparatur, Auftanken, Munition und Search and Rescue. Es werden ausschließlich tatsächlich gelieferte Services angezeigt.

Der Testcache liegt ausschließlich im oben genannten lokalen Benutzerpfad. Die Option wurde nicht automatisch aktiviert. Die reale DB wurde nur gelesen: Schema **20**, **336 station_observations**; Datei-Hash unverändert. Kein fachfremder Import, keine Migration.

## Gezielte Prüfung und Dateien

**134 Tests erfolgreich:** 34 neue Spansh-Tests und 100 ausgewählte bestehende Regressionstests. Abgedeckt sind Live-/Historiengrenze, Cachealter, Offline/Fehler, atomisches Schreiben, Validierung, MarketID, Parent-Ergänzung/Konflikte, Carrierfilter, Qt-Worker, gezielte Aktualisierung, Details/Services/Pads/Quellen, Dark/Light, Karteninteraktion und Pfad-/Releaseausschluss. Keine vollständige Testsuite. Qt-Prüfung unter Linux offscreen; Windows-Pfadlogik geprüft, kein nativer Windows-Lauf.

Alle zwölf Sprachen geprüft: **29 neue Schlüssel**, insgesamt **1535** Referenzschlüssel; Platzhalter und Schlüssel vollständig.

Für diesen Auftrag geändert/angelegt:

- `cmdrhelper/spansh_cache.py`, `cmdrhelper/spansh_stations.py`
- `cmdrhelper/state.py`
- `cmdrhelper/ui/main_window.py`, `cmdrhelper/ui/system_overview.py`, `cmdrhelper/ui/station_details.py`
- `cmdrhelper/i18n/{de,en,el,es,fi,fr,it,nl,no,pl,sv,tr}.py`
- `tests/test_spansh_stations.py`
- `docs/spansh-stations.md`

Bereits vorhandene Änderungen an Datenbank, Journal, Flotte, HUD und Stationsgrundfunktion gehören nicht zu diesem Auftrag. Version bleibt 3.5. Kein Commit, Push oder Release.

## Manueller Refresh und Tagesschutz

In der grafischen Systemübersicht steht neben „100 %“ und „An Fenster anpassen“ der Button „Spansh-Daten aktualisieren“. Er verwendet ausschließlich die id64 dieser Ansicht, auch einer ausdrücklich geöffneten Chronikansicht. Kein Durchlaufen historischer Systeme. Der Request läuft im vorhandenen Worker, umgeht Cachealter und automatisches Tageslimit und aktualisiert gezielt das betroffene Anzeigemodell. Während einer Anfrage für dieselbe id64 ist der Button deaktiviert. Erfolg oder Fehler erscheinen als kurze, nichtmodale Statuszeile.

Automatisch gilt: jünger als sieben Tage → vorhandenen Cache verwenden; ab sieben Tagen bzw. ohne Cache → nur beim Liveeintritt und höchstens ein Versuch je lokalem Kalendertag und id64. Unter `external/spansh/attempts/<id64>.json` werden Systemadresse und lokales Datum vor dem Request atomar gespeichert. Auch Fehler oder Prozessabbruch sperren damit weitere automatische Versuche an diesem Tag, über Helper-Neustarts hinweg. Am nächsten lokalen Kalendertag ist ein erneuter Versuch möglich, sofern der eigentliche Cache nicht frisch ist. Kann der Schutz nicht sicher gespeichert/gelesen werden, unterbleibt die automatische Anfrage; manuelle Aktualisierung bleibt möglich.

Manuelle Aktionen dürfen mehrfach am Tag erfolgen, aber nicht parallel für dieselbe id64. Die laufenden Aufträge sind systemübergreifend nicht global gesperrt; andere Systeme können unabhängig eingereiht werden. Bei Fehlern oder ungültigen Antworten bleibt die alte Cachedatei unverändert. Es gibt keine automatische Cachelöschung und keinen globalen Löschbutton.

Bei ausgeschaltetem Service sind automatische und manuelle Abfragen deaktiviert. Vorhandenes Spansh-Wissen wird wie bisher ausgeblendet, die Dateien bleiben erhalten. Abrufdatum und Spansh-Datenstand bleiben getrennt. Keine DB-/Schema-, Merge-, Parent-, Carrier- oder Pfadänderung.

Gezielte Prüfung dieser Ergänzung: **90 Tests erfolgreich**, davon elf neue Refresh-/Tagesschutztests, einschließlich offen gebliebener Systemübersicht nach einem Sprung. Keine vollständige Testsuite. Drei neue i18n-Schlüssel in allen zwölf Sprachen, insgesamt 1538. Geändert für diese Ergänzung: `spansh_cache.py`, `spansh_stations.py`, `state.py`, `ui/main_window.py`, `ui/system_overview.py`, zwölf Sprachdateien, `tests/test_spansh_stations.py`, `tests/test_system_overview.py` und diese Dokumentation. Keine reale Spansh-Abfrage für diese Tests.
