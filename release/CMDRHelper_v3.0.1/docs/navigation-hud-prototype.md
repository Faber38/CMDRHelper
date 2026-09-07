# Transparentes Navigations-HUD unter X11

Der persistente Schalter **Navigations-HUD** steht links unter **auto einblenden**
als vierte Option nach Wertvolle Körper, BIO-Funde und Frachtraum.
Er steuert ausschließlich das zusätzliche Overlay. Der Planeten-Navigator behält
seine Berechnung, Zielverwaltung, Detailwerte, Geometriespeicherung und den Wechsel
zwischen Planetenkugel (> 380 km) und Perspektivraster (≤ 380 km, 50-km-Skalierung).
Im Navigator gibt es keinen HUD-Testschalter mehr.

Das HUD zeigt drei bestätigte Navigationswerte oben mittig:

- Relative Richtung groß, beispielsweise **2° RECHTS** oder **GERADEAUS**.
- Absoluter Zielkurs darunter kleiner, beispielsweise **ZIELKURS: 017°**.
- Zielentfernung darunter, beispielsweise **ENTFERNUNG: 145,6 km**.

Die Werte stammen direkt aus dem bestehenden Navigationscontroller. Richtung und
Kurs verwenden dessen bisherige Textformatierung; Entfernung wird in Kilometern
mit einer Nachkommastelle angezeigt. Orange Schrift mit dunkler Kontur bleibt vor
hellen und dunklen Spielhintergründen lesbar. Der Hintergrund ist transparent.

Ohne gültigen Snapshot bzw. eindeutige Navigationsrichtung wird das HUD verborgen.
Der Haken bleibt gesetzt: Neue gültige Werte blenden es automatisch wieder ein.
Ausschalten verbirgt es sofort und beeinflusst den Navigator nicht. Bei aktiviertem
HUD läuft der gemeinsame Controller auch nach Schließen des Navigatorfensters weiter.

Es gibt weder Tunnel noch Zielpunkt, Interpolation oder eigene HUD-Navigationslogik.

## Fensterverhalten

Voraussetzungen: Linux, Qt `xcb`, X11-Compositor, `wmctrl`, `xprop` und `xwininfo`.
Das Overlay folgt alle 200 ms der Clientgeometrie des aktiven sichtbaren
Elite-Fensters (`steam_app_359320`, Titel „Elite - Dangerous …“).
Über anderen Anwendungen und bei minimiertem Elite bleibt es verborgen.

- `WA_TranslucentBackground`: transparenter Hintergrund.
- `FramelessWindowHint`, `WindowStaysOnTopHint` und unter X11
  `X11BypassWindowManagerHint`: rahmenlos über Elite, unabhängig von der
  Arbeitsfläche des Helper-Fensters. Native Sichtbarkeit wird geprüft.
- `WindowDoesNotAcceptFocus`, `WA_X11DoNotAcceptFocus`, `NoFocus` und
  `WA_ShowWithoutActivating`: keine Fokusanforderung.
- `WindowTransparentForInput` plus `WA_TransparentForMouseEvents`:
  Klickdurchlässigkeit. Vor dem Anzeigen muss die native X11-ShapeInput-Region
  nachweislich leer sein; sonst wird nicht eingeblendet.

