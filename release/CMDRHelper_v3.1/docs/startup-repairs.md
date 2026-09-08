# Automatische historische Reparaturen nach Updates

Die normale Initialisierung migriert die vorhandene Datenbank automatisch auf
Schema 16. Der Start-Worker führt anschließend vor Live-Abgleich und Archivimport
drei getrennte Reparaturrevisionen aus:

| Feature | Revision | Bestehender Datenweg |
| --- | --- | --- |
| `biology_findings` | 1 | `plan_biology_backfill` und bisheriger BIO-Schreibweg, nur fehlende Funde |
| `system_visits` | 1 | `plan_visits_backfill` / `apply_visit_plan`, fehlende Aufenthalte und redundante Fortsetzungen |
| `mapping_metadata` | 1 | Erweiterter Mapping-Backfill und gemeinsamer `apply_mapping_plan`, nur fehlende Metadaten |

Es gibt keine neue parallele fachliche Reparaturimplementierung. Manuelle
Backfill-Einstiegspunkte bleiben verfügbar und verwenden dieselben Planer bzw.
Schreibwege. Der normale Archivimport wird nicht ersetzt und seine Auswahl
neuer/geänderter Dateien bleibt bestehen.

## Zustände, Transaktionen und Sicherung

`commander_state_repairs.revision` bleibt die zuletzt **erfolgreiche** Revision.
`status`, `attempted_revision`, `last_attempt_at` und `last_error` dokumentieren
Versuche. Die Interpretation für die angeforderte Revision ist:

- `not_run`: noch kein Versuch dieser Revision;
- `complete`: erfolgreich und vollständig abgeschlossen;
- `incomplete`: benötigte historische Quelle oder Mapping-Angabe fehlt;
- `failed`: beispielsweise beschädigtes Journal, Lesefehler oder Backupfehler.

Eine vollständige SQLite-Sicherung wird unmittelbar vor der ersten fachlichen
Datenänderung des Start-Reparaturlaufs erstellt und geprüft. Ein gemeinsamer
Sicherungshelfer wird auch von den manuellen Backfills verwendet. Reparaturen
halten eine SQLite-Schreibsperre; Datenänderung und Erfolgsmarkierung werden in
derselben Transaktion abgeschlossen. Fehler rollen Änderungen der betroffenen
Revision zurück. Bei einem harten Prozessabbruch bleibt die Revision unerledigt.
Ein separat gespeicherter Versuchsmarker (`running`) unterscheidet einen
abgebrochenen Lauf von einer nie gestarteten Revision; ohne abgeschlossenen
Lauf wird er als fehlgeschlagener Versuch behandelt und erneut ausgeführt.
Bereits erfolgreich abgeschlossene andere Revisionen müssen nicht erneut laufen.

Bei fehlenden optionalen Mapping-Angaben können belegte fehlende Metadaten
transaktional ergänzt werden, während die Revision ausdrücklich `incomplete`
bleibt. Es wird weder ein Zeitpunkt noch eine Sondenzahl erfunden.

Erfolgreiche Revisionen prüfen beim nächsten Start nur ihre Markierung. Sie
öffnen keine Journale erneut. Fehlgeschlagene/unvollständige Revisionen werden
beim nächsten Start erneut versucht und nachvollziehbar protokolliert. Der
normale Start wird bei konsistenter DB fortgesetzt, auch wenn der Journalindex
wegen einer unlesbaren historischen Datei nicht vollständig aufgebaut werden
kann oder kein Journalordner verfügbar ist.

## Historische Abdeckung

Die Reparaturen verwenden DB-seitig bekannte Journalbereiche, einschließlich
älterer Importnachweise ohne damalige Byteoffsets. Sie prüfen die FID im Inhalt;
eine alte Importzuordnung allein genügt nicht. Alte reine Menü-/Shutdown-Dateien
ohne Ereignisse dieser drei Reparaturen dürfen ohne Commanderzuordnung als
inhaltlich irrelevant erkannt werden. Fehlende Dateien mit benötigtem Inhalt
werden nicht übersprungen und nicht als erfolgreich geprüft ausgegeben.

