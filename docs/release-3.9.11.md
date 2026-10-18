# CMDRHelper v3.9.11

- Windows: automatisches Folgen bei bestätigter Zuordnung von Elite-Prozess, aktueller Journaldatei und Commander-FID; ältere Folgeeinstellungen kompatibel übernehmen.
- Handelsassistent: Empfehlungen verwenden den Marktbeobachter der ausgewählten Journalquelle; kein fremder Stationskontext beim Quellenwechsel.
- PP2-Chronik: alle Details einzeilig mit „ | “, Auslassungszeichen bei Platzmangel und vollständigem Tooltip.
- Modelose Zusatzfenster bleiben dauerhaft im Vordergrund; Hauptfenster und modale Dialoge bleiben unverändert.

Die Windows-Zuordnung verwendet die vorhandene Prozessauswahl mit Windows-
Toolhelp und Restart Manager über Python ctypes. Eine automatische Auswahl
benötigt genau eine Elite-Instanz, deren PID und exakte Prozessstartzeit als
Benutzer der aktuellen Journaldatei bestätigt werden, sowie deren bereits
geprüfte Commander-FID. Unmittelbar vor der Rückgabe der Auswahl wird die
Prozesslage erneut geprüft. Mehrere Prozesse, fehlende Ressourceninformationen,
beendete Prozesse oder unklare FIDs führen nicht zur Umschaltung. Es werden keine
Prozesse beendet oder neu gestartet und keine zusätzlichen Dienste eingerichtet.
Der bestehende Linux-Erkennungspfad bleibt erhalten.

Ohne Spiel bleibt die bisherige Auswahl bestehen. Ein explizites follow_live=false
wird respektiert. Alte Einstellungen ohne follow_live-Eintrag behalten den
automatischen Modus; eine gespeicherte Commander-ID allein gilt nicht als
bewusste Deaktivierung.

Der Handelsassistent erhält den bereits vorhandenen Marktbeobachter der
gewählten Quelle. Ohne Quelle bleibt kein vorheriger Stationskontext aktiv.
Marktimport und Handelsberechnungen bleiben unverändert.

Die PP2-Chronik deaktiviert automatischen Zeilenumbruch. Detailbestandteile
werden mit „ | “ verbunden, lange Texte rechts gekürzt und vollständig im
Tooltip angeboten. Ereigniszuordnung, Merits, Rang, Filter und Sortierung
bleiben unverändert.

Modelose Zusatzfenster ergänzen WindowStaysOnTopHint zu ihren vorhandenen Flags.
Qt-Eigentümerschaft, Datenanbindung und das Schließen beim Programmende bleiben
erhalten; Hauptfenster und modale Dialoge sind ausgenommen.

Prüfgrenzen: Die Windows-Korrektur wurde unter Linux synthetisch geprüft.
Eine native Windows-Bestätigung durch Nanjan steht aus. Falls Windows die Nutzung
der aktuellen Journaldatei nicht nachweisen kann, bleibt die Auswahl unverändert.
Das Always-on-Top-Verhalten gegenüber anderen Programmen unter KDE X11/KWin wurde
nur auf Qt-Ebene offscreen vorgeprüft, nicht praktisch bestätigt.

Das Datenbankschema bleibt bei Version 23. Dieses Korrektur-Release enthält
keine Änderungen an EDSM/Inara, Journalverarbeitung oder Fachberechnungen.
