# CMDRHelper 3.9.24

- Stabile Marktlisten ohne vorübergehendes Leeren bei gleichem Bezugssystem; weniger Filteraktualisierungen und drei exklusive Modi für alle Waren, Bergbaurohstoffe oder Schiffsfracht.
- Sechs frei belegbare Aktionen in einer zentralen, kompakten Tastenkürzelverwaltung mit Konfliktprüfung zum globalen Schnellfavoriten.
- Einheitliches sicheres Beenden über Button, Fensterkreuz und Shortcut: ungespeicherte Einstellungen schützen, wichtige Hintergrundarbeiten abschließen und Mining-Checkpoints übernehmen. Ein verbesserter Wartedialog zeigt den Fortschritt.
- Die technische Fußzeile entfällt. Datenschutzgerechte Fehlergründe bleiben im Diagnose-ZIP, kritische Startfehler sichtbar. Der schwarze Einrückungsbalken in Odyssey ist korrigiert.
- Weniger wiederholte Prozessscans und ein schnellerer Mining-Seitenaufbau durch weniger unnötige Tabellen- und Layoutaktualisierungen.
- Unveränderte Anzeigeeinstellungen werden nicht erneut geschrieben; Mining-Bestände werden mit weniger Kopieraufwand rekonstruiert. Bestandsnachweise und sichere Speicherabschlüsse bleiben erhalten.

## Umfang

Diese Version fasst die abgeschlossenen Änderungen seit 3.9.23 zusammen.
Keine Datenbankmigration; das Datenbankschema bleibt bei 23. Handelsmarkierungen und EDSM-/Inara-Transfer-Rückstau werden durch diese Releasevorbereitung nicht verändert.

## Verhalten und Grenzen

Die sechs lokalen Tastenkürzel öffnen Explorer, Handel, Materialien, PP2 oder
Navigator beziehungsweise beenden CMDRHelper. Die Einstellungen sind frei belegbar;
reservierte Eingabekombinationen und Konflikte mit dem globalen Schnellfavoriten
werden geprüft. Der globale Schnellfavorit behält seinen bisherigen Geltungsbereich.

Die Prozessscan-Optimierung fasst kurze GUI-Abfragefolgen zusammen. Update- und
Migrationsschutz prüfen weiterhin frisch. Beim Mining-Aufbau werden unveränderte
Zellen und unnötige Layoutdurchläufe vermieden. Beim historischen Mining-Replay
werden flache, validierte Mengenwörterbücher unabhängig kopiert; alle relevanten
Ereignisse und Bestandsnachweise werden weiterhin geprüft. Es gibt keinen neuen
Inventarergebnis-Cache. Material- und Odyssey-Replay bleiben unverändert.

Unveränderte Anzeigepräferenzen werden nicht erneut geschrieben. Geänderte
unkritische Präferenzen nutzt QSettings sofort im Prozess und schreibt sie über
die Ereignisschleife. Der sichere reguläre Beenden-Ablauf synchronisiert mit
Fehlerprüfung. Ein sofort gestarteter zweiter Prozess kann vor dieser Speichergrenze
noch den vorherigen Wert sehen; nach einem harten Prozessabbruch kann die letzte
ungeflushte Anzeigeauswahl fehlen. Kritische Nachweise und explizite Speicheraktionen
behalten ihre bisherigen Speichergrenzen. Einzelne echte Einstellungsänderungen
können weiterhin Datenträgerwartezeit verursachen.

Die gemessenen Verbesserungen hängen von Datenumfang, Dateisystem und Oberfläche
ab. Xvfb-Messungen sind keine Geschwindigkeitsgarantie für jeden Desktop.
Der EDSM-/Inara-Transfer-Rückstau und Handelsmarkierungen wurden nicht verändert.

## Release-Abschlussprüfung

Die gezielte Abschlussserie umfasst **1.595 Tests in 109 getrennten Modulläufen**.
105 Module sind erfolgreich; vier Module enthalten die unten einzeln bewerteten
Auffälligkeiten. Vier Offscreen-Skips betreffen zwei optionale Referenzdatenbanken
und zwei X11-Eingabe-/Fenstermanagerfälle. Die beiden X11-Fälle wurden anschließend
unter Xvfb/Openbox erfolgreich geprüft. Keine Assertion wurde abgeschwächt und
kein fehlschlagender Test übersprungen, um einen grünen Lauf zu erzeugen.

Abgedeckt sind Start und Journalimport, Quellen-/Commanderwechsel, Marktlisten und
Warenfilter, Material-/Mining-/Odyssey-Bestände, Cargo/Carrier/Checkpoints,
Tastenkürzel und Konflikte, sicheres Beenden samt laufender Arbeit, Diagnose-ZIP
und Datenschutz, Odyssey-Pixel, bestehende Performance-Caches, Update-Download,
Windows-Update- und Migrationsschutz sowie Paketierung und Publisher-Simulationen.
Die Publisher-Tests arbeiten ausschließlich mit temporären Repositories und
kontrollierten Remote-Antworten; keine Testveröffentlichung.

Zusätzlich bestanden unter **Xvfb :97 mit Openbox bei 1280 × 850** acht Tests für
das Updatefenster in allen zwölf Sprachen und beiden Themes, responsive Shortcut-
und Beenden-Layouts, Odyssey-Pixel und Fenstermanager-Schließen. Ein weiterer
Xvfb-Lauf bestand alle 18 Shortcut-Tests einschließlich des nativen X11-Falls.
Der produktive Desktop wurde nicht benutzt. Journale, Einstellungen und Datenbanken
waren ausschließlich synthetisch/temporär; keine echten EDSM-/Inara-Testuploads.

