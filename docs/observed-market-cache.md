# Lokal beobachtete Märkte (Phase 6)

Der Cache hält ausschließlich Marktstände, die Elite selbst bei einem neuen
Marktbesuch während laufender Beobachtung bereitstellt. Er ist Infrastruktur für
spätere Handelsfunktionen: keine UI, Empfehlungen, Routen oder Quellenfusion.

## Datenpfad und Zeitpunkt

`AppState.observed_markets` ist ein `ObservedMarketObserver` in der vorhandenen
`JournalWatcher.live_observers`-Liste. Der Watcher prüft das aktuelle Journal mit
seinem vorhandenen Ein-Sekunden-Timer, neue Dateien beim periodischen
Verzeichnisdurchlauf. Alle Live-Leser nutzen `live_journal.journal_batch` und
`open_journal`; die vorhandene Sidecar-Dateisignatur und JSON-Duplikatprüfung
werden wiederverwendet. Cargo-, Odyssey-, Mining- und Carrier-Verarbeitung bleiben
unverändert. Vor Phase 6 gab es keinen Market.json-Leser.

Elite schreibt `Market` beim Öffnen des Warenmarktes und den Preisstand in die
separate `Market.json` im Journalverzeichnis. Bloßes Andocken reicht nicht. Eine
atomare Reihenfolge der beiden Schreibvorgänge wird nicht vorausgesetzt.

Quellen zur Struktur und Semantik:

