# Planeten-Navigator: i18n-Prüfbericht

Stand: 2026-09-06. Referenz ist der deutsche Arbeitsbestand, nicht der letzte Commit.

## Ausgangsbestand und exakt aufgeschlüsselte 590 Meldungen

43 `planet_nav.*`-Keys. Deutsch und Englisch vollständig; in fr, it, no, sv, fi, pl, nl, es, tr und el war jeweils nur `planet_nav.target_course` vorhanden.

420 eindeutige fehlende Übersetzungen (42 × 10) plus 170 zusätzliche Meldungen derselben Lücken bei direkt verwendeten Keys (17 × 10) ergeben die 590 Meldungen. Keine weiteren Fehlerkategorien.

| Key | Fehlende Sprachen (Anzahl) | Zusätzliche Verwendungsmeldungen |
|---|---:|---:|
| `planet_nav.active` | 10 | 10 |
| `planet_nav.age` | 10 | 10 |
| `planet_nav.ahead` | 10 | 10 |
| `planet_nav.antipodal` | 10 | 0 |
| `planet_nav.backside` | 10 | 0 |
| `planet_nav.bearing` | 10 | 0 |
| `planet_nav.behind` | 10 | 10 |
| `planet_nav.body` | 10 | 10 |
| `planet_nav.body_name` | 10 | 10 |
| `planet_nav.current_coords` | 10 | 0 |
| `planet_nav.distance` | 10 | 0 |
| `planet_nav.enter_target` | 10 | 10 |
| `planet_nav.heading` | 10 | 0 |
| `planet_nav.hud_active` | 10 | 0 |
| `planet_nav.hud_error` | 10 | 0 |
| `planet_nav.hud_foreground` | 10 | 0 |
| `planet_nav.hud_hidden` | 10 | 0 |
| `planet_nav.hud_native_hidden` | 10 | 0 |
| `planet_nav.hud_no_compositor` | 10 | 0 |
| `planet_nav.hud_not_found` | 10 | 0 |
| `planet_nav.hud_off` | 10 | 0 |
| `planet_nav.hud_outside` | 10 | 0 |
| `planet_nav.hud_test` | 10 | 0 |
| `planet_nav.invalid_target` | 10 | 10 |
| `planet_nav.left` | 10 | 0 |
| `planet_nav.legend` | 10 | 10 |
| `planet_nav.no_status` | 10 | 10 |
| `planet_nav.no_target` | 10 | 0 |
| `planet_nav.pole` | 10 | 0 |
| `planet_nav.relative` | 10 | 0 |
| `planet_nav.right` | 10 | 0 |
| `planet_nav.same_position` | 10 | 0 |
| `planet_nav.schematic` | 10 | 10 |
| `planet_nav.set_target` | 10 | 10 |
| `planet_nav.start` | 10 | 0 |
| `planet_nav.stop` | 10 | 10 |
| `planet_nav.target_body` | 10 | 10 |
| `planet_nav.target_coords` | 10 | 0 |
| `planet_nav.target_course` | 0 | 0 |
| `planet_nav.target_distance` | 10 | 10 |
| `planet_nav.target_name` | 10 | 10 |
| `planet_nav.title` | 10 | 10 |
| `planet_nav.waiting_planetary_position` | 10 | 0 |

## Ergänzungen

Drei zusätzliche Keys für bislang nicht an die Anwendungssprache angebundene Dialogtexte: `planet_nav.latitude`, `planet_nav.longitude`, `planet_nav.cancel`. Keine bestehenden deutschen Referenztexte geändert.

| Sprache | Bestehende Lücken ergänzt | Neue Dialogtexte | Ergänzungen gesamt | planet_nav-Keys danach | i18n-Keys danach |
|---|---:|---:|---:|---:|---:|
| de | 0 | 3 | 3 | 46 | 893 |
| en | 0 | 3 | 3 | 46 | 893 |
| fr | 42 | 3 | 45 | 46 | 893 |
| it | 42 | 3 | 45 | 46 | 893 |
| no | 42 | 3 | 45 | 46 | 893 |
| sv | 42 | 3 | 45 | 46 | 893 |
| fi | 42 | 3 | 45 | 46 | 893 |
| pl | 42 | 3 | 45 | 46 | 893 |
| nl | 42 | 3 | 45 | 46 | 893 |
| es | 42 | 3 | 45 | 46 | 893 |
| tr | 42 | 3 | 45 | 46 | 893 |
| el | 42 | 3 | 45 | 46 | 893 |

456 Einträge ergänzt: 420 bestehende Lücken und 36 neue Dialogübersetzungen. Andere Katalogeinträge unverändert.

## Prüfungen

- `tools/check_i18n.py`: erfolgreich; 893 Keys vollständig in 12 Sprachen, keine Platzhalterabweichungen, keine Duplikate. Hinweis auf dynamische `tr()`-Aufrufe bleibt erwartungsgemäß bestehen.
- Zusätzlicher AST-/Formatvergleich gegen Deutsch: identische vollständige Keymengen; auch Platzhalterhäufigkeit, Format-Spezifikationen und Konvertierungen identisch.
- Alle drei `hud_lines()`-Ausgaben für relative Richtung 2°, Zielkurs 017° und Entfernung 145,6 km in allen zwölf Sprachen gegen sprachspezifische Erwartungswerte geprüft. Zahlenformatierung unverändert: Deutsch verwendet hier ein Komma, übrige Sprachen wie bisher einen Punkt.
- HUD-Entfernung verwendet bereits `navigation_hud.distance`, Sidebar bereits `settings.navigation_hud`; beide Keys sind in allen Sprachen vorhanden. Keine hartcodierten deutschen HUD-Ausgaben im aktiven Python-Code.
- Navigation-/HUD-Tests: 72 erfolgreich.
- Gesamtsuite (`python -m unittest discover -s tests`, Qt offscreen): 394 Tests erfolgreich in 98,114 s.
- `compileall` für cmdrhelper, tests, tools und main.py: erfolgreich.
- `git diff --check`: erfolgreich.

## UI-Stichprobe und Grenzen

Qt-Offscreen-Aufbau in Deutsch, Englisch und Französisch: Kugel, Perspektivraster, aktiver/inaktiver Navigator sowie Zieleingabedialog. Fenstergrößen 360×500, 450×620, 900×1000 und 1400×620 (Qt berücksichtigt die vorhandene Mindestgröße). Labelgrößen, Textbreiten, Umbruchhöhen, Buttonbreiten und Fenstergrenzen geprüft; in diesen regulären Navigationsfällen keine Abschneidungen oder deutschen Textreste in Englisch/Französisch gefunden. Screenshots unter `/tmp/planet-i18n-screenshots/` visuell kontrolliert.

Erweiterte Randfallprüfung: Die bestehende Formularanordnung schneidet im sehr schmalen Fenster lange Sondermeldungen ab, z. B. Deutsch „Gegenpunkt – Peilung nicht eindeutig“. Auch der griechische Zielkurs ist bei 360 px zu breit für seine Wertespalte. Eine uneingeschränkte Bestätigung „keine Abschneidungen“ ist daher nicht möglich. Layout, Geometrie und Navigationslogik wurden gemäß Arbeitsumfang nicht geändert. Keine Live-Prüfung eines Windows-/X11-Spieloverlays; die vorhandenen Overlay-Tests wurden ausgeführt.

Kein Commit erstellt. Vorhandene fremde Arbeitsänderungen wurden beibehalten.
