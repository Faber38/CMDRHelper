# Handel: Empfehlungen und „Hier verkaufen“

Der Reiter **Empfehlungen** beantwortet sichtbar und mit dynamischem Prozentsatz:
„Ich stehe hier mit diesem Schiff – welche Ware kann ich hier kaufen und innerhalb
meiner Vorgaben mit mindestens X % Gewinn verkaufen?“ Die Suche startet nur über
**Empfehlungen suchen** oder die ausdrückliche Merkzettelaktion **Hinweg suchen**.
Das bloße Öffnen des Reiters oder eine Zustandsänderung startet keine Suche.

## Einkauf und Schiff

Der Einkauf verwendet ausschließlich den bestätigten lokalen Markt. Die GUI prüft
dessen Header über `current_market()` / `ObservedMarketCache.get_header()`; der
Worker liest den vollständigen Markt über den bestehenden Store-/Cachepfad.
FID, MarketID, Stationsname und System müssen zum aktuellen Journal-Kontext des
bestehenden Observers und zum aktiven AppState passen. Ein zuletzt besuchter Markt
ist kein Ersatz für die aktuelle Station. Fehlt ein gültiger `local_elite`-Stand
innerhalb des eingestellten maximalen Marktdatenalters (Standard: 24 Stunden),
fordert die Oberfläche zum Öffnen des Elite-Warenmarkts auf.
Spansh wird niemals als Einkaufsquelle verwendet.

Schiffsname, -typ und Kapazität stammen aus dem vorhandenen ShipLoadout/AppState.
Die Belegung wird in `ship_cargo.py` unabhängig vom Wareninventar validiert:

1. Aktueller Ship-Cargo-Snapshot mit passender FID, ShipID und Journalgeneration.
2. Autoritativer Ship-Gesamtzähler eines Cargo-Ereignisses desselben Kontexts,
   auch ohne vollständiges Inventory oder passende Cargo.json.
3. Validiertes `Status.json.Cargo` für das aktuelle Schiff.
4. Andernfalls unbekannt.

Der Journalreader bindet Cargo beim chronologischen Einlesen an FID, Journal,
Spielstart, Fahrzeug, ShipID und Ereignisgeneration. Wechsel und Mengenänderungen
invalidieren frühere Ship-Zähler; alte Ereignisse erhalten niemals eine neue
ShipID. SRV-Cargo ist keine Ship-Belegung, auch nicht bei Count=0.

Der gemeinsame Status-Fallback für Handel und HUD verlangt eine identifizierte
aktuelle Sitzung, ein vollständiges nicht veraltetes Loadout aus dieser Sitzung,
Schiffsmodus (kein SRV/Fighter/OnFoot/Taxi/Multicrew), gültige ganzzahlige Belegung
zwischen 0 und Kapazität. Für **neu zu bestätigende Status-Evidenz** gilt ein Alter
von höchstens 120 Sekunden (maximal fünf Sekunden in der Zukunft). Status muss
mindestens so neu wie das Loadout und strikt
neuer als der letzte Fahrzeugwechsel oder mögliche Cargo-Eingriff sein. Gleiche
Sekunden beweisen bei solchen Eingriffen keine Reihenfolge. Fehlendes `first_event_at`
in der DB wird durch den tatsächlich eingelesenen Journal-/LoadGame-Kontext abgedeckt.

Bereits bestätigte, identische Status-Evidenz bleibt auch nach 120 Sekunden gültig,
solange ihre vollständige Kontextbindung und alle Validierungen unverändert gelten.
Dazu gehören Commander/FID, Journal und Sitzung, Schiff/Fahrzeug, Ereignisgeneration,
Invalidierungsgrenze, Loadout und Kapazität sowie Statuszeitpunkt, Flags und Menge.
Ein geänderter Status ist neue Evidenz und muss wieder die Altersgrenze erfüllen.
Ungültige oder fehlende Statusdaten dürfen keine frühere Bestätigung ersetzen.
Die Bestätigung existiert nur im Arbeitsspeicher; nach einem Helper-Neustart kann
ein alter Status nicht allein deshalb verwendet werden, weil er zuvor bestätigt war.

