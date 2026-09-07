# Dauerhafte BIO-Körperfunde

Der Journal-Delta-Abgleich speichert `ScanOrganic` mit `Log`, `Sample` und
`Analyse`/`Analyze` in `biology`. `BodyID` hat Vorrang; fehlt es, wird ein
numerisches `Body` verwendet. Die lokalisierten Namen haben wie beim
Archivimport Vorrang vor den internen Namen.

Der bestehende Schlüssel aus Commander, SystemAddress, BodyID, Genus, Species
und Variant identifiziert den Fund. Scanfortschritt und Zeitstempel sind keine
zusätzlichen Arten. Delta-Import, Speicherhelfer und Archivimport verwenden
denselben SQL-Schreibweg; wiederholte Verarbeitung stuft eine Analyse nicht
zurück. Delta-Import und Journaloffset werden gemeinsam committed.

`commander_unsold_biology` enthält ausschließlich den Verkaufsbestand.
`SellOrganicData` entfernt keine dauerhaften Körperfunde. Beim Wiederbesuch
ergänzt der Explorer gespeicherte BIO-Arten auch dann, wenn die aktuelle
Journaldatei keine oder nur einzelne Arten enthält.

## Fehlende historische Funde nachziehen

Der Backfill ist ein explizites Werkzeug, kein automatischer Startimport.
Er ändert weder Schema noch Journaloffsets, Verkaufsbestände oder vorhandene
BIO-Zeilen. Er ergänzt ausschließlich fehlende Schlüssel in `biology`.

Vorschau (ohne `--apply` wird die DB nur lesend geöffnet):

```bash
venv/bin/python tools/backfill_biology.py \
  --database data/cmdrhelper.db --commander-id 1 \
  --journal '/vollständiger/Pfad/Journal.2026-09-04T134325.01.log' \
  --system-address 20154100423162 --body-id 51
```

`--journal` kann mehrfach angegeben werden. Ohne diese Option werden alle
eindeutig dem angegebenen Commander zugeordneten, bereits gelesenen Journale
geprüft. System- und Body-Filter sind ebenfalls optional. Der Backfill liest
nur den bestätigten Präfix bis zum gespeicherten Leseoffset; bei vollständig
archivierten Dateien bis zum gespeicherten vollständigen Zeilenoffset.
Er prüft die FID im Dateipräfix erneut. Fehlende Dateien, ungültige Zeilen,
unvollständige Präfixe und widersprüchliche Identitäten brechen den Lauf ab.
Es gibt keine Body-Zuordnung anhand eines vermuteten aktuellen Standorts.

Nach Prüfung der Vorschau führt derselbe Aufruf mit `--apply` die Ergänzung
aus. Vor dem ersten Insert legt er mittels SQLite-Backup eine konsistente
Sicherung `cmdrhelper.db.pre-biology-<UTC-Zeit>.bak` an. Ein anderer Pfad kann
mit `--backup-path` angegeben werden; bestehende Dateien werden nie überschrieben.
Während Planung, Sicherung und Ergänzung verhindert eine SQLite-Schreibsperre
konkurrierende DB-Schreibzugriffe. Bei Fehlern wird die Transaktion verworfen.

Die Ausgabe enthält die geprüften Journale, die gefundenen Arten, die fehlenden
Zeilen, die Anzahl eingefügter Zeilen und den Sicherungspfad. Wiederholung
ergänzt null Zeilen. Bereits vorhandene, auch unvollständige BIO-Zeilen werden
von diesem bewusst auf fehlende Funde begrenzten Backfill nicht verändert.
