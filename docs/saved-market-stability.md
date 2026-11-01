# Stabile Marktansicht und exklusive Warenfilter

Stand: 31.10.2026. Freigegebene Vorbereitung für 3.9.24 auf dem unveränderten
Versionsstand 3.9.23, HEAD vor Beginn `92799cc`. Keine Veröffentlichung.

## Umfang und geänderte Dateien

- `cmdrhelper/ui/saved_markets_view.py`: lokale Referenzwiederverwendung in
  `showEvent`, `reload`, `_start_reference`, `change_reference`; Aktualisierung
  bestehender Marktzeilen und Erhalt der Ansicht in `_render_markets` und
  `filter_markets`; Radiobutton-Gruppe und `_goods_mode_changed`; Vergleich des
  wirksamen Warenfilters in `filter_goods`.
- `cmdrhelper/i18n/{de,en,el,es,fi,fr,it,nl,no,pl,sv,tr}.py`: Alle-Waren-Modus,
  Referenz-Wartehinweis und eindeutige Beschriftung des Schiffs-Frachtfilters.
- `tests/test_saved_markets.py`, `tests/test_saved_market_cargo_filter.py`:
  bestehende Kombinations-/Abwahltests gezielt auf die exklusive Auswahl
  umgestellt, Filterinvalidierung und UI-Verhalten zusätzlich abgesichert.
- `tests/test_saved_market_stability.py`: Referenz-, Modell- und Ansichtstests.
- `tools/benchmark_saved_market_stability.py`: reproduzierbare isolierte Messung.
- Dieser Bericht und `tools/data/saved-market-stability-x11.json`: Ergebnisse.

Frachtberechnung, Cargo-Snapshots, Mining, Carrier-Verwaltung, Datenbankschema,
Version, Release-Metadaten und technische Fußzeile wurden nicht geändert.

## Referenz und Marktliste

Die Seite merkt sich lokal genau einen Referenzschlüssel aus Datenbankpfad und
normalisiertem Systemnamen. Wiederanzeigen derselben sauberen Seite verwendet
bereits gelesene Koordinaten und startet keine Referenz- oder Markt-SQL-Abfrage.
Die Darstellung des Datenalters wird weiterhin aktualisiert.

Ein anderer Referenzname oder eine andere Koordinaten-Datenbank verwirft die
alten Referenzkoordinaten sofort. Während der asynchronen Auflösung zeigt die
Seite einen übersetzten Wartehinweis und unbekannte Entfernungen. Bei aktivem
Radius sind dann zu Recht keine unbestätigten Treffer sichtbar. Ein unbekanntes
oder fehlgeschlagenes Ergebnis zeigt weiterhin den Hinweis auf fehlende eindeutige
Koordinaten. »Übernehmen« kann eine erfolglose Auflösung erneut versuchen.

Explizites Aktualisieren, eine Marktänderungsmeldung oder ein abgeschlossener
Datenbankimport laden Marktmetadaten und Referenz erneut. Für denselben
Referenzschlüssel bleiben bekannte Koordinaten während dieser Prüfung verfügbar;
ein anschließend unbekanntes/fehlgeschlagenes Ergebnis entfernt sie. Ein Import
bei versteckter Seite setzt das vorhandene Dirty-Flag. Reine Inventarsignale
starten diese Leser nicht. Änderungen an Datenbankinhalten ohne die vorhandenen
Benachrichtigungen werden weiterhin durch explizites Aktualisieren übernommen.

Generationen und Abbruchereignisse bleiben erhalten. Ein verspätetes Ergebnis
für ein vorheriges Bezugssystem darf die aktuelle Referenz nicht überschreiben.

Solange die Folge der MarketIDs gleich bleibt, werden geänderte Zeilen mit
`dataChanged` aktualisiert. Ein vollständiger Modell-Reset erfolgt nur bei
geänderter Zeilenstruktur. Filter und Detailanzeige verwenden weiterhin dieselben
Marktköpfe und Commodity-Snapshots. Auswahl wird nach MarketID wiederhergestellt;
vertikale und horizontale Scrollposition werden gesichert und wiederhergestellt.
Die Proxy-Sortierung bleibt bestehen. Bei tatsächlich entfallenen/ausgefilterten
Zeilen kann Qt eine Scrollposition nur auf den verbleibenden Bereich begrenzen.

## Warenfilter und Bedienung

Drei Radio-Buttons in einer exklusiven `QButtonGroup`:

1. Alle Waren (Standard)
2. Nur Bergbaurohstoffe
3. Nur Waren im Schiffs-Frachtraum

Die Gruppe steht kompakt unter der unabhängigen Warensuche, mit geringem
vertikalem Abstand. Dadurch passen auch die längeren Übersetzungen in die rechte
Hälfte der Marktansicht. Nur das Einschalten des neuen Modus ruft den Filter auf;
das gleichzeitige Ausschalten des alten erzeugt keinen zweiten Durchlauf.