Kauf/Verkauf, Sammeln, Auswerfen, Raffinieren, Transfers, Limpets und mögliche
Missions-/Spezialfrachtänderungen werden konservativ invalidiert, nicht als Deltas
addiert. Ein anschließender autoritativer Cargo-Zähler ersetzt den Zustand. So gibt
es keine Doppelzählung. Neustarts rekonstruieren denselben Kontext aus dem Journal;
Status wird weder als Inventar noch dauerhaft gespeichert.

Der bestehende Watcher-Timer liest Status und verspätete Cargo-Sidecars erneut,
prüft Kontext und Statusgültigkeit und meldet Änderungen über
`cargoSnapshotChanged`. Solange Journalbytes nicht übernommen sind oder eine neue
Journaldatei auf Übernahme wartet, wird kein alter Kontext mit Status kombiniert.
Ausstehende Journalbytes sperren die Nutzung vorübergehend; nach dem Einlesen
entscheidet der daraus entstandene Kontext, ob die Bestätigung weiter gilt.

Der Gesamtzähler enthält alle Güter einschließlich Missionsfracht, gestohlener
Fracht und Limpets; diese werden nicht nochmals addiert. Die Freiraumrechnung ist
`max(0, capacity-count)`. Unplausible Belegungen oberhalb der Kapazität werden zuvor
verworfen. Bei unbekannter Kapazität/Belegung oder vollem Frachtraum gibt es keine
Empfehlungen und keine manuelle Ersatzmenge.

## Ziele und Quellenvergleich

Ziele stammen aus gültigen lokal beobachteten Märkten und dem bestehenden
`SpanshMarketProvider.search_sell()`. Lokale Marktbeobachtungen werden nach den
vorhandenen Regeln auch über Commander hinweg geteilt; pro MarketID zählt der
aktuelle Stand. Das eingestellte maximale Marktdatenalter gilt für beide Quellen;
zukünftige Zeitstempel bleiben ungültig. Die aktuelle Einkaufs-MarketID
wird als Ziel ausgeschlossen.

Der Vergleich benutzt `observed_at` beziehungsweise `market_updated_at`, jeweils
mit UTC-Offset. `retrieved_at` ist kein Marktzeitpunkt. Pro Commodity und MarketID
gewinnt der jüngere gültige Stand. Bei identischem Zeitpunkt wird deterministisch
der lokale Stand verwendet. Der Vergleich erfolgt **vor** Nachfrage-, Gewinn- und
Metadatenfiltern: Ein neuerer lokaler Stand ohne Nachfrage oder ohne die Ware darf
nicht durch ein attraktives älteres Spansh-Angebot ersetzt werden.

Treffer ohne positive MarketID werden verworfen. Es gibt keinen unsicheren
Stationsnamen-Fallback. Marktidentität, Preissemantik und Zielinformationen werden
im bestehenden `MarketOffer` wiederverwendet; das neue Empfehlungsobjekt ergänzt
nur lokalen Einkaufspreis und mögliche Menge sowie daraus abgeleitete Gewinne.

Lokale Entfernungen verwenden denselben gespeicherten Koordinatenresolver und
`Coordinates.distance_to` wie Favoriten. Gleiche sicher bekannte SystemAddress
bedeutet 0 ly. Unbekannte oder mehrdeutige Koordinaten werden nicht geschätzt:
solche lokalen Ziele entfallen. Es gibt dafür keine zusätzlichen Onlineabfragen.

Lokale Marktstände enthalten selbst keine Landeplatzgröße und keinen Anflugabstand.
Bekannte Landeplatzgrößen werden über die vorhandene Pad-Metadatenzuordnung aus
Journalen und dem lokalen Spansh-Stationscache ergänzt. Die Zuordnung prüft
MarketID, Stationsname, System und bekannte SystemAddress; sie errät keine Größe
aus dem Stationstyp. Pad-Metadaten werden unabhängig von der Preisquelle behandelt,
ohne Preise oder Marktzeitpunkte eines älteren Angebots zu übernehmen.
Ohne bekannte Padgröße ist nur „Alle“ erfüllbar. Fehlender Anflug erfüllt keine
gesetzte Anfluggrenze. Ohne bekannten Stationstyp lässt sich „Fleet Carrier aus“
nicht sicher erfüllen. Unbekannte Werte erscheinen als „–“.

