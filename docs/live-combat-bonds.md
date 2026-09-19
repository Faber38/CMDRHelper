# Live-Kampfbelohnungen unter Missionen

Die Karte zeigt ausschließlich live beobachtete Kampfbelohnungen, keinen
vollständigen Ingame-Kontostand. Keine Abschüsse oder Kampfgebiete werden als
Historie gespeichert. Keine DB-Migration, Archivsuche oder produktive Vorbefüllung.
Die fünf realen Rewards vom 19.09.2026 (237.632 Cr für Explorers of Nabudis)
stehen ausschließlich in isolierten Tests.

## Verarbeitung und Persistenz

`FactionKillBond` addiert den vollständigen ganzzahligen `Reward` zur
`AwardingFaction`. `VictimFaction` und `SharedWithOthers` ändern die Gutschrift
nicht. Fehlende/unbrauchbare Fraktionen werden unter `""` gespeichert und als
„Unbekannte Fraktion“ übersetzt. Ungültige Beträge markieren eine Erfassungslücke.
`CapShipBond`, `Bounty`, `RedeemVoucher(bounty)`, `Resurrect` und
`SRVDestroyed` verändern den Combat-Bond-Bestand nicht. `Died` leert alle
Fraktionsbeträge der aktuellen FID und setzt einen neuen atomaren Journalanker.
Einlösungszweifel werden dabei gelöscht, unabhängig erfasste Lücken bleiben
als Unsicherheit erhalten. Ohne solche Lücken ist der beobachtete Nullstand sicher.

Pfad: `QStandardPaths.AppDataLocation / combat_bonds / <FID>.json`.
Schema 1:

```json
{
  "schema": 1,
  "fid": "FID-EXAMPLE",
  "commander_name": "Example",
  "updated_at": "2026-09-19T14:00:00+00:00",
  "total": 0,
  "factions": {},
  "uncertain": false,
  "from_now": true,
  "last_reset": "",
  "last_event": {
    "file": "<current journal path>",
    "offset": 1234,
    "prefix_sha256": "<SHA-256 of journal bytes up to offset>"
  },
  "redemption_pending": false,
  "last_redemption": null,
  "capture_gap": false,
  "pending_redemptions": []
}
```

Jede Gutschrift/Einlösung und jeder Verlust durch `Died` speichert Betrag und Anker gemeinsam: temporäre Datei
im Zielverzeichnis, Schreiben, flush, fsync, os.replace. Erst danach wird der
Cursor bestätigt und die UI aktualisiert. Schreibfehler behalten den vorherigen
Stand und werden über den bestehenden Watcher erneut versucht. Beschädigte JSON
wird vor dem Überschreiben unter einem eindeutigen `.corrupt-...`-Namen gesichert.
Es gibt keine zusätzlichen Timer, Poller oder DB-Zugriffe.

## Start und Journalzustellung

Ohne JSON beginnt die Erfassung am vollständigen Ende des aktuellen Journals.
Es wird ausdrücklich nicht von einem früheren Tod oder Einlösungsevent aus
rekonstruiert. Ein gültiger Anker desselben aktuellen Journals erlaubt den
Suffix-Catch-up nach Präfixprüfung. Frühere Bytes dieser Datei werden dabei
gehasht, nicht erneut verbucht. Bei ungültigem/anderem Anker bleibt der Betrag
erhalten, wird unsicher markiert und die Erfassung beginnt am aktuellen Ende.
Die im alten Anker genannte Datei wird nie geöffnet.

Der vorhandene Watcher unterstützt mehrere Live-Beobachter. Bounty, Combat Bonds
und der bestehende Odyssey-Sidecar-Beobachter teilen Journalbytes pro Durchlauf;
bereits gelesene Bereiche werden nicht erneut von der Datei gelesen. Unterschiedliche
Cursor können das Nachlesen eines bisher ungelesenen Präfixbereichs erfordern.
Der kurzlebige Cache wird nach jedem Durchlauf verworfen. Dateiveränderungen
während einer gemeinsamen Lesung führen zu einem erneuten Versuch. Die getrennten
Cursor und Schreibbestätigungen verhindern, dass ein Speicherfehler eines
Beobachters den anderen zurücksetzt oder blockiert. Bounty-Regeln bleiben gleich.

Laufende Rotation behält höchstens die aktuelle und vorherige Live-Datei für
neue Anhänge. Nummerierte Teile derselben Sitzung übernehmen die bekannte FID;
andere Sitzungen benötigen Commander/LoadGame. Zustände bleiben pro FID getrennt.

## Einlösung und Diagnose für den Praxistest

`RedeemVoucher(Type=CombatBond)` wird unabhängig von Groß-/Kleinschreibung erkannt.
Der reale Praxistest vom 19.09.2026 bestätigt den einzelnen Fraktionspfad:

