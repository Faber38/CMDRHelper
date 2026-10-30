# Gezielte Lebensdauerabsicherung des Cursorfilters

Stand: 30.10.2026, weiterhin Version 3.9.21. Keine allgemeine Änderung der
Cursorarchitektur und keine weiteren Funktionsänderungen.

## Geänderte Dateien und Funktionen

- `cmdrhelper/ui/cursors.py`: ausschließlich `CursorPolicy.eventFilter()`.
- `tests/test_cursor_lifetime.py`: acht neue Lebensdauer- und Weiterleitungstests.
- `docs/cursor-lifetime-fix.md`: dieser Abschlussbericht.

Alle anderen vorhandenen Änderungen bleiben erhalten. Es wurden weder Inventar-,
Mining-, Journal- noch Datenbankfunktionen bearbeitet.

## Ursache und genaue Schutzmaßnahme

Ein Python-Widgetwrapper kann weiter existieren, obwohl das zugrunde liegende
C++-Objekt zerstört wurde. `isinstance(watched, QWidget)` bleibt dann wahr.
`update()` prüfte bereits `isValid()` und kehrte bei ungültigem Widget zurück;
der anschließende ungesicherte Zugriff auf `watched.parentWidget()` in der
bisherigen Zeile 161 löste dennoch einen RuntimeError aus. Außerdem kann ein
Widget während `update()` durch reentrante Ereignisverarbeitung ungültig werden.

Die Korrektur verwendet ausschließlich das schon importierte
`shiboken6.isValid()`:

1. Beim Eintritt in den QWidget-Filter wird die Gültigkeit geprüft, noch vor
   dem `_setting`-Rücksprung und vor jedem Zugriff auf Qt-Widgetmethoden.
2. Nach `update()` im MouseMove-/HoverMove-Zweig wird erneut geprüft, bevor
   `parentWidget()` oder die Viewportprüfung ausgeführt wird.
3. Der Leave-Zweig verändert für ein inzwischen ungültiges Ziel keine
   vorgemerkte Cursorposition mehr.
4. Ist der Empfänger ungültig geworden, liefert der Filter `True` und verhindert
   weitere Ereigniszustellung an ihn. Für weiterhin gültige Widgets bleibt das
   bisherige `False` erhalten. Dies gilt auch am gemeinsamen Filterende für die
   übrigen Update-Zweige.

Ein bloßer Eintrittscheck würde die reentrante Löschung während `update()` nicht
abdecken. Es gibt keine pauschale RuntimeError-Unterdrückung. Ein unabhängiger
RuntimeError bei gültigem Widget wird weiterhin weitergegeben und ist explizit
getestet.