## Berechnung und Auswahl

Nur lokal angebotene Waren mit `commander_buy_price > 0` und `supply > 0` werden
betrachtet. Ziele benötigen `commander_sell_price > 0` und `demand > 0`.

- Gewinn/t = Ziel-Verkaufspreis − lokaler Einkaufspreis.
- Gewinn % = Gewinn/t / lokaler Einkaufspreis × 100.
- Menge = Minimum aus freiem Frachtraum, lokalem Supply und Ziel-Demand.
- Gesamtgewinn = Gewinn/t × Menge.
- Einkaufskosten = lokaler Einkaufspreis × Menge.
- Verkaufserlös = Ziel-Verkaufspreis × Menge.

Die Mindestmarge ist ganzzahlig zwischen 0 und 1000 %, standardmäßig 10 %.
Der Vergleich verwendet rationale Zahlen ohne vorheriges Runden: 9,99 % erreicht
10 % nicht, 10,00 % dagegen schon. Nur positive Mengen werden angezeigt. Bei
Mindestmarge 0 ist ein Geschäft ohne Gewinn zulässig, ein Verlust nicht.

Pro Ware zeigt die Haupttabelle höchstens ein Ziel: größter Gesamtgewinn, bei
Gleichstand jüngerer Marktstand, geringere Entfernung, geringerer Anflug (unbekannt
zuletzt), dann Stationsname, Systemname und MarketID als deterministische Reihenfolge.
Die Zielstation und das Zielsystem bleiben im Ergebnisobjekt erhalten. Es gibt
keine automatische Rundreiseplanung und keine Rare-Goods-Sonderbehandlung.

Die Tabelle zeigt Ware, Einkauf/t, Zielsystem/-station, Verkauf/t, Gewinn/t,
Gewinn %, Menge, Gesamtgewinn, Entfernung, Anflug, Landeplatz, Quelle und Zielalter.
Initial wird Gesamtgewinn absteigend sortiert; Zahlen, Landeplatz und Alter nutzen
die bestehenden fachlichen Tabellenklassen, keine lexikografische Zahlensortierung.

## Requeststrategie und unvollständige Ergebnisse

Ein Worker wertet zunächst lokale Ziele aus und zeigt sie als vorläufige Ergebnisse
während des sichtbaren Fortschritts. Anschließend folgt genau eine serielle
Provider-Suche je bekannter, lokal kaufbarer Commodity. Es wird nicht der gesamte
Commodity-Master durchsucht. Unbekannte zukünftige Waren werden ohne Fehler lokal
bewertet; eine fehlende Spansh-Unterstützung wird als unvollständige Suche angezeigt.
Lokale Treffer allein überspringen keine Community-Suche, damit neuere oder bessere
Ziele nicht systematisch fehlen.

Verkaufen, Einkaufen, Empfehlungen und „Hier verkaufen“ teilen dieselbe Provider-Instanz. Damit gelten
weiter deren Lock, mindestens eine Sekunde Requestabstand, begrenzte Seitenanzahl,
Abbruchmechanismus und fünfminütiger RAM-Cache. Es gibt keine neue HTTP-Schicht und
keine parallelen Commodity-Requests. Die Suchmenge beim Provider ist 1, damit kleine
Nachfragen nicht vor der möglichen Mengenberechnung verloren gehen. Pro Commodity
werden höchstens 100 Provider-Treffer berücksichtigt. Beste bedeutet deshalb immer
„bestes geprüftes Ziel innerhalb der begrenzten Suche“, nicht globales Optimum.

Die bestehende Spansh-Suche liefert bereits serverseitig gefilterte Ankaufangebote;
unsichtbare, nicht gelieferte Community-Marktstände können nicht verglichen werden.
Bei Suchbegrenzung, unbekannten Waren oder Teilfehlern kennzeichnet die Oberfläche
das Gesamtergebnis ausdrücklich als unvollständig. Erfolgreiche Teilabfragen und
lokale Ziele bleiben nutzbar. Rate-Limit, Systemfehler und Verbindungsfehler beenden
die weitere Requestfolge; andere Commodity-Fehler verhindern nicht die restlichen
Abfragen. Bestehende Provider-Retries bleiben begrenzt. Abbrechen verwirft Ergebnisse
und kann auf eine laufende Netzwerkantwort warten.

