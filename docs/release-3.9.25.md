# CMDRHelper 3.9.25

- Normale Checkboxen und Radio-Buttons erhalten einen dünnen gelben Rahmen im Dark-Mode (#FFCC33) und einen blauen im Light-Mode (#1565C0). Native Häkchen und Auswahlpunkte bleiben erhalten.
- Die Auswahlrahmen folgen Themewechseln und berücksichtigen neu erzeugte Auswahlfelder. Beschriftungen, Gruppen und bestehende Sonderindikatoren bleiben unverändert.
- Zuverlässigere Qt-Tests durch vollständige Chronicle-/EDSM-/Inara-Testattrappen, kontrollierte Worker- und Widgetbereinigung sowie gezielte Verarbeitung ausstehender Löschereignisse.

## Umfang und Grenzen

Die Produktänderungen beschränken sich auf die bereits implementierten Auswahlrahmen.
Journal-, Handels-, Mining- und Uploadlogik, Handelsmarkierungen und Datenbankschema
23 bleiben unverändert. Keine Datenbankmigration. Die bestehende ZIP-Ausschlussliste
bleibt unverändert; frühere Versionshinweise und README-Abschnitte bleiben erhalten.

Der Akzentstil umschließt nur den Auswahlindikator, nicht Gruppen oder Beschriftungen.
Er unterstützt die Qt-Stile Fusion und Windows. Unbekannte/native Plattformstile
behalten ihre ursprüngliche Darstellung. Der Qt-Stil Windows unter Linux ist kein
nativer Windows-Test. Native Windows-Prüfungen stehen aus.

## Referenz der Qt-Belastungsläufe

Vom Auftraggeber übermittelte Ergebnisse der sechs vorherigen Läufe:

| Akzentstil | Modulreihenfolge | Bestanden | Skips | Fehler |
| --- | --- | ---: | ---: | ---: |
| Ohne | Ursprünglich | 355 | 3 | 0 |
| Ohne | Umgekehrt | 355 | 3 | 0 |
| Ohne | Fest gemischt | 355 | 3 | 0 |
| Mit | Ursprünglich | 355 | 3 | 0 |
| Mit | Umgekehrt | 355 | 3 | 0 |
| Mit | Fest gemischt | 355 | 3 | 0 |
| Gesamt | | 2130 | 18 | 0 |

Die genannten Rohprotokolle unter `/tmp/cmdr-qt-fix/` waren in der aktuellen
Prüfumgebung nicht verfügbar. Diese Tabelle ist eine übermittelte Referenz,
kein hier wiederholter oder unabhängig anhand der Rohdaten geprüfter Lauf.

## Abschlussprüfung

Linux, Python 3.12.3, PySide6/Qt 6.11.2. Normale Abschlussläufe verwenden
Qt offscreen mit explizit 1280 × 850; GUI-Prüfungen Xvfb/Openbox auf Display :97
mit 1280 × 850. Display :0 und der produktive Desktop wurden nicht verwendet.
Alle Daten und Einstellungen sind synthetisch beziehungsweise temporär; externe
Netzwerkverbindungen der Testtreiber sind gesperrt. Keine echten EDSM-/Inara-Uploads.

- Gemeinsamer Abschlusslauf mit Akzentstil: 259 Tests, davon 257 bestanden und
  zwei erwartete Offscreen-Skips für native X11-Bedienung, keine Fehler.
- Xvfb/Openbox: 62 Tests bestanden, keine Skips. Auswahlindikatoren, zwölfsprachiger
  Updatedialog, Tastenkürzel samt nativem X11-Fall, responsive Layouts und sicherer
  Beenden-Ablauf einschließlich Fenstermanager-Schließen.
- Metadaten, Auswahlindikatoren, Updatedialog und Fenstergeometrie: 32 Tests
  offscreen bestanden. Pixelvergleiche prüfen alle Auswahlzustände, Häkchen und
  Punkte, deaktivierte Felder, Fokus/Hover, beide Themes, Themewechsel, dynamische
  Felder, zwölf Sprachen und geschützte Sonderindikatoren. Tastatur- und
  Mausbedienung werden synthetisch geprüft.
- Ergänzende gemeinsame Prüfung von Chronicle-Zeitraumfiltern und sicherem
  Beenden nach der Fixture-Korrektur: 46 Tests, 45 bestanden, ein erwarteter
  Offscreen-Skip, keine Fehler. Alle 165 bisherigen Assertion-Aufrufe der drei
  zusätzlich korrigierten Testdateien sind nach AST-Vergleich erhalten.
- Sprachprüfung: 2.385 Referenzschlüssel in zwölf Sprachen, passende Platzhalter,
  keine doppelten Schlüssel. Bestehende Materialnamen-Fallbacks bleiben erhalten.
  Alle früheren Übersetzungen und README-Inhalte sind unverändert erhalten.
- Syntaxprüfung von 614 Python-Dateien, Imports der geänderten Laufzeitmodule
  und `git diff --check` bestanden.

Die breite modulweise Serie umfasst 1.382 Tests in 91 Modulen. Nach der separat
bestandenen Wiederholung des korrigierten Chronicle-Moduls: 1.376 bestanden,
vier Skips und die zwei unten beschriebenen, bereits in 3.9.24 vorhandenen
Persistenz-Assertions. Die Skips betreffen zwei ausdrücklich optionale persönliche
Referenzdatenbanken und zwei native X11-Fälle; letztere bestehen im Xvfb-Lauf.
Die zusätzlichen gemeinsamen Läufe werden separat ausgewiesen, nicht als weitere
einzigartige Tests dieser Serie gezählt.

Abgedeckt sind Chronicle und Carrier, EDSM-/Inara-Sicherheits- und Transferprüfungen,
sicheres Beenden, Markt-/Handels-/Material-/Mining-Regressionen, Update-Download,
Windows-Update-Simulationen und Migrationsschutz, Diagnose-Datenschutz sowie
Paketierung und Publisher-Simulationen. Keine reale Testveröffentlichung.

## Testkorrekturen und bekannte Grenzen

Zusätzlich zum übernommenen Arbeitsstand wurden drei Testdateien korrigiert:
`test_edsm_transfer.py` übernimmt die neue Fixture-Bereinigung und meldet rein
synthetische, nicht ausgeführte Threadmocks nicht als dauerhaft laufende Threads;
`test_inara_uploader.py` bildet den Thread-Lebenszyklus vollständig ab und beendet
seine Worker unter dem gepatchten Transport; `test_chronicle_period.py` zerstört
sein nur teilweise aufgebautes MainWindow direkt mit der vorhandenen Qt-Testhilfe.
Letzteres besitzt keine vollständige App-Beenden-Infrastruktur. Keine fachliche
Assertion wurde entfernt oder abgeschwächt. Diese Ergänzungen betreffen nur Tests.

Ein erster gemeinsamer Lauf wurde wegen der EDSM-Threadmock-Verunreinigung
abgebrochen; der oben ausgewiesene erfolgreiche Lauf ist die Wiederholung nach
der Korrektur. Die zunächst verwendete Offscreen-Standardauflösung wurde für die
Abschlussserie explizit auf 1280 × 850 korrigiert. Frühere Diagnoseläufe werden
nicht als erfolgreiche Abschlussprüfung gezählt.

Zwei bereits in 3.9.24 dokumentierte Persistenz-Assertions in `test_odyssey_ranks`
und `test_odyssey_sort` bleiben sichtbar: Ein zweiter Prozess liest Einstellungen,
bevor die Qt-Ereignisschleife sie geschrieben hat (`None` statt `rank_asc` bzw.
`cleanup`). Beide Fehler wurden zusätzlich mit dem unveränderten Produktcode des
3.9.24-Commits reproduziert. Der reguläre sichere Beenden-Ablauf wird separat
geprüft. Keine Änderung der bestehenden Speicherung und keine Behauptung einer
vollständig fehlerfreien historischen Testsuite.

Bekannte Qt-/PySide6-Lebensdauer- und Teardown-Probleme werden durch die
Testbereinigungen nicht als allgemein behoben erklärt. Die Testtreiber protokollieren
Qt-Meldungen mit Testzuordnung und verwenden keinen periodischen Python-Stackdump.
Der gemeinsame Abschlusslauf zeigt keine native Qt-Absturzmeldung. Offscreen
meldet weiterhin fehlende Unterstützung für `propagateSizeHints`, `raise` und
Tastatur-Grabbing; die betreffenden Bedienwege wurden zusätzlich unter Xvfb geprüft.
Kein nativer Windows-Test, keine Langzeit-Leak-Aussage und kein Test mit
produktiven Spielständen. Nicht unterstützte native Stile behalten ihre Darstellung.

## Probebuild und Updatepfad

Der vollständige Probebuild mit dem unveränderten `create_release.sh` besteht.
ZIP-Integrität und bytegenaue Übereinstimmung mit dem Releaseverzeichnis wurden
geprüft. 478 Dateien; keine Tests, Tools, Caches, Datenbanken oder persönlichen
Dateien. Alle zwölf READMEs und diese Releasebeschreibung sind enthalten; die
bestehenden gezielten Dokumentationsausschlüsse bleiben unverändert.

Der synthetische Updateversuch verwendet die echten ZIPs von 3.9.24 und 3.9.25
und den normalen `apply_update`-Dateipfad: Backup, Kopieren und Versionskontrolle
bestehen; synthetische Datenbank- und Einstellungsdateien bleiben byteidentisch.
Prozesswarten, Abhängigkeitsinstallation und Neustart sind kontrolliert ersetzt;
dies ist kein nativer Windows-End-to-End-Nachweis.

Der Publisher baut nach der interaktiven Bestätigung erneut aus dem finalen Commit
und normalisiert das ZIP. Die veröffentlichte SHA-256-Prüfsumme und Größe werden
im Abschlussbericht festgehalten; die Probebuild-Prüfsumme ist nicht die finale
Releaseprüfsumme.
