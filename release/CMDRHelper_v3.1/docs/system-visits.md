# Besuchshistorie

`Location`, `FSDJump` und `CarrierJump` schreiben commanderbezogene Besuche mit
SystemAddress, Systemname, Journalzeitpunkt und vorhandenen StarPos-Koordinaten.
Der Delta-Abgleich speichert Besuche in derselben Transaktion wie Standort und
Journaloffset. Archivimport und Backfill verwenden dieselbe Besuchssemantik.
Die bestehende Low-Level-API `store_visit` zum Anlegen expliziter einzelner
historischer Besuche bleibt unverändert; sie verarbeitet keine Journalereignisse.

Ein Besuch beginnt beim Wechsel der SystemAddress. Zusammenhängende Ereignisse
in A ergeben einen Aufenthalt mit dessen erstem Zeitstempel; A → B → A behält
drei Besuche. Die gemeinsame Speicherung sortiert vorhandene und einzufügende
Besuche zeitlich, bevor sie unmittelbar aufeinanderfolgende gleiche Adressen
zusammenführt. Historische Ereignisse müssen als vollständiger Batch übergeben
werden, damit dazwischenliegende Systemwechsel vor der Zusammenführung bekannt
sind. Die Übersicht liest weiterhin direkt `system_visits`, neueste Besuche zuerst.

## Kontrollierter Backfill

Vorschau, ohne Initialisierung oder Migration der DB:

```sh
venv/bin/python tools/backfill_visits.py --database data/cmdrhelper.db --commander-id 1
```

Das Werkzeug prüft die FID aller ausgewählten, identifizierten Journale und liest
nur bereits verarbeitete Bereiche: `last_read_offset`, bei vollständig
archivimportierten Dateien `last_complete_line_offset`. Fehlende, gekürzte,
fehlerhafte oder fremde Journalpräfixe brechen den gesamten Lauf ab. Ungelesene
Dateianhänge bleiben unberührt. `missing` enthält fehlende Aufenthaltsanfänge,
`redundant_ids` die zusammenzuführenden bisherigen Mehrfacheinträge.

Vor Anwendung eine temporäre Test-DB und anschließend eine vollständige Kopie
per SQLite-Backup prüfen. Zwei Läufe auf der Kopie müssen beim zweiten Lauf
jeweils null Ergänzungen und null Bereinigungen ergeben. Außerdem Integrität,
Fremdschlüssel und unveränderte übrige Tabellen prüfen.

```sh
venv/bin/python tools/backfill_visits.py --database data/cmdrhelper.db --commander-id 1 --apply
```

`--apply` sperrt konkurrierende Schreiber, berechnet den Plan erneut und erstellt
vor der Änderung ein konsistentes SQLite-Backup mit Integritätsprüfung unter
`*.pre-visits-<UTC-Zeit>.bak`. Ein vorhandenes Backup wird niemals überschrieben.
Optional lässt sich mit `--backup-path` ein neuer Sicherungspfad bestimmen.
Anschließend werden ausschließlich `system_visits` und dessen SQLite-ID-Zähler
geändert. Fehler rollen die gesamte Änderung zurück. Ein weiterer Lauf ist ein
No-op. Zusätzlich führt der normale Programmstart die versionierte Reparatur
`system_visits` über dieselben Planer und Schreibwege automatisch aus. Der
Startlauf sichert die DB vor schreibenden Datenreparaturen und markiert die
Revision nur nach vollständigem Erfolg. Fehlende oder unlesbare Quellen lassen
den Versuch offen; beim nächsten Start wird erneut geprüft. Erfolgreiche
Revisionen werden nicht erneut vollständig analysiert. Details stehen in
[startup-repairs.md](startup-repairs.md).

## Durchgeführte Reparatur am 08.09.2026

Nach Tests auf temporärer DB und vollständiger SQLite-Kopie wurde Commander 1
(FABER38) in `data/cmdrhelper.db` repariert:

- 409 identifizierte Journalpräfixe, 3.883 Positionsereignisse geprüft.
- 22 fehlende Aufenthaltsanfänge eingefügt, 600 redundante Ereigniszeilen
  zusammengeführt; anschließend 3.274 Besuche statt zuvor 3.852 Zeilen.
- Zweiter Backfill auf Kopie und echter DB: jeweils 0 Ergänzungen,
  0 Bereinigungen.
- `integrity_check` erfolgreich, keine Fremdschlüsselfehler; alle 32 anderen
  Tabellen gegenüber der Sicherung inhaltlich unverändert.
- Sicherung: `data/cmdrhelper.db.pre-visits-20260908T063636306854Z.bak`.

Die tatsächliche Besuchsfolge für das Beispiel lautet (UTC):

| Aufenthaltsbeginn | System |
| --- | --- |
| 05.09.2026 13:29:42 | Prua Hypai RB-D c29-73 |
| 07.09.2026 09:22:53 | Prua Hypai RB-D c29-39 |
| 07.09.2026 09:33:54 | Prua Hypai QB-D c29-69 |
| 07.09.2026 09:48:14 | Prua Hypai TK-C d14-58 |
| 07.09.2026 10:09:08 | Prua Hypai RB-D c29-73 |

Die Location-Ereignisse vom 07.09. um 04:52:22 und 05:16:17 UTC gehören zum
bereits am 05.09. begonnenen Aufenthalt. Das Location-Ereignis um 11:34:53 UTC
gehört zum Rückkehrbesuch von 10:09:08 UTC. Sie erzeugen keine weiteren Besuche.

Teststand der Besuchsreparatur vor der späteren Start-Reparaturintegration
und Dokumentationspflege: 95 gezielte Journal-/Besuchs-/Übersichts- und
Chronik-Regressionstests erfolgreich; Gesamtsuite mit
`QT_QPA_PLATFORM=offscreen venv/bin/python -m unittest discover -s tests`:
555 Tests erfolgreich. `venv/bin/python -m compileall -q cmdrhelper tests tools main.py`
und `git diff --check` ebenfalls erfolgreich. Kein Commit, kein Push.