System-, Stations-, Commander-, Schiffs- und Marktwechsel invalidieren Ergebnisse.
Normale Empfehlungen bleiben bei Teilkäufen mit weiter verfügbarem Frachtraum
bestehen; voller oder unbekannter Frachtraum invalidiert sie. „Hier verkaufen“
invalidiert bereits bei geänderter freier Kapazität oder gewählter Menge. Reiterwechsel bricht ab. Es startet keine
automatische neue Suche. Vor Annahme eines Worker-Ergebnisses wird der aktuelle
Kontext erneut geprüft. Es gibt keinen neuen Timer. Bei vollständig inaktiver UI
wird das Alter erst mit dem nächsten normalen Aktualisierungsereignis neu angezeigt.

## Persistenz und Grenzen

Kein neues DB-Schema, keine Migration, keine Speicherung von Empfehlungen und keine
dauerhafte Speicherung von Spansh-Marktpreisen. Der Phase-6-Cache bleibt unverändert.
Die eigenen Daten werden weiterhin allein durch dessen normale API und Observer
verwaltet. Quelle und Alter sind für jeden Treffer sichtbar. Preise, Supply und
Demand können sich bis zur Ankunft ändern; Empfehlungen sind keine Preis- oder
Bestandsgarantie. Verfügbare Credits, Handelssteuern, Zugangsberechtigungen und
Reisekosten sind keine zusätzlichen Optimierungsgrößen in Phase 7.

## Laufdiagnose (nur Arbeitsspeicher)

`RecommendationsView.current_run` hält eine unabhängige Momentaufnahme des laufenden
Workers, `last_run` den zuletzt abgeschlossenen Lauf einschließlich Abbruch. Beim
nächsten Abschluss wird dieser ersetzt. Es gibt keine Diagnosehistorie, neue Datei,
Logausgabe oder Datenbank. Nach Beenden des Helpers sind diese Diagnosen weg.
Die Diagnose enthält Commodity-ID/Symbol, keine Preise, Commander/FID, Stationslisten,
Response-Bodies oder URLs. Start/Ende sind UTC; die Dauer verwendet eine monotone Uhr.

Der kompakte Status zeigt während der Suche geprüfte/geplante Waren und nach dem
Abschluss die geprüfte Anzahl. Ein unvollständiger Lauf nennt zusätzlich einen
verständlichen Grund und kennzeichnet die Ergebnisse weiterhin als Teilergebnisse.
Der Status-Tooltip nennt lokale Warenschritte, begonnene/abgeschlossene Spansh-Schritte,
HTTP-Anfragen, Cache-Treffer und das erste betroffene Commodity-Symbol. Technische
Providerstatus bleiben im strukturierten RAM-Modell, nicht in normalen Fehlermeldungen.

Zählerdefinitionen:

- `planned_commodities`: lokal kaufbare Waren; `checked_commodities`: abgeschlossene
  Commodity-Versuche einschließlich fehlgeschlagener Versuche. `successful_commodities`
  zählt vollständige Schritte mit OK/NO_RESULTS ohne Truncation; `failed_commodities`
  Fehler; `skipped_commodities` noch nicht abgeschlossene Schritte. Eine begrenzte
  erfolgreiche Antwort ist geprüft, aber nicht vollständig erfolgreich.
- `local_target_markets`: gültige lokale Zielmärkte ohne Einkaufsmarkt; eine aktive
  feste Zielbeschränkung wird berücksichtigt.
  `local_combinations_checked`: geprüfte Commodity/Ziel-Paare. `local_candidates`:
  daraus nach Filtern/Marge/Menge mögliche Geschäfte vor dem Quellen-Merge.
  `local_recommendations`: zuletzt ausgegebene Empfehlungen mit lokalem Ziel.
  Die lokale Vorschau kann bereits alle Waren geprüft haben, während Spansh noch
  bei 0 steht. Wiederholtes Berechnen der Vorschau zählt dieselben Paare nicht erneut.
