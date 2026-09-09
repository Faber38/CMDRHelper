# Windows-Updater: Reparatur und lokaler Test

Stand: Arbeitskopie auf Basis v3.2, ohne Commit/Push/Tag/öffentliches Release.

## Befund und Grenze der historischen Rekonstruktion

Das vollständige lokale Git enthält **v2.0.5**, aber keinen Tag, Branch oder
Versionsstand **v2.5**. v2.0.5 wurde deshalb als möglicher gemeinter Altstand
untersucht, nicht stillschweigend mit v2.5 gleichgesetzt. Der Updater von v2.3
und v3.2 ist bytegleich. v2.0.5 enthält bereits denselben Modulstart,
`os.kill(pid, 0)` und direkten Python-Neustart; spätere Änderungen ergänzten
venv-Prüfung, Rollbackprüfung und Windows-Konsolenablösung.

Die Meldung „CMDRHelper läuft bereits“ entsteht ausschließlich in
`cmdrhelper.app.run()`, nach gescheitertem `QLockFile.tryLock(100)`, vor
`AppState` und Hauptfenster. Sie stammt damit aus einem Hauptprogrammstart.
Der vorhandene Helfer startet dagegen als
`<sys.executable> -m cmdrhelper.update --apply ... --parent-pid ...`.
Weder das Paket `__init__` noch dieser Modulpfad ruft `app.run()` auf.
Es gibt keinen separaten Batch-/PowerShell-Updatehelfer im untersuchten Git.

**Welcher konkrete Windows-Prozess den frühen Dialog erzeugte, ist mit den
vorliegenden Angaben nicht eindeutig belegt.** Bei normalem Python-Start
enthält der untersuchte Pfad vor dem Installationsabschluss keinen zweiten
Aufruf von `main.py`. Ein abweichender EXE-/Launcher-Start könnte
`sys.executable -m ...` anders behandeln; dafür fehlt bisher ein Beleg.
Die gemeldete Dialogreihenfolge lässt sich daher nicht allein aus diesem
Quellstand exakt herleiten. Benötigt werden die Bestätigung der Ausgangsversion,
der tatsächliche Startweg und `backup/update.log` des ersten Versuchs.
Die neue Diagnose protokolliert Haupt-PID, Interpreter, Argumente, Helfer-PID,
Neustart-PID und bei Doppelstart den Sperrinhaber.

Ein unabhängig davon **bewiesener Fehler** ist die Windows-Prozessprüfung:
`os.kill(pid, 0)` ist unter Windows keine POSIX-Existenzprüfung, sondern kann
`TerminateProcess` mit Exitcode 0 auslösen. Zudem wurden sonstige OSError als
„Prozess beendet“ behandelt. Damit war weder kontrolliertes Beenden noch die
Freigabe der Qt-Sperre gesichert. Das erklärt einen realen Fehler im
Ende-/Neustartpfad, beweist aber ohne Windows-Log nicht die alleinige Ursache
des beobachteten ausgebliebenen Neustarts. Beim alten v2.0.5-Helfer fehlt
zusätzlich die spätere Konsolenablösung und die Prüfung, ob der gestartete
GUI-Prozess sofort wieder endet. Eine Erfolgsmeldung des alten Helfers wäre
somit kein Nachweis für einen erfolgreichen GUI-Neustart.