Keine Aufrufe von `activateWindow()`, `setFocus()` oder `raise_()` im HUD.
Qt-Referenzen: [Fensterflags](https://doc.qt.io/qt-6/qt.html),
[Transparenz unter X11](https://doc.qt.io/qt-6/qwidget.html#creating-translucent-windows).

## Probeprogramm

`QT_QPA_PLATFORM=xcb venv/bin/python tools/hud_x11_probe.py --journal-folder PFAD --live-target LAT LON`

Der Prozess verwendet den bestehenden Kompass mit echten Statusdaten und endet
nach 180 Sekunden (`--seconds N` ändert die Dauer). `--window` öffnet zusätzlich
das normale Navigationsfenster. Ohne gültiges Ziel und Statusdaten
bleibt das HUD verborgen. `--capture` speichert bei sichtbarem Overlay Desktop-,
Overlay- und Fensterbilder unter `/tmp/hud-feedback-*.png`.

Das Protokoll enthält den bestätigten Kurs, Heading, relative Richtung, die drei
Textzeilen sowie native Sichtbarkeit, Geometrie, Paint-Zähler und Eingaberegion.
Nur der ausdrückliche Testmodus `--verify-switch` holt Elite zur Vorbereitung in
den Vordergrund, schaltet das Overlay aus und wieder ein und stellt das zuvor
aktive Fenster wieder her. Im normalen HUD erfolgt keine Fokusanforderung.

## Plattformstatus und Windows-Unterbau

- **Linux/X11: real getestet.** Der bestehende X11-Tracker, seine Erkennung,
  Eingaberegion und Geometriebehandlung bleiben unverändert.
- **Windows 11: mit Elite real getestet.** Zusätzlich simulieren die automatisierten
  Tests Win32 unter Linux/Qt offscreen und prüfen API-Verträge und Zustandswechsel.

`navigation_hud.py` wählt unter Windows ausschließlich den separat und verzögert
importierten `navigation_hud_windows.py`-Unterbau. Win32-DLLs werden erst bei dessen
Initialisierung geladen; Linux benötigt keine Windows-Pakete. Zeichnung und
Navigationswerte sind weiterhin gemeinsam. `Win32Api` kapselt die nativen Aufrufe
mit expliziten Zeigerbreiten und kann für Tests vollständig ersetzt werden.

Die Erkennung verwendet `EnumWindows`, Fenster-PID und
`QueryFullProcessImageNameW`: ausschließlich `EliteDangerous64.exe`, unabhängig
vom Fenstertitel. Launcher, fremde Prozesse, Child-/Toolfenster und Fenster mit
Owner werden ignoriert. Bei mehreren Spielfenstern hat das aktive Vorrang.
Wie unter X11 wird nur über dem sichtbaren Spiel im Vordergrund angezeigt.
Minimieren, Schließen und Wechsel zu einer anderen Anwendung verbergen das HUD;
Wiederherstellung wird über den bestehenden 200-ms-Timer erkannt.

`GetClientRect` und `ClientToScreen` liefern den Clientbereich ohne Titelleiste
und Rahmen. Native Abfragen laufen kurzzeitig im DPI-Kontext Per-Monitor V2;
der vorherige Thread-Kontext wird auch bei Fehlern wiederhergestellt. Die globale
DPI-Einstellung der Anwendung wird nicht geändert. Qt-Koordinaten werden relativ
zum passenden Monitorursprung mit dessen Qt-Skalierung berechnet; native
Positionierung übernimmt anschließend die exakten Clientpixel, auch bei
Rundungen oder negativen Bildschirmkoordinaten. Dies gilt für Windowed und
Borderless Window. Ein echtes Spiel im exklusiven Vollbild ist nicht bestätigt.

Die vorhandenen Qt-Transparenz- und No-Focus-Flags werden unter Windows durch
`WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW` ergänzt;
`WS_EX_APPWINDOW` wird entfernt. Qt behält die Verwaltung des transparenten
Backing Stores. Die Stile werden vor dem Anzeigen gesetzt und anschließend
geprüft. Topmost wird einmal pro nativem HUD-Fenster mit `SWP_NOACTIVATE` gesetzt;
Geometrieupdates verwenden zusätzlich `SWP_NOZORDER`, ohne laufendes Hochsetzen.

Fehlende APIs, unsichere Eingabestile, unbekannte Monitorzuordnung oder nicht
bestätigte Geometrie deaktivieren das HUD und erzeugen einen Logeintrag. Der
Navigator und der gespeicherte Haken bleiben unabhängig davon erhalten. Nach einem
solchen Fehler erfolgt ein neuer Versuch erst beim erneuten Einschalten; normale
Sichtbarkeitswechsel bleiben automatisch. Es werden keine Administratorrechte
angefordert, um nicht lesbare fremde Prozesse zu untersuchen.

Automatisierte Prüfung:

```sh
QT_QPA_PLATFORM=offscreen venv/bin/python -m unittest discover -s tests -p 'test_navigation_hud*.py'
QT_QPA_PLATFORM=offscreen venv/bin/python -m unittest discover -s tests -p 'test_planet_navigation.py'
```

Das HUD wurde unter Windows 11 mit Elite im Spiel getestet. Daraus folgt keine
pauschale Bestätigung sämtlicher DPI-, Monitor- und Vollbildkonfigurationen.

Referenzen: [Microsoft: Layered Windows und Hit Testing](https://learn.microsoft.com/en-us/windows/win32/winmsg/window-features),
[Extended Window Styles](https://learn.microsoft.com/en-us/windows/win32/winmsg/extended-window-styles),
[SetWindowPos](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos),
[ClientToScreen](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-clienttoscreen),
[Thread-DPI-Kontext](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setthreaddpiawarenesscontext),
[Prozesspfad](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew),
[Qt: High DPI und Bildschirmgeometrie](https://doc.qt.io/qt-6/highdpi.html).