- `spansh_commodities_started/completed/failed` unterscheiden Beginn, Rückkehr und
  Fehler der Provideraufrufe. Abgeschlossen bedeutet nicht zwingend erfolgreich.
  Jeder Schritt enthält Status, Truncation, Seitenversuche/erfolgreiche Seiten,
  konfigurierte Grenzen, tatsächlich erreichte Grenzen und Transportdiagnose.
- `http_requests` zählt wirkliche Transportaufrufe, einschließlich Metadaten und
  Wiederholungen. Ein RAM-Treffer zählt nur unter `cache_hits`. `retries`, letzter
  verfügbarer HTTP-Status und `Retry-After` werden getrennt erfasst. Die Zähler
  gehören zum jeweiligen Provideraufruf, auch wenn andere Handelsreiter denselben
  Provider verwenden. Ein bereits aktives Rate-Limit kann einen Providerstatus
  liefern, ohne einen weiteren HTTP-Aufruf auszulösen.
- Merge-Zähler zählen Commodity/MarketID-Vergleiche zwischen den beiden Quellen:
  Überschneidungen, jüngere lokale Daten, jüngere Spansh-Daten, Zeitgleichheit sowie
  Merge-Ausnahmen. Ein normaler Merge setzt niemals `partial`.

`partial_reason` benennt den ersten konkreten Grund; `reasons` und die jeweiligen
Warenschritte erhalten auch weitere Gründe. Unterschieden werden Netzwerk, Timeout,
HTTP, Rate-Limit, ungültige Antwort, unbekanntes System, allgemeine Truncation,
Seitenlimit, Ergebnislimit, Commodity-Fehler und sonstige Fehler. Ein aus dem
Provider-RAM-Cache übernommenes begrenztes Ergebnis bleibt als begrenzt erkennbar,
verursacht aber keine aktuellen Seiten-/HTTP-Aufrufe. Gründe werden aus strukturierten
Statuswerten und Grenzflags abgeleitet, nicht aus Fehlermeldungstexten geraten.

Benutzerabbruch/Reiterwechsel (`CANCELLED`) und Kontextänderungen (`CONTEXT_CHANGED`)
haben Vorrang vor Providergründen; bereits festgestellte Gründe bleiben in `reasons`.
Auch ein erst nach Worker-Abschluss verworfenes, verspätetes Ergebnis erhält den
zutreffenden Abbruchgrund. Es entsteht keine irreführende Providerfehlermeldung.

Diese Instrumentierung ändert weder Suchreihenfolge und Abbruchstellen noch
Requestabstand, Timeout, Retry, Grenzen, Cache, Quellen-Merge, Gewinn-/Mengenformel
oder Auswahl und Sortierung der Ergebnisse. Sie startet keine zusätzliche Suche.

### Diagnose kopieren

Der dezente Button „Diagnose kopieren“ im Statusbereich wird verfügbar, sobald
`last_run` einen abgeschlossenen Lauf mit Endzeit enthält, auch bei Teilfehlern
oder Abbruch. Während einer neuen Suche kopiert er weiterhin den letzten
abgeschlossenen Lauf. Erst dessen Nachfolger ersetzt ihn wie bisher.

Nur ein Klick schreibt Klartext in die Qt-Systemzwischenablage: feste englische
`key=value`-Felder für Zeiten, Lauf-/Provider-/Merge-Zähler, Gründe und technische
Commodity-Identitäten. Beim ersten betroffenen Schritt werden vorhandene
Providerstatus und Seiten-/Ergebnisgrenzen ergänzt. Das Format liest gespeicherte
Werte; es aggregiert den Lauf nicht erneut und ruft keinen Cache oder Provider auf.
Eine separate Bestätigung verschwindet nach drei Sekunden, ohne Fortschritt,
Fehlermeldung oder Ergebnistabelle zu ersetzen.

