# CMDRHelper 3.6.2

## Neu

- Kampfbelohnungen unter „Missionen & Belohnungen“: Fraktionsbeträge, Gesamtsumme und bestätigter manueller Reset der lokalen Anzeige.
- Commanderbezogene Live-Persistenz von Combat Bonds, getrennt von Kopfgeldern.

## Verbessert

- Gemeinsamer Live-Journal-Leseweg für Kopfgelder, Kampfbelohnungen und Odyssey mit unabhängigen Bestätigungen.
- Bestandserhalt über Helper-Neustarts und sichere Journalanker gegen Doppelzählung.
- Der Bereich „Missionen“ heißt jetzt „Missionen & Belohnungen“.

## Abgesichert

- Eine Combat-Bond-Einlösung mit eindeutiger Fraktion entfernt deren beobachteten Bestand. Der Einlösungsbetrag dient nur der Diagnose; andere Fraktionen bleiben unverändert.
- Unbekannte Altbestände werden nicht rekonstruiert oder mit der lokalen Momentaufnahme verrechnet.
- Tod entfernt nicht eingelöste beobachtete Combat Bonds der aktuellen FID. Wiederbelebung und SRV-Verlust lösen keinen weiteren Reset aus.
- Erfassungslücken und Schreibfehler bleiben sichtbar; Kopfgeld- und Combat-Bond-Bestände sind unabhängig.

Die Anzeige erfasst lokale Live-Ereignisse ab Erfassungsbeginn und ersetzt keine vollständige Bestandsabfrage im Spiel.
