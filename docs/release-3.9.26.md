# CMDRHelper v3.9.26

- Checkboxen und Radio-Buttons sind auch mit nativen Windows-Qt-Stilen klar erkennbar: gelbe Rahmen im Dark-Mode, blaue im Light-Mode und deutlich sichtbare Auswahlpunkte.
- Mining bewertet Live-Daten und historische Journale einheitlich. Nach einem Rhino-Neustart bleiben ältere Schiffsbestände als zuletzt bekannt gekennzeichnet; eine kompakte Legende erklärt die Bestandsfarben in zwölf Sprachen.
- Beim erfolgreichen Schiffswechsel wird gültige Fracht einschließlich bereits verarbeiteter Carrier-Transfers auf das neue Schiff fortgeschrieben. Neue vollständige Cargo-Snapshots bestätigen den Bestand erneut; unbekannte Bestände bleiben unbekannt.
- Diagnose-ZIPs erfassen Beenden-Phase, offene Hintergrundaufgaben und Marktwriterzustände mit datenschutzgerechten Fehlercodes. Der Export bleibt beim Warten auf das Beenden erreichbar; wiederholte Exporte zeigen einen Neustart-Hinweis.
- Fehlgeschlagene Marktaufträge und abgelaufene Markterfassungen blockieren das Beenden nicht dauerhaft. Laufende Schreibarbeiten werden abgeschlossen; wichtige Einstellungen und Mining-Checkpoints bleiben geschützt.

## Umfang und Bestandsschutz

Ausgangsbasis: veröffentlichter Commit f207f1139f3bc9e8c9ecb2cf348683b4e185ecbc
(v3.9.25), Branch main. Die vorhandenen 30 geänderten und sieben unversionierten
Dateien wurden vollständig übernommen. Datenbankschema bleibt Version 23.
Keine Favoritenkorrektur, insbesondere keine behauptete Behebung von NANJANs
Favoritennamen. Keine Änderungen an EDSM-/Inara-Transfers, Carrier-Buchungsregeln
oder der Architektur der zehn Cargo-Sicherungen je Kontext.

ShipyardSwap übernimmt ausschließlich einen gültigen aktuellen Schiffsbestand
bei passender alter und gültiger neuer Schiff-ID. Der übernommene Bestand wird
als fortgeschrieben markiert, einschließlich 0 t. Alte Snapshots werden nicht
umetikettiert; ein neuer vollständiger Cargo-Snapshot ist wieder bestätigt.

## Praxisergebnisse

Die Windows-11-Auswahlindikatoren wurden vom Benutzer auf dem Testsystem
praktisch bestätigt. Entwicklung und Releaseprüfung erfolgen unter Linux;
die Linux-Tests ersetzen keinen nativen Windows-Test.

Der reale Schiffswechsel mit 128 t Samarium bestätigte die Fortschreibung auf
das neue Schiff. Beim späteren Elite-Neustart lieferte das Journal ein neues
vollständiges Cargo-Inventar mit 128 t; die anschließende grüne Anzeige war eine
neue Bestätigung und keine Aufwertung eines alten Bestands.

## Abschlussprüfung

Die Releaseprüfung wurde auf Wunsch des Auftraggebers auf vorhandene,
codebezogene Entwicklungsnachweise, Metadaten, Paketprüfung und kurze isolierte
Smoke-Tests begrenzt. Seit den Entwicklungsprüfungen gab es keine weiteren
fachlichen Produktänderungen; ergänzt wurden Version, Releasehinweise,
README-Abschnitte und der Release-Metadatentest.

Vorhandene Entwicklungsnachweise: 211 Mining-Tests bestanden, darunter 18 neue
ShipyardSwap-Regressionen für die 14 untersuchten Szenarien sowie Identitäts-,
Quellen- und Statusschutz. Die bereits dokumentierten Windows-Indikatorprüfungen
und die vom Benutzer bestätigten Praxistests bleiben maßgeblich. Die spätere
Beobachtung des Elite-Neustarts bestätigte einen neuen vollständigen Cargo-Nachweis.

Zusätzliche abgeschlossene Releaseprüfungen unter Linux:

- 2.395 Referenzschlüssel in zwölf Sprachen, passende Platzhalter und keine
  doppelten Übersetzungsschlüssel; alle früheren Releaseeinträge bleiben erhalten.
