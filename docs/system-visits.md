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

## Reproduzierbare Besuchsregression

Ein neutraler Testablauf A → B → C → D → A ergibt fünf Aufenthalte.
Weitere `Location`-Ereignisse während des ersten oder letzten A-Aufenthalts
sind Fortsetzungen und dürfen keine zusätzlichen Besuche erzeugen.

Die Tests prüfen fehlende Aufenthaltsanfänge, redundante Ereigniszeilen,
Commandertrennung und Wiederholbarkeit. Ein zweiter Backfill darf keine weiteren
Änderungen vornehmen. Integrität, Fremdschlüssel und die übrigen Tabellen müssen
unverändert bleiben. Sicherungen verwenden das Muster
`data/cmdrhelper.db.pre-visits-<UTC-Zeit>.bak`.

Gezielte Prüfung: `tests/test_system_visits.py` und
`tests/test_startup_repairs.py`.