Die zusätzliche SQLite-Prüfung mit zwei synthetischen Commandern meldete
`integrity_check = ok`, keine Fremdschlüsselverletzungen und korrekt getrennte
Mining-Bestände nach Journaländerung und Commanderwechsel. Datenbankschema 23
und Migrationsimplementierung bleiben unverändert.

Sprachprüfung: 2.382 Referenzschlüssel in zwölf Sprachen, passende Platzhalter,
keine doppelten Schlüssel. Alle vorherigen Übersetzungen und README-Abschnitte
sind unverändert erhalten. Syntaxprüfung von 622 Python-Dateien und Import aller
55 zuvor geänderten/neuen Anwendungsmodule bestanden; `git diff --check` ohne Befund.
Historische, auf eine alte aktuelle Versionsnummer festgelegte Release-Tests werden
nicht auf 3.9.24 umgeschrieben; der neue Release-Test prüft den aktuellen Stand.

### Bekannte und zusätzlich untersuchte Testauffälligkeiten

- **Drei bekannte P1-Assertions:** `test_resolve_is_per_path_and_shared_feed_equals_separate_reader`
  zählt fünf statt zwei Pfadauflösungen. Die beiden Subtests von
  `test_windows_drive_and_unc_comparisons_keep_path_semantics` erhalten
  `snapshot_verified=False` für synthetische Laufwerks-/UNC-Pfade.
  Alle drei wurden auch im unveränderten veröffentlichten 3.9.23-Commit reproduziert.
  Die Pfadauflösungszahl ist eine Performance-Erwartung; die beiden anderen Fälle
  verweigern die Bestätigung statt einen unsicheren Bestand zu bestätigen.
  Kein neuer Datenintegritätsfehler nachgewiesen, aber auch kein Ersatz für einen
  nativen Windows-End-to-End-Test. Die Assertions bleiben unverändert sichtbar.
- **Zwei neu aufgefallene Persistenz-Erwartungen im übernommenen Arbeitsstand:**
  `test_rank_persists_commander_navigation_and_process` und
  `test_sort_persists_navigation_new_view_and_new_process` lesen direkt aus einem
  zweiten Prozess, bevor die Qt-Ereignisschleife einen Flush ausführen kann.
  Sie bestehen in 3.9.23 und scheitern bereits im unveränderten 79-Einträge-Stand
  nach der freigegebenen QSettings-Optimierung. Diese Erwartung entspricht nicht
  mehr dem oben beschriebenen gepufferten Speichern unkritischer Präferenzen.
  Separate Prüfungen bestätigen die richtigen Werte im neuen Prozess nach
  Eventverarbeitung und nach dem geprüften Exit-Sync. Der reguläre MainWindow-Exit
  wird zusätzlich durch die neuen Persistenztests geprüft. Kein Verlust beim
  regulären Beenden nachgewiesen; die ursprünglichen Tests bleiben unverändert.
- **Unvollständiger alter Test-Dummy:**
  `test_initial_commodity_refresh_runs_after_commander_view_resolution` scheitert
  beim Aufräumen an fehlendem `setValue()` in `_SettingsStub`. Im übernommenen
  Arbeitsstand identisch reproduziert. Der reale QSettings-Pfad und der sichere
  Fensterabschluss bestehen die dafür vorgesehenen Tests. Keine Produktänderung
  oder Abschwächung der Assertion für diesen Fixture-Fehler.
- **Weitere bereits dokumentierte Grenzen:** Quellenpanel-Zählungen können bei
  zusätzlichem WAL-Checkpoint beziehungsweise in Gruppenläufen zeitabhängig sein;
  im jetzigen isolierten Modullauf bestand das Panel. Die früher beobachtete
  Qt-Teardown-Meldung zu einem bereits gelöschten Timer trat in dieser Serie nicht
  auf; daraus wird keine allgemeine Behebung behauptet. Optionale persönliche
  Referenzdatenbanken wurden bewusst nicht verwendet. Kein nativer Windows-Lauf,
  keine Prüfung mit produktiven Spielständen und keine Langzeit-Leak-Aussage.

Die gesamte historische Testsuite wird ausdrücklich nicht als fehlerfrei bezeichnet.
Aus den untersuchten Auffälligkeiten ergibt sich kein neuer kritischer
Veröffentlichungsblocker; sie werden vor der interaktiven Releasebestätigung genannt.

## Paketierung und Bestandsschutz

Die bestehende ZIP-Ausschlussliste bleibt unverändert. Der Probebuild und seine
Integritätsprüfung bestehen; 492 ZIP-Einträge enthalten keine Datenbanken,
persönlichen Einstellungen, Logs, Tests, Entwicklungsumgebungen oder Python-Caches.
Die synthetische Rohmessdatei `saved-market-stability-x11.json` wurde byteidentisch
von `docs/` nach `tools/data/` verlegt. Sie bleibt im Quellrepository erhalten,
liegt aber außerhalb des Programm-ZIP. Die Dokumentation verlinkt auf den
versionierten GitHub-Quellstand. Es wurde keine JSON-Sperre umgangen oder gelockert.

Alle 79 übernommenen unveröffentlichten Änderungen sind erhalten. Die
Releasevorbereitung ergänzt ausschließlich Version, zwölfsprachige Metadaten und
READMEs, diese Beschreibung und den versionsbezogenen Test sowie die dokumentierte
Ablagekorrektur der Rohmessdatei. Keine weiteren Funktionen oder Optimierungen.
`github.sh` baut nach regulärer Bestätigung erneut aus dem finalen Commit,
normalisiert das ZIP und prüft das veröffentlichte Asset. Die Probe-ZIP-Prüfsumme
ist deshalb nicht die spätere veröffentlichte Prüfsumme.