Die Ausgabe verwendet eine ausdrückliche Feldauswahl. FIDs, Commander-/Schiffsnamen,
Pfade, Preise, Cargo-Inhalte, URLs und Response-Bodies werden nicht kopiert.
Unerwartete freie Inhalte in Commodity-Symbol oder Retry-After werden durch einen
neutralen technischen Platzhalter ersetzt. Die Funktion schreibt keine Datei,
keine Datenbank/QSettings und keine Diagnosehistorie; sie überträgt nichts über das
Netz. Der technische Text kann anschließend bewusst für Support eingefügt werden.

## Nur eigene Marktdaten und aktueller Marktstatus

Die Checkbox „Nur eigene Marktdaten“ steht vor dem Carrierfilter und ist zunächst
ausgeschaltet. Ausgeschaltet bleibt die kombinierte Suche unverändert. Eingeschaltet
wertet der Worker ausschließlich gültige `local_elite`-Ziele gemäß der bestehenden
Commander-übergreifenden Marktfreigabe aus.
Er ruft keinen Community-Provider auf, auch nicht für unbekannte zukünftige Waren.
Die Einstellung lebt nur in der bestehenden View-Instanz, ohne QSettings.

Der Einkaufsmarkt bleibt in beiden Modi ausschließlich der gültige eigene Markt
am aktuellen Standort. Andere eigene MarketIDs können Ziele sein. Radius,
Zieldatenalter, Mindestgewinn und die bisherigen Metadatenfilter gelten weiter;
unbekannte Entfernungen oder für einen aktiven Filter fehlende Stationsangaben
werden nicht geraten. Für eigene Ziele gilt das eingestellte maximale
Marktdatenalter. Gewinn und Menge
werden mit denselben Funktionen wie im kombinierten Modus berechnet.

Im lokalen Modus bedeutet ein abgeschlossener Warenschritt vollständig lokal
geprüft. `local_only=true` wird im bestehenden RAM-Datensatz und kopierten Text
angegeben. Spansh-Schritte, HTTP-Requests und Cache-Hits bleiben null. Bewusst
nicht abgefragte Community-Daten verursachen weder Fehler noch `partial` oder
übersprungene Warenschritte. Fortschritt und Abbruch verwenden die vorhandenen
Signale, ohne Wartezeiten. Ein passender lokaler Hinweis ersetzt die allgemeine
Community-Erklärung.

Neben der aktuellen Marktangabe zeigt ein von Qt gezeichneter grüner Kreis mit
weißem Haken „Eingelesen“, wenn der normale Cachezugriff einen gültigen eigenen
Marktstand genau der bestätigten aktuellen MarketID/Station liefert; der
Live-Kontext muss zur aktiven FID passen. Der Text
und Tooltip ergänzen die Farbe; das bisherige Marktalter bleibt sichtbar.
Fehlt ein solcher Stand, zeigt die Ansicht „Warenmarkt öffnen“. Im Flug ohne
bestätigten Dock-Kontext wird kein positiver Status für die letzte Station gezeigt.

Wenn ein zuvor in dieser Ansicht bekannter aktueller Snapshot beim normalen
Cachezugriff ungültig wird, erscheint „Marktstand veraltet“. Die Gültigkeitsprüfung
bleibt allein beim Cache. Die Ansicht merkt sich dafür nur die Identität des
aktuellen veralteten Markts, bis ein neuer Stand oder anderer Kontext vorliegt.
Es entsteht keine Snapshot-Historie. Bereits vor dem Öffnen der Ansicht physisch
entfernte Stände sind nicht von fehlenden Beobachtungen unterscheidbar; dann lautet
der Status „Warenmarkt öffnen“. Beide Zustände erlauben keine Empfehlungssuche.

Observer-/Cache-, Stations-, Commander- und State-Signale aktualisieren den Status,
ohne neuen Poller. Die erneute Aufnahme derselben MarketID aktualisiert wie bisher
Inhalt und Alter, ohne zusätzliche Station oder Historienzeile. Der Status betrifft
den Einkaufsmarkt; die Checkbox betrifft ausschließlich die Auswahl der Zielquellen.

## Gemerkte Handelsziele

