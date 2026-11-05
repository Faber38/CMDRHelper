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

## Strukturierte Warenmengen und Teamfähigkeit

Ergänzende Fakten liegen ohne neue Tabelle oder Migration unter
`mission_details/v1/<FID>/<MissionID>` in `app_meta`. Die Speicherung erfolgt
zusammen mit Missionszeile und Journalcursor in derselben Transaktion.
Gespeichert werden `commodity`, `commodity_symbol`, `required_count`,
`delivered_count`, `collected_count`, `wing` und `depot_update_type`.
Das bestehende `count` wird beim Laden aus der bekannten Gesamtmenge ergänzt.

- `MissionAccepted.Commodity` und `Count` liefern Ware und Bedarf;
  `Wing` wird nur als tatsächlicher boolescher Wert übernommen.
- `CargoDepot` verarbeitet `Collect`, `Deliver` und `WingUpdate`.
  `ItemsDelivered` und `ItemsCollected` sind kumulative Stände und werden
  nicht addiert. `TotalItemsToDeliver` ist der Bedarf; `Count` ist nur die
  einzelne Bewegung. `Progress` wird nicht als Fertigstellungsgrad verwendet.
- Fehlende Felder erhalten bekannte Werte. Negative Mengen, boolesche/string-
  Mengen, Gesamtmenge null oder eine Lieferung über der Gesamtmenge werden
  nicht als neuer Depotstand übernommen. Gesammelte Ware muss nicht größer
  als gelieferte Ware sein (z. B. gekauftes Gold einer Abbaumission).
- Alte Missionszeilen bleiben lesbar. Fehlende strukturierte Angaben bleiben
  unbekannt; weder Name noch Beschreibung oder `progress_text` werden geparst.
  Es gibt keine automatische historische Ergänzung und keinen neuen Replaypfad.
- Spärliche `Missions`-Snapshots bewahren Depotstände und Teamfähigkeit.
  Terminale Einzelereignisse entfernen auch die Zusatzdaten. Die explizite
  Bereinigung berücksichtigt nur Metadaten der tatsächlich entfernten Zeilen.
- FID-Trennung und bestehender Missionsanker gelten unverändert. Ein Teamstand
  wird ausschließlich aus dem Journal dieses Commanders übernommen, ohne
  Zusammenführung fremder Bestände oder Zuschreibung persönlicher Beiträge.

Die bestehende Detailanzeige zeigt Bedarf, geliefert und Restmenge, sofern
bekannt. Vor einem belegten Lieferstand steht dort „Lieferstand unbekannt“.
Ein Fortschrittsbalken wird nicht eingeführt.

Ein kleines gezeichnetes Teamsymbol beim Missionsnamen bedeutet ausschließlich
„teamfähig“, nicht „Mitspieler vorhanden“. Es erscheint nur bei `wing=true`.
Der Hinweis „Am Missionsziel“ verwendet dieselbe geprüfte Treffermenge wie die
bestehende goldene Markierung, unabhängig von deren Blinkphase. Er erscheint
bei Ort und Details; Zielorterkennung und gespeicherter Missionsstatus bleiben
unverändert. Bei Verlust gültiger Positionsinformationen verschwindet er.

Ein belegter vollständiger Depotstand bleibt bis zum terminalen Einzelereignis
in der Liste. Für Warenaufträge der internen Familien `Mission_Delivery…`,
`Mission_Collect…` und `Mission_Mining…` mit bekannter Ware zeigt die Oberfläche
„Lieferung abgeschlossen – Belohnung abholen“. Andere Depotmissionen erhalten
„Lieferung abgeschlossen – Mission prüfen“. Ein allgemeines „Aufgabe erledigt“,
eine Kuriermission, Spende oder ein vorläufiges Encounter-Angebot löst für sich
keinen Belohnungshinweis aus. Der bisherige Abschlussmechanismus bleibt bestehen.

Alle zusätzlichen Texte stehen in den zwölf Anwendungssprachen zur Verfügung.
Missionsfracht-Markierungen in den Handelsansichten, Cargo-Snapshots, Mining,
Carrier, Handelsfilter, Uploads und sicheres Beenden werden nicht verändert.

Direkt über der Missionstabelle erklärt eine kompakte, bei Bedarf umbrechende
Legende die tatsächlich verwendeten Bedeutungen: goldene Zeile = am Missionsziel,
goldene Statusschrift = angenommen, grüne Statusschrift = Ziel erreicht/geändert,
Daten erhalten oder Aufgabe/Lieferung erledigt, Teamsymbol = teamfähig. Sie nutzt
das gleiche Teamsymbol sowie die vorhandenen Dark-/Light-Farben. Auswahl- und
Hoverfarben werden nicht als Status erklärt. Es gibt keine zusätzliche Infobox;
bei ausreichender Breite benötigt die Legende nur eine Textzeile.


## Mögliche Missionsfracht in den Handelsansichten

Die blaue Missionskugel bleibt ausschließlich expliziter `Cargo.Inventory[].MissionID`
vorbehalten. Daneben kennzeichnet eine rosa Kugel mit kleinem Ausrufezeichen
passende, nicht ausdrücklich zugeordnete Schiffsfracht. Beide Symbole können
bei Mischfracht nebeneinander stehen; kompakte Legenden erläutern sie in
„Verkaufen“ und „Markt ansehen“ in allen zwölf Sprachen und beiden Farbschemata.

Der Abgleich verwendet nur `current_ship_inventory` und die bereits geladenen
bestätigten offenen Warenmissionen (ohne vorläufige Angebote). Waren werden über
den Katalog identifiziert, nicht über lokalisierte Missionstitel. Alle Mengen mit
MissionID werden aus dem gemeinsam verfügbaren Bestand ausgeschlossen. Bei
bekanntem Lieferstand wird der Restbedarf berechnet und die bereits genau dieser
Mission zugeordnete Fracht berücksichtigt. Mehrere Missionen derselben Ware teilen
sich einen einzigen Bestand; es erfolgt keine künstliche Reservierung pro Mission.
Unbekannte Lieferstände bleiben unbekannt: Der Tooltip nennt deren angeforderte
Gesamtmenge separat und behauptet keinen Restbedarf oder sicheren Liefererfolg.

Cargo-, Missions-, Commander- und Schiffsänderungen nutzen die bestehenden
Signale. Bei unbestätigtem Bestand verschwindet die rosa Kennzeichnung bis zum
nächsten gültigen Inventar. Reine Kennzeichnungsänderungen aktualisieren in
„Verkaufen“ nur Rollen und Tooltips; Auswahl, Suchergebnisse und laufende Suchen
bleiben erhalten. Tatsächlich geänderte Warenmengen behalten den bisherigen
Suchabbruch. Keine zusätzliche Speicherung, Journal-Scans oder Worker.

Der Silbertest vom 05.11.2026 (MissionID 1070464739) belegt die Annahme gekauften
Silbers für genau diese Mission_Mining. Daraus folgt keine allgemeine Regel zur
Annahme gekaufter Waren bei anderen Abbaumissionen.

Eine frühe Prüfung der geladenen Missionsliste beendet den rosa Abgleich, wenn
keine bestätigte offene Warenmission mit auswertbaren Mengen und Warenart mehr
vorliegt. Dann findet dafür keine zusätzliche Frachtraumvalidierung statt;
vorhandene rosa Symbole werden entfernt. Erst mit einer passenden Mission wird
der vorhandene gültige Bestand geprüft. Die blaue MissionID-Auswertung bleibt
von dieser Bedingung unabhängig. Es kommen keine Timer oder Datenbankabfragen hinzu.
