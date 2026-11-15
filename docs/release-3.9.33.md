# CMDRHelper v3.9.33

## SRV-Frachtanzeige

Die SRV-Frachtanzeige verwendet den veröffentlichten MiningInventory-Bestand wie die Mining-Tabelle. Beide Fenster zeigen identische Mengen, auch unabhängig vom aktiven SRV-Kontext. Eine fehlende Kapazität unterdrückt keine vorhandene Fracht. Unbekannte Bestände und bestätigte Leerbestände bleiben unterscheidbar; veraltete Snapshot-Mengen werden nicht als Bestand übernommen.

## Commander-Auswahl für EDSM und Inara

Die Auswahlfelder bleiben kompakt und ihre Dropdown-Pfeile sichtbar. Lange Namen werden im geschlossenen Feld gekürzt dargestellt. Die vollständigen Namen bleiben im Dropdown auswählbar; bei Bedarf kann horizontal gescrollt werden.

## Validierung

Die SRV-Korrektur und die EDSM-/Inara-Auswahl unter KDE wurden vom Benutzer live bestätigt. Vor der Releasevorbereitung waren 79 Cargo-Tests bestanden.

Für dieses Release bestanden unter Linux erneut 79 Cargo-Tests und zusätzlich 428 gezielte Regressionstests für Mining, Schiffsfracht, EDSM/Inara einschließlich Commander-Auswahl, Release-Verpackung, Veröffentlichungsablauf und Update-Bestätigung. Im zusätzlichen Testlauf wurden keine unbehandelten Qt-Callback-Ausnahmen festgestellt. Version, Release-Kurztexte in zwölf Sprachen und unveränderte Release-Skripte wurden geprüft.