Mehrere Treffer lassen sich mit den Checkboxen unabhängig voneinander merken.
Kaufen, Verkaufen und Empfehlungen verwenden den gemeinsamen sitzungslokalen
Merkzettel und identifizieren ihre Stationseinträge über System- und Stationsnamen.
Die Einträge zeigen System, Station, bekannte Körperinformation und Landeplatz.
Sie sind unabhängig von der aktuellen Ergebnistabelle: Neusuche, Kauf,
Frachtraumänderung, Reise oder Marktaktualisierung löschen sie nicht generell.
Beim Wiederanzeigen passender Treffer wird die Markierung wiederhergestellt.

Einträge lassen sich über die Markierung oder den Entfernen-Knopf löschen.
Ein bestätigter Commanderwechsel leert den Merkzettel; eine vorübergehend unbekannte
FID tut dies nicht. Die Einträge bleiben ausschließlich im RAM der Ansicht und
überleben keinen Helper-Neustart. „System kopieren“ kopiert das System der
gemerkten Station, bei Empfehlungen also das Verkaufsziel.

## Hier verkaufen: Bezugsquellen für den aktuellen Markt

Der Reiter **Hier verkaufen** verwendet den aktuellen bestätigten lokalen Markt
als festes Verkaufsziel. **Bezugsquellen suchen** betrachtet automatisch alle dort
nachgefragten Waren mit `commander_sell_price > 0` und `demand > 0`; eine einzelne
Warenauswahl ist nicht nötig. Geeignete Bezugsquellen benötigen
`commander_buy_price > 0` und `supply > 0`. Der Zielmarkt selbst ist ausgeschlossen.

- Gewinn/t = Verkaufspreis am festen Ziel − Einkaufspreis an der Quelle.
- Handelsmenge = Minimum aus gewählter Menge, freiem Frachtraum,
  Angebot an der Quelle und Nachfrage am Ziel.
- Gesamtgewinn = Handelsmenge × Gewinn/t.

Nur positiver Gewinn und die eingestellte Mindestmarge sind zulässig.
Pro Ware wird eine beste Quelle nach Gesamtgewinn und den bestehenden Tie-Breakern
gewählt. Die Treffer sind Alternativen, kein addierbarer gemeinsamer Frachtraumplan.

Mindestmarge, Menge/Frachtraum, Radius, maximales Datenalter, Landeplatz,
Fleet Carrier, maximaler Anflug und „Nur eigene Marktdaten“ verwenden die vorhandene
Such-, Filter- und Freshness-Logik. Lokale Null-/Leerstände können ältere
Communityangebote verdrängen. Fehlender oder veralteter Zielmarkt verhindert eine
gültige Suche; Kontextwechsel invalidieren laufende Ergebnisse. Abbruch,
Fortschritt und die Kennzeichnung von Teilfehlern bleiben verfügbar.

Die Tabelle enthält Ware, tatsächliche Menge, Quellsystem/-station, Entfernung,
Einkaufs- und Zielverkaufspreis, Gewinn/t, Gesamtgewinn, Quellangebot, Zielnachfrage,
Anflug, Landeplatz, Datenalter, Datenquelle und den bekannten Körper der Bezugsstation.
Die Körperanzeige verwendet `known_station_body()`; unbekannte Werte bleiben „–“.

Beim Merken bleibt die vollständige Route **Bezugsquelle → festes Verkaufsziel**
mit Ware, Preisen, möglicher Menge und den zugehörigen Marktdaten erhalten.
Die Routenidentität berücksichtigt auch MarketIDs und bekannte Systemadressen.
Neue Ergebnisse überschreiben den gespeicherten Preis-/Mengenstand nicht.
Der bekannte Körpername wird beim Merken festgehalten; die Ergebnistabelle
ermittelt ihn beim erneuten Anzeigen aus den vorhandenen Stationsdaten.
„System kopieren“ kopiert hier stets das **Quellsystem**.
Die Aktion „Hinweg suchen“ am jeweiligen Merkeintrag ist im Abschnitt
„Hinweg zu einer gemerkten Bezugsquelle“ beschrieben; ihr Qt-Tooltip erklärt
den Hin- und Rückweg.

## Vom Benutzer bestätigte Live-Abnahmen

Die folgenden Ergebnisse wurden vom Benutzer aus realen Elite-Läufen bestätigt;
sie sind keine Behauptung einer erneut durchgeführten Onlineprüfung:

