# Hierarchische Systemanalyse – v3.3, fachliche API Version 1

Die bisherige Sprungtipp-Seite heißt in v3.3 **Analyse**. Sie bietet die
hierarchische **Systemanalyse** und die weiterhin vorhandenen **Erfahrungsdaten**.
Die historische Auswertung bleibt erhalten; ihr SQL-Gruppierungsfeld ist nun
eindeutig als `b.system_address` qualifiziert. API der Systemanalyse:

```python
from cmdrhelper.jump_tip import HierarchicalJumpTip, evaluate_observations

analyzer = HierarchicalJumpTip(database)  # aktiver Commander
result = analyzer.evaluate("Plio Aip KN-B d13-201")
# Für mehrere Ziele dieselbe Beobachtungsbasis verwenden:
rows = analyzer.observations()
result = evaluate_observations("Plio Aip KN-B d13-227", rows)
```

## Namen und Identität

`ScoreAnalyzer.parse_system_name` ergänzt die bisherigen lexikalischen Felder
`number` und `suffix` um `boxel_number`, `system_index`, `family_key`.
`Plio Aip KN-B d13-201` ergibt Boxel 13, Index 201 und Familie
`Plio Aip KN-B d13`. `Floarps PI-B e2` bedeutet Boxel 0 und Index 2.
Die bisherigen Rückgabefelder bleiben für den alten Tipp kompatibel.
Gruppenvergleiche ignorieren Groß-/Kleinschreibung. Unpassende Namen ergeben
`ok=False, reason=unsupported_name` und keinen schwachen Score.

Der Index geht nirgendwo in die Bewertung ein. Auch bereits besuchte Ziele
werden nicht automatisch aus ihrer Gruppe entfernt: bei identischer Historie
erhalten alle Mitglieder einer Familie dieselbe Schätzung. Für Rücktests gibt
es `excluded_system_addresses`; bei Vergleichen denselben Ausschluss für alle
Ziele verwenden. Historische Selbstbeobachtung ist keine Vorhersagevalidierung.

## Beobachtungsqualität

- `complete`: `commander_systems.all_bodies_found` ist gesetzt.
- `partial`: ohne diesen Nachweis, aber FSS oder Körperdaten vorhanden.
- `unknown`: weder FSS noch astronomische Körperdaten vorhanden.

Nur `complete` kann qualifiziert sein. Zusätzlich müssen echte persönliche
Körperdaten vorhanden sein, deren Zahl mit der positiven `body_count_seen`
übereinstimmt. Alle müssen `scanned` und einen bekannten Stern-/Planetentyp haben.
Die Zahl allein beweist niemals Vollständigkeit. Abweichungen erzeugen
`body_count_unverified_or_inconsistent`; fehlende Details eine weitere Ursache.
Da gespeicherte Gesamtzahlen historisch aufgebläht sein können, ist das bewusst
konservativ: auch manche tatsächlich vollständigen Systeme bleiben ausgeschlossen.
Es wird keine Journal-Reparatur oder Migration ausgelöst.

Belt Cluster (bestehende Erkennung), Ring-Einträge und Baryzentren sind keine
normalen Körper. Sterne, Planeten und Monde zählen. Insbesondere reicht der
historische DB-Typ `Planet` nicht aus, Cluster/Ringe auszuschließen.
`partial` und `unknown` gehen weder als negative noch als positive Beobachtung
in diese Version ein. Erkannte Funde bleiben in `observations()` nachvollziehbar.

## Treffer und Hierarchie

Wertvoll bedeutet WW, ELW, AW oder terraformierbarer Körper wie bisher;
terraformierbare HMC/WW werden zusätzlich separat gezählt. Diese Anzahlen
erklären das Potenzial, erzeugen aber keine zusätzlichen Credit-Punkte.

Die persönliche Gesamtheit qualifizierter prozeduraler Systeme liefert eine
Referenz. Die Ebenen sind Massencode → Sektor+Massencode → exakte Familie.
Jede Ebene verwendet dieselbe Pseudo-Stichprobe `PRIOR_SYSTEMS=25`:

```
p = (Treffer + 25 * übergeordnete Trefferquote) / (n + 25)
V = (n * robuster Gruppenwert + 25 * übergeordneter Wert) / (n + 25)
lokales Gewicht = n / (n + 25)
```

Auch die Massencode-Ebene wird zur persönlichen Gesamtheit hin geglättet, damit
seltene Massencodes nicht mit einer einzigen Beobachtung dominieren. Ohne
qualifizierte Massencode-Beobachtungen ist der Tipp nicht auswertbar.
Leere regionale/familiäre Gruppen erben unverändert den übergeordneten Wert.
5/25/50 Systeme bedeuten 16,7/50/66,7 Prozent lokales Gewicht; es gibt keine
harte Umschaltung. 25 ist ein dokumentierter konservativer Startparameter,
kein statistisch optimierter Hyperparameter.

Je Ebene: n, Treffer, rohe/geglättete Quote, lokales Gewicht, Einfluss gegenüber
der Elternebene, Körperklassen, Median, winsorisierter Mittelwert und BIO-Belege.
Qualitätsgrenzen: <5 `very_low`, 5–24 `low`, 25–49 `usable`, ab 50 `good`.
`data_quality` im Gesamtergebnis bezeichnet die Massencode-Basis;
`family_data_quality` und die Ebenenqualität müssen daneben sichtbar bleiben.