Bei aktiviertem Frachtmodus wird `_cargo_filter()` bei jedem relevanten Signal
weiterhin aufgerufen. Es verwendet unverändert `current_ship_inventory()` und
seine Commander-/FID-/Journal-/Schiffs-/Bestätigungsprüfungen. Erst danach werden
Suchtext, ausgewählter Modus, positive Commodity-IDs und Hinweisstatus mit dem
vorherigen wirksamen Zustand verglichen. Identische Zustände benötigen kein
`invalidateFilter()`. Mengenänderungen ohne geänderte Warenarten fallen darunter.

`None` (inaktiver/pausierter Frachtfilter) und die leere Menge (bestätigt leer)
bleiben verschieden. Unbekannte Commodity-Zuordnung wird weiterhin nicht geraten.
SRV und Carrier werden nicht als Schiffsbestand verwendet. Ein anderer Kontext
wird auch dann neu validiert, wenn daraus dieselbe effektive Warenmenge entsteht.
Ohne Frachtmodus führt `_cargo_changed()` keine Filterarbeit aus.

Der Warenzähler wird auch nach einem Wechsel des Markt-Snapshots aktualisiert,
wenn der Filterzustand selbst gleich bleibt. Das Source-Model informiert den
Proxy beim Laden neuer Waren unabhängig vom Filtervergleich.

## Vorher-/Nachher-Messung

Echtes X11 (`xcb`, Display `:0`), jeweils eigener Prozess, dieselben temporären
Datenbanken mit 110 Märkten, festes Bezugsdatum und drei kanonische Waren für die
Frachtfiltermessung. Keine produktiven Journale oder Einstellungen. Vorher lädt
das Messskript die vor der Bearbeitung gesicherte Marktseiten-Datei; nachher die
Arbeitskopie. Zähler werden erst nach Initialisierung und abgeschlossenen Reads
aktiviert. SQLite-SELECTs werden über die neu geöffneten Verbindungen verfolgt.