Quellen: [Python os.kill](https://docs.python.org/3/library/os.html#os.kill),
[Windows OpenProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocess),
[WaitForSingleObject](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject),
[Qt QLockFile](https://doc.qt.io/qt-6/qlockfile.html).

## Reparierter Ablauf

1. ZIP-Download und Prüfung wie bisher.
2. Unter Windows zuerst den Download-/Beendigungshinweis bestätigen. Ein
   beliebig lang offener Dialog verbraucht dadurch keine Helfer-Wartezeit.
3. Externen Modulhelfer mit aktuellem lokalen venv starten; Hauptprogramm
   fordert über `QApplication.quit()` sein normales Ende an.
4. Helfer öffnet die alte PID ausschließlich mit SYNCHRONIZE-Recht und wartet
   bis zu 30 Sekunden auf den signalisierenden Prozesshandle. Kein Kill,
   kein festes Sleep als Ersatz. Bereits verschwundene PID wird akzeptiert;
   Zugriffs-/API-Fehler und Timeout führen zum Abbruch ohne Austausch/Neustart.
5. Helfer wartet zusätzlich bis zu 10 Sekunden auf dieselbe Qt-Sperre wie
   das Hauptprogramm. Er hält sie während Backup, Austausch und Prüfungen.
   Unter Windows gilt für beide `setStaleLockTime(0)`: Eine lange laufende
   Installation darf nicht allein wegen des Dateialters als verwaist gelten.
6. Vorhandenes Backup, geschütztes `data/`, venv und DB-Dateien bleiben im
   bisherigen Schutzmodell. Bei Kopierfehlern bleibt der Rollback erhalten.
7. Erst nach Requirements- und Zielversionsprüfung Sperre freigeben und
   genau einen Neustart anfordern. Bei Windows-Installationsfehlern erfolgt
   kein automatischer Start; Reparatur-/Rollbackstatus bleibt erhalten.
8. Neustart mit demselben geprüften `sys.executable` und absoluter `main.py`
   im Installationsordner. Das entspricht dem Anwendungsstart von `start.bat`
   (`venv\Scripts\python.exe main.py`). Kein fest installierter Python-Pfad,
   kein Shell-Quoting und keine Linux-Kommandos. Die Batch-Vorprüfungen werden
   weiterhin durch die Interpreter-/Abhängigkeitsprüfungen des Updaters ergänzt.
   Im Repository gibt es keine gepackte EXE-Installation; fremde Interpreter
   werden wie bisher abgewiesen.
9. Vorhandene kurze Neustartprüfung und Helfer-Aufräumen. Diese Prüfung
   erkennt sofortiges Prozessende, garantiert aber nicht die vollständige
   spätere GUI-Initialisierung; das prüft der reale Windows-Test.

Die sichtbaren `\\n\\n` im Single-Instance-Text wurden in allen zwölf
Sprachdateien in echte Zeilenumbrüche korrigiert. Der manuelle Doppelstart
bleibt blockiert.

## Altversion und Folgeupdate getrennt testen

Ein laufender alter Updater wird aus der **alten Installation** geladen,
bevor er das neue ZIP entpackt. Neue Paketdateien können seinen schon
laufenden Prozesswait/Neustart nicht rückwirkend reparieren. Die gewöhnliche
Paketstruktur bleibt kompatibel; keine Legacy-Sonderlösung wurde eingebaut.

- Altversion → reparierte 3.2: alter Ablauf kann einmalig weiter unsauber
  bleiben. Falls installiert, aber nicht neu gestartet: manuell starten.
- Reparierte 3.2 → nächste Version: erst dieser Durchlauf prüft den reparierten
  Helfer. Ein alleiniger Wiederholungstest von v2.0.5 → 3.2 genügt dafür nicht.

## Bevorzugt: bestehende v3.2-Releasekopie nur mit Runtime-Dateien patchen

**Ja: Ein Austausch ausschließlich der folgenden 16 Runtime-Dateien reicht.**
15 Dateien ersetzen; `cmdrhelper/windows_update.py` neu hinzufügen:

```text
cmdrhelper/app.py
cmdrhelper/update.py
cmdrhelper/windows_update.py                 (NEU)
cmdrhelper/ui/main_window.py
cmdrhelper/i18n/de.py
cmdrhelper/i18n/en.py
cmdrhelper/i18n/el.py
cmdrhelper/i18n/es.py
cmdrhelper/i18n/fi.py
cmdrhelper/i18n/fr.py
cmdrhelper/i18n/it.py
cmdrhelper/i18n/nl.py
cmdrhelper/i18n/no.py
cmdrhelper/i18n/pl.py
cmdrhelper/i18n/sv.py
cmdrhelper/i18n/tr.py
```

`start.bat`, `install.bat`, `install-windows.ps1`, `requirements.txt`,
`version.py`, das venv und `data/` werden für den Fix nicht ausgetauscht.
Die Anwendung bleibt Version 3.2. Es kommen keine Abhängigkeiten hinzu.
Testdateien und Testwerkzeug gehören nicht in die Runtime.

Das separat bereitgestellte `CMDRHelper_v3.2_windows_update_fix.zip` enthält
nur diese 16 Dateien mit relativen Pfaden. Bei beendeter Testanwendung auf
**eine lokale Kopie** des vorhandenen v3.2-Releases anwenden:

```powershell
Expand-Archive -LiteralPath 'C:\CMDRHelper-Testpakete\CMDRHelper_v3.2_windows_update_fix.zip' -DestinationPath 'C:\CMDRHelper Update Test' -Force
```

Das Ziel muss der Ordner sein, in dem `main.py` liegt. Keine produktive
Installation überschreiben. Die neue `windows_update.py` muss mitkopiert
werden. Mit `start.bat` lässt sich danach direkt der normale Start und
manuelle Doppelstart prüfen.

Um **den Updater** dieser weiterhin als 3.2 bezeichneten Kopie zu testen,
braucht die Versionsprüfung ein neueres Ziel. Dafür ist kein öffentliches
Release nötig. Für einen vollständig unter Windows vorbereiteten Test:

1. Eine frische, noch **nicht installierte** v3.2-Releasekopie mit genau diesen
   Runtime-Dateien patchen (noch kein venv, keine Benutzer-DB).
2. Diese saubere Kopie als lokales Quell-ZIP packen, bevor `install.bat` läuft:

```powershell
Compress-Archive -Path 'C:\CMDRHelper Update Test\*' -DestinationPath 'C:\CMDRHelper-Testpakete\CMDRHelper_v3.2_patched.zip'
& 'C:\CMDRHelper Update Test\install.bat'
Set-Location 'C:\CMDRHelper Update Test'
& .\venv\Scripts\python.exe 'C:\CMDRHelper-Testpakete\local_update_test.py' prepare --source-zip 'C:\CMDRHelper-Testpakete\CMDRHelper_v3.2_patched.zip' --output 'C:\CMDRHelper-Testpakete\lokales-ziel' --next-version 3.2.1
New-Item -ItemType File -Path '.cmdrhelper-update-test' -Force
New-Item -ItemType Directory -Path 'data' -Force
Set-Content -Path 'data\update-sentinel.txt' -Value 'Nicht ersetzen'
Get-FileHash 'data\update-sentinel.txt'
& .\venv\Scripts\python.exe 'C:\CMDRHelper-Testpakete\local_update_test.py' run --install-dir 'C:\CMDRHelper Update Test' --zip 'C:\CMDRHelper-Testpakete\lokales-ziel\CMDRHelper_v3.2.1.zip'
```

`prepare` ändert die Versionsdatei ausschließlich im lokalen Ziel-ZIP,
nicht in eurer gepatchten v3.2-Kopie und nicht im Repository. Die Testkennung
3.2.1 wird nicht veröffentlicht. Der Ausgabeordner muss neu sein.
Die unten beschriebenen Beobachtungen für **Durchlauf B** gelten auch hier.
Bei einer schon installierten Testkopie mit Daten/venv das Quell-ZIP stattdessen
aus einer zweiten frischen, gepatchten Releasekopie bilden.

## Lokale Testpakete erzeugen (Linux-Arbeitskopie)

Der vorhandene Paketbauer verändert weder Git noch die Produktversionsdatei:

```bash
bash create_release.sh
venv/bin/python tools/local_update_test.py prepare \
  --source-zip release/CMDRHelper_v3.2.zip \
  --output /tmp/CMDRHelper-Windows-Updatetest \
  --next-version 3.2.1
```

Der Ausgabeordner muss neu sein. Er enthält das reparierte 3.2-ZIP, ein
3.2.1-Test-ZIP und `local_update_test.py`. Das Testziel unterscheidet sich
vom Quell-ZIP ausschließlich durch `cmdrhelper/version.py`; 3.2.1 ist hier
nur eine lokale Testkennung. Kein GitHub-Release oder Git-Tag wird angelegt.
Diese Anleitung zusätzlich mitnehmen. Beide ZIPs und das Werkzeug auf das
Windows-Testsystem nach `C:\CMDRHelper-Testpakete` kopieren.

## Zweiter realer Windows-Test (PowerShell)

Eine separate, zurücksetzbare Testinstallation verwenden, etwa
`C:\CMDRHelper Update Test`. Keine produktive Installation und keine echte
Benutzer-DB verwenden. Andere CMDRHelper-Instanzen schließen, da die Sperre
auch zwischen verschiedenen Installationsordnern gilt. Normale GUI-Nutzung
kann Testdatenbanken ändern; für den Datenerhaltstest deshalb eine separate
unveränderte Sentinel-Datei verwenden.

**Durchlauf A – alter Updater:** Den alten Stand in diesem Testordner mit
seinem eigenen `install.bat` bereitstellen. Ausgangsversion festhalten:

```powershell
Set-Location 'C:\CMDRHelper Update Test'
& .\venv\Scripts\python.exe -c "from cmdrhelper.version import __version__; print(__version__)"
New-Item -ItemType File -Path '.cmdrhelper-update-test' -Force
New-Item -ItemType Directory -Path 'data' -Force
Set-Content -Path 'data\update-sentinel.txt' -Value 'Nicht ersetzen'
Get-FileHash 'data\update-sentinel.txt'
& .\venv\Scripts\python.exe 'C:\CMDRHelper-Testpakete\local_update_test.py' run --install-dir 'C:\CMDRHelper Update Test' --zip 'C:\CMDRHelper-Testpakete\CMDRHelper_v3.2.zip'
```

Im Programm gegebenenfalls Einstellungen → Update → Jetzt prüfen öffnen,
Update mit Yes bestätigen. Der normale Download liest das lokale ZIP über
`file://` und kopiert es in das übliche temporäre Downloadverzeichnis.
Damit werden GUI, Downloadworker, Helfer, Backup, Installation und Neustart
wirklich benutzt; nur die Release-Metadaten stammen aus dem Testwerkzeug.
GitHub-API und HTTP-Transport werden durch diesen lokalen Test nicht geprüft.

Nach dem alten Ablauf bei Bedarf `start.bat` manuell starten, Version 3.2
prüfen und wieder normal beenden. `backup/update.log` dieses Durchlaufs
separat sichern. Falls der Altstand nicht sicher identifiziert werden kann,
kann Durchlauf B direkt mit dem frisch entpackten reparierten 3.2-ZIP und
dessen `install.bat` in einem neuen Testordner beginnen.

**Durchlauf B – reparierter Updater:** Derselbe Testordner muss jetzt die
reparierte 3.2 enthalten. Die Sentinel-Datei und Markierung bleiben erhalten.

```powershell
Set-Location 'C:\CMDRHelper Update Test'
& .\venv\Scripts\python.exe 'C:\CMDRHelper-Testpakete\local_update_test.py' run --install-dir 'C:\CMDRHelper Update Test' --zip 'C:\CMDRHelper-Testpakete\CMDRHelper_v3.2.1.zip'
```

Update bestätigen. Den heruntergeladen-Hinweis absichtlich mindestens
40 Sekunden offen lassen: Die alte GUI muss weiter reagieren, es darf weder
ein Backup beginnen noch die Doppelstartmeldung erscheinen. Danach OK.
Erwartet: altes Fenster schließt, Backup/Austausch laufen und **genau ein**
3.2.1-Hauptfenster öffnet automatisch. Der externe Helfer beendet sich.
Der Neustart verwendet die normale `main.py`, ohne Test-Metadatenumleitung.

Prüfen und Ergebnisse sichern:

```powershell
Get-Content '.\backup\update.log'
Get-FileHash '.\data\update-sentinel.txt'
& .\venv\Scripts\python.exe -c "from cmdrhelper.version import __version__; print(__version__)"
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*CMDRHelper Update Test*' } | Select-Object ProcessId, ParentProcessId, ExecutablePath, CommandLine
```

Im Log muss die Reihenfolge stehen: Elternprozess beendet → Sperre
übernommen → Backup erfolgreich → Programmdateien installiert → Sperre
freigegeben → genau eine Neustart-PID → erfolgreich abgeschlossen.
Windows-venv-Redirector und Interpreter können zwei Betriebssystemprozesse
für eine GUI ergeben; maßgeblich sind **ein Hauptfenster** und ein GUI-Start
im Anwendungslog, nicht pauschal die Anzahl aller python.exe-Prozesse.
Das Backup muss die vorherige 3.2-Version enthalten; Sentinel-Hash identisch.
Die Benutzer-DB nicht byteweise vor/nach GUI-Start vergleichen: normale
Anwendungsinitialisierung kann sie berechtigt ändern.

Während 3.2.1 läuft, zusätzlich `start.bat` manuell öffnen: genau die normale
Doppelstartmeldung mit echtem Absatz muss erscheinen; die erste Instanz
bleibt offen. Danach alle Testinstanzen normal schließen. Testinstallation
anschließend verwerfen/zurücksetzen, da 3.2.1 keine veröffentlichte Version ist.

Bei Abbruch weder Prozesse gewaltsam beenden noch die Sperrdatei löschen.
Logs, tatsächlichen Startbefehl und Prozessliste sichern. Das Zeitlimit
bricht sicher ab; ein nicht bestätigtes Prozessende darf keinen Austausch
oder falschen Neustart auslösen.

## Automatisierte Prüfung und Dateien

Teststand: **81 gezielte Tests bestanden** unter Linux mit Qt offscreen.
Native Windows-Ausführung steht noch aus.

Gezielte Suite: Windows-Prozess-API mit simulierten Handles/Fehlercodes;
Backup/Austausch/Rollback mit temporären Dateien; simulierte GUI-/Prozessstarts;
Dialogreihenfolge; manueller Doppelstart; alle Sprachen; bestehende Windows-
und Linux-Bootstrap-, Download-, Dialog-, Paket- und v3.2-Dokumentationstests.
Kein echter Systemprozess wird von Unit-Tests beendet, keine Benutzer-DB
verwendet. Linux behält POSIX-Wait, Spawn, Dialogreihenfolge und Neustart nach
Rollback; das neue Handle-/Sperrverfahren läuft ausschließlich unter Windows.

Betroffene Produktdateien: `cmdrhelper/update.py`, neues
`cmdrhelper/windows_update.py`, `cmdrhelper/ui/main_window.py`,
`cmdrhelper/app.py` (Sperrkonfiguration/Prozessdiagnose) sowie die zwölf
`cmdrhelper/i18n/*.py`-Sprachkataloge. Dazu kommen
`tools/local_update_test.py`, `tests/test_windows_update.py`,
`tests/test_local_update_test.py` und diese Anleitung.
