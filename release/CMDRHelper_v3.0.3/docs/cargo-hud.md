# Frachtraum im Elite-HUD

Der kleine Schalter **Im Elite-HUD anzeigen** im Frachtraumfenster ist
standardmäßig aus. `cargo_hud/enabled` speichert ihn unabhängig vom
Navigations-HUD und vom automatischen Einblenden des Frachtraumfensters.
Das Schließen oder Ausblenden des Frachtraumfensters beendet das HUD nicht.

## Daten und Fahrzeugwechsel

`ui/cargo_hud.py` stellt ausschließlich bestätigte Daten dar:

- Inhalt und SRV-Kapazität: `AppState.cargo_snapshot` der aktiven Journal-FID.
  Die bestehende SRV-Kapazitätsauswertung einschließlich typabhängiger
  Fallbackwerte bleibt unverändert.
- Schiffsname und aktuelle Schiffskapazität: `AppState.ship_loadout`, erst nach
  Abgleich der ShipID mit dem Cargo-Snapshot. Fehlt der Name, werden vorhandene
  Schiffsbezeichnung bzw. Typ verwendet.
- SRV-Name: `vehicle_name` des Snapshots. Der bereits im Journal erkannte
  `active_srv_type` wird zur Darstellung durch AppState weitergereicht; ein
  inzwischen anderer SRV-Typ verhindert die Anzeige des alten Snapshots.
- `Status.json` bestätigt den aktuellen Fahrzeugmodus. Die
  [Status-Flagdefinitionen](https://github.com/EDCD/EDMarketConnector/blob/main/edmc_data.py)
  unterscheiden Hauptschiff, SRV, Fighter, On-Foot, Taxi und Multicrew.
  Ein explizites gültiges `CargoCapacity` im Status des bestätigten aktiven
  Fahrzeugs hat Vorrang. Der gemeinsame vollständige Dateilesevorgang wurde aus
  `read_status` extrahiert; die planetare Statusvalidierung bleibt unverändert.

Beim Wechsel Schiff → SRV oder zurück wird ein noch zum anderen Fahrzeug
gehörender Snapshot vorübergehend ausgeblendet. Sobald Status und bestätigter
Cargo-Snapshot zusammenpassen, erscheint die Anzeige automatisch wieder.
Es gibt keinen zusätzlichen Inventarcache, keine rekonstruierten Transfers und
keine Umrechnung von Engineering-Materialien in Tonnen. Aufnahme und Abgabe von
Fracht erscheinen über den vorhandenen Cargo-Datenfluss. Namen aus Elite und
Benutzerwerte werden weder übersetzt noch durch fest eingebaute Namen ersetzt.

Ohne bekannte Maximal-Kapazität erscheint nur der bestätigte Inhalt; der Balken
bleibt verborgen. Eine Kapazität von null erzeugt ebenfalls keinen Prozentwert.
Bei positiver Kapazität wird der Füllstand auf 0–100 % begrenzt.
Fehlende, unvollständige oder zum Snapshot veraltete Statusdaten, unpassende
Fahrzeug-/Commander-Identität und nicht unterstützte Fahrzeugkontexte verbergen
die Frachtraumgruppe, ohne den gespeicherten Schalter auszuschalten.

## Gemeinsamer Overlay-Dienst

`NavigationHud` verwaltet drei unabhängig aktive Gruppen: Navigation,
Frachtraum und temporäre Schnellfavoriten-Meldungen. Der Ablauf des
Meldungstimers löscht nur die Meldung. Der bestehende 200-ms-Timer aktualisiert
Geometrie, Sichtbarkeit und Frachtraumdaten auch bei ausgeschaltetem
Navigations-HUD; dessen Navigationscontroller muss dafür nicht gestartet werden.

Die Frachtraumgruppe besteht aus einer konturierten orangefarbenen Textzeile
(16 Pixel) und einem 5 Pixel hohen Balken auf transparentem Hintergrund.
Sie beginnt links oben mit 16 Pixel Sicherheitsabstand, maximal 420 Pixel breit.
Bei gleichzeitigen mittigen Anzeigen wird ihre Breite bei Bedarf verkleinert;
bei sehr schmalen Clientbereichen steht sie darunter links, damit sich die
Gruppen nicht überdecken. Lange Fahrzeugnamen werden gekürzt, die Mengenangabe
bleibt erhalten. Die mittigen Navigations-/Meldungsinhalte bleiben unverändert.

Linux/X11 und Windows verwenden dieselben bisherigen Tracker, Clientgeometrien,
Monitorzuordnungen sowie nativen Click-through-/No-Activate-Prüfungen.
Elite muss sichtbar und im Vordergrund sein. Minimieren, Schließen oder der
Wechsel zu einer anderen Anwendung blendet das Overlay aus; bei Rückkehr wird
es wieder sichtbar. Das HUD sendet keine Eingaben und fordert keinen Fokus an.

## Prüfung dieser Erweiterung

- Automatisierte Frachtraumtests: Einstellungen, aktive Fahrzeuge, Datenwechsel,
  Kapazitäten, unbekannte Typen, Grenzwerte, parallele Gruppen und Darstellung.
- Automatisierte Windows-Tests: bestehender Win32-Unterbau mit FakeApi,
  Eingabestile, No-Activate, Geometrie, Minimieren/Wiederherstellen und Ablauf
  temporärer Meldungen bei weiterhin aktivem Frachtraum-HUD.
- Linux/X11: nativ über einem Testfenster geprüft. Nur die Zielerkennung wurde
  ersetzt; Compositor, native Eingaberegion, Mapping und Geometrie verwenden den
  produktiven Unterbau. Fokus blieb unverändert. Keine Eingaben wurden erzeugt.
- Für diese Erweiterung gab es keinen neuen realen Windows- oder Elite-Spieltest.

Der wiederholbare native Test lautet:

```sh
QT_QPA_PLATFORM=xcb venv/bin/python tools/test_cargo_hud_x11.py
```

Er beendet sich selbst und speichert die überprüften HUD-Ebenen unter
`/tmp/cargo-hud-x11-layer.png` und `/tmp/cargo-hud-x11-combined.png`.