- Vollständige Empfehlungssuche: 52 von 52 Waren erfolgreich. Spansh meldete
  53 HTTP-Requests, 0 Fehler, HTTP 200 und `partial=false`. Eigene Zielmärkte und
  Spansh wurden gemeinsam verwendet.
- Die Laufdiagnose grenzte den live gefundenen PadSize-Fehler ein:
  `required_pad` war ein String statt eines `PadSize`-Enums. Nach der Korrektur
  der Enum-Übergabe aus der Empfehlungen-UI lief die vollständige Spansh-Suche.
  Die Provider-Validierung wurde dafür nicht gelockert.
- Reale Handelsflüge bestätigten mindestens zwei Gewinnberechnungen praktisch:
  Berechneter möglicher Gewinn und tatsächlicher Elite-Profit stimmten in einem
  Fall exakt und in einem weiteren bis auf wenige Credits überein.
- Fortschrittsanzeige und Diagnose wurden sichtbar abgenommen. Der Status
  „Eingelesen“ für den aktuellen gültigen `local_elite`-Markt wurde implementiert
  und geprüft. Der gemerkte Handelsflug wurde von der Ergebnistabelle getrennt.
- „Nur eigene Marktdaten“ ist für lokalen Handel vorgesehen und wurde offline
  mit 0 Provider-/HTTP-Aufrufen geprüft. Vollständige lokale Suchen haben
  ausschließlich `local_elite`-Ziele, 0 Cache-Hits, `partial=false` und
  `partial_reason=NONE`.

Diese Dokumentation enthält keine persönlichen Laufzeitdaten, Commanderangaben
oder Markt-Snapshots. Die Regressionstests verwenden synthetische Marktdaten;
reale Handelsdaten und Diagnosedumps werden nicht als Fixtures übernommen.

## Hinweg zu einer gemerkten Bezugsquelle

„Hier verkaufen“ bietet im bestehenden Merkzettel pro Route „Hinweg suchen“.
Die Aktion übernimmt die gespeicherte **Bezugsquelle** als festes Verkaufsziel
in „Empfehlungen“, wechselt den Reiter und startet die Suche. Der aktuelle
bestätigte lokale Markt bleibt Einkaufsquelle. Alle dort kaufbaren Waren werden
bewertet; die Ware des gemerkten Rückwegs beschränkt die Hinwegsuche nicht.

Die Zielanzeige enthält die ausgewählte Station, das System, bekannte Körper-
und Padinformationen sowie den zugehörigen gemerkten Rückweg. „Nur dieses Ziel
verwenden“ lässt sich ausschalten, ohne Filterwerte zu verändern. Danach läuft
die nächste Suche wieder wie die normale Empfehlungen-Suche. Auch ein festes
Ziel muss Radius-, Alters-, Pad-, Carrier-, Anflug-, local_only- und
Wirtschaftlichkeitsfilter erfüllen. Unbekannte Metadaten werden nicht erfunden.

Die bestehende RecommendationStoreSession schränkt Kandidaten bereits über
`market_ids` und gegebenenfalls `system_address` ein. Communityabfragen verwenden
den belegten exakten Spansh-Filter (siehe market-data-provider.md). Lokale
Null-/Leerstände bleiben Freshness-Evidenz vor der wirtschaftlichen Bewertung.
Im Mischbetrieb können neuere Communitydaten weiterhin gewinnen; local_only
verhindert Communityabfragen vollständig.

Der Rückweg bleibt unverändert im gemeinsamen, sitzungslokalen Merkzettel.
Routenidentitäten enthalten zusätzlich zu Namen/Ware auch die vorhandenen
MarketIDs/Systemadressen, damit gleichnamige Stationen nicht zusammenfallen.
Entfernen des ausgewählten Merkeintrags löscht dessen abgeleitete Zielauswahl.
Zielwechsel, Ausschalten und Kontextwechsel invalidieren laufende Ergebnisse;
ein bestätigter Commanderwechsel löscht die Auswahl. Reisebewegungen behalten
die Auswahl, benötigen für eine neue Suche aber einen bestätigten aktuellen
Markt. Fehlende Zielmarktdaten führen niemals zu einer Ersatzstation.
