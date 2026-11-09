# Spansh-Stationsverwaltung

## Umfang und bestehende Architektur

Die optionale Einstellung `spansh_stations/enabled` ergänzt lokale
Journalstationen. Standard ist aus. Einschalten zeigt vorhandenes Spansh-Wissen,
löst allein aber keine Netzabfrage aus. Deaktivieren blendet dieses Wissen aus,
ohne Dateien zu löschen; automatische und manuelle Abrufe sind dann gesperrt.

Der vorhandene Ein-Thread-Pool lädt einzelne öffentliche System-Dumps über
`GET https://spansh.co.uk/api/dump/<SystemAddress>`. Es werden keine FID,
Commandernamen, Inventare oder Journalereignisse übertragen. Es gibt keinen
zusätzlichen Worker, periodischen Aktualisierungstimer oder Datenbankdienst.

**Die 90 Tage gelten ausschließlich für den Stationsbestand.** Marktpreise,
Warenbestände, Handelsangebote, EDSM-Körperdaten und deren Cachefristen bleiben
unverändert. Die Stations-Whitelist übernimmt keine Markt-, Modul- oder
Schiffsangebote. Das Vorhandensein des Dienstes „Markt“ ist nur Stationsmetadatum.

## Speicherung und Aktualität

Qt bestimmt `QStandardPaths.AppDataLocation`. Unter Linux ist der Standard:
`~/.local/share/CMDRHelper/CMDRHelper/external/spansh/<id64>.json`
(beziehungsweise unter `$XDG_DATA_HOME`). Die bestehende plattformneutrale
Pfadermittlung bleibt erhalten. Spansh-Stationen werden nicht in SQLite gespeichert.

Schema 1 enthält Quelle, Systemadresse, Systemname, `fetched_at`, Stationsliste
und optional Quelldatenstand/Koordinaten/Teilabdeckung. Die Systemadresse ist die
Journal-`SystemAddress` beziehungsweise Spansh-`id64`, nicht der Systemname.

- Vollständiger erfolgreicher Abruf: `fetched_at` wird erneuert.
- Alter kleiner als 90 Tage: keine automatische Anfrage.
- Alter ab exakt 90 Tagen: Aktualisierung beim nächsten qualifizierten Besuch.
- Fehlender oder nur partieller Bestand: Anfrage beim nächsten qualifizierten Besuch.
- Alte Daten werden sofort weiter angezeigt, auch offline und während eines Abrufs.
- Alter allein löscht keine Daten. Der Arbeitsspeicher-LRU hält acht Systeme;
  sein Verdrängen löscht keine Dateien.

Ein Erfolg ersetzt den vollständigen Spansh-Bestand atomar mittels temporärer
Datei, Flush/fsync und Replace. `source_updated_at` und `station_updated_at`
bleiben die von Spansh gelieferten Zeitpunkte und sind nicht die Cachefrist.
Bestehende gültige Dateien werden ohne Schema-Migration anhand ihres bisherigen
`fetched_at` nach der 90-Tage-Regel bewertet.

## Qualifizierte Systembesuche

FSDJump, CarrierJump und Location qualifizieren sich bei geänderter Adresse,
gleichbleibendem Commander und gültiger Systemidentität. Der Ereigniszeitpunkt
muss nach Beginn der laufenden Gate-Instanz liegen, höchstens fünf Minuten alt
und nicht mehr als fünf Minuten in der Zukunft sein.

Der SourceManager übergibt ausschließlich committed Ereignisse der aktuellen,
identifizierten Sitzung der ausgewählten, aktivierten Quelle. Quellenwechsel,
Commanderwechsel, Archivimport und alte Ereignisse sind keine neuen Livebesuche.
Die Quelle muss bereits dieselbe dargestellte Quelle gewesen sein; ein Wechsel
auf eine andere Quellenprojektion holt keine Ereignisse als Livebesuch nach.

Die Spansh-spezifische Kennzeichnung `_spansh_live_refresh` benötigt keine
Bestätigung einer laufenden Spielinstanz. Der gemeinsame `_watcher_live_refresh`
und seine Verwendung durch andere Funktionen bleiben unverändert. Dadurch geht
ein echter, eindeutig zugeordneter aktueller Journalsprung nicht mehr allein
wegen fehlender Prozessbestätigung verloren.

Nach erfolgreicher Initialisierung gibt es zusätzlich die bestehende einmalige
Prüfung des aktuellen Systems. Catch-up/Import müssen abgeschlossen und Standort
und Commander-Baseline gültig sein. Es gibt keinen Durchlauf historischer Systeme.

## Fehlerpause und serverseitige Wartezeit

Unter `external/spansh/attempts/<id64>.json` liegen jetzt Fehlerzustände mit
`system_address`, `kind` und `retry_not_before` (UTC, mit Zeitzone).

Gewöhnliche Abruf-, Validierungs- oder Speicherfehler:

- alter Stationsbestand und Erfolgszeitpunkt bleiben erhalten;
- automatische Versuche dieses Systems pausieren fünf Minuten;
- andere Systeme bleiben unabhängig;
- die Pause überlebt einen Programmneustart;
- nach Ablauf darf der nächste qualifizierte Besuch erneut versuchen;
- bei Verbleib im System gibt es keinen zusätzlichen zeitgesteuerten Retry.

Manuelle Anfragen dürfen diese lokale Pause umgehen. Ein vollständiger Erfolg
beseitigt den Fehlerzustand. Kann Fehlermetadatum nicht gespeichert werden,
bleibt die Pause wenigstens in der laufenden Instanz wirksam; eine Persistenz
über Neustarts ist bei einem nicht beschreibbaren Datenträger nicht möglich.

