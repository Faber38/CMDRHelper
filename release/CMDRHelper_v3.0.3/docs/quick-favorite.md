# Schnell-Favorit

Implementierung vom 07.09.2026. Keine neue Favoritentabelle und kein zweites Overlay.

## Ablauf

`GlobalHotkey.activated` ruft auf dem Qt-GUI-Thread unmittelbar
`save_quick_favorite` auf. `freeze_surface_location` liest wie beim vorhandenen
Standort-Button erneut den Status über den Navigator-Controller und kopiert die
skalaren Commander-, System-, Body- und Positionswerte. Nach dem Einfrieren werden
keine Livewerte mehr für diesen Eintrag gelesen. Ein bekannter beendeter
Journal-Spielkontext wird zusätzlich abgelehnt. Die Navigation selbst bleibt
unverändert. Es gibt keinen Rückgriff auf den letzten erfolgreichen Snapshot,
wenn die aktuelle Statusdatei unvollständig ist oder keine Koordinaten enthält.
Ein unveränderter, weiterhin gültiger Status wird wie bisher nicht allein aufgrund
seines Alters verworfen: Elite schreibt Statusdaten bei Änderungen.

`FavoriteStore.save` übernimmt Validierung, Commandertrennung, IDs, Zeitstempel
und Persistenz. Der vorläufige Name besteht aus übersetztem „Marker“, Datum und
Uhrzeit mit Sekunden; bei Namensgleichheit folgt eine laufende Nummer. Kategorie
ist `other`, Notiz und Bild sind leer. Die bestehende Favoritenansicht wird ohne
`show`, `raise_`, `activateWindow` oder Dialog aktualisiert. Aktive Such-/Typ- und
Kategoriefilter bleiben wirksam.

## Belegung und Plattformen

Die globale Einstellung `quick_favorite/hotkey` enthält eine einzelne
`QKeySequence` im portablen Textformat. Fehlende/leere Einstellung initialisiert
kein natives Backend. Die Einstellungsseite bietet Festlegen, Ändern und Entfernen.
Eine fehlgeschlagene Registrierung erscheint dort als lokalisierte Meldung; bei
fehlgeschlagener Wiederherstellung zusätzlich in der Statusleiste. Eine gespeicherte,
aber derzeit nicht registrierbare Kombination wird nicht als aktiv dargestellt.

Windows verwendet `RegisterHotKey` mit `MOD_NOREPEAT`, verarbeitet ausschließlich
zugehörige `WM_HOTKEY`-Nachrichten per Qt-Native-Event-Filter und gibt Registrierungen
mit `UnregisterHotKey` frei. Dies ist kein Keyboard-Hook.
Siehe [Microsoft: RegisterHotKey](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey).