```json
{"timestamp":"2026-09-19T14:44:30Z","event":"RedeemVoucher","Type":"CombatBond","Amount":953470,"Faction":"Explorers of Nabudis"}
```

Der Helper kannte 43.684 Cr. Die Ingame-Aktion „ALLE KAMPFBELOHNUNGEN-
BESCHEINIGUNGEN EINLÖSEN“ führte laut Benutzer unmittelbar zur Anzeige
„KEINE KAMPFBELOHNUNGEN ENTDECKT“. Deshalb entfernt ein Event mit eindeutigem,
nichtleerem `Faction` den gesamten beobachteten Bestand dieser Fraktion.
Andere Fraktionen bleiben unverändert; `total` wird neu summiert. `Amount`
ist ausschließlich Diagnose und wird weder verglichen noch abgezogen.
Auch `BrokerPercentage` verändert diese fraktionsbezogene Leerung nicht.
Eine zusätzliche `Factions`-Struktur ist nicht real bestätigt und wird deshalb
nicht geraten: Beträge bleiben dann erhalten, die Einlösung wird als ungeklärt
markiert. Dasselbe gilt bei fehlendem/unbrauchbarem `Faction`.

Schema 1 wird additiv um getrennte Unsicherheitsgründe ergänzt:
`capture_gap` steht für unabhängige Erfassungs-/Integritätslücken;
`pending_redemptions` enthält offene Fraktionszuordnungen, wobei `""` eine
nicht zuordenbare Einlösung bezeichnet. Eine eindeutige Einlösung entfernt nur
einen passenden Fraktionseintrag aus dieser Liste. Andere Fraktionen und nicht
zuordenbare Einlösungen bleiben ungeklärt. `redemption_pending` wird aus der
Liste, `uncertain` aus Liste und `capture_gap` abgeleitet. `Died` leert die Liste,
behält aber `capture_gap`. Ein bestätigter manueller Reset bereinigt beide Gründe.

Ältere JSON ohne diese Gründe wird nur im Speicher konservativ eingeordnet:
Ein altes `uncertain=true` kann eine zusätzliche Lücke nicht ausschließen.
Es erfolgt keine automatische Korrektur des Altbetrags, keine Rücksetzung des
Cursors und keine Wiederholung des gespeicherten Einlösungsevents. Eine bestehende Momentaufnahme wird dabei nicht automatisch verändert. Über
„Zurücksetzen…“ lässt sie sich mit einem bestätigten leeren Ingame-Bestand abgleichen.

`last_redemption` enthält das letzte vollständige CombatBond-Einlösungsevent,
inklusive Type, Amount, Faction/Factions, BrokerPercentage und unbekannter Felder.
Es ist eine einzelne lokale Diagnose, keine wachsende Historie. Es wird bei der
nächsten Einlösung ersetzt und bei manuellem Reset entfernt. Allgemeine Logs
enthalten nur den technischen Erfassungshinweis, Feldanzahl und Verrechnungserfolg,
keine FID, Commandernamen oder Eventinhalte. Für den realen Test vor einem Reset
`last_redemption` in der aktuellen FID-Datei prüfen und den Ingame-Restbestand
vergleichen. Andere reale Eventstrukturen, insbesondere mehrere Fraktionen in
einem Event, müssen separat geprüft werden.

## UI und manueller Reset

Reihenfolge: Aktive Missionen, Kopfgelder, Kampfbelohnungen, Missionsdetails.
Erstnutzung zeigt „Erfassung ab jetzt.“; nach einer gültigen Gutschrift endet
dieser Erstnutzungshinweis. Der allgemeine Hinweis auf ausgeschlossene Altbestände
bleibt immer sichtbar. Gesichert beobachtete 0 zeigt den Leerzustand.
Unsicherheit zeigt „Beobachteter Betrag“ statt „Gesamt“, eine Erklärung und ggf.
„Einlösung erkannt – Bestand prüfen.“ Vorhandene Beträge bleiben sichtbar.

„Zurücksetzen…“ bestätigt ausschließlich die aktuelle FID. Abbrechen ist
Standard- und Escape-Aktion. Der Reset prüft Identität, Datei und Präfix bis zum
vollständigen aktuellen Zeilenende, berücksichtigt also noch nicht zugestellte
Events. Nullbetrag, leere Fraktionen, bereinigter Unsicherheitsstatus und neuer
Anker werden atomar gespeichert. Ohne sichere Grenze wird abgebrochen. Elite,
Journale, Bounties und Datenbank bleiben unverändert.

## Gezielte Prüfung

```sh
PYTHONPATH=tests QT_QPA_PLATFORM=offscreen venv/bin/python -m unittest \
  tests.test_combat_bonds tests.test_bounties \
  tests.test_journal_watcher_retry tests.test_odyssey_sidecars
```

Alle Journaldateien und Bestände dieser Tests liegen in temporären Verzeichnissen.
