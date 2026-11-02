# Windows-Auswahlindikatoren – Prüfprotokoll

## Ergänzung zur Releasevorbereitung v3.9.26

Der Auftraggeber hat die Korrektur auf Windows 11 praktisch bestätigt und die
Veröffentlichung von v3.9.26 nach erfolgreicher Linux-Abschlussprüfung freigegeben.
Die folgenden Abschnitte dokumentieren den ursprünglichen Prüfstand vor dieser
Rückmeldung. Sie sind keine Aussage über eine weiterhin ausstehende Freigabe.
Die vollständige Matrix aller Windows-/Qt-/DPI-Kombinationen bleibt ungeprüft.
Aktuelle Releaseergebnisse: [v3.9.26](release-3.9.26.md).

## Ursprünglicher Prüfstand

Stand: 2026-11-02. Basis und unveränderte Programmversion: **3.9.25**.
HEAD: `f207f1139f3bc9e8c9ecb2cf348683b4e185ecbc`.
**Noch nicht vollständig validiert: native Windows-Prüfung durch den Auftraggeber ausstehend. Keine Releasefreigabe.**

## Umfang und Ursache

Vor Beginn war `git status --short` leer; HEAD entsprach dem vorgegebenen
veröffentlichten Commit. Keine vorgefundenen Änderungen.

Die bisherige Installation des ProxyStyle akzeptierte ausschließlich
`QFusionStyle` und `QWindowsStyle`. Bei `QWindowsVistaStyle` und
`QWindows11Style` wurde daher weder der Akzent-Zeichenpfad noch die
`accentIndicator`-Eigenschaft für die vorhandene Unchecked-QSS-Regel aktiviert.