Linux/X11 verwendet passive `XGrabKey`-Registrierungen auf einer eigenen Verbindung
und `QSocketNotifier` für deren Ereignisse. Caps Lock sowie die tatsächlich
zugeordneten Num-/Scroll-Lock-Masken sind berücksichtigt. Ein temporärer Xlib-
Fehlerhandler mit `XSync` erkennt auch asynchrone Grab-Konflikte. Teilregistrierungen
werden zurückgenommen, fremde X-Verbindungsfehler an den vorherigen Handler gereicht.
Detectable Autorepeat beziehungsweise die Release-/Press-Paarerkennung verhindert
Mehrfachspeicherung durch Gedrückthalten.
Siehe [X.Org: XGrabKey / XUngrabKey](https://xorg.freedesktop.org/archive/X11R6.7.0/doc/XGrabKey.3.html).

Die neue Kombination wird zunächst registriert; erst nach Erfolg wird die alte
freigegeben. Bei Konflikten bleiben aktive Belegung und persistente Einstellung
erhalten. `aboutToQuit` schließt das Backend. Nicht verfügbare Tasten oder
Plattformen werden ausdrücklich abgelehnt, statt eine lokale Ersatzbelegung
vorzutäuschen. Es werden keine Tastendrücke an Elite geschickt.

## Temporäre Anzeige

`NavigationHud.show_message` nutzt dieselbe native Transparenz, Click-through-
Prüfung und Elite-Fenster-/Monitorzuordnung wie das Navigations-HUD. Ein separater
Single-Shot-Timer löscht den Meldungstext nach ungefähr 2000 ms. Die temporäre
Anzeige benötigt weder ein Navigationsziel noch einen eingeschalteten HUD-Schalter.
Der gespeicherte Schalter wird nicht geschrieben. Bei eingeschaltetem HUD stehen
die Meldungszeilen unter den unveränderten Navigationszeilen; nach Ablauf bleiben
nur diese. Bei ausgeschaltetem HUD werden Fenster und Polling wieder abgeschaltet.
Eine erneute Meldung ersetzt die vorherige und startet die Frist neu.

Die vorhandenen Voraussetzungen des Overlays gelten weiterhin, insbesondere
X11 mit Compositor und ein sichtbares aktives Elite-Fenster. Ungültige native
Eingabetransparenz führt wie bisher zu einem verborgenen Overlay.

## Hilfe und Übersetzungen

Alle elf neuen UI-Schlüssel sind in allen zwölf UI-Sprachen vorhanden. Nur der
deutsche Explorer-Hilfemaster wurde um „Schnell-Favorit ohne Maus“ ergänzt und gegen
das implementierte Verhalten geprüft. Die elf anderen Hilfekataloge sind absichtlich
unverändert. Die Strukturtests klammern ausschließlich diesen zur Übersetzung noch
ausstehenden Abschnitt aus; die bisherige Hilfeparität wird weiterhin geprüft.

## Verifikation

Abschließende Ergebnisse: Gesamtsuite 494 Tests bestanden; separat
27 Hotkey-/Schnell-Favoritentests, 29 bestehende Favoritentests, 54 HUD-Tests,
42 Navigator- und 21 Explorer-Tests bestanden. `compileall` und
`git diff --check` erfolgreich. i18n: 948 Schlüssel in zwölf Sprachen vollständig,
Platzhalter passend und keine doppelten Schlüssel.

- Hotkey-/Schnell-Favoritentests: Default ohne Backend, persistente Belegung,
  Einstellungsdialog, Wechsel, Entfernen, Konflikterhalt, Cleanup, native Windows-
  und X11-Verträge, Repeat-Unterdrückung, Keypad und Lock-Masken.
- Favoriten: gültiger Status genau einmal, zu Fuß/SRV/Schiff, Nullkoordinaten und
  Null-IDs, erneutes Lesen beim Tastendruck, Einfrieren vor Speicherung, ungültige
  aktuelle Datei ohne alte Koordinaten, Speicherfehler, Commandertrennung und
  Aktualisierung der offenen Ansicht ohne Fokusanforderung.
- HUD: temporärer Erfolg/Fehler ohne Ziel, HUD aus/an, Fristverlängerung,
  Schalterwechsel während einer Meldung, unveränderte Präferenz, Fokus-/Input-
  Flags sowie Windows-Platzierung und Rückkehr zur Navigation.
- Bestehende Favoriten-, HUD-, Navigator-, Explorer- und Hilferegressionen,
  Gesamtsuite, `compileall`, vollständiger i18n-Check und `git diff --check`.

Realer Linux/X11-Test über `tools/test_quick_favorite_x11.py`:

- Zwei echte X-Verbindungen: Registrierung, erkannter Konflikt, Ersatzbelegung,
  Freigabe und erneute Registrierung nach Cleanup bestanden.
- Reales Desktop-Testfenster mit Compositor: Overlay nativ sichtbar und gezeichnet,
  ShapeInput leer, Vordergrundfenster unverändert, nach etwa zwei Sekunden wieder
  vollständig unsichtbar bei ausgeschaltetem HUD.
- Separater Xephyr-X-Server: Fenster eines anderen Prozesses fokussiert, globaler
  Hotkey genau einmal erkannt; nach Entfernung keine weitere Aktivierung.
  Synthetische Tastendrücke wurden ausschließlich an diesen privaten Server gesendet.

Elite lief während des Tests nicht. Daher ist dies kein realer Elite-Fokustest.
Windows wurde automatisiert auf Linux geprüft; ein neuer realer Windows-Test fand
nicht statt. Die vorhandenen manuellen Änderungen im Release-Verzeichnis wurden
nicht bearbeitet.