`rate_interval_95` ist ein nominales Wilson-Intervall der **rohen** Trefferquote.
Es ist weder ein Vorhersageintervall noch ein formal berechnetes hierarchisches
Posterior: Gruppen überlappen und Reiseauswahl/räumliche Abhängigkeit bleiben.
`valuable_rate` darf nicht als garantierte Fundwahrscheinlichkeit angezeigt werden.

## Einheitliches wirtschaftliches Szenario

`calculate_body_values` berechnet alle Planeten als bereits entdeckt/kartiert,
mit effizientem normalem DSS-Mapping und Korrekturfaktor 1. Sterne erhalten den
Scanwert. Eigene Kartierung, damalige Erstentdeckungsboni und Credit-Caches
werden ignoriert. Das Ergebnis ist Vergleichspotenzial, kein Verkaufserlös.
Fehlende Massen nutzen die bestehenden Schätz-Fallbacks der Bewertungsfunktion.

Jede Ebene zeigt den ungekürzten Median und einen winsorisierten Mittelwert:
Systemwerte werden bei der **gemeinsamen persönlichen 95%-Quantile** der
qualifizierten Historie gedeckelt. Diese Grenze ist für alle Ebenen gleich;
ein einzelner lokaler Ausreißer setzt keine eigene hohe Kappungsgrenze.
Die geglätteten winsorisierten Mittelwerte bestimmen die Empfehlung.
Damit werden seltene Spitzen bewusst unterschätzt. Median und Rohfunde bleiben
als Erklärung verfügbar, werden nicht zusätzlich gewichtet.

## Empfehlung und BIO

Standard ist **100 % Explorationspotenzial, 0 % BIO**. Index 100 bedeutet den
persönlichen winsorisierten Gesamtdurchschnitt, 200 dessen doppeltes Potenzial.
Der Index ist nicht auf 100 begrenzt und kein Prozentwert einer Fundchance.
Die Produktgrenzen sind relativ zu dieser Referenz:

| Verhältnis | Klasse |
|---|---|
| <0,5 | `weak` – Schwach |
| 0,5 bis <1,25 | `average` – Durchschnittlich |
| 1,25 bis <2 | `interesting` – Interessant |
| 2 bis <4 | `good` – Gut |
| ab 4 | `very_good` – Sehr gut |

BIO unterscheidet `unknown`, `signals_only`, `analyses_present` und
`known_signals_analysed`. Letzteres verlangt qualifizierte astronomische Daten,
positive bekannte Signalzahlen und je Körper genau so viele unterschiedliche
vollständig analysierte Arten/Varianten mit bekannten Werten wie Signale.
Es ist ausdrücklich nur Abdeckung **bekannter** Signale, kein Nachweis einer
vollständigen Untersuchung aller möglichen Organismen. Fehlende Analyse und
unbekannter Wert ergeben `None`, niemals 0 Cr Potenzial.

`weight_comparison` vergleicht 100/0, 80/20 und 70/30. BIO wird separat auf seinen
persönlichen winsorisierten Referenzwert normalisiert und hierarchisch geglättet;
Millionen BIO-Credits dürfen kleine Kartographiewerte nicht einfach überrollen.
Mindestens fünf vergleichbare BIO-Systeme im Massencode sind für diagnostische
Mischwerte nötig. Ohne diese Daten bleiben die Mischwerte `None`. Auch mit Daten
sind sie `diagnostic_selection_biased`: analysierte BIO-Proben sind selektiv und
beweisen keine bessere Prognose. Daher verändern sie den Standardtipp nicht.

## Lesender Entwicklungsvergleich

```
venv/bin/python -B tools/compare_jump_tips.py --database data/cmdrhelper.db
```

Das Werkzeug öffnet SQLite mit `mode=ro`, erstellt einen konsistenten Snapshot
im Arbeitsspeicher und verwendet dort `query_only`. Es konstruiert keine
CMDRDatabase, importiert nichts und führt keine Migration aus. Bei mehreren
Commandern ist `--commander-id` erforderlich. Es vergleicht den echten alten
historischen Musterpfad mit der hierarchischen API für das Beispiel sowie drei starke und drei
schwache historische Systeme. Ein zusätzlicher gemeinsamer Ausschluss dieser
Ziele zeigt die Empfindlichkeit gegenüber deren eigenen Funden. Das ersetzt
keinen räumlich/zeitlich getrennten Prognosetest.

## Oberfläche in v3.3

Die Systemanalyse wertet einen vollständigen Zielnamen auf Benutzeraktion aus.
Sie zeigt Bewertung und Potenzialindex sowie davon getrennt Datenbasis und
Aussagekraft für Massencode, Region und Familie. Historische Ergebnisse zeigen
Systemzahl, Treffer, Median und geglättetes Potenzial der feinsten belegten Ebene;
deren Bezug ist ausdrücklich angegeben. Die Endnummer beeinflusst den Score
nicht. BIO bleibt informativ und hat keine Wirkung auf die Hauptbewertung.
Der bisherige Kürzelvergleich ist im Reiter Erfahrungsdaten weiterhin verfügbar.
Diagnostische Gewichtungsvergleiche des Werkzeugs sind keine GUI-Bewertung.

Lokale JSON-Vergleichsausgaben sind Momentaufnahmen persönlicher Daten und
gehören nicht zum Release. Das Vergleichswerkzeug und die feste
Test-Fixture `tests/fixtures/system_analysis.json` bleiben zur Prüfung erhalten.
