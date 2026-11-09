# Teststrategie für CMDRHelper

Der Prüfumfang richtet sich nach der Änderung und ihren direkten Abhängigkeiten.
Entwicklung und Release erfolgen unter Linux; native Windows-Prüfungen ergänzen
bei betroffenen Plattformfunktionen die Linux-Tests. Ein Release allein verlangt
keinen vollständigen Testlauf.

| Stufe | Wann | Umfang |
| --- | --- | --- |
| A – Gezielte Tests | Kleine, abgegrenzte Änderung | Betroffene Module und direkte Abhängigkeiten, einschließlich relevanter Fehlerfälle. Bei einer Symbolfarbe beispielsweise Darstellung, Legenden und betroffene Ansichten. |
| B – Erweiterte Regression | Mehrere betroffene Funktionsbereiche | Zusammenhängende Bereiche gemeinsam prüfen, etwa Schiffsfracht, Mining, Missionsanzeigen und Marktfilter bei einer Änderung ihrer gemeinsamen Bestandsquelle. |
| C – Gesamtsuite | Zentrale Änderungen oder begründeter Integrationsverdacht | Beispielsweise Persistenz, Commander-Zuordnung, gemeinsame Infrastruktur oder Laufzeitabhängigkeiten. Anlass ausdrücklich festhalten; keine automatische Pflicht vor jeder Veröffentlichung. |
| D – Technische Releaseprüfungen | Autorisierte Veröffentlichung | Bestehender Ablauf über `github.sh`: Version und Sprachtexte, Repository und Berechtigungen, Commit-Snapshot, Paketinhalt und ZIP-Integrität, Tag sowie GitHub-Asset mit Größe und SHA-256. Anwendungstests nach A, B oder begründet C ergänzen. |

## Auswahl und Ausführung

Vor der Änderung Git-Stand und aktuelle Version prüfen. Relevante Testmodule
anhand der geänderten Funktionen und ihrer Aufrufer auswählen. Auswahl und
Ergebnisse einschließlich übersprungener oder abgebrochener Tests berichten.
Ein erfolgreiches Paket ist kein Nachweis fachlich bestandener Anwendungstests.

Beispiel für gezielte Tests im Projektverzeichnis:

```sh
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. \
  venv/bin/python -B -m unittest -v \
  test_popup_ui_settings test_edsm_ui_status
```

Dateimuster können eine fachliche Auswahl ergänzen. Für Änderungen an der
Testverwaltung die Discovery vor und nach der Änderung vergleichen. Folgender
Befehl sammelt Tests, führt ihre Methoden jedoch nicht aus:

```sh
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B - <<'PY'
import unittest

loader = unittest.TestLoader()
suite = loader.discover('tests')

def cases(group):
    for item in group:
        if isinstance(item, unittest.TestSuite):
            yield from cases(item)
        else:
            yield item

for case in cases(suite):
    print(case.id())
print('Anzahl:', suite.countTestCases())
if loader.errors:
    raise SystemExit('\n'.join(loader.errors))
PY
```

Discovery importiert die Testmodule. Daher gehören Testaktionen in Testmethoden,
nicht in den Importpfad. Beim Vergleich müssen auch mehrfach vorkommende IDs und
unterschiedliche Modulpfade desselben Tests berücksichtigt werden. Die Anzahl
definierter Methoden allein erfasst weder Vererbung noch dynamische Tests oder
die Varianten innerhalb von `subTest`.

## Historische Prüfungen und gemeinsame Vorbereitung

Historische Release-Prüfungen verwenden die feste damalige Release-Version für
Sprachtexte, README-Abschnitte, Update-Dialoge und Versionsvergleiche. Die aktuelle
Anwendungsversion wird separat auf Format und Übereinstimmung ihrer Quellen
geprüft. Historische Daten dürfen nicht auf die aktuelle Version umgeschrieben
werden. README-Historie und aktuelle Veröffentlichungsmetadaten sind getrennte
Prüfgegenstände.

Gemeinsame Testvorbereitung enthält keine `test_*`-Methoden und erbt nicht von
`unittest.TestCase`. Vollständige Testklassen nicht als Hilfsklassen auf Modulebene
importieren: `unittest` kann sie dort nochmals entdecken. Testmethoden nur dann
bewusst erben, wenn unterschiedliche fachliche Bedingungen geprüft werden, etwa
Kauf und Verkauf. Reine Aufbauwiederverwendung erfolgt über testfreie Fixtures.

`github.sh` startet keine Anwendungstests und wählt keine Teststufe aus. Die
Testauswahl bleibt Teil der Vorbereitung; der Veröffentlichungsablauf bleibt
unverändert. Einzelheiten stehen in [github-release.md](github-release.md).
