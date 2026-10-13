# CMDRHelper v3.9.8

- Favoriten und Planeten-Navigation sind als zwei Reiter direkt in die Hauptoberfläche integriert.
- Navigation öffnet eine gemeinsame Hauptseite ohne zusätzliche Favoriten- oder Navigatorfenster.
- Der Schnell-Favorit-Hinweis erscheint ohne eingerichteten Hotkey in Elite-Gelb, blinkt dreimal dezent und erklärt die Einrichtung unter Einstellungen.
- Die integrierte Hilfe beschreibt die neuen Reiter und Bedienwege in allen zwölf Sprachen.

„Navigation“ ist ein normaler Hauptmenüpunkt. Rechts stehen die Reiter
„Favoriten“ und „Planeten-Navigation“ bereit; beim Start ist „Favoriten“ aktiv.
Bestehende Aufrufstellen öffnen den passenden Reiter. Funktionen, gespeicherte
Favoriten, Filter, Einstellungen und Navigationsberechnungen bleiben erhalten.
Bei wenig Platz sind die Inhalte scrollbar. Beide Themes werden unterstützt.

Überschrift und Text des Schnell-Favorit-Hinweises erscheinen in Elite-Gelb
(#FFCC33). Beim Einblenden blinkt der Text dreimal dezent und bleibt danach gelb.
Beim Ausblenden wird die Animation beendet. Der Hinweis erklärt in allen zwölf
Sprachen, dass der Hotkey unter Einstellungen eingerichtet werden kann.
Sichtbarkeitsbedingungen, Hotkey-Erkennung und -Verarbeitung bleiben unverändert.

Die integrierte Hilfe beschreibt Navigation → Favoriten und
Navigation → Planeten-Navigation als Reiter im Hauptbereich. Die bisherigen
Hilfekontexte und die Hilfe-Suche bleiben erhalten.

DB-Schema bleibt **23**, ohne neue Datenmigration. Persönliche Datenbanken und
Einstellungen bleiben beim regulären Update erhalten. Das Release erzwingt
keine vollständige Neuindizierung. Updatefunktion und Startskripte werden
unverändert weiterverwendet.