Der [offizielle Qt-Windows11-Zeichenpfad](https://github.com/qt/qtbase/blob/6.11/src/plugins/styles/modernwindows/qwindows11style.cpp)
verwendet im Radio-Primitiv `palette.window()` für den inneren Auswahlpunkt.
`controlFillBrush()` bevorzugt eine explizit gesetzte Button-Palettenrolle.
Mit gleichen Button-/Window-Hintergrundfarben kann deshalb auch nach Ergänzung
eines äußeren Rahmens der innere Auswahlpunkt verschwinden. Das wurde unter
Linux mit einer gezielten Zeichenpfad-Attrappe reproduziert, nicht mit einem
nativen Windows-Stil.

## Korrektur

- Die vorhandene Installation erzeugt zusätzlich eigene Instanzen der passenden
  Factory-Stile `windowsvista` und `windows11`. Unbekannte Stile und fehlende
  Factory-Stile werden weiterhin unverändert belassen.
- Der bestehende 1-Pixel-Rahmen bleibt gelb `#FFCC33` beziehungsweise blau
  `#1565C0`. Es gibt keine Änderungen an Größenmetriken oder Trefferflächen.
- Ausschließlich beim ausgewählten normalen Windows11-Radio wird eine lokale
  Kopie der Zeichenoption verwendet: deren Window-Pinsel erhält den jeweiligen
  WindowText-Pinsel für Active, Inactive und Disabled. Die Originalpalette wird
  nicht verändert. Der native Stil zeichnet weiterhin Punktform, Zustandsradien,
  Animation und Fokus. Nur die problematische Punktfarbe wird korrigiert.
- Checkbox-Häkchen und Teilmarkierungen werden nicht ersetzt. Die bisherigen
  Ausschlüsse für Sonderindikatoren bleiben erhalten. Kein SVG-/Fusion-Fallback,
  keine globale Palette und keine neue Styling-Architektur.

Tatsächlich geänderte/neue Repository-Dateien:

1. `cmdrhelper/ui/selection_indicators.py` – einzige Produktcodeänderung.
2. `tests/test_selection_indicators.py` – Windows-Regressionen; vorhandene
   Sprach-/Bedien- und Markt-Repaintprüfungen zusätzlich mit Qt-Windows.
3. `tools/probe_selection_indicators.py` – isolierter interaktiver Teststarter.
4. `docs/windows-selection-indicators-validation.md` – dieser Prüfbericht.

Vorhandene Qt-Fixtures und deren Cleanup-Regeln wurden nicht geändert.
Markt-, Material-, Inventar-, Journal-, Favoriten-, Beenden- und Transferlogik,
Datenbankschema, Versionsdatei und Veröffentlichungsskripte bleiben unverändert.

## Linux-Ergebnisse

Linux, PySide6/Qt **6.11.2**. Temporäre/synthetische Daten und separate
XDG-Verzeichnisse. Kein Start des produktiven MainWindow/AppState und kein
Zugriff auf Display `:0`. Xvfb/Openbox wurden nach `/tmp` entpackt; keine
Systeminstallation oder Systemkonfigurationsänderung.

| Prüfung | Ergebnis |
| --- | --- |
| Offscreen, gezielte Indikatorprüfungen | 12 Tests bestanden |
| Offscreen, 1280 × 850, Indikatoren/Markt/Fracht/Stabilität/Merken/Schiffsfracht | 110 Tests bestanden |
| Offscreen, zusätzlicher Lauf mit Proxy-Installation vor jedem Test | 61 Tests bestanden |
| Xvfb/Openbox, Display :97, 1024 × 768 | 61 Tests bestanden |
| Direkter Vergleich veröffentlichter HEAD gegen Korrektur, Fusion und Windows | 360 identische Pixelbilder, Indikatorrechtecke und Größenhinweise |
| Neue Windows-Tests gegen alten Produktcode | Beide Testmethoden scheitern erwartungsgemäß: 17 fehlgeschlagene Assertions/Subtests |
| Syntaxprüfung der drei Python-Dateien; `git diff --check` | bestanden |

Die Läufe überschneiden sich; die Zahlen sind keine Summe einzigartiger Tests.
Die gesamte historische Repository-Testsuite wurde nicht wiederholt.

Die Matrix deckt beide Themes, Checkbox aus/an/teilmarkiert, Radio aus/an,
deaktiviert, Hover, Tastaturfokus, Themewechsel, dynamische Checkboxen und
Schriftgrößen 10/14/18 pt ab. Die zwölf Sprachvarianten werden mit Maus und
Tastatur in beiden Linux-Stilen geprüft. Markt-Repaint/Themewechsel dürfen
weder Auswahl-Signale noch zusätzliche Filter-/Markt-Leseaufrufe auslösen;
die bestehenden Markt-/Frachtfiltertests prüfen weiterhin die fachlichen
Ergebnisse. Sonderindikatoren werden pixelgenau verglichen, einschließlich
Screenshot-Checkboxen, Carrier-Bestätigung, Tabellen-Merken, Listen/Bäumen,
Menüs und checkbaren Schaltflächen.

32 Xvfb-Screenshots und 16 Stilprotokolle zeigen beide Linux-Stile in beiden
Themes bei 10/18 pt, jeweils ohne Proxy (`before`) und mit Korrektur (`after`).
Die Marktansicht wird für die Aufnahme zu ihren Radiofiltern gescrollt.
Bei großer Schrift und 1024 × 768 bleiben vorhandene Scrollbereiche erforderlich;
die Korrektur verändert dieses Layout nicht. Die Aufnahmen wurden stichprobenartig
visuell geprüft; die vollständige Zustandsmatrix ist automatisiert geprüft.

`before` in diesen Screenshots bedeutet nativer Stil ohne Proxy, nicht der
Linux-Produktstand 3.9.25: Letzterer besaß den Proxy bereits. Dessen Gleichheit
mit dem neuen Linux-Verhalten belegt der separate 360-Fälle-Vergleich.

## Windows-Test durch den Auftraggeber

Das ZIP wird vollständig unter Linux in einem temporären Buildverzeichnis mit
dem unveränderten `create_release.sh` erzeugt und um die isolierte Diagnose
ergänzt. Die darin angezeigte Programmversion bleibt **3.9.25**. Das ZIP ist
kein Release, kein Updatepaket zum Einspielen und enthält keine Benutzerdaten.

1. ZIP in einen neuen, leeren Testordner entpacken.
2. `START_INDICATOR_TEST.bat` mit dem Pfad zur vorhandenen Windows-Python-Datei
   aus dem CMDRHelper-venv starten, beispielsweise:
   `START_INDICATOR_TEST.bat "C:\CMDRHelper\venv\Scripts\python.exe"`.
   Dadurch wird der Code aus dem entpackten Probebuild verwendet. Alternativ
   aus diesem Ordner direkt `"C:\CMDRHelper\venv\Scripts\python.exe" tools\probe_selection_indicators.py`.
   Für den isolierten Test nicht den normalen `start.bat`-/`main.py`-Startweg verwenden.
3. Die Kopfzeile muss die echte aktive Stilklasse dokumentieren, insbesondere
   `QWindows11Style`, sowie `SelectionIndicatorStyle` als Proxy. Ein erzwungener
   Fusion-Stil genügt nicht als nativer Nachweis. Qt-/PySide-Version werden ebenfalls angezeigt.
4. Im ersten Tab das echte Widget „Markt ansehen“ mit synthetischen Markt- und
   Frachtbeständen prüfen: Alle Waren / Bergbau / Schiffsfracht durchschalten;
   ausgewählte und ungewählte Kreise in Dark und Light vergleichen. Bei Bedarf
   den vorhandenen Scrollbereich nach unten bewegen.
5. Im zweiten Tab Checkbox-Zustände, Radio-Zustände, deaktivierte Felder,
   Hover, Tab-/Leertastenbedienung, dynamische Checkbox und die echten
   Screenshot-/Carrier-Sonderindikatoren kontrollieren. Schrift 10/14/18 pt
   und Themewechsel prüfen; Auswahl muss erhalten bleiben.
6. Mit „Screenshots + Stilprotokoll speichern“ beide Tabs und JSON-Protokoll in
   `indicator-test-results` sichern. Jeweils Dark und Light aufnehmen. Zusätzlich
   Windows-Version und Skalierung (z. B. 100/150 %) mitteilen; möglichst auch
   höhere DPI prüfen.
7. Für einen nativen Vorher-Vergleich denselben Python-Aufruf mit `--baseline`
   ausführen. Optional gezielt `--style windowsvista`, falls von Qt angeboten.

Der Diagnose-Starter verwendet bestehende synthetische Markt-/Fracht-Fixtures,
keinen AppState, keine echten Journale und keine produktiven Einstellungen.
Temporäre Datenbanken werden beim Beenden bereinigt; Screenshots/JSON bleiben
nur im angegebenen Ausgabeordner. Kein Fernzugriff, keine automatische
Windows-Ausführung und keine Quellcodeänderungen auf Windows.

## Testlücke und verbleibende Risiken

Native Windows11-/Vista-Zeichenpfade, Systemfarbschema, native Animation und
DPI-Skalierung sind unter Linux nicht ausführbar. Der Qt-Windows-Stil unter
Linux und die Windows11-Attrappe sind dafür kein Ersatz. Die Palettenkorrektur
orientiert sich am untersuchten Qt-6.11-Zeichenpfad; andere unterstützte
Qt-Versionen und native Windows-Konfigurationen müssen praktisch geprüft
werden. Falls der echte Zeichenpfad den Proxy nicht wie erwartet erreicht oder
Kontrastprobleme zeigt, sind weitere eng begrenzte Anpassungen vor einer
Releasefreigabe nötig. Ein größerer Umbau wurde nicht vorgenommen.

Git-Status nach Abschluss: zwei geänderte und zwei neue Dateien wie oben;
HEAD unverändert. Kein Commit, Tag, Push, Versionswechsel oder Release.
`github.sh` wurde nicht ausgeführt. Warten auf Windows-Testergebnisse und weitere Freigabe.
