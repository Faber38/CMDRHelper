# Live-Kopfgelder unter Missionen

Die Karte zeigt eine lokale, FID-getrennte Momentaufnahme, keinen vollständigen
Ingame-Kontostand und keine Abschusshistorie. Combat Bonds bleiben ausgeschlossen.

## Verarbeitung und Speicherung

`Bounty` addiert alle `Rewards[].Reward` zur jeweiligen `Rewards[].Faction`.
Leere/nicht textuelle Fraktionen werden unter dem internen Schlüssel `""` geführt
und übersetzt als „Unbekannte Fraktion“ angezeigt. `TotalReward` wird validiert;
`SharedWithOthers` und `VictimFaction` verändern die Gutschrift nicht.
`RedeemVoucher` mit Typ `bounty` und `Died` setzen die gesamte Momentaufnahme auf
null. Schiff-/Systemwechsel und `SRVDestroyed` setzen sie nicht zurück.

Die Dateien liegen in `QStandardPaths.AppDataLocation / bounties / <FID>.json`.
Es gibt keine fest codierten Betriebssystempfade und keine DB-Migration.
Schema 1 enthält:

```json
{
  "schema": 1,
  "fid": "FID-EXAMPLE",
  "commander_name": "Example",
  "updated_at": "2026-09-18T14:00:00+00:00",
  "total": 0,
  "factions": {},
  "uncertain": false,
  "from_now": false,
  "last_reset": "manual",
  "last_event": {
    "file": "<current journal path>",
    "offset": 1234,
    "prefix_sha256": "<SHA-256 of journal bytes up to offset>"
  }
}
```

Beträge und Anker werden nach jedem relevanten Ereignis gemeinsam in eine
temporäre Datei desselben Verzeichnisses geschrieben, geflusht, mit `fsync`
gesichert und mit `os.replace` atomar ersetzt. Bei Schreibfehlern werden Betrag
und Cursor nicht bestätigt; der vorhandene Watcher versucht die Verarbeitung
wieder. Andere App-Funktionen werden dadurch nicht blockiert.

## Start und Fortsetzung

Nur das beim Start aktuelle Journal kommt für eine Fortsetzung infrage.
Ein Anker desselben Journals wird durch Bytegrenze und Präfix-Prüfsumme validiert.
Zur Validierung werden frühere Bytes **dieser Datei** gehasht, aber keine alten
Ereignisse erneut verbucht. Anschließend wird ausschließlich der neue Suffix
verarbeitet. Ein abschließender Checkpoint bestätigt auch irrelevante Ereignisse.

Ohne sicheren Anker wird ausschließlich im aktuellen Journal nach dem letzten
`Died` oder `RedeemVoucher(bounty)` des Commanders gesucht. Ab diesem Nullpunkt
wird neu synchronisiert. Gibt es keinen Nullpunkt, bleibt ein vorhandener Bestand
erhalten und wird als möglicherweise lückenhaft markiert. Ohne vorherige JSON
beginnt die Erfassung bei null am aktuellen vollständigen Zeilenende mit dem
Hinweis „Erfassung ab jetzt“.

Ein alter Anker veranlasst **niemals** das Öffnen seiner vorherigen Journaldatei.
Bereits vorhandene ältere Journale werden nicht eingelesen. Laufende Rotation
verwendet Bytecursor; höchstens die aktuelle und unmittelbar vorherige Live-Datei
bleiben für neue Anhänge bekannt. Es gibt keinen zusätzlichen Timer oder Poller:
Die Integration verwendet Änderungsanlässe des bestehenden JournalWatchers.

## Manueller Reset und Fehler

„Zurücksetzen…“ öffnet einen Bestätigungsdialog mit **Abbrechen** als Standard-
und Escape-Aktion. Bei Bestätigung wird nur die aktive FID zurückgesetzt, zusammen
mit dem sicher überprüften vollständigen Ende des bekannten aktuellen Journals.
Noch nicht vom Watcher gelieferte vollständige Ereignisse vor dem Reset sind
somit ebenfalls ausgeschlossen. Ohne sichere Identität/Journalgrenze erfolgt
kein Reset. Elite, Credits, Journale und Datenbank werden nicht verändert.

Ein manueller Reset wird als `last_reset: "manual"` gespeichert. Bei ungültigem
Anker desselben Journals wird vorsichtshalber keine Rekonstruktion von einem
älteren Journal-Nullpunkt gestartet, damit alte Kopfgelder nicht wiederkehren.

Beschädigte JSON wird geloggt und als leer/ungeklärt behandelt. Vor dem nächsten
Schreiben werden ihre ursprünglichen Bytes in einer eindeutigen
`.json.corrupt-<id>`-Datei gesichert. Schlägt die Sicherung fehl, bleibt die
ursprüngliche Datei unangetastet. Der Unsicherheitsstatus bleibt bis zu einem
sicheren Reset bestehen. Ungültige Reward-Summen werden nicht geraten.

## Bewusste Grenzen

Ein Einlösen setzt gemäß diesem vereinfachten Modell auch dann alles auf null,
wenn im Spiel möglicherweise nur ein Teil eingelöst wurde. Lücken über mehrere
Journale werden nicht nachgeholt. `EngineerContribution(Type=Bounty)` bleibt eine
spätere Erweiterung. Es gibt keine Kill-Historie und keine produktive Vorbefüllung.
