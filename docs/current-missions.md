# Aktueller Missionsbestand in 3.6.1

`commander_missions` speichert bestätigte aktuelle Missionen je
`(commander_id, mission_id)`. Die bestehende Tabelle und Schema-Version 20
bleiben erhalten. Es gibt keine neue Missions- oder Historientabelle.

## Ereignisse

- `MissionAccepted`, `MissionRedirected` und `CargoDepot` speichern offene
  Missionen beziehungsweise ihren Fortschritt.
- `MissionCompleted`, `MissionFailed` und `MissionAbandoned` entfernen nur die
  passende Commander-/MissionID-Zeile. Ein unbekannter Abschluss legt keine
  historische Zeile an. Andere Ereignisverbraucher werden weiterhin bedient.
- Ein gültiger, neuer `Missions`-Snapshot gleicht `Active` ab. Bestehende
  Beschreibung, Belohnung, Ziele, Warenbeschreibung, Fortschritt und nächster
  Schritt werden bei spärlichen Einträgen erhalten.
- `Complete` wird vorsichtig als weiterhin relevanter Bestand mitgeführt.
  Die Liste ist kein Ersatz für `MissionCompleted`. Auch der Anzeigestatus
  „Aufgabe erledigt“ bei vollständiger Depotlieferung ist kein Löschsignal.
- Für `Failed` wird mangels sicherer Gleichsetzung kein neues Löschverhalten
  eingeführt. Bekannte Missionen, die weder in `Active` noch in `Complete`
  stehen, bleiben mit `is_open=0`, `terminal_state=inactive` gespeichert.
  Unbekannte `Failed`-Einträge erzeugen keine Historienzeile.
- Fehlende oder fehlerhafte Snapshotlisten gelten nicht als leerer Bestand.
  Ein Snapshot benötigt eine eindeutig zugeordnete Journalsitzung.

Die Frontier-Dokumentation beschreibt die drei Snapshotlisten, belegt aber
keine für diese Anwendung ausreichend sichere Gleichsetzung mit den
terminalen Einzelereignissen:
[Journal Manual v37, Abschnitt 3.6](https://hosting.zaonce.net/community/journal/v37/Journal_Manual_v37.pdf).

## Reihenfolge und Wiederherstellung

Ein kompakter Anker in `app_meta` unter `mission_state_anchor/<FID>` speichert
den zuletzt übernommenen Missionszeitpunkt samt Journalquelle und Position.
Er wird zusammen mit Missionsänderung, Encounter-Promotion und Delta-Cursor
transaktional geschrieben. Er enthält keine abgeschlossenen MissionIDs und
wächst nicht mit der Missionshistorie.

Der Anker ist erforderlich, weil eine gelöschte Zeile ältere Ereignisse nicht
mehr abweisen kann. Er wird bei bestehenden Daten zunächst aus deren spätestem
Missionszeitpunkt abgeleitet. UTC-Zeitpunkte entscheiden zuerst; innerhalb
derselben Zeit sorgen Journalquelle und Byteposition für eine stabile Ordnung.
Live-Reader und Catch-up verwenden dafür die ursprünglichen Bytepositionen.
Der Fallback für Aufrufer ohne Positionen nutzt Delta-Ende und Ereignisindex.

Ältere Ereignisse dürfen die Missionsprojektion nicht zurücksetzen. Sie werden
für andere Verbraucher weiterhin verarbeitet. Das ist bewusst konservativ:
Ein nachträglich auftauchendes altes Annahmeereignis wird nicht zur Ergänzung
eines schon neueren Bestands benutzt. Ein neuer Snapshot kann fehlende aktuelle
MissionIDs wieder liefern; nicht enthaltene Detailfelder bleiben dabei unbekannt.
Ohne neuen Snapshot bleibt der persistierte Bestand der zuletzt bekannte Stand.

Eine historische Missions-Vollrekonstruktion wird weder beim Start noch über
`repair_commander_state(features=('missions',))` ausgeführt. Reparaturen anderer
Funktionen und Journal-Catch-up bleiben bestehen. Offene Missionen werden beim
Neustart beziehungsweise Commanderwechsel aus der Persistenz geladen.

## Oberfläche und Encounter

Beide Missionsansichten zeigen nur offene Zeilen. Der widersprüchliche globale
Missionsreset wurde aus der aktiven Oberfläche und dem App-State entfernt;
alte Reset-Settings werden nicht mehr ausgewertet. „Journal aktualisieren“
bleibt verfügbar, erzwingt aber keinen neuen Elite-Snapshot.

Encounter-Pending bleibt unverändert unter `pending_mission_offers/<FID>`:
vorläufige Anzeige, 24-Stunden-TTL, eindeutiges Matching über Annahme,
`Active` oder Depot und atomare Überführung ohne Dublette. Ein bestätigter
Encounter folgt anschließend demselben aktuellen Missionslebenszyklus.
Die Kopfgeldimplementierung wird nicht geändert.

## Kontrollierte Altzeilen-Bereinigung

Keine automatische Bereinigung beim Start. Das Prüfwerkzeug öffnet die Quelle
read-only und erstellt zwingend eine neue DB-Kopie. Existierende Ziele werden
abgewiesen, auch wenn Quelle und Ziel auf dieselbe Datei verweisen:

```sh
venv/bin/python -m tools.check_mission_cleanup data/cmdrhelper.db /tmp/mission-copy.db --clean
```

Ohne `--clean` wird nur kopiert und geprüft. Mit `--clean` werden ausschließlich
geschlossene `completed`-, `failed`- und `abandoned`-Zeilen auf der Kopie gelöscht.
Die Funktion `cleanup_terminal_missions` arbeitet commanderbezogen in der
Transaktion des Aufrufers; sie wird nicht von der Anwendung automatisch aufgerufen.

Das Werkzeug prüft Integrität, Fremdschlüssel, Schema-Version, offene Zeilen,
`inactive`, andere Tabellen und sämtliche anderen `app_meta`-Einträge einschließlich
Encounter-Pending. Der notwendige Missionsanker ist von diesem Metadatenvergleich
ausgenommen. Es gibt weder Migration noch VACUUM oder Journal-Neuimport.

Die produktive Datenbank wurde nicht bereinigt. Die Umstellung allein entfernt
keine Altarchive; deren Bereinigung bleibt eine separate, kontrollierte Aktion.