- Xvfb/Openbox bei 1024 × 768: 13 Tests für Auswahlindikatoren und Releasefenster
  bestanden. Zusätzlich alle zwölf Sprachen in beiden Themes auf Fenstergröße
  geprüft; scrollbar dargestellte Releasehinweise passen in die bestehende Ansicht.
- Syntaxprüfung von 622 Python-Dateien und Imports der betroffenen Laufzeitmodule
  bestanden. Synthetische Datenbank: integrity_check OK, keine Fremdschlüsselverletzung,
  Schema unverändert Version 23. git diff --check bestanden.
- Paketierter Programmstart mit synthetischem Journal und separaten Einstellungen
  unter Xvfb/Openbox bei 1280 × 850: Fenster sichtbar, reguläres Beenden erfolgreich.
  Kein produktives Display, keine produktiven Journale und keine echten Uploads.
- Synthetischer Updatepfad 3.9.25 → 3.9.26 mit den vollständigen Release-ZIPs:
  Entpacken, Backup, Kopieren und echte Versionsprüfung bestanden. Synthetische
  Datenbank und Einstellungen blieben byteidentisch; Datenbankintegrität danach OK.
  Prozesswarten, Abhängigkeitsinstallation und Neustart waren kontrolliert ersetzt.
  Das temporäre Downloadverzeichnis lag außerhalb des produktiven release-Ordners.

## Bekannte Testbefunde und Grenzen

Eine zunächst gestartete breite Wiederholungsserie wurde auf ausdrücklichen
Wunsch beendet; sie wird nicht als vollständig bestanden ausgewiesen.
Ein erster Xvfb-Versuch scheiterte an den Socket-Beschränkungen der Sandbox;
die gültigen Xvfb-Läufe erfolgten danach außerhalb der Sandbox auf eigenen Displays.

Bereits mit dem unveränderten veröffentlichten v3.9.25-Stand reproduzierbar sind
Befunde in analysis_view, bounties, cargo_presentation, commodity_picker,
commodity_picker_identity, edsm_ui_status (importierter Popup-Geometrietest),
external_search_lifecycle, favorite_title_delegate und inara_uploader.
Sie betreffen unter anderem unvollständige Testattrappen, Fokus/Geometrie,
Pixelvergleiche und Worker-/Qt-Teardown. Der Inara-Fall scheitert im Test-Cleanup
an einem fehlenden Task-Gate; keine Inara-Produktänderung wurde vorgenommen.
Die bekannten Persistenzbefunde aus v3.9.25 werden ebenfalls nicht als behoben
behauptet. Unterbrochene Tests zählen nicht als Ergebnisse.

Ein konkreter neuer Assertion-Befund war die alte Diagnose-ZIP-Dateiliste in
test_footer_removal: Sie erwartete die neu hinzugefügte exit_diagnostics.json
noch nicht. Nur diese Dateiliste wurde ergänzt; die Datenschutz-Assertions
bleiben erhalten. Der betroffene Test besteht anschließend gezielt.
Keine Favoritenänderung, keine Behauptung einer vollständigen historischen
Testsuitenbereinigung und kein neuer nachgewiesener kritischer Produktfehler.

## Probebuild und Veröffentlichung

Vollständiger Probebuild mit unverändertem create_release.sh. ZIP-Integrität,
bytegenaue Übereinstimmung mit dem Paketverzeichnis und bestehende Ausschlüsse
werden geprüft. Das Paket enthält 481 Dateien, alle zwölf READMEs und diese
Releasebeschreibung; keine Tests, Tools, Datenbanken, Caches oder persönlichen
Dateien. Der Teststarter für Windows bleibt ausschließlich im Quellrepository.

Die Veröffentlichung erfolgt ausschließlich über github.sh nach persönlicher
interaktiver Bestätigung. Der Publisher baut erneut aus dem finalen Commit und
normalisiert ZIP-Zeitstempel. Die finale Größe und SHA-256-Prüfsumme werden mit
dem heruntergeladenen GitHub-Asset verglichen und im Abschlussbericht angegeben;
die Probebuild-Prüfsumme ist deshalb nicht die finale Releaseprüfsumme.