Rohdaten: [saved-market-stability-x11.json](https://github.com/Faber38/CMDRHelper/blob/v3.9.24/tools/data/saved-market-stability-x11.json).
Zahlenpaare bedeuten vorher → nachher; fehlende Arbeit zählt als null.

| Szenario | Marktresets | Waren-Neufilterungen | Filterprüfungen | SELECTs |
|---|---:|---:|---:|---:|
| Unverändert geöffnet | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| 5 identische Zustandssignale | 0 → 0 | 5 → 0 | 5 → 5 | 0 → 0 |
| Schiff: Menge geändert, gleiche Warenarten | 0 → 0 | 1 → 0 | 1 → 1 | 0 → 0 |
| Schiff: neue Warenart | 0 → 0 | 1 → 1 | 1 → 1 | 0 → 0 |
| Schiff: Warenart entfernt | 0 → 0 | 1 → 1 | 1 → 1 | 0 → 0 |
| Schiff → SRV, Filter pausiert | 0 → 0 | 1 → 1 | 1 → 1 | 0 → 0 |
| Weitere SRV-Mengenänderung | 0 → 0 | 1 → 0 | 1 → 1 | 0 → 0 |
| SRV-Mengenänderung, Frachtfilter aus | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| Wechsel zu Bergbau / zurück zu alle, jeweils | 0 → 0 | 1 → 1 | 1 → 1 | 0 → 0 |
| Wiederanzeigen, unveränderte Referenz, Radius aktiv | 3 → 0 | 1 → 0 | 1 → 1 | 1 → 0 |
| Marktänderungssignal bei identischen Marktköpfen | 3 → 0 | 1 → 0 | 1 → 1 | 12 → 12 |

Beim Wiederanzeigen sinkt die Zahl der Renderaufrufe von drei auf einen. Die
kleinste beobachtete Trefferzahl steigt von **0 auf 110**. Bei der expliziten
Marktänderungsmeldung ebenfalls **0 → 110**. Die gespeicherte Auswahl und
Sortierspalte bleiben gleich. Die Scrollposition beim Marktänderungssignal war
vorher 25 → 0, nachher 25 → 25. Die explizite Hide-/Show-Aktion erzeugt natürlich
je ein Hide-/Show-Ereignis; gemessen wird das zusätzliche Leeren der Inhalte.

Die kumulierte Zeit innerhalb `_render_markets()` beim Wiederanzeigen beträgt
5,083 → 2,346 ms, beim Marktänderungssignal 5,825 → 4,115 ms. Gesamtdauern inklusive
Qt-Ereignisverarbeitung: 131,589 → 53,487 ms bzw. 102,002 → 96,267 ms.
Das sind instrumentierte Einzelmessungen, keine statistisch abgesicherten
Latenzversprechen. Der gesicherte Befund sind weniger Resets, SQL-Abfragen und
Neufilterungen sowie das Ausbleiben des vorübergehend leeren Radius-Ergebnisses.

Die zwölf SELECTs beim Marktänderungssignal bleiben absichtlich erhalten: eine
Meldung über Marktdatenänderungen darf weiterhin die aktuellen Header, Details
und Referenzdaten prüfen. Es wurde keine globale Cache-Verwaltung eingeführt.

Reproduktion aus dem Projektverzeichnis:

```sh
# Baseline aus dem unveränderten Ausgangscommit, falls /tmp nicht mehr existiert:
git show 92799cc:cmdrhelper/ui/saved_markets_view.py > /tmp/saved_markets_view_before.py
QT_QPA_PLATFORM=xcb PYTHONDONTWRITEBYTECODE=1 venv/bin/python tools/benchmark_saved_market_stability.py --baseline-module /tmp/saved_markets_view_before.py --output /tmp/saved-market-before.json
QT_QPA_PLATFORM=xcb PYTHONDONTWRITEBYTECODE=1 venv/bin/python tools/benchmark_saved_market_stability.py --output /tmp/saved-market-after.json
```

## Regressionen und Grenzen

Breite gezielte X11-Suite: **187 Tests bestanden in 195,756 Sekunden**, Qt 6.11.2.
Keine Fehler oder übersprungenen Tests. Ein abschließender X11-Nachlauf der
zuletzt erweiterten Scroll- und Layout-Assertions bestand ebenfalls:
**7 Tests in 3,832 Sekunden** (Teilmenge, keine zusätzlichen unabhängigen Fälle).
Die Suite umfasst:

```sh
QT_QPA_PLATFORM=xcb PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. venv/bin/python -m unittest test_saved_market_stability test_saved_markets test_saved_market_cargo_filter test_ship_cargo test_ship_inventory test_cargo_live test_inventory_invalidation test_source_manager test_ship_inventory_trade test_trade_view test_i18n_checker
```

Der bestehende Test für zwölf Sprachen, zwei Themes und zwei Schriftgrößen der
gesamten Handelsansicht benötigt im gemeinsamen X11-Lauf besonders lange; auch
er hat bestanden. Zusätzlich bestehen `tools/check_i18n.py` (2348 Referenz-Keys,
zwölf Sprachen, gleiche Platzhalter, keine doppelten Keys), die Syntaxprüfung der
17 geänderten/neuen Python-Dateien und `git diff --check`.

Die gezielte Suite prüft Referenzwiederverwendung mit aktivem Radius, ausbleibendes
Leeren, geänderte/fehlende/fehlerhafte Referenzen, Import und Wiederherstellung,
späte Worker-Ergebnisse, andere Koordinaten-Datenbank, Datenalter, Auswahl,
Scrollposition und Sortierung einschließlich echter neuer Märkte.

Die Frachttests prüfen Mengenänderungen, neue/entfernte Warenarten, bestätigt leer,
unbekannt, veraltet, widersprüchlichen Status, Commander/FID, Journalquelle,
Schiffswechsel, SRV, Carrier, unveränderte wiederholte Signale und vollständige
Validierung trotz übersprungener Neufilterung. Hinzu kommen alle drei Modi,
unabhängige Suche, Tastaturbedienung und Layout in zwölf Sprachen und zwei Themes.

Keine Prüfung mit einem laufenden Elite-Client oder NANJANs produktiven Daten,
keine Windows-Liveprüfung und keine vollständige projektweite Testsuite. Die
ursprüngliche Kette Mining → Wiederanzeigen war bereits in der Analyse nicht
reproduzierbar. Diese Änderung behebt den nachgewiesenen Radius-Leerzustand und
die unnötigen Waren-Neufilterungen, ohne eine unbekannte weitere Ursache zu
behaupten. Qt meldet für das vorhandene `invalidateFilter()` eine DeprecationWarning;
die API bleibt wegen der unterstützten Qt-Versionen unverändert.

## Bestandsschutz

Git vorher: `## main...origin/main`, sauber. Sämtliche Änderungen dieses Auftrags
bleiben uncommittet. `github.sh` wurde nicht ausgeführt. Kein Commit, Tag, Push
oder Release; Version weiterhin 3.9.23. Test- und Messdaten sind synthetisch.

Git nachher:

```text
## main...origin/main
 M cmdrhelper/i18n/de.py
 M cmdrhelper/i18n/el.py
 M cmdrhelper/i18n/en.py
 M cmdrhelper/i18n/es.py
 M cmdrhelper/i18n/fi.py
 M cmdrhelper/i18n/fr.py
 M cmdrhelper/i18n/it.py
 M cmdrhelper/i18n/nl.py
 M cmdrhelper/i18n/no.py
 M cmdrhelper/i18n/pl.py
 M cmdrhelper/i18n/sv.py
 M cmdrhelper/i18n/tr.py
 M cmdrhelper/ui/saved_markets_view.py
 M tests/test_saved_market_cargo_filter.py
 M tests/test_saved_markets.py
?? docs/saved-market-stability-x11.json
?? docs/saved-market-stability.md
?? tests/test_saved_market_stability.py
?? tools/benchmark_saved_market_stability.py
```