Alte Einträge mit `local_date` lösen keine Kalendertagssperre mehr aus. Sie werden
beim nächsten Fehler ersetzt beziehungsweise beim nächsten Erfolg entfernt.
Unbekannte oder beschädigte Versuchseinträge erzeugen keine unbegrenzte Sperre.

HTTP `Retry-After` wird als Sekundenwert oder HTTP-Datum ausgewertet. Eine
konkrete Serverwartezeit gilt auch manuell und über Neustarts. HTTP 429 ohne
brauchbare Dauer wird als Serverbegrenzung ohne bekannte Frist angezeigt;
es wird keine Serverwartezeit erfunden. Eine erneute ausdrückliche Anfrage ist
dann möglich. Diese Metadaten betreffen den Stationsabruf, nicht den Marktcache.

## Antwortvalidierung und leere Systeme

Eine akzeptierte vollständige Antwort mit null berücksichtigten Stationen ist
ein Erfolg und gilt ebenfalls 90 Tage. Das heißt „bei der Prüfung keine
berücksichtigten Stationen geliefert“, nicht „dieses System bleibt garantiert leer“.

Der Dump muss ein passendes System mit gültigem Namen, expliziter Stationsliste
und expliziter Körperliste enthalten; auch jeder enthaltene Körper muss eine
Stationsliste besitzen. Listen dürfen leer sein. Fehlende Listen, falsche
Listentypen, ungültige Stationsidentitäten oder widersprüchliche Datensätze
werden konservativ abgelehnt. Der bisherige vollständige Bestand und sein
`fetched_at` bleiben dann unverändert. Identische Wiederholungen derselben
MarketID werden dedupliziert. Stationen mit gleichem Namen und unterschiedlichen
MarketIDs bleiben getrennt.

Formatabgleich am 08.11.2026 mit zwei begrenzten öffentlichen Dump-Abfragen:
Sol enthält explizite Listen, darunter leere Körper-Stationslisten, und gültige
Stationen ohne `type`. Sagittarius A* enthält ausschließlich Carrier; nach dem
bestehenden Filter ist die Stationsliste leer. Ein fehlender optionaler Stationstyp
ist deshalb zulässig. Diese Beobachtungen ersetzen keinen garantierten externen
Schema-Vertrag: Fehlen künftig verpflichtend ausgewertete Listenfelder, erhält
der konservative Fehlerpfad den bisherigen Bestand statt ihn leer zu ersetzen.
Die Regressionstests verwenden ausschließlich lokale Antworten.

## Zusammenführung, Carrier und Teilabdeckung

MarketID ist die Stationsidentität. Journalwissen hat Vorrang. Explizite
Spansh-Parents können fehlende Körperzuordnungen ergänzen; Namen und Entfernungen
begründen keine Zuordnung. Konflikte mit Journalwissen bleiben gekennzeichnet.
Ein leerer vollständiger Dump entfernt nur bisherigen Spansh-Bestand, nicht
unabhängige Journalbeobachtungen.

Fleet Carrier werden weiterhin über Typ beziehungsweise Carrier-Dienste
herausgefiltert. Sie werden nicht als ortsfeste 90-Tage-Stationen gespeichert.
Die eigene Carrier-Verwaltung aus Journalwissen bleibt unverändert.

Bedarfsgesteuerte MarketID-Lookups, etwa für Rare-Goods-Herkünfte, verwenden
weiterhin `coverage: partial`. Sie ergänzen Identität, gelten aber nicht als
vollständige Prüfung. Beim Ergänzen eines vorhandenen vollständigen Dokuments
ändern sie dessen Dump-Zeitpunkt nicht. Sie erzeugen keine Handelsangebote.
Details: [Commodity-Master](commodity-master.md).

## Manuelle Bedienung und Veröffentlichung

Die vorhandenen Buttons in Explorer und Gesamtansicht verwenden denselben
Cache-/Workerpfad. Sie dürfen auch nach einem erfolgreichen Abruf am selben
Tag erneut abfragen. Es gibt keine Tages-Erfolgssperre mehr.

Eine laufende Anfrage derselben Adresse verhindert Doppelstarts, auch über
Generationswechsel hinweg. Andere Adressen können im bestehenden Pool warten.
Vor Workerstart und vor HTTP werden passende Fristen erneut geprüft. Ein
wartender automatischer Auftrag für ein inzwischen verlassenes System entfällt.
Ein bereits laufendes Ergebnis darf nur den Cache seiner eigenen Adresse ändern.
Generations- und Adressprüfung verhindern, dass es das aktuelle System verfälscht.

Die bestehenden Anzeigen unterscheiden aktuelle Daten, alten/partiellen Bestand,
laufenden Abruf, Fehler sowie konkrete oder zeitlich unbekannte Serverbegrenzung.
Es gibt keinen Countdown-Timer: Zustände werden bei vorhandenen Aktualisierungen
und beim manuellen Klick erneut geprüft. Die Buttons bleiben bei Serverwartezeit
bedienbar, um die Frist ohne zusätzlichen Timer nachprüfen zu können; vor ihrem
Ablauf startet trotzdem kein HTTP-Abruf.

## Gezielte Prüfung

Teststrategie Stufe B: Stationscache, Spansh-Koordinator, Teilabdeckung,
Quellenveröffentlichung, Systemzuordnung, Carrierfilter, Stationsansichten,
Hilfetexte und Übersetzungsschlüssel. Keine vollständige Suite und keine echten
Journalübertragungen. Versionsdatei und Veröffentlichung bleiben unverändert.