Schema 16 bewahrt außerdem `repair_read_offset` und `repair_commander_id` in
`journal_sessions`. Dadurch geht die Information über einen früher gelesenen
Bereich nicht verloren, wenn ein beschädigtes/verkürztes Journal beim nächsten
Indexlauf neu klassifiziert oder dessen normaler Leseoffset zurückgesetzt wird.
Diese Felder verändern nicht den normalen Importoffset. Auch die Migration auf
Schema 16 ist transaktional und nach Abbruch erneut ausführbar.

## Geprüfte Upgrade-Simulationen vom 08.09.2026

Die echte Benutzer-DB wurde nicht verändert. Die Journale wurden für die
Simulation in einen temporären Ordner kopiert und damit für beide Starts
unverändert gehalten. Der normale Start-Worker wurde mit synchron ausgeführtem
Test-Thread und abgefangenen UI-Signalen verwendet.

1. Vollständige Kopie der echten Sicherung
   `cmdrhelper.db.pre-biology-20260907T112201835317Z.bak`:
   Schema 15 → 16, BIO am bekannten Körper 0 → 6, alle drei Revisionen erfolgreich,
   Sicherung vorhanden. Start 2: kompletter SQL-Datenbestand unverändert, kein
   erneuter Aufruf der Reparaturplaner.
2. Vollständige Schema-15-Kopie mit den echten BIO-/Besuchsdaten vor den jeweiligen
   früheren Reparaturen sowie der noch bestehenden Mapping-Lücke:
   alle drei Revisionen erfolgreich; Start 2 ebenfalls vollständig unverändert.

Reale Regressionen in der zweiten Kopie:

- **Prua Hypai RB-D c29-73 AB 2 f:** dauerhaft 6/6 BIO-Funde.
- **07.09.2026:** laufender Aufenthalt in RB-D c29-73 (Beginn 05.09. 13:29:42Z),
  anschließend RB-D c29-39 um 09:22:53Z, QB-D c29-69 um 09:33:54Z,
  TK-C d14-58 um 09:48:14Z und echte Rückkehr nach RB-D c29-73 um 10:09:08Z.
  Location-Fortsetzungen ergeben keinen künstlichen weiteren Aufenthalt.
- **Plio Aip KN-B d13-229 5 d:**
  `mapped_at=2026-09-08T08:12:40Z`, `probes_used=3`, `efficiency_target=4`,
  `self_mapped=1`, `efficient_mapping=1`.
- Insgesamt erhielten in dieser Kopie 1.128 Körper ausschließlich fehlende
  Mapping-Metadaten; die veränderten Spalten waren genau die drei vorgesehenen.

Testartefakte des abschließenden Wiederholungslaufs liegen unter
`/tmp/cmdr-full-upgrade-eoh4vm9x/`, einschließlich der
vor Datenreparatur automatisch erstellten SQLite-Sicherungen.

Teststand der Start-Reparaturimplementierung vor der anschließenden
Dokumentationspflege: 99 gezielte Start-/Persistenz-/Migrationstests bestanden;
vollständige Gesamtsuite mit 629 Tests bestanden (Qt offscreen). Darin enthalten
sind 20 neue Start-Reparaturtests einschließlich fehlender/unlesbarer/beschädigter
Journale, Commandertrennung, Backupfehler, unterbrochener Migration und hartem
Prozessabbruch. `compileall` und `git diff --check` sind ebenfalls erfolgreich.

## Zusage und Grenze

Bei vorhandenen, lesbaren und eindeutig zuordenbaren Journalquellen genügt
**Update installieren → CMDRHelper starten** für diese drei historischen
Reparaturen. Manuelle Skripte, Datenbanklöschung und manueller Neuimport sind
nicht erforderlich. Fehlende oder beschädigte Belege lassen sich technisch
nicht ersetzen; der betreffende Versuch bleibt offen statt einen falschen
Erfolg zu melden. Nach Wiederherstellung der Quellen wird beim nächsten Start
erneut versucht zu reparieren.