- [Frontier Journal Manual v31, §§2.1, 7.5–7.6, 8.17](https://hosting.zaonce.net/community/journal/v31/Journal_Manual_v31.pdf)
- [EDCD/EDDN: Market-Ereignis als Signal zum Lesen von Market.json](https://github.com/EDCD/EDDN/blob/master/schemas/commodity-README.md)

Beim Setzen des Journalordners wird dessen aktuelle EOF-Grenze festgehalten.
Vorhandene Zeilen des neuesten Journals liefern ausschließlich Kontext; kein
historisches Market-Ereignis wird importiert. Unvollständige Zeilen werden erst
nach Abschluss gelesen. Neue Ereignisse müssen zusätzlich mindestens aus der
aktuellen Beobachtungsperiode stammen (eine Sekunde Toleranz wegen der
Journal-Zeitauflösung). Archive und Catch-up-Importe sind keine Marktquelle.

Bei Rotation wird nur das neueste Journal verwendet. Eine unmittelbar folgende
nummerierte Datei derselben Sitzung darf ihren Commander-/Stationskontext
erben. Eine neue Sitzung muss ihre eigene FID über `Commander`/`LoadGame`
belegen. Ersetzte, verkürzte, ohne Größenänderung umgeschriebene oder fehlerhafte
Journale werden für diese Sitzung gesperrt, nicht zurückgespult.

## Sichere Kopplung

Ein Snapshot erfordert:

1. ein neu beobachtetes `Market`-Ereignis mit gültiger FID im Journal-Kontext;
2. identische MarketID, StationName, StarSystem und UTC-Zeitpunkte in Ereignis
   und Sidecar; Namen sind Vergleichsfelder, keine Ersatzidentitäten;
3. widerspruchsfreie FID-, Stations-, System-, StationType- und
   SystemAddress-Felder, soweit vorhanden;
4. eine stabile Dateisignatur vor/nach dem begrenzten Lesen und vor Speicherung
   (auch das Journal darf sich inzwischen nicht geändert haben);
5. plausible Sidecar-mtime: nicht vor dem Ereignis oder nach der aktuellen Uhr,
   jeweils mit zwei Sekunden Dateisystemtoleranz;
6. vollständig valide Commodity-Identitäten, Preise und Mengen.

Market.json enthält üblicherweise keine FID. Ihre Zuordnung stammt aus der
Kopplung mit dem neu beobachteten, FID-gebundenen Journalereignis. Eine eventuell
vorhandene FID darf dem nicht widersprechen. Ein Zeitstempel allein genügt nicht.
Mehrere neue Market-Ereignisse mit gleichem Zeitstempel in einer Datei sind
mehrdeutig und werden nicht neu aufgenommen.

Bei kurzzeitig fehlender, unvollständiger oder noch alter Sidecar-Datei wird über
das vorhandene Watcher-Retry-Flag höchstens 15 Sekunden erneut versucht. Es gibt
keinen zusätzlichen Timer. Stations-/Commanderwechsel, Abflug, Sitzungsende und
neue Markt-Events verwerfen einen ausstehenden Versuch. Fehler werden geloggt
und über `last_error` diagnostizierbar; der bisherige Cache bleibt erhalten.

## Pfad, Schema und Commander

Plattformabhängig über `QStandardPaths.AppDataLocation`, wie die bestehenden
Snapshot-Manager:

`<AppDataLocation>/market_cache/observed_markets.json`

Damit werden Linux/XDG und Windows von Qt aufgelöst; keine persönlichen Pfade,
keine SQLite-Datei, keine QSettings. Schema-Version 1:

```json
{"version": 1, "markets": [
  {"fid": "F_SYNTHETIC", "market_id": 123,
   "station_name": "Fixture Port", "system_name": "Fixture System",
   "system_address": 555, "station_type": "Coriolis",
   "observed_at": "2026-01-02T12:00:00+00:00", "source": "local_elite",
   "commodities": [
     {"commodity_id": 199999999, "symbol": "$future_fixture_name;",
      "localized_name": "Future Fixture", "category": "$MARKET_category_metals;",
      "commander_buy_price": 524, "commander_sell_price": 411,
      "supply": 1500, "demand": 0}
   ]}
]}
```

Die Datei ist intern nach `(FID, MarketID)` getrennt: genau ein vollständiger
aktueller Snapshot pro Markt **je Commander**, keine Historie. Preise sind zwar
öffentliche Informationen, aber die Aussage „selbst beobachtet“ bleibt
Commander-spezifisch. Kein API-Zugriff ohne explizite FID; keine automatische
Vermischung der Profile. Cleanup umfasst alle FIDs in der Datei.

Optionale Felder: SystemAddress, StationType, Commodity-ID, lokalisierter Name
und Kategorie. Namen werden nie zur Commodity-Identifikation verwendet. Der
412er Master liefert kanonische ID/Symbol-Paare; widersprüchliche Paare werden
abgelehnt. Unbekannte zukünftige Waren bleiben mit ihrer Original-ID und ihrem
Originalsymbol erhalten, auch ohne numerische ID. Es gibt keine vollständige
Rohkopie und keine Speicherung von Commander-Namen.

## Preis- und Zeitsemantik

| Market.json | Intern | Bedeutung |
|---|---|---|
| BuyPrice | commander_buy_price | Commander zahlt beim Einkauf |
| SellPrice | commander_sell_price | Commander erhält beim Verkauf |
| Stock | supply | Markt bietet Ware an |
| Demand | demand | Markt kauft Ware an |

Alle vier Werte müssen echte nichtnegative Ganzzahlen sein; fehlende Werte,
Strings, Bool-Werte, NaN oder negative Zahlen werden nicht zu null geraten.
Die Zuordnung ist separat getestet und nicht aus Spansh-Feldnamen abgeleitet.

`observed_at` ist der übereinstimmende Journal-/Sidecar-Zeitstempel, normalisiert
auf UTC mit Offset. Weder Helper-Startzeit, Lesezeit noch mtime ersetzen ihn.
Zukünftige Beobachtungen werden nicht angenommen.

## TTL, Persistenz und Fehler

Gültig genau für `0 <= jetzt - observed_at < 24 Stunden`. Bei exakt 24 Stunden
ist der Eintrag abgelaufen. Cleanup entfernt abgelaufene Einträge **physisch**
beim Laden, bei Cache-Abfragen und beim Schreiben. Es betrifft auch andere FIDs.
Ein neuer Markt ersetzt den alten vollständig. Ältere Beobachtungen überschreiben
keine neueren; widersprüchliche Daten bei identischem Zeitpunkt werden abgelehnt.

Ein neuer gültiger Stand wird sofort geschrieben: temporäre Datei im selben
Verzeichnis, vollständiges UTF-8-JSON, `flush`, `fsync`, dann `os.replace`.
Erst nach erfolgreichem Ersatz wird der In-Memory-Stand übernommen. Fehler vor
dem Ersatz erhalten die alte Datei, temporäre Dateien werden entfernt. Auch
Cleanup schreibt atomar; bei Schreibfehlern werden abgelaufene Daten trotzdem
nicht ausgeliefert und das physische Cleanup beim nächsten Zugriff erneut
versucht. Ein ungültiger neuer Stand wird nie geschrieben.

Beschädigtes JSON, doppelte Schlüssel, falsche Version, ungültige Feldtypen,
fehlende Pflichtfelder, doppelte Identitäten oder auch nur einzelne beschädigte
Commodity-Datensätze machen den geladenen Cache insgesamt unvertrauenswürdig.
Er wird leer verwendet und diagnostiziert. Die beschädigte Datei wird nicht beim
Lesen überschrieben; eine spätere gültige neue Beobachtung kann sie ersetzen.

Grenzen: 64 MiB Cache-Datei, insgesamt 2.048 Marktstände über alle FIDs,
2.048 Commodities je Markt, 4 MiB Sidecar, 64 MiB aktives Journal und 4 MiB je
Journalzeile. Überschreitungen werden abgelehnt, nicht still gekürzt; gültige
Märkte werden nicht zugunsten neuer verdrängt. Textfelder sind auf 512 Zeichen
begrenzt, numerische Werte auf den nichtnegativen 64-Bit-Bereich.

## Interne API und Quellentrennung

`ObservedMarketCache(path, clock=...)` hat keine UI-Abhängigkeit. Nur die separate
Pfadauflösung verwendet Qt. `AppState.observed_markets.cache` stellt die Instanz
bereit:

- `get(fid, market_id)`: letzter gültiger Snapshot oder `None`;
- `find(fid, system_name, station_name)`: passende gültige Märkte;
- `all(fid)`: alle gültigen Marktstände dieses Commanders;
- `age(snapshot, now)` / `is_valid(snapshot, now)`: Alter und strikte TTL;
- `cleanup()`: physisches Aufräumen;
- `put(snapshot)`: validierter normalisierter lokaler Snapshot, sofort persistiert.

Abfragen liefern defensive Kopien. Der Produktions-Schreibpfad führt
Journal → Beobachter → `normalize_observation` → Cache. Nur `source=local_elite`
ist zulässig. Es existiert keine Verbindung zu den Spansh-Providern und keine
Persistenz ihrer Suchergebnisse. Der bestehende Spansh-Suchcache bleibt flüchtig
(5 Minuten, maximal 32 Einträge).

Später müssen lokale `observed_at` und Spansh-`market_updated_at` verglichen
werden. „Lokal“ darf nicht unabhängig vom tatsächlichen Alter bevorzugt werden.
Phase 6 implementiert weder diesen Vergleich noch Empfehlungen.

## Neustart und bekannte Grenzen

Erfolgreiche Writes überstehen einen späteren Helper-/Elite-Absturz und werden
beim nächsten Start geladen. Keine Speicherung erst beim Beenden. PC-Neustart
ändert daran nichts; die üblichen Grenzen der Dateisystem-/Hardware-Durabilität
bleiben bestehen. Es wird kein Produktivcache aus alten Journalen aufgebaut.

Ohne laufenden Helper gibt es keine neuen Aufnahmen. Fehlende FID, fehlende
Sitzungsvorgänger bei nummerierten Journalteilen, Uhrabweichungen oder verpasste
Sidecars führen bewusst zu Lücken statt geschätzter Zuordnung. Nur der letzte
noch eindeutig gekoppelte Markt eines zusammen gelesenen Batches kann erfasst
werden; bereits überschriebene Sidecars werden nicht rekonstruiert. Späte Tails
alter Journale nach Rotation werden nicht als neue Marktquelle verarbeitet.

Die Datei wird nicht von einem Hintergrunddienst bearbeitet: bei beendetem oder
vollständig inaktivem Helper erfolgt physisches Cleanup erst beim nächsten
Start/Zugriff/neuen Markt. Bei Schreibschutz bleibt eine abgelaufene Datei bis
zum nächsten erfolgreichen Cleanup bestehen, wird aber nicht als gültig benutzt.
Die Persistenz ist für eine Helper-Instanz ausgelegt, nicht für gleichzeitige
Schreiber mehrerer Prozesse. Eine Marktbeobachtung ist keine Preisgarantie und
keine laufende Bestandsaktualisierung nach jedem Kauf/Verkauf.

## Status auf der Handel-Seite

Direkt unter „Ausgangspunkt“ zeigt eine dezente, bei Bedarf umbrechende Zeile
„Eigene Marktdaten: 2 Stationen · zuletzt vor 3 Min.“. Bei einem Markt steht
„1 Station“, ohne gültige Märkte „0 Stationen“ ohne Altersangabe.

Gezählt werden ausschließlich die von `ObservedMarketCache.all(fid)` gelieferten
lokalen Snapshots des aktuell aktiven Commanders: eine Station je MarketID,
`source=local_elite`, Alter strikt unter 24 Stunden. Bei exakt 24 Stunden zählt
ein Snapshot nicht mehr. Die UI liest die JSON-Datei nicht selbst und besitzt
keine eigene TTL-Prüfung. Spansh-Suchergebnisse gehören nicht zu dieser Zahl.
„Zuletzt“ verwendet das jüngste `observed_at`, niemals eine Dateizeit.

Die Aufnahme erfolgt automatisch, wenn bei laufendem Helper in Elite der
Warenmarkt geöffnet wird. Erneutes Öffnen desselben Markts aktualisiert dessen
Snapshot und Zeitstempel, erhöht aber nicht die Stationszahl. Der Tooltip erklärt
die Aufnahme und die automatische Entfernung älterer Marktstände.

Nach erfolgreichem atomischem Cache-Schreiben meldet ein optionaler Callback die
Änderung über `AppState.observedMarketsChanged`. Damit aktualisieren sowohl neue
Aufnahmen und Ersetzungen als auch physisches Cleanup durch normalen Cachezugriff
die Anzeige. Commanderwechsel, State-Aktualisierung und Öffnen der Handel-Seite
aktualisieren sie ebenfalls. Es gibt keinen zusätzlichen Timer: Bei vollständig
inaktiver Anwendung verändern sich Altersangabe und Zahl erst beim nächsten
solchen Ereignis. Die Cache-Semantik und die Verkauf-/Einkaufssuche bleiben gleich.

## Manuelle Live-Abnahme von Phase 6

Vom Benutzer vor dem Entwicklungscommit erfolgreich geprüft und abgenommen:

- Das Öffnen des Elite-Warenmarkts bei laufendem Helper erfasste den ersten
  Stationsmarkt automatisch und speicherte ihn persistent.
- Nach Beenden und Neustarten des Helpers blieb der Markt ohne erneutes Öffnen
  des Warenmarkts mit unverändertem `observed_at` erhalten.
- Der Besuch einer zweiten Station mit Öffnen ihres Warenmarkts führte zu genau
  zwei unterschiedlichen MarketIDs im Cache.
- Erneute Beobachtung derselben MarketID ersetzte den bisherigen Snapshot;
  es entstand keine Historienzeile und die Stationszahl erhöhte sich nicht.
- Beide geprüften Snapshots waren jünger als 24 Stunden, hatten ausschließlich
  `source=local_elite` und vollständig valide Commodity-ID/Symbol-Zuordnungen
  gegen den Master. Es waren keine Spansh-Daten enthalten.
- Die dezente Statuszeile „Eigene Marktdaten: 2 Stationen · zuletzt vor …“ wurde
  im real laufenden Helper geprüft und vom Benutzer abgenommen.

Dies dokumentiert die manuelle Benutzerabnahme, keine fest erwarteten Livewerte
für automatisierte Tests. Reale FIDs, Stations-/Systemnamen, Markt-IDs, Preise
und persönliche Laufzeitdateien werden dafür nicht ins Repository übernommen.
Die Tests verwenden ausschließlich synthetische Daten. Für den Commit wird
keine zusätzliche Live-Marktbeobachtung erzeugt.