Der vorhandene `_setting`-Mechanismus, die Cursorzuordnung, Disabled-Zustände,
Timer, WeakKeyDictionary-Strukturen und Registrierung des globalen Filters
bleiben unverändert. Es wurden keine zusätzlichen Probleme nebenbei korrigiert.
Die Rückgabe `True` für während der Filterausführung zerstörte Empfänger folgt
der [Qt-Ereignisfilter-Regel](https://doc.qt.io/qt-6.11/qobject.html#eventFilter).

## Vorher-/Nachher-Reproduktion

Beide in der Analyse nachgewiesenen Fehlerpfade wurden vor der Produktänderung
nochmals ausgeführt:

| Kontrollierter Fehlerpfad | Vorher | Nachher |
|---|---|---|
| QWidget-C++-Objekt gelöscht, Python-Referenz behalten, direkter MouseMove-Filteraufruf | RuntimeError an Zeile 161 | `True`, kein weiterer Widgetzugriff |
| Gültiges Widget wird während des synchron ausgelösten CursorChange gelöscht | RuntimeError an Zeile 161 | `True`, kein anschließendes `parentWidget()` |
| 112 wiederholte direkte Aufrufe mit ungültigem Empfänger | 112 Ausnahmen | 0 Ausnahmen |

Die zwei zugehörigen neuen Testmethoden schlugen vor der Korrektur erwartungsgemäß
fehl und bestehen nachher. Die Vorherprüfung enthält mehrere Unterfälle, deshalb
weist ihr Testlog mehrere Fehler/fehlgeschlagene Assertions für zwei Testmethoden
aus. Diese Fehler-Injektion ist keine natürliche Reproduktion aller gemeldeten
Windowsfehler.

Zur sicheren Vorherprüfung wird ein bereits gelöschter Wrapper ausschließlich
an die Python-Filtermethode übergeben, niemals als freigegebener C++-Zeiger an
Qt `sendEvent()`. Beim reentranten Test läuft das verschachtelte CursorChange
über die tatsächliche Qt-Ereigniszustellung; ein nur im Test installierter
Handler erzwingt DeferredDelete. Die Produktdatei wird dafür nicht verändert.

## Neue Regressionstests

Die acht neuen Tests prüfen:

- Bereits zerstörten Empfänger beim Eintritt, einschließlich `_setting=True`
  sowie MouseMove, HoverMove, Show, Polish, CursorChange, Enter, Leave und
  EnabledChange.
- Zerstörung eines Tabellen-Parents während `update()`: Der ebenfalls ungültig
  gewordene Viewport darf anschließend weder `parentWidget()` aufrufen noch eine
  Cursorreparatur vormerken.
- Tatsächlichen synchronen CursorChange mit reentranter Löschung des Empfängers.
- Keine Ereignisweiterleitung nach Löschung in weiteren Update-Zweigen.
- Weiterleitung an ein gültiges Widget über Qt `sendEvent()`, weiterhin Handcursor
  und unveränderte Behandlung anderer QObject-Empfänger.
- Sichtbarkeit unabhängiger RuntimeErrors bei weiterhin gültigen Widgets.
- Überspringen einer vorgemerkten Cursorreparatur nach Viewportzerstörung.
- 30 Zyklen mit Dialogen, Menüs, Mausbewegungen, Deaktivieren/Aktivieren,
  Dark-/Light-Stylesheets und DeferredDelete ohne unbehandelte Ausnahme.

## Testergebnisse

| Prüfung | Ergebnis |
|---|---|
| Acht neue Tests + 18 bestehende Cursor-/Chronicle-Cursortests, Linux offscreen | 26 bestanden, 0 Fehler |
| Dieselbe Serie unter nativem Linux/X11 (`xcb`) | 26 bestanden, 0 Fehler |
| Angrenzende GUI-Serie mit zusätzlich global installiertem Cursorfilter und Exceptionhook-Erfassung | 70 bestanden, 0 unbehandelte Qt-/Python-Ausnahmen |
| Zusätzlicher Lebensdauer-Stresstest unter echtem X11 | 250 Zyklen, 0 unbehandelte Ausnahmen |
| Python-Kompilierungsprüfung und `git diff --check` | erfolgreich |

Die 70 GUI-Tests umfassen Favoritenbilder/-dialoge/-cache, Carrier-Eingabefeedback,
Carrier-Bearbeitungsmarker, Quick-Favorite-Hinweis sowie die 18 bestehenden
Cursortests. Damit wurden insgesamt 78 unterschiedliche Testmethoden geprüft;
die genannten Serien überlappen und werden nicht addiert.

Die bestehenden Cursorregressionen decken Hand-, Text- und Standardcursor,
deaktivierte Widgets, native Resize-/Pan-/Drag-/Wait-Cursor, globalen Override,
Tab-/Menü-/Itemview-Hit-Tests und wiederholte Filterinstallation ab.

Der zusätzliche X11-Stresslauf erzeugt Tabellen, Buttons, Eingabefelder, Tabs und
Menüs, bewegt die Maus, wechselt Themes und schließt bzw. zerstört die Dialoge.
Dabei bleiben absichtlich Python-Referenzen auf 1.000 zerstörte Widgets erhalten.
Vorgemerkte Cursorreparaturen und gepostete Ereignisse sind während der Löschung
noch vorhanden. Auch dieser Lauf verwendete ausschließlich synthetische Widgets.

Reproduzierbarer Aufruf der Cursorserie:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=tests venv/bin/python -m unittest test_cursor_lifetime test_ui_cursors test_chronicle_map_cursor
QT_QPA_PLATFORM=xcb PYTHONPATH=tests venv/bin/python -m unittest test_cursor_lifetime test_ui_cursors test_chronicle_map_cursor
```

Die zusätzlichen Instrumentierungs-/Stressprogramme aus der vorherigen Analyse
liegen unter `/tmp/cmdr-cursor-analysis/`. Die Ergebnisse dieses Auftrags liegen
unter `/tmp/cmdr-cursor-fix/`, insbesondere `repro-before.json`, `repro-after.json`,
`tests-before.log`, `cursor-tests.log`, `cursor-x11.log`, `gui-offscreen.json` und
`stress-x11.json`. Keine Originaldiagnosedaten wurden als Testfixture übernommen.

## Windows-Einschränkung und verbleibende Risiken

Es stand kein natives Windows-Testsystem zur Verfügung. Getestet wurde unter
Linux mit Python 3.12.3 und Qt/PySide6 6.11.2, sowohl offscreen als auch mit echtem
X11. Die Windowsdiagnose stammt von Python 3.13.2 und Qt/PySide6 6.11.2.

Behoben ist die konkret reproduzierte Schutzlücke. Ob sie sämtliche 300
protokollierten Windowsfehler erklärt, bleibt wegen der anonymisierten
Exceptiontexte und fehlenden nativen Reproduktion offen. Eine Bestätigung durch
den betroffenen Windows-Anwender steht aus. Es wird nicht behauptet, dass alle
Windows-Cursorfehler behoben seien.

Es gab keine komplette projektweite Testsuite und keinen Live-Elite-Test.
Andere, bisher nicht nachgewiesene Lebensdauerprobleme werden nicht durch eine
allgemeine Ausnahmeunterdrückung verdeckt. Insbesondere wurde keine allgemeine
Überarbeitung aller Cursor-Hilfsmethoden vorgenommen.

## Bestandsschutz und Git-Status

Vor der Arbeit wurden alle 22 bereits geänderten bzw. ungetrackten Dateien per
SHA-256 festgehalten. Sie sind nach Abschluss sämtlich bytegleich erhalten.
Damit bleiben Journalquellen-, Favoriten-Bild- und Planetengrafik-Cache, gezielte
Inventarinvalidierung und frühe EDSM-Positionsveröffentlichung vollständig erhalten.
Alle sieben bereitgestellten Originaldateien sind ebenfalls per Prüfsumme
unverändert bestätigt.

Keine Versionsänderung, kein Commit, Tag, Push oder Release. `github.sh` wurde
nicht ausgeführt. Keine produktiven Daten oder Einstellungen wurden verändert.

Vorher:

```text
 M cmdrhelper/edsm_system_status.py
 M cmdrhelper/source_manager.py
 M cmdrhelper/source_processing.py
 M cmdrhelper/state.py
 M cmdrhelper/ui/favorites_view.py
 M cmdrhelper/ui/journal_sources.py
 M cmdrhelper/ui/system_overview.py
 M tests/test_journal_sources_ui.py
 M tests/test_source_manager.py
?? cmdrhelper/inventory_invalidation.py
?? cmdrhelper/ui/favorite_preview_cache.py
?? docs/edsm-publication-x11.json
?? docs/edsm-publication.md
?? docs/inventory-invalidation-x11.json
?? docs/inventory-invalidation.md
?? tests/test_edsm_status_queue.py
?? tests/test_favorite_preview_cache.py
?? tests/test_inventory_invalidation.py
?? tests/test_source_publication.py
?? tests/test_system_overview_cache.py
?? tools/benchmark_edsm_publication.py
?? tools/benchmark_inventory_invalidation.py
```

Nachher:

```text
 M cmdrhelper/edsm_system_status.py
 M cmdrhelper/source_manager.py
 M cmdrhelper/source_processing.py
 M cmdrhelper/state.py
 M cmdrhelper/ui/cursors.py
 M cmdrhelper/ui/favorites_view.py
 M cmdrhelper/ui/journal_sources.py
 M cmdrhelper/ui/system_overview.py
 M tests/test_journal_sources_ui.py
 M tests/test_source_manager.py
?? cmdrhelper/inventory_invalidation.py
?? cmdrhelper/ui/favorite_preview_cache.py
?? docs/cursor-lifetime-fix.md
?? docs/edsm-publication-x11.json
?? docs/edsm-publication.md
?? docs/inventory-invalidation-x11.json
?? docs/inventory-invalidation.md
?? tests/test_cursor_lifetime.py
?? tests/test_edsm_status_queue.py
?? tests/test_favorite_preview_cache.py
?? tests/test_inventory_invalidation.py
?? tests/test_source_publication.py
?? tests/test_system_overview_cache.py
?? tools/benchmark_edsm_publication.py
?? tools/benchmark_inventory_invalidation.py
```

Die Cursorkorrektur bleibt uncommittet. Weitere Arbeiten warten auf Freigabe.
